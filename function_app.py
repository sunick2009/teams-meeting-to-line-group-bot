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
import time
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

# 匯入 webhook logger
try:
    from webhook_logger import webhook_logger
except ImportError:
    # 如果無法匯入，創建一個簡單的替代品
    class SimpleLogger:
        def log_webhook(self, request_id, headers, body, signature=None):
            logging.info(f"[{request_id}] Webhook received: {len(body) if body else 0} bytes")
            return {}
    webhook_logger = SimpleLogger()

# 匯入 reply token 管理器
try:
    from reply_token_manager import reply_token_manager
except ImportError:
    # 如果無法匯入，創建一個簡單的替代品
    class SimpleReplyTokenManager:
        def is_token_used(self, token): return False
        def mark_token_used(self, token, request_id=None): return True
        def is_test_token(self, token): return token in ['test_reply_token', 'mock_reply_token']
        def get_stats(self): return {}
    reply_token_manager = SimpleReplyTokenManager()

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
            
            # 測試模式配置
            self.test_mode = os.getenv("LINE_TEST_MODE", "false").lower() == "true"
            self.test_signature_skip = os.getenv("LINE_SKIP_SIGNATURE", "false").lower() == "true"
            
            if self.test_mode or self.test_signature_skip:
                logging.warning("⚠️ 測試模式已啟用 - 簽章驗證已跳過！僅供測試使用")
            
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
                    FlexText(text=meeting["title"], weight="bold", size="md"),
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
    
    def _build_prompts(self, message_text: str) -> tuple[str, str]:
        """根據語言方向產生 system / user 兩段 prompt"""
        is_zh = self.is_chinese(message_text)

        lang_inst = (
            "Translate the text from Traditional Chinese to fluent English."
            if is_zh else
            "Translate the text from English to fluent Traditional Chinese."
        )

        system_prompt = (
            "You are a STRICT translator.\n"
            f"{lang_inst}\n"
            "Rules:\n"
            "1. Only translate the text between <source> and </source>.\n"
            "2. Preserve line breaks; one output line per input line.\n"
            "3. Keep every URL (any string containing 'http' or 'https') exactly as‑is.\n"
            "4. Do NOT add, delete, reorder, summarise or explain anything.\n"
            "5. Return ONLY the translation, with no extra commentary."
        )

        user_prompt = f"<source>\n{message_text.strip()}\n</source>"
        return system_prompt, user_prompt

    def translate_message(self, message_text: str, request_id: str) -> str:
        """翻譯訊息（加強約束版）"""
        system_prompt, user_prompt = self._build_prompts(message_text)

        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.0,
                top_p=1.0,
                # 預估輸出長度：原文字元數 ×1.5 足夠，又能防暴衝
                max_tokens=int(len(message_text) * 1.5),
                presence_penalty=0,
                frequency_penalty=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logging.error(f"[{request_id}] OpenAI 翻譯錯誤: {exc}")
            return "發生錯誤，無法翻譯此訊息。"

    
    def handle_events(self, events: List, request_id: str) -> None:
        """處理 LINE Bot 事件"""
        for i, event in enumerate(events):
            logging.info(f"[{request_id}] 處理事件 {i+1}/{len(events)}: {type(event).__name__}")
            
            # 檢查是否為訊息事件和文字訊息 (支援真實事件和模擬事件)
            is_message_event = (
                isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent)
            ) or (
                # 模擬事件的檢查
                hasattr(event, 'type') and event.type == 'message' and 
                hasattr(event, 'message') and hasattr(event.message, 'type') and 
                event.message.type == 'text' and hasattr(event.message, 'text')
            )
            
            if is_message_event:
                try:
                    logging.info(f"[{request_id}] 收到文字訊息: {event.message.text[:50]}...")
                    
                    # 取得和驗證 reply token
                    reply_token = getattr(event, 'reply_token', None)
                    if not reply_token:
                        logging.warning(f"[{request_id}] 事件沒有 reply_token，跳過回覆")
                        continue
                    
                    # 檢查是否為測試用的假 token
                    if reply_token_manager.is_test_token(reply_token):
                        logging.warning(f"[{request_id}] 檢測到測試用假 reply token，跳過 LINE API 呼叫: {reply_token}")
                        continue
                    
                    # 檢查 reply token 是否已經使用過
                    if reply_token_manager.is_token_used(reply_token):
                        logging.warning(f"[{request_id}] Reply token 已使用過，跳過重複回覆: {reply_token[:10]}...")
                        continue
                    
                    # 標記 token 為已使用
                    if not reply_token_manager.mark_token_used(reply_token, request_id):
                        logging.warning(f"[{request_id}] 無法標記 reply token 為已使用，跳過處理")
                        continue
                    
                    # 翻譯訊息（已有內部錯誤處理）
                    translation = self.translate_message(event.message.text, request_id)
                    
                    # 發送回覆（加入錯誤處理）
                    try:
                        with ApiClient(self.line_config) as api_client:
                            messaging_api = MessagingApi(api_client)
                            messaging_api.reply_message_with_http_info(
                                ReplyMessageRequest(
                                    reply_token=reply_token,
                                    messages=[TextMessage(text=translation)],
                                )
                            )
                            logging.info(f"[{request_id}] 翻譯回覆發送成功")
                    except Exception as line_error:
                        error_message = str(line_error)
                        logging.error(f"[{request_id}] LINE API 回覆失敗: {error_message}")
                        
                        # 檢查是否為 reply token 相關錯誤
                        if any(keyword in error_message for keyword in ["Invalid reply token", "reply token", "replyToken"]):
                            logging.warning(f"[{request_id}] Reply token 錯誤，可能已過期或已使用: {reply_token[:10]}...")
                            # 不嘗試重新發送，因為 reply token 問題無法通過重試解決
                            continue
                        
                        # 對於其他錯誤，不嘗試重新發送，因為 reply token 已被標記為使用
                        logging.error(f"[{request_id}] 由於 reply token 已使用，無法發送備用錯誤訊息")
                            
                except Exception as event_error:
                    logging.error(f"[{request_id}] 處理事件時發生未預期錯誤: {event_error}")
                    logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
                    # 由於 reply token 已被標記為使用，不再嘗試發送錯誤訊息
            else:
                logging.info(f"[{request_id}] 忽略非文字訊息事件: {type(event).__name__}")
    
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
            "test_mode": {
                "enabled": config.test_mode if config else False,
                "signature_skip": config.test_signature_skip if config else False,
                "warning": "⚠️ 測試模式已啟用 - 僅供開發測試使用" if (config and (config.test_mode or config.test_signature_skip)) else None
            },
            "reply_token_manager": reply_token_manager.get_stats(),
            "request_id": request_id,
            "version": "unified-1.1.0"
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
            # 更強健的請求內容讀取
            raw_body = req.get_body()
            logging.info(f"[{request_id}] 收到原始內容大小: {len(raw_body)} 字節")
            
            # 檢查內容是否為空
            if not raw_body:
                logging.warning(f"[{request_id}] 收到空的請求內容")
                return func.HttpResponse(
                    "OK",  # LINE webhook 驗證請求可能是空的，返回 200 避免重試
                    status_code=200,
                    headers={"Content-Type": "text/plain; charset=utf-8"}
                )
            
            # 嘗試多種解碼方式
            body = None
            try:
                body = raw_body.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    body = raw_body.decode('utf-8', errors='ignore')
                    logging.warning(f"[{request_id}] UTF-8 解碼時忽略了一些字元")
                except Exception as decode_error:
                    logging.error(f"[{request_id}] 字元解碼完全失敗: {decode_error}")
                    return func.HttpResponse(
                        "OK",  # 返回 200 避免 LINE 重試
                        status_code=200,
                        headers={"Content-Type": "text/plain; charset=utf-8"}
                    )
            
            if not body:
                logging.warning(f"[{request_id}] 解碼後內容為空")
                return func.HttpResponse(
                    "OK",
                    status_code=200,
                    headers={"Content-Type": "text/plain; charset=utf-8"}
                )
            
            logging.info(f"[{request_id}] 成功解碼內容大小: {len(body)} 字元")
            
            # 使用 webhook logger 記錄完整的 webhook 資訊
            try:
                webhook_data = webhook_logger.log_webhook(
                    request_id=request_id,
                    headers=req.headers,
                    body=body,
                    signature=signature
                )
                
                # 檢查是否為重複投遞
                if body:
                    try:
                        parsed_body = json.loads(body)
                        events_data = parsed_body.get('events', [])
                        for event_data in events_data:
                            delivery_context = event_data.get('deliveryContext', {})
                            is_redelivery = delivery_context.get('isRedelivery', False)
                            if is_redelivery:
                                logging.warning(f"[{request_id}] ⚠️ 檢測到重複投遞事件，可能導致 reply token 重複使用")
                    except:
                        pass  # 解析失敗不影響主要流程
                        
            except Exception as log_error:
                logging.warning(f"[{request_id}] Webhook 日誌記錄失敗: {log_error}")
                # 繼續處理，不因為日誌記錄失敗而中斷
            
        except Exception as e:
            logging.error(f"[{request_id}] 讀取請求內容時發生錯誤: {e}")
            logging.error(f"[{request_id}] 錯誤類型: {type(e).__name__}")
            logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
            
            # 對於請求讀取錯誤，返回 200 避免 LINE 重試
            return func.HttpResponse(
                "OK",
                status_code=200,
                headers={"Content-Type": "text/plain; charset=utf-8"}
            )
        
        # 測試模式檢查
        test_mode_active = config.test_mode or config.test_signature_skip
        if test_mode_active:
            logging.warning(f"[{request_id}] ⚠️ 測試模式已啟用 - 將跳過簽章驗證")
        
        # 簽章驗證 (測試模式下可跳過)
        signature_valid = True
        if not test_mode_active:
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
        else:
            logging.info(f"[{request_id}] 測試模式: 跳過簽章驗證")
            # 在測試模式下，為了解析事件，我們需要提供一個假的簽章
            if not signature:
                signature = "test_signature"
                logging.info(f"[{request_id}] 測試模式: 使用假簽章進行事件解析")
        
        # 解析事件
        try:
            if test_mode_active:
                # 測試模式：直接解析 JSON 內容，不使用 parser
                logging.info(f"[{request_id}] 測試模式: 直接解析 JSON 事件")
                try:
                    webhook_data = json.loads(body)
                    events = webhook_data.get('events', [])
                    logging.info(f"[{request_id}] 測試模式: 從 JSON 解析到 {len(events)} 個原始事件")
                    
                    # 檢查是否為 LINE 的驗證請求（空事件數組）
                    if len(events) == 0:
                        logging.info(f"[{request_id}] 收到 LINE 驗證請求（空事件）")
                        return func.HttpResponse(
                            "OK", 
                            status_code=200,
                            headers={"Content-Type": "text/plain; charset=utf-8"}
                        )
                    
                    # 將原始事件轉換為模擬事件物件
                    processed_events = []
                    for event_data in events:
                        if event_data.get('type') == 'message' and event_data.get('message', {}).get('type') == 'text':
                            # 創建完整的模擬事件物件，匹配真實 LINE 事件結構
                            class SimpleTextMessage:
                                def __init__(self, message_data):
                                    self.text = message_data.get('text', '')
                                    self.type = 'text'
                                    self.id = message_data.get('id', 'mock_message_id')
                                    self.quote_token = message_data.get('quoteToken', None)
                            
                            class SimpleSource:
                                def __init__(self, source_data):
                                    self.type = source_data.get('type', 'user')
                                    self.user_id = source_data.get('userId', None)
                                    self.group_id = source_data.get('groupId', None)
                                    self.room_id = source_data.get('roomId', None)
                            
                            class SimpleDeliveryContext:
                                def __init__(self, delivery_data):
                                    self.is_redelivery = delivery_data.get('isRedelivery', False)
                            
                            class SimpleMessageEvent:
                                def __init__(self, event_data):
                                    self.type = 'message'
                                    self.mode = event_data.get('mode', 'active')
                                    self.timestamp = event_data.get('timestamp', int(time.time() * 1000))
                                    self.source = SimpleSource(event_data.get('source', {}))
                                    self.webhook_event_id = event_data.get('webhookEventId', 'mock_webhook_event_id')
                                    self.delivery_context = SimpleDeliveryContext(event_data.get('deliveryContext', {}))
                                    self.reply_token = event_data.get('replyToken', 'test_reply_token')
                                    self.message = SimpleTextMessage(event_data.get('message', {}))
                            
                            mock_event = SimpleMessageEvent(event_data)
                            processed_events.append(mock_event)
                            
                            logging.info(f"[{request_id}] 測試模式: 創建模擬事件")
                            logging.info(f"[{request_id}] - 訊息: {mock_event.message.text[:50]}...")
                            logging.info(f"[{request_id}] - 來源類型: {mock_event.source.type}")
                            logging.info(f"[{request_id}] - Reply Token: {mock_event.reply_token[:10]}...")
                    
                    events = processed_events
                except json.JSONDecodeError as je:
                    logging.error(f"[{request_id}] 測試模式: JSON 解析失敗: {je}")
                    # JSON 解析失敗也返回 200，避免 LINE 重試
                    return func.HttpResponse(
                        "OK", 
                        status_code=200,
                        headers={"Content-Type": "text/plain; charset=utf-8"}
                    )
                except Exception as parse_error:
                    logging.error(f"[{request_id}] 測試模式: 事件處理失敗: {parse_error}")
                    logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
                    return func.HttpResponse(
                        "OK", 
                        status_code=200,
                        headers={"Content-Type": "text/plain; charset=utf-8"}
                    )
            else:
                # 正常模式：使用 LINE SDK parser
                try:
                    events = translation_handler.parser.parse(body, signature)
                except Exception as parser_error:
                    logging.error(f"[{request_id}] LINE SDK parser 失敗: {parser_error}")
                    logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
                    return func.HttpResponse(
                        "OK", 
                        status_code=200,
                        headers={"Content-Type": "text/plain; charset=utf-8"}
                    )
            
            logging.info(f"[{request_id}] 解析到 {len(events)} 個事件")
            
            # 處理事件（內部已有完整錯誤處理）
            try:
                translation_handler.handle_events(events, request_id)
                logging.info(f"[{request_id}] LINE callback 處理完成")
            except Exception as handle_error:
                logging.error(f"[{request_id}] 事件處理失敗: {handle_error}")
                logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
                # 即使事件處理失敗，也返回 200 避免 LINE 重試
            
            # 總是返回 200 給 LINE，即使內部處理有錯誤
            return func.HttpResponse(
                "OK", 
                status_code=200,
                headers={"Content-Type": "text/plain; charset=utf-8"}
            )
            
        except InvalidSignatureError:
            if not test_mode_active:
                logging.warning(f"[{request_id}] LINE 簽章格式無效")
                return func.HttpResponse(
                    json.dumps({"error": "Invalid signature format", "request_id": request_id}, ensure_ascii=False),
                    status_code=400,
                    headers={"Content-Type": "application/json; charset=utf-8"}
                )
            else:
                logging.warning(f"[{request_id}] 測試模式: 忽略簽章格式錯誤")
                return func.HttpResponse(
                    "OK", 
                    status_code=200,
                    headers={"Content-Type": "text/plain; charset=utf-8"}
                )
        except Exception as parse_error:
            # 解析錯誤，但仍然返回 200 避免 LINE 重試
            logging.error(f"[{request_id}] 事件解析錯誤: {parse_error}")
            logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
            return func.HttpResponse(
                "OK", 
                status_code=200,
                headers={"Content-Type": "text/plain; charset=utf-8"}
            )
    
    except Exception as e:
        logging.error(f"[{request_id}] LINE callback 處理錯誤: {e}")
        logging.error(f"[{request_id}] 錯誤堆疊: {traceback.format_exc()}")
        
        # 對於系統級錯誤，我們也返回 200 避免 LINE 重試
        # 但會在日誌中記錄詳細錯誤
        return func.HttpResponse(
            "OK", 
            status_code=200,
            headers={"Content-Type": "text/plain; charset=utf-8"}
        )
