# teams_webhook.py  —— 可與 translation_bot.py 併在同一 Flask app

import os, json, re, html
from flask import Flask, request, abort
from bs4 import BeautifulSoup  # pip install beautifulsoup4
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    PushMessageRequest, FlexMessage, FlexBubble, FlexBox, FlexText, FlexButton, URIAction
)

# LINE 基本設定
cfg = Configuration(access_token=os.getenv("LINE_ACCESS_TOKEN"))
line_api = MessagingApi(ApiClient(cfg))
# 清理 TARGET_ID，移除引號和註解
target_id_raw = os.getenv("TARGET_ID", "").strip()
target_id_no_comment = target_id_raw.split('#')[0].strip()  # 移除 # 後的註解
TARGET_ID = target_id_no_comment.strip("'\"")  # 移除前後的引號
VERIFY_TOKEN = os.getenv("FLOW_VERIFY_TOKEN")  # Flow URL ?token=xxx 用以驗證

# 檢查必要的環境變數
if not TARGET_ID:
    raise ValueError("TARGET_ID 環境變數未設定")
if not os.getenv("LINE_ACCESS_TOKEN"):
    raise ValueError("LINE_ACCESS_TOKEN 環境變數未設定")
if not VERIFY_TOKEN:
    raise ValueError("FLOW_VERIFY_TOKEN 環境變數未設定")

app = Flask(__name__)

def extract_meeting_info(payload: dict) -> dict:
    """從 Teams JSON 取會議主題、時間與 Join URL。"""
    # 1. 會議主題／Join URL
    att = payload.get("attachments", [{}])[0]
    title = att.get("name", "Teams 會議")
    join_url = json.loads(att.get("content", "{}")).get("meetingJoinUrl", "")
    # 2. 會議時間 —— 從 HTML 內找 yyyy-mm-dd HH:MM 形式
    raw_html = payload["body"]["content"]
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    m = re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", text)
    time_str = m.group(0) if m else "時間未解析"
    return {"title": title, "time": time_str, "link": join_url}

def build_flex(meeting: dict) -> FlexMessage:
    flex_bubble = FlexBubble(
        body=FlexBox(
            layout="vertical",
            contents=[
                FlexText(text=meeting["title"], weight="bold", size="xl"),
                FlexText(text=f'時間：{meeting["time"]}', size="sm", color="#666666"),
            ],
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[
                FlexButton(
                    style="primary",
                    action=URIAction(uri=meeting["link"], label="加入 Teams 會議")
                )
            ],
        ),
    )
    return FlexMessage(
        alt_text=f'會議通知：{meeting["title"]} {meeting["time"]}',
        contents=flex_bubble,
    )

@app.route("/teamshook", methods=["POST"])
def teamshook():
    # 1. 驗證 token
    if request.args.get("token") != VERIFY_TOKEN:
        abort(401, "invalid token")
    payload = request.get_json(force=True)
    # 2. 只處理 message + meetingReference
    if payload.get("messageType") != "message":
        return "ignored", 204
    if not any(att.get("contentType") == "meetingReference" for att in payload.get("attachments", [])):
        return "ignored", 204
    
    try:
        # 3. 擷取資訊並推播
        meeting = extract_meeting_info(payload)
        print(f"解析的會議資訊: {meeting}")  # Debug: 印出會議資訊
        
        flex_msg = build_flex(meeting)
        print(f"FlexMessage 結構: {flex_msg.to_dict()}")  # Debug: 印出 FlexMessage 結構
        print(f"TARGET_ID: {TARGET_ID}")  # Debug: 印出目標 ID
        
        # 檢查 TARGET_ID 是否有效
        if not TARGET_ID or TARGET_ID.strip() == "":
            raise ValueError("TARGET_ID 是空值")
            
        line_api.push_message(PushMessageRequest(to=TARGET_ID, messages=[flex_msg]))
        print("訊息推播成功")
        return "OK", 200
        
    except Exception as e:
        print(f"錯誤: {str(e)}")
        print(f"錯誤類型: {type(e).__name__}")
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(port=29999, debug=True)
