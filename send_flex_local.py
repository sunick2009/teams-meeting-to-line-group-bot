import os, json, datetime
from pathlib import Path
from dotenv import load_dotenv

# --- LINE v3 SDK ---
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    PushMessageRequest, FlexMessage
)
from linebot.v3.messaging.models import (
    FlexBubble, FlexBox, FlexText, FlexButton, URIAction
)

load_dotenv()  # 讀取 .env

cfg = Configuration(access_token=os.getenv("LINE_ACCESS_TOKEN"))
api = MessagingApi(ApiClient(cfg))

# 會議資料（示範）
meeting = {
    "title":  "團隊週會",
    "time":   datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
    "link":   "https://teams.microsoft.com/l/meetup-join/XXXX"
}

# 使用程式建構 Flex Message 而不是 JSON
flex_bubble = FlexBubble(
    body=FlexBox(
        layout="vertical",
        contents=[
            FlexText(text=meeting["title"], weight="bold", size="xl"),
            FlexText(text=f'時間：{meeting["time"]}', size="sm", color="#666666")
        ]
    ),
    footer=FlexBox(
        layout="vertical",
        contents=[
            FlexButton(
                style="primary",
                action=URIAction(uri=meeting["link"], label="加入 Teams 會議")
            )
        ]
    )
)

# 建立 FlexMessage
flex_msg = FlexMessage(
    alt_text=f'會議通知：{meeting["title"]} {meeting["time"]}',
    contents=flex_bubble
)

# 組裝 PushMessageRequest 並送出
target_id = os.getenv("TARGET_ID")
print(f"🔍 原始 TARGET_ID: {target_id}")

# 清理 TARGET_ID，移除註解部分
if target_id and '#' in target_id:
    target_id = target_id.split('#')[0].strip()
    print(f"🔍 清理後 TARGET_ID: {target_id}")

req = PushMessageRequest(
    to=target_id,
    messages=[flex_msg]
)
api.push_message(req)
print("✅ 已推送 Flex Message（v3 SDK）")
