#!/usr/bin/env python3
# verify_deployment.py - 驗證 Azure Functions 部署

import requests
import sys
import json
import time

def verify_deployment(function_app_name, max_retries=5, retry_delay=10):
    """驗證 Azure Functions 部署是否成功"""
    
    health_url = f"https://{function_app_name}.azurewebsites.net/api/health"
    
    print(f"🔍 驗證部署: {function_app_name}")
    print(f"健康檢查 URL: {health_url}")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n📡 嘗試 {attempt}/{max_retries}...")
            
            response = requests.get(health_url, timeout=30)
            
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ 部署驗證成功！")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    
                    # 檢查關鍵指標
                    if data.get("status") == "healthy":
                        print("🎉 應用程式狀態: 健康")
                    
                    env_vars = data.get("environment_variables", {})
                    missing_vars = [k for k, v in env_vars.items() if v in ["未設定", "佔位符"]]
                    
                    if missing_vars:
                        print(f"⚠️  需要設定的環境變數: {missing_vars}")
                        return False
                    else:
                        print("✅ 所有環境變數都已正確設定")
                        return True
                        
                except json.JSONDecodeError:
                    print(f"⚠️  回應不是有效的 JSON: {response.text}")
                    
            else:
                print(f"❌ HTTP 錯誤: {response.status_code}")
                if response.text:
                    print(f"錯誤內容: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print(f"🔄 連接失敗，等待 {retry_delay} 秒後重試...")
        except requests.exceptions.Timeout:
            print("⏰ 請求超時")
        except Exception as e:
            print(f"❌ 未預期錯誤: {e}")
        
        if attempt < max_retries:
            time.sleep(retry_delay)
    
    print(f"\n❌ 部署驗證失敗，已重試 {max_retries} 次")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python verify_deployment.py <function_app_name>")
        print("範例: python verify_deployment.py yzuimsc-linebot")
        sys.exit(1)
    
    function_app_name = sys.argv[1]
    success = verify_deployment(function_app_name)
    sys.exit(0 if success else 1)
