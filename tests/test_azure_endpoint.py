# test_azure_endpoint.py - 專門測試 Azure 端點
# 快速測試 Azure Function App 的各個端點

import json
import os
import requests
import time
from datetime import datetime

# Azure 端點配置
AZURE_ENDPOINT = "https://<your-azure-endpoint>.azurewebsites.net/api"
TEST_TOKEN = "test_verify_token_12345"  # 測試用 token，實際部署時應該使用真實值
TIMEOUT = 30

def test_azure_health_check():
    """測試 Azure 健康檢查端點"""
    print("\n🏥 測試 Azure 健康檢查端點...")
    
    try:
        url = f"{AZURE_ENDPOINT}/health"
        print(f"請求 URL: {url}")
        
        response = requests.get(url, timeout=TIMEOUT)
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Azure 健康檢查成功")
            print(f"服務狀態: {data.get('status')}")
            print(f"服務名稱: {data.get('service')}")
            print(f"版本: {data.get('version', 'unknown')}")
            print(f"配置狀態: {'✅' if data.get('config_initialized') else '❌'}")
            
            # 檢查環境變數狀態
            env_vars = data.get('environment_variables', {})
            print("\nAzure 環境變數狀態:")
            for var, status in env_vars.items():
                icon = "✅" if status == "已設定" else "⚠️" if status == "佔位符" else "❌"
                print(f"  {icon} {var}: {status}")
            
            # 檢查處理器狀態
            handlers = data.get('handlers_initialized', {})
            print("\n處理器狀態:")
            for handler, initialized in handlers.items():
                icon = "✅" if initialized else "❌"
                print(f"  {icon} {handler}: {'已初始化' if initialized else '未初始化'}")
                
            return True
        else:
            print(f"❌ Azure 健康檢查失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"錯誤內容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 連線失敗 - Azure 端點無法訪問")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 請求超時 - Azure 端點回應時間超過 {TIMEOUT} 秒")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_azure_teams_webhook():
    """測試 Azure Teams Webhook 端點"""
    print("\n🔗 測試 Azure Teams Webhook 端點...")
    
    # 模擬 Teams 會議通知 payload
    test_payload = {
        "messageType": "message",
        "attachments": [
            {
                "contentType": "meetingReference",
                "name": "Azure 測試會議 - 整合版本",
                "content": json.dumps({
                    "meetingJoinUrl": "https://teams.microsoft.com/l/meetup-join/azure-test-unified"
                })
            }
        ],
        "body": {
            "content": "<div>Azure 測試會議時間: 2025-07-26 14:30</div>"
        }
    }
    
    try:
        url = f"{AZURE_ENDPOINT}/teamshook"
        params = {"token": TEST_TOKEN}
        
        print(f"請求 URL: {url}")
        print(f"Token: {TEST_TOKEN[:8]}...")
        
        response = requests.post(
            url, 
            params=params,
            json=test_payload,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ Azure Teams Webhook 測試成功")
            return True
        elif response.status_code == 401:
            print("⚠️ Token 驗證失敗 - 需要設定正確的 FLOW_VERIFY_TOKEN")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            return False
        elif response.status_code == 500:
            print("⚠️ 伺服器內部錯誤 - 可能是環境變數配置問題")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            return False
        else:
            print(f"❌ Azure Teams Webhook 測試失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_azure_line_callback():
    """測試 Azure LINE Callback 端點"""
    print("\n📱 測試 Azure LINE Callback 端點...")
    
    try:
        url = f"{AZURE_ENDPOINT}/callback"
        
        # 簡單的無效請求測試（預期會失敗，但驗證端點存在）
        response = requests.post(
            url, 
            data="test",
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"回應狀態碼: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Azure LINE Callback 端點存在（如預期返回 400 - 缺少簽章）")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            return True
        elif response.status_code == 500:
            print("⚠️ 伺服器內部錯誤 - 可能是環境變數配置問題")
            try:
                error_data = response.json()
                print(f"錯誤詳情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            return False
        else:
            print(f"⚠️ 意外的回應: {response.status_code}")
            print(f"回應內容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_azure_unknown_endpoint():
    """測試 Azure 未知端點處理"""
    print("\n❓ 測試 Azure 未知端點處理...")
    
    try:
        url = f"{AZURE_ENDPOINT}/unknown-endpoint"
        
        response = requests.get(url, timeout=TIMEOUT)
        
        print(f"回應狀態碼: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Azure 未知端點正確返回 404")
            # Azure Functions 可能返回 HTML 或 JSON
            try:
                data = response.json()
                print(f"JSON 回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
            except:
                print("HTML 回應（標準 Azure Functions 404 頁面）")
            return True
        else:
            print(f"⚠️ 意外的回應: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """執行 Azure 端點測試"""
    print("🌩️ Azure Function App 端點測試")
    print("=" * 60)
    print(f"目標端點: {AZURE_ENDPOINT}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 執行測試
    tests = [
        ("Azure 健康檢查", test_azure_health_check),
        ("Azure Teams Webhook", test_azure_teams_webhook),
        ("Azure LINE Callback", test_azure_line_callback),
        ("Azure 未知端點", test_azure_unknown_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        success = test_func()
        results.append((test_name, success))
        time.sleep(2)  # 較長的延遲，避免對 Azure 端點造成壓力
    
    # 總結結果
    print(f"\n{'='*60}")
    print("📊 Azure 端點測試結果總結:")
    
    passed = 0
    for test_name, success in results:
        icon = "✅" if success else "❌"
        print(f"  {icon} {test_name}")
        if success:
            passed += 1
    
    print(f"\n通過測試: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 所有 Azure 端點測試通過！Function App 運作正常。")
        print("\n✨ 您的 Azure Function App 已成功部署並運行！")
    elif passed > 0:
        print("⚠️ 部分 Azure 端點測試通過。")
        print("\n🔧 建議檢查:")
        print("  1. Azure Function App 的應用程式設定中的環境變數")
        print("  2. Application Insights 的日誌記錄")
        print("  3. Function App 的運行狀態")
    else:
        print("❌ 所有 Azure 端點測試失敗。")
        print("\n🚨 請檢查:")
        print("  1. Azure Function App 是否正確部署")
        print("  2. 環境變數是否正確設定")
        print("  3. Function App 是否正在運行")
    
    print(f"\n📍 Azure Portal: https://portal.azure.com")
    print(f"📊 監控端點: {AZURE_ENDPOINT}/health")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
