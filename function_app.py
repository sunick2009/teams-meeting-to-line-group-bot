# function_app_unified.py - 整合版：Teams Webhook + Translation Bot for Azure Functions
# 將 app_unified.py 和 function_app.py 完全整合，確保 logging 正確發送到 Application Insights

import azure.functions as func
import logging
import json
import traceback
from datetime import datetime
import uuid
import base64
import hashlib
import hmac
import os
import re
import sys
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    FlexMessage,
    FlexBubble,
    FlexBox,
    FlexText,
    FlexButton,
    URIAction,
    TextMessage,
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, TextMessageContent

try:
    from openai import OpenAI
except ImportError as exc:
    raise ImportError(
        "The 'openai' package is required. Add it to requirements.txt and install via pip."
    ) from exc

# 創建 Azure Functions 應用程式
app = func.FunctionApp()

# 設定日誌級別 - 這會自動整合到 Application Insights
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class EnvironmentConfig:
    """統一管理所有環境變數的配置類"""
    
    def __init__(self):
        logging.info("開始初始化環境變數配置...")
        
        try:
            self.line_access_token = self._get_required_env("LINE_ACCESS_TOKEN")
            self.line_channel_secret = self._get_required_env("LINE_CHANNEL_SECRET")
            self.target_id = self._clean_target_id()
            self.verify_token = self._get_required_env("FLOW_VERIFY_TOKEN")
            self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
            self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
            
            logging.info("環境變數配置初始化完成")
        except Exception as e:
            logging.error(f"環境變數配置失敗: {e}")
            raise
        
    def _get_required_env(self, key: str) -> str:
        """取得必要的環境變數，如果不存在則拋出錯誤"""
        value = os.getenv(key)
        logging.info(f"檢查環境變數 {key}: {'已設定' if value else '未設定'}")
        if not value:
            raise ValueError(f"必要的環境變數 {key} 未設定或為空值")
        return value
    
    def _clean_target_id(self) -> str:
        """清理 TARGET_ID，移除引號和註解"""
        target_id_raw = os.getenv("TARGET_ID", "").strip()
        target_id_no_comment = target_id_raw.split('#')[0].strip()
        target_id = target_id_no_comment.strip("'\"")
        
        if not target_id:
            raise ValueError("TARGET_ID 環境變數未設定或為空值")
        return target_id


class TeamsWebhookHandler:
    """處理 Teams Webhook 的類別"""
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.line_config = Configuration(access_token=config.line_access_token)
        self.line_api = MessagingApi(ApiClient(self.line_config))
    
    def extract_meeting_info(self, payload: dict) -> dict:
        """從 Teams JSON 取會議主題、時間與 Join URL"""
        try:
            # 1. 會議主題／Join URL
            att = payload.get("attachments", [{}])[0]
            title = att.get("name", "Teams 會議")
            join_url = json.loads(att.get("content", "{}")).get("meetingJoinUrl", "")
            
            # 2. 會議時間 —— 從 HTML 內找 yyyy-mm-dd HH:MM 形式
            raw_html = payload.get("body", {}).get("content", "")
            soup = BeautifulSoup(raw_html, "html.parser")
            text = soup.get_text(" ", strip=True)
            m = re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", text)
            time_str = m.group(0) if m else "時間未解析"
            
            return {"title": title, "time": time_str, "link": join_url}
        except Exception as e:
            logging.error(f"解析會議資訊時發生錯誤: {e}")
            return {"title": "Teams 會議", "time": "時間未解析", "link": ""}
    
    def build_flex_message(self, meeting: dict) -> FlexMessage:
        """建立 Flex Message"""
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
                ] if meeting["link"] else [],
            ),
        )
        return FlexMessage(
            alt_text=f'會議通知：{meeting["title"]} {meeting["time"]}',
            contents=flex_bubble,
        )
    
    def handle_webhook(self, payload: dict, request_id: str) -> tuple:
        """處理 Teams Webhook"""
        try:
            logging.info(f"[{request_id}] 開始處理 Teams webhook payload")
            
            # 1. 只處理 message + meetingReference
            if payload.get("messageType") != "message":
                logging.info(f"[{request_id}] 忽略非訊息類型: {payload.get('messageType')}")
                return "ignored - not a message", 204
                
            if not any(att.get("contentType") == "meetingReference" 
                      for att in payload.get("attachments", [])):
                logging.info(f"[{request_id}] 忽略非會議參考的訊息")
                return "ignored - no meeting reference", 204
            
            # 2. 擷取資訊並推播
            meeting = self.extract_meeting_info(payload)
            logging.info(f"[{request_id}] 解析的會議資訊: {meeting}")
            
            flex_msg = self.build_flex_message(meeting)
            logging.info(f"[{request_id}] 推播目標 ID: {self.config.target_id}")
            
            self.line_api.push_message(
                PushMessageRequest(to=self.config.target_id, messages=[flex_msg])
            )
            logging.info(f"[{request_id}] Teams 會議通知推播成功")
            return "OK", 200
            
        except Exception as e:
            logging.error(f"[{request_id}] Teams Webhook 處理錯誤: {str(e)}")
            logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
            return f"Error: {str(e)}", 500


