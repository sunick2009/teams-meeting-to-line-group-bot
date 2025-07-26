#!/usr/bin/env python3
"""
環境變數診斷腳本
檢查 Azure Functions 中是否設定了所有必要的環境變數
"""

import requests
import json

BASE_URL = "https://<your-azure-endpoint>.azurewebsites.net/api"

def test_environment_check():
    """測試環境變數檢查端點"""
    print("=== 環境變數診斷 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"健康檢查狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"服務名稱: {data.get('service', 'unknown')}")
            print(f"服務版本: {data.get('version', 'unknown')}")
            print("✅ 基本服務正常運行")
        else:
            print("❌ 基本服務異常")
            return False
            
    except Exception as e:
        print(f"❌ 連線錯誤: {e}")
        return False
    
    print()
    print("=== 檢查必要環境變數 ===")
    print("根據 app_unified.py，需要以下環境變數:")
    print("1. LINE_ACCESS_TOKEN - LINE Bot API 存取權杖")
    print("2. LINE_CHANNEL_SECRET - LINE Bot 頻道密鑰")
    print("3. TARGET_ID - LINE 群組或用戶 ID")
    print("4. FLOW_VERIFY_TOKEN - Teams webhook 驗證權杖")
    print("5. OPENAI_API_KEY - OpenAI API 金鑰")
    print("6. OPENAI_MODEL (選用) - OpenAI 模型名稱")
    print()
    
    print("💡 要檢查 Azure Functions 中的環境變數設定:")
    print("1. 前往 Azure Portal")
    print("2. 找到您的 Function App: yzuimsc-linebot")
    print("3. 點選 'Configuration' > 'Application settings'")
    print("4. 確認上述所有環境變數都已設定且有值")
    print()
    
    return True

def test_minimal_teams_request():
    """測試最小化的 Teams 請求，看能否取得更詳細的錯誤資訊"""
    print("=== 最小化 Teams 請求測試 ===")
    import os
    
    token = os.getenv("FLOW_VERIFY_TOKEN", "test-token")
    
    # 根據 Teams webhook 處理邏輯，需要正確的格式
    simple_payload = {
        "type": "message",
        "messageType": "message",  # 關鍵：這個欄位是必要的
        "text": "test",
        "attachments": [
            {
                "contentType": "meetingReference",  # 關鍵：這個也是必要的
                "name": "測試會議",
                "content": json.dumps({
                    "meetingJoinUrl": "https://teams.microsoft.com/l/meetup-join/test"
                })
            }
        ],
        "body": {
            "content": "<div>測試會議內容 2025-07-24 16:00</div>"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/teams/webhook",
            json=simple_payload,
            params={"token": token},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 500:
            print("⚠️ 仍然是 500 錯誤，問題可能在:")
            print("   - LINE_ACCESS_TOKEN 未設定或無效")
            print("   - TARGET_ID 未設定或無效")
            print("   - LINE API 呼叫失敗")
        elif response.status_code == 204:
            print("ℹ️ 204 回應 - Teams webhook 正確處理但忽略了請求")
        elif response.status_code == 200:
            print("✅ Teams webhook 處理成功！")
            
    except Exception as e:
        print(f"錯誤: {e}")
    
    print()
    print("--- 測試不符合格式的請求 ---")
    
    # 測試不符合格式的請求（應該被忽略）
    invalid_payload = {
        "type": "message",
        "text": "test"
        # 沒有 messageType 和 meetingReference
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/teams/webhook",
            json=invalid_payload,
            params={"token": token},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"不符合格式的請求 - 狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 204:
            print("✅ 正確忽略了不符合格式的請求")
            
    except Exception as e:
        print(f"錯誤: {e}")

def test_minimal_line_request():
    """測試最小化的 LINE 請求"""
    print("=== 最小化 LINE 請求測試 ===")
    import os
    import hmac
    import hashlib
    import base64
    
    secret = os.getenv("LINE_CHANNEL_SECRET", "test-secret")
    
    # 最簡單的 payload
    simple_payload = {
        "events": []
    }
    
    body_str = json.dumps(simple_payload, separators=(',', ':'))
    
    # 生成簽名
    if secret != "test-secret":
        hash_bytes = hmac.new(
            secret.encode('utf-8'),
            body_str.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(hash_bytes).decode('utf-8')
    else:
        signature = "test-signature"
    
    try:
        response = requests.post(
            f"{BASE_URL}/line/callback",
            data=body_str,
            headers={
                "Content-Type": "application/json",
                "X-Line-Signature": signature
            },
            timeout=30
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 500:
            print("⚠️ 仍然是 500 錯誤，問題確實在環境變數或程式邏輯")
            
    except Exception as e:
        print(f"錯誤: {e}")

def main():
    """主函數"""
    print("🔍 Azure Functions 環境診斷工具")
    print("=" * 50)
    print()
    
    # 基本環境檢查
    if not test_environment_check():
        return 1
    
    print()
    test_minimal_teams_request()
    print()
    test_minimal_line_request()
    print()
    
    print("=== 診斷完成 ===")
    print("如果上述測試都顯示 500 錯誤，請:")
    print("1. 檢查 Azure Functions 的應用程式日誌")
    print("2. 確認所有環境變數都已在 Azure Portal 中正確設定")
    print("3. 重新部署應用程式")
    
    return 0

if __name__ == "__main__":
    exit(main())
