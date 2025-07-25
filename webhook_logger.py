# webhook_logger.py - 詳細記錄 LINE webhook 的工具
import json
import os
from datetime import datetime
import logging

class WebhookLogger:
    """詳細記錄 LINE webhook 的類別"""
    
    def __init__(self, log_file="webhook_logs.json"):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """設定日誌記錄"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def log_webhook(self, request_id, headers, body, signature=None):
        """記錄完整的 webhook 資訊"""
        
        webhook_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "headers": dict(headers) if headers else {},
            "signature": signature,
            "body_raw": body,
            "body_size": len(body) if body else 0
        }
        
        # 嘗試解析 JSON
        try:
            if body:
                webhook_data["body_parsed"] = json.loads(body)
                webhook_data["parse_success"] = True
        except json.JSONDecodeError as e:
            webhook_data["body_parsed"] = None
            webhook_data["parse_success"] = False
            webhook_data["parse_error"] = str(e)
        
        # 記錄到檔案
        self.save_to_file(webhook_data)
        
        # 記錄到日誌
        self.log_to_console(webhook_data)
        
        return webhook_data
    
    def save_to_file(self, webhook_data):
        """儲存到 JSON 檔案"""
        try:
            # 讀取現有的日誌
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 新增新的記錄
            logs.append(webhook_data)
            
            # 只保留最近 100 筆記錄
            if len(logs) > 100:
                logs = logs[-100:]
            
            # 寫回檔案
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"儲存 webhook 日誌失敗: {e}")
    
    def log_to_console(self, webhook_data):
        """記錄到控制台"""
        request_id = webhook_data["request_id"]
        
        self.logger.info(f"[{request_id}] ===== LINE WEBHOOK 接收 =====")
        self.logger.info(f"[{request_id}] 時間: {webhook_data['timestamp']}")
        self.logger.info(f"[{request_id}] 內容大小: {webhook_data['body_size']} 字元")
        
        # 記錄重要的標頭
        headers = webhook_data.get("headers", {})
        important_headers = ["user-agent", "content-type", "x-line-signature"]
        for header in important_headers:
            value = headers.get(header.lower(), "未提供")
            self.logger.info(f"[{request_id}] {header}: {value}")
        
        # 記錄解析狀態
        if webhook_data["parse_success"]:
            parsed_body = webhook_data["body_parsed"]
            self.logger.info(f"[{request_id}] JSON 解析: 成功")
            
            if parsed_body:
                # 記錄事件數量
                events = parsed_body.get("events", [])
                self.logger.info(f"[{request_id}] 事件數量: {len(events)}")
                
                # 記錄每個事件的詳細資訊
                for i, event in enumerate(events):
                    event_type = event.get("type", "未知")
                    self.logger.info(f"[{request_id}] 事件 {i+1}: {event_type}")
                    
                    if event_type == "message":
                        message = event.get("message", {})
                        message_type = message.get("type", "未知")
                        self.logger.info(f"[{request_id}] - 訊息類型: {message_type}")
                        
                        if message_type == "text":
                            text = message.get("text", "")
                            self.logger.info(f"[{request_id}] - 訊息內容: {text[:100]}...")
                        
                        # 記錄來源資訊
                        source = event.get("source", {})
                        source_type = source.get("type", "未知")
                        self.logger.info(f"[{request_id}] - 來源類型: {source_type}")
                        
                        if source_type == "group":
                            group_id = source.get("groupId", "未提供")
                            self.logger.info(f"[{request_id}] - 群組ID: {group_id}")
                        
                        # 記錄 reply token
                        reply_token = event.get("replyToken", "未提供")
                        self.logger.info(f"[{request_id}] - Reply Token: {reply_token[:10]}...")
        else:
            self.logger.error(f"[{request_id}] JSON 解析: 失敗")
            self.logger.error(f"[{request_id}] 錯誤: {webhook_data.get('parse_error', '未知錯誤')}")
        
        # 記錄原始內容（前 500 字元）
        body_preview = webhook_data["body_raw"][:500] if webhook_data["body_raw"] else ""
        self.logger.info(f"[{request_id}] 原始內容預覽: {body_preview}...")
        
        self.logger.info(f"[{request_id}] ===== WEBHOOK 記錄結束 =====")
    
    def get_recent_logs(self, count=10):
        """取得最近的日誌記錄"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                return logs[-count:] if logs else []
            return []
        except Exception as e:
            self.logger.error(f"讀取日誌失敗: {e}")
            return []
    
    def clear_logs(self):
        """清除日誌檔案"""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
                self.logger.info("日誌檔案已清除")
            return True
        except Exception as e:
            self.logger.error(f"清除日誌失敗: {e}")
            return False

# 全域 webhook logger 實例
webhook_logger = WebhookLogger()