class TranslationBotHandler:
    """處理翻譯 Bot 的類別"""
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.line_config = Configuration(access_token=config.line_access_token)
        self.parser = WebhookParser(config.line_channel_secret)
        self.openai_client = OpenAI(api_key=config.openai_api_key)
    
    def is_chinese(self, text: str) -> bool:
        """判斷文字是否包含中文字元"""
        for char in text:
            code = ord(char)
            if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
                return True
        return False
    
    def translate_message(self, message_text: str, request_id: str) -> str:
        """翻譯訊息"""
        if self.is_chinese(message_text):
            system_prompt = (
                "You are a professional translator. Translate the provided text from "
                "Traditional Chinese into natural, fluent English. Preserve names and "
                "technical terms. Return only the translation without additional commentary."
            )
            logging.info(f"[{request_id}] 翻譯方向: 繁體中文 -> 英文")
        else:
            system_prompt = (
                "You are a professional translator. Translate the provided text from "
                "English into natural, fluent Traditional Chinese. Preserve names and "
                "technical terms. Return only the translation without additional commentary."
            )
            logging.info(f"[{request_id}] 翻譯方向: 英文 -> 繁體中文")

        try:
            logging.info(f"[{request_id}] 開始 OpenAI 翻譯請求")
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_text},
                ],
                temperature=0.0,
            )
            result = response.choices[0].message.content.strip()
            logging.info(f"[{request_id}] 翻譯完成，長度: {len(result)}")
            return result
        except Exception as exc:
            logging.error(f"[{request_id}] OpenAI 翻譯錯誤: {exc}")
            return "發生錯誤，無法翻譯此訊息。 (An error has occurred; this message cannot be translated.)"
    
    def handle_events(self, events: List, request_id: str) -> None:
        """處理 LINE Bot 事件"""
        for i, event in enumerate(events):
            logging.info(f"[{request_id}] 處理事件 {i+1}/{len(events)}: {type(event).__name__}")
            
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                logging.info(f"[{request_id}] 收到文字訊息: {event.message.text[:50]}...")
                
                translation = self.translate_message(event.message.text, request_id)
                
                with ApiClient(self.line_config) as api_client:
                    messaging_api = MessagingApi(api_client)
                    messaging_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=translation)],
                        )
                    )
                    logging.info(f"[{request_id}] 翻譯回覆發送成功")
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """驗證 LINE 簽章"""
        hash_bytes = hmac.new(
            self.config.line_channel_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).digest()
        computed_signature = base64.b64encode(hash_bytes).decode()
        return signature == computed_signature


# 初始化配置（全域）
config = None
teams_handler = None
translation_handler = None

try:
    logging.info("開始初始化全域配置...")
    config = EnvironmentConfig()
    teams_handler = TeamsWebhookHandler(config)
    translation_handler = TranslationBotHandler(config)
    logging.info("全域配置初始化成功")
except ValueError as e:
    logging.error(f"環境變數配置錯誤: {e}")
    config = None
    teams_handler = None
    translation_handler = None
