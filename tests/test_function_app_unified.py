# test_function_app_unified.py - 測試整合版 Azure Function
# 測試新的 function_app_unified.py

import json
import os
import sys
import time
import requests
from datetime import datetime

# 測試配置
TEST_CONFIG = {
    "local_url": "http://localhost:7071/api",
    "azure_url": "https://<your-azure-endpoint>.azurewebsites.net/api",
    "test_token": os.getenv("FLOW_VERIFY_TOKEN", "test_verify_token_12345"),
    "timeout": 30
}

def test_health_check(use_azure=False):
    """測試健康檢查端點"""
    base_url = TEST_CONFIG['azure_url'] if use_azure else TEST_CONFIG['local_url']
    endpoint_type = "Azure" if use_azure else "本地"
    
    print(f"\n🏥 測試{endpoint_type}健康檢查端點...")
    
    try:
        url = f"{base_url}/health"
        print(f"請求 URL: {url}")
        
        response = requests.get(url, timeout=TEST_CONFIG['timeout'])
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {endpoint_type}健康檢查成功")
            print(f"服務狀態: {data.get('status')}")
            print(f"服務名稱: {data.get('service')}")
            print(f"配置狀態: {'✅' if data.get('config_initialized') else '❌'}")
            
            # 檢查環境變數狀態
            env_vars = data.get('environment_variables', {})
            print("\n環境變數狀態:")
            for var, status in env_vars.items():
                icon = "✅" if status == "已設定" else "⚠️" if status == "佔位符" else "❌"
                print(f"  {icon} {var}: {status}")
                
            return True
        else:
            print(f"❌ {endpoint_type}健康檢查失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {error_data}")
            except:
                print(f"錯誤內容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 連線失敗 - 請確認 {endpoint_type} 端點是否可訪問")
        if not use_azure:
            print("請執行: func host start")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 請求超時 - {endpoint_type} 端點回應時間過長")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_teams_webhook(use_azure=False):
    """測試 Teams Webhook 端點"""
    base_url = TEST_CONFIG['azure_url'] if use_azure else TEST_CONFIG['local_url']
    endpoint_type = "Azure" if use_azure else "本地"
    
    print(f"\n🔗 測試{endpoint_type} Teams Webhook 端點...")
    
    # 模擬 Teams 會議通知 payload
    test_payload = {
        "messageType": "message",
        "attachments": [
            {
                "contentType": "meetingReference",
                "name": "測試會議 - 整合版本",
                "content": json.dumps({
                    "meetingJoinUrl": "https://teams.microsoft.com/l/meetup-join/test-unified"
                })
            }
        ],
        "body": {
            "content": "<div>會議時間: 2025-01-26 14:30</div>"
        }
    }
    
    try:
        url = f"{base_url}/teamshook"
        params = {"token": TEST_CONFIG['test_token']}
        
        print(f"請求 URL: {url}")
        print(f"Token: {TEST_CONFIG['test_token'][:8]}...")
        
        response = requests.post(
            url, 
            params=params,
            json=test_payload,
            timeout=TEST_CONFIG['timeout'],
            headers={"Content-Type": "application/json"}
        )
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ {endpoint_type} Teams Webhook 測試成功")
            return True
        elif response.status_code == 401:
            print("⚠️ Token 驗證失敗 - 請檢查 FLOW_VERIFY_TOKEN 環境變數")
            return False
        else:
            print(f"❌ {endpoint_type} Teams Webhook 測試失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {error_data}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_line_callback(use_azure=False):
    """測試 LINE Callback 端點（包含測試模式）"""
    base_url = TEST_CONFIG['azure_url'] if use_azure else TEST_CONFIG['local_url']
    endpoint_type = "Azure" if use_azure else "本地"
    
    print(f"\n📱 測試{endpoint_type} LINE Callback 端點...")
    
    # 模擬真實的 LINE webhook 事件 payload
    test_payload = {
        "destination": "Ub674ca6348e71cb0f83d207f5c47862d",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "571554379032428596",
                    "quoteToken": "test_quote_token_12345",
                    "text": "Hello, this is a test message for translation!"
                },
                "webhookEventId": "01K12FZ9PADTV4XWXH9BWT7D99",
                "deliveryContext": {
                    "isRedelivery": False
                },
                "timestamp": int(time.time() * 1000),
                "source": {
                    "type": "group",
                    "groupId": "Cac46406dff58a905c3887258a8f30c7a",
                    "userId": "U8466cce1687cc9a24d7c66de1a93bfa5"
                },
                "replyToken": "770760f4352a4961b2ef9f07beaac54c",
                "mode": "active"
            }
        ]
    }
    
    try:
        url = f"{base_url}/callback"
        
        print(f"請求 URL: {url}")
        print(f"測試訊息: {test_payload['events'][0]['message']['text']}")
        
        # 測試 1: 不帶簽章的測試（預期在測試模式下成功）
        print(f"\n🔸 測試 1: 測試模式下不帶簽章的請求")
        response = requests.post(
            url, 
            json=test_payload,
            timeout=TEST_CONFIG['timeout'],
            headers={"Content-Type": "application/json"}
        )
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ 測試 1 成功 - {endpoint_type} LINE Callback 在測試模式下正常運作")
            test1_success = True
        else:
            print(f"❌ 測試 1 失敗 - 狀態碼: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {error_data}")
            except:
                pass
            test1_success = False
        
        # 測試 2: 帶有無效簽章的測試
        print(f"\n🔸 測試 2: 帶有無效簽章的請求")
        response2 = requests.post(
            url, 
            json=test_payload,
            timeout=TEST_CONFIG['timeout'],
            headers={
                "Content-Type": "application/json",
                "X-Line-Signature": "invalid_signature_test"
            }
        )
        
        print(f"回應狀態碼: {response2.status_code}")
        print(f"回應內容: {response2.text}")
        
        if response2.status_code == 200:
            print(f"✅ 測試 2 成功 - {endpoint_type} LINE Callback 在測試模式下忽略無效簽章")
            test2_success = True
        else:
            print(f"⚠️ 測試 2 - 可能未啟用測試模式或簽章驗證仍然啟用")
            test2_success = False
        
        # 測試 3: 中文翻譯測試
        print(f"\n🔸 測試 3: 中文翻譯測試")
        chinese_payload = {
            "destination": "Ub674ca6348e71cb0f83d207f5c47862d",
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "571554379032428597",
                        "quoteToken": "test_quote_token_67890",
                        "text": "新增翻譯機器人功能，實作即時翻譯中英文訊息"
                    },
                    "webhookEventId": "01K12FZ9PADTV4XWXH9BWT7D98",
                    "deliveryContext": {
                        "isRedelivery": False
                    },
                    "timestamp": int(time.time() * 1000),
                    "source": {
                        "type": "group",
                        "groupId": "Cac46406dff58a905c3887258a8f30c7a",
                        "userId": "U8466cce1687cc9a24d7c66de1a93bfa5"
                    },
                    "replyToken": "770760f4352a4961b2ef9f07beaac54d",
                    "mode": "active"
                }
            ]
        }
        
        print(f"測試中文訊息: {chinese_payload['events'][0]['message']['text']}")
        
        response3 = requests.post(
            url, 
            json=chinese_payload,
            timeout=TEST_CONFIG['timeout'],
            headers={"Content-Type": "application/json"}
        )
        
        print(f"回應狀態碼: {response3.status_code}")
        print(f"回應內容: {response3.text}")
        
        if response3.status_code == 200:
            print(f"✅ 測試 3 成功 - {endpoint_type} LINE Callback 中文翻譯測試完成")
            test3_success = True
        else:
            print(f"❌ 測試 3 失敗 - 狀態碼: {response3.status_code}")
            test3_success = False
        
        # 總結測試結果
        success_count = sum([test1_success, test2_success, test3_success])
        print(f"\n📊 LINE Callback 測試總結: {success_count}/3 項測試成功")
        
        return success_count >= 2  # 至少 2 項測試成功才算通過
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 連線失敗 - 請確認 {endpoint_type} 端點是否可訪問")
        if not use_azure:
            print("請執行: func host start")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 請求超時 - {endpoint_type} 端點回應時間過長")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_unknown_endpoint(use_azure=False):
    """測試未知端點的處理"""
    base_url = TEST_CONFIG['azure_url'] if use_azure else TEST_CONFIG['local_url']
    endpoint_type = "Azure" if use_azure else "本地"
    
    print(f"\n❓ 測試{endpoint_type}未知端點處理...")
    
    try:
        url = f"{base_url}/unknown-endpoint"
        
        response = requests.get(url, timeout=TEST_CONFIG['timeout'])
        
        print(f"回應狀態碼: {response.status_code}")
        
        if response.status_code == 404:
            try:
                data = response.json()
                print(f"✅ {endpoint_type}未知端點正確返回 404")
                print(f"可用端點數量: {len(data.get('available_endpoints', []))}")
                return True
            except:
                print(f"✅ {endpoint_type}未知端點正確返回 404（標準 HTML 回應）")
                return True
        else:
            print(f"⚠️ 意外的回應: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """執行所有測試"""
    print("🚀 開始測試整合版 Azure Function App")
    print("=" * 50)
    
    # 讓用戶選擇測試端點
    print("\n請選擇要測試的端點:")
    print("1. 本地端點 (http://localhost:7071)")
    print("2. Azure 端點 (https://<your-azure-endpoint>.azurewebsites.net/api)")
    print("3. 兩者都測試")
    
    try:
        choice = input("\n請輸入選擇 (1/2/3): ").strip()
    except KeyboardInterrupt:
        print("\n測試已取消")
        return False
    
    test_local = choice in ['1', '3']
    test_azure = choice in ['2', '3']
    
    if not (test_local or test_azure):
        print("無效選擇，預設測試 Azure 端點")
        test_azure = True
    
    # 檢查環境變數
    print("\n📋 檢查關鍵環境變數...")
    required_vars = ["LINE_ACCESS_TOKEN", "LINE_CHANNEL_SECRET", "TARGET_ID", "FLOW_VERIFY_TOKEN", "OPENAI_API_KEY"]
    test_vars = ["LINE_TEST_MODE", "LINE_SKIP_SIGNATURE"]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            is_placeholder = value.startswith("你的_") or value == "YOUR_" + var
            status = "⚠️ 佔位符" if is_placeholder else "✅ 已設定"
            print(f"  {status} {var}")
            if is_placeholder:
                missing_vars.append(var)
        else:
            print(f"  ❌ {var}: 未設定")
            missing_vars.append(var)
    
    # 檢查測試模式變數
    print("\n🧪 檢查測試模式環境變數...")
    for var in test_vars:
        value = os.getenv(var, "").lower()
        if value == "true":
            print(f"  ✅ {var}: 已啟用")
        else:
            print(f"  ⚪ {var}: 未啟用 (預設)")
    
    test_mode_enabled = any(os.getenv(var, "").lower() == "true" for var in test_vars)
    if test_mode_enabled:
        print("  ⚠️ 測試模式已啟用 - LINE 簽章驗證將被跳過")
    else:
        print("  ℹ️ 如需測試 LINE Callback，請設定 LINE_TEST_MODE=true 或 LINE_SKIP_SIGNATURE=true")
    
    if missing_vars:
        print(f"\n⚠️ 警告: {len(missing_vars)} 個環境變數需要設定:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n某些測試可能會失敗。")
    
    # 執行測試
    tests = [
        ("健康檢查", test_health_check),
        ("Teams Webhook", test_teams_webhook),
        ("LINE Callback", test_line_callback),
        ("未知端點", test_unknown_endpoint)
    ]
    
    all_results = []
    
    if test_local:
        print(f"\n{'='*30}")
        print("🏠 測試本地端點")
        print(f"{'='*30}")
        
        local_results = []
        for test_name, test_func in tests:
            success = test_func(use_azure=False)
            local_results.append((f"{test_name} (本地)", success))
            time.sleep(1)  # 短暫延遲
        
        all_results.extend(local_results)
    
    if test_azure:
        print(f"\n{'='*30}")
        print("☁️ 測試 Azure 端點")
        print(f"{'='*30}")
        
        azure_results = []
        for test_name, test_func in tests:
            success = test_func(use_azure=True)
            azure_results.append((f"{test_name} (Azure)", success))
            time.sleep(1)  # 短暫延遲
        
        all_results.extend(azure_results)
    
    # 總結結果
    print(f"\n{'='*50}")
    print("📊 測試結果總結:")
    
    passed = 0
    for test_name, success in all_results:
        icon = "✅" if success else "❌"
        print(f"  {icon} {test_name}")
        if success:
            passed += 1
    
    print(f"\n通過測試: {passed}/{len(all_results)}")
    
    if passed == len(all_results):
        print("🎉 所有測試通過！整合版 Function App 運作正常。")
    elif passed > 0:
        print("⚠️ 部分測試通過。請檢查失敗的測試項目。")
    else:
        print("❌ 所有測試失敗。請檢查 Function App 設定。")
    
    return passed == len(all_results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
