#!/usr/bin/env python3
# test_webhook.py - 測試 Teams webhook

import requests
import json

def test_webhook():
    """測試 Teams webhook 端點"""
    # 模擬 Teams 會議邀請的 payload
    test_payload = {
        "messageType": "message",
        "attachments": [
            {
                "contentType": "meetingReference",
                "name": "測試 Teams 會議",
                "content": json.dumps({
                    "meetingJoinUrl": "https://teams.microsoft.com/l/meetup-join/test123"
                })
            }
        ],
        "body": {
            "content": '<div>會議時間：2025-07-24 16:30</div>'
        }
    }
    
    # 發送測試請求
    url = "http://127.0.0.1:29999/teamshook?token=<your_verify_token_here>"
    
    try:
        print("發送測試請求到 webhook...")
        response = requests.post(url, json=test_payload, timeout=10)
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✓ Webhook 測試成功！")
        else:
            print("✗ Webhook 測試失敗")
            
    except requests.exceptions.ConnectionError:
        print("✗ 無法連接到 webhook 服務，請確認服務是否在執行")
    except Exception as e:
        print(f"✗ 測試過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    test_webhook()