except Exception as e:
    logging.error(f"初始化過程中發生未預期錯誤: {e}")
    logging.error(f"錯誤堆疊: {traceback.format_exc()}")
    config = None
    teams_handler = None
    translation_handler = None


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """健康檢查端點"""
    request_id = str(uuid.uuid4())
    
    try:
        logging.info(f"[{request_id}] 健康檢查請求")
        
        # 診斷模式：檢查環境變數
        env_status = {}
        required_vars = ["LINE_ACCESS_TOKEN", "LINE_CHANNEL_SECRET", "TARGET_ID", "FLOW_VERIFY_TOKEN", "OPENAI_API_KEY"]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # 檢查是否為預設佔位符
                is_placeholder = value.startswith("你的_") or value == "YOUR_" + var
                env_status[var] = "佔位符" if is_placeholder else "已設定"
            else:
                env_status[var] = "未設定"
        
        health_data = {
            "status": "healthy" if config else "configuration_error",
            "service": "unified-bot",
            "timestamp": datetime.utcnow().isoformat(),
            "environment_variables": env_status,
            "config_initialized": config is not None,
            "handlers_initialized": {
                "teams_handler": teams_handler is not None,
                "translation_handler": translation_handler is not None
            },
            "request_id": request_id,
            "version": "unified-1.0.0"
        }
        
        logging.info(f"[{request_id}] 健康檢查完成: {health_data['status']}")
        
        return func.HttpResponse(
            json.dumps(health_data, ensure_ascii=False, indent=2),
            status_code=200,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    except Exception as e:
        logging.error(f"[{request_id}] 健康檢查失敗: {e}")
        logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
        return func.HttpResponse(
            json.dumps({
                "error": "Health check failed",
                "details": str(e),
                "request_id": request_id
            }, ensure_ascii=False),
            status_code=500,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


@app.route(route="teamshook", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def teams_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Teams Webhook 端點"""
    request_id = str(uuid.uuid4())
    
    try:
        logging.info(f"[{request_id}] 開始處理 Teams webhook...")
        
        if not config:
            logging.error(f"[{request_id}] 配置未初始化，檢查環境變數")
            return func.HttpResponse(
                json.dumps({
                    "error": "Configuration error", 
                    "message": "Please check environment variables in Azure Function App settings",
                    "request_id": request_id
                }, ensure_ascii=False),
                status_code=500,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 驗證 token
        token = req.params.get("token")
        logging.info(f"[{request_id}] 收到 token: {token[:8]}..." if token else f"[{request_id}] 未收到 token")
        
        if not token:
            logging.warning(f"[{request_id}] Token 參數遺失")
            return func.HttpResponse(
                json.dumps({"error": "Missing token parameter", "request_id": request_id}, ensure_ascii=False),
                status_code=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        if token != config.verify_token:
            logging.warning(f"[{request_id}] Token 驗證失敗: 期望 {config.verify_token[:8]}..., 收到 {token[:8]}...")
            return func.HttpResponse(
                json.dumps({"error": "Invalid token", "request_id": request_id}, ensure_ascii=False),
                status_code=401,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 解析請求內容
        try:
            payload = req.get_json()
            logging.info(f"[{request_id}] 收到 payload 大小: {len(str(payload))} 字元")
            # 不要記錄完整的 payload，太大會影響效能
        except Exception as e:
            logging.error(f"[{request_id}] 無法解析 JSON payload: {e}")
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON payload", "details": str(e), "request_id": request_id}, ensure_ascii=False),
                status_code=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 處理 webhook
        logging.info(f"[{request_id}] 調用 teams_handler.handle_webhook...")
        result = teams_handler.handle_webhook(payload, request_id)
        logging.info(f"[{request_id}] Teams webhook 處理完成: {result}")
        
        return func.HttpResponse(
            "OK", 
            status_code=200,
            headers={"Content-Type": "text/plain; charset=utf-8"}
        )
        
    except Exception as e:
        logging.error(f"[{request_id}] Teams webhook 處理錯誤: {e}")
        logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
        return func.HttpResponse(
            json.dumps({
                "error": "Teams webhook processing failed",
                "details": str(e),
                "request_id": request_id
            }, ensure_ascii=False),
            status_code=500,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


@app.route(route="callback", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def line_callback(req: func.HttpRequest) -> func.HttpResponse:
    """LINE Bot Callback 端點"""
    request_id = str(uuid.uuid4())
    
    try:
        logging.info(f"[{request_id}] 開始處理 LINE callback...")
        
        if not config:
            logging.error(f"[{request_id}] 配置未初始化，檢查環境變數")
            return func.HttpResponse(
                json.dumps({
                    "error": "Configuration error", 
                    "message": "Please check environment variables in Azure Function App settings",
                    "request_id": request_id
                }, ensure_ascii=False),
                status_code=500,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 獲取簽章和內容
        signature = req.headers.get("X-Line-Signature", "")
        logging.info(f"[{request_id}] 收到簽章: {signature[:16]}..." if signature else f"[{request_id}] 未收到簽章")
        
        try:
            body = req.get_body().decode('utf-8')
            logging.info(f"[{request_id}] 收到內容大小: {len(body)} 字元")
        except Exception as e:
            logging.error(f"[{request_id}] 無法讀取請求內容: {e}")
            return func.HttpResponse(
                json.dumps({"error": "Cannot read request body", "details": str(e), "request_id": request_id}, ensure_ascii=False),
                status_code=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 驗證簽章
        if not signature:
            logging.warning(f"[{request_id}] 遺失 X-Line-Signature 標頭")
            return func.HttpResponse(
                json.dumps({"error": "Missing X-Line-Signature header", "request_id": request_id}, ensure_ascii=False),
                status_code=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        if not translation_handler.verify_signature(body, signature):
            logging.warning(f"[{request_id}] LINE 簽章驗證失敗")
            return func.HttpResponse(
                json.dumps({"error": "Invalid signature", "request_id": request_id}, ensure_ascii=False),
                status_code=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 解析事件
        try:
            events = translation_handler.parser.parse(body, signature)
            logging.info(f"[{request_id}] 解析到 {len(events)} 個事件")
            
            translation_handler.handle_events(events, request_id)
            logging.info(f"[{request_id}] LINE callback 處理完成")
            
            return func.HttpResponse(
                "OK", 
                status_code=200,
                headers={"Content-Type": "text/plain; charset=utf-8"}
            )
            
        except InvalidSignatureError:
            logging.warning(f"[{request_id}] LINE 簽章格式無效")
            return func.HttpResponse(
                json.dumps({"error": "Invalid signature format", "request_id": request_id}, ensure_ascii=False),
                status_code=400,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
    
    except Exception as e:
        logging.error(f"[{request_id}] LINE callback 處理錯誤: {e}")
        logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
        return func.HttpResponse(
            json.dumps({
                "error": "LINE callback processing failed",
                "details": str(e),
                "request_id": request_id
            }, ensure_ascii=False),
            status_code=500,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
