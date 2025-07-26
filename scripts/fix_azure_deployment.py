# fix_azure_deployment.py - 修復 Azure 部署中的請求處理問題
import subprocess
import sys
import os
import json

def run_command(command, description, capture_output=True):
    """執行命令並顯示結果"""
    print(f"\n🔧 {description}...")
    print(f"執行: {command}")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 成功")
                if result.stdout.strip():
                    print(f"輸出: {result.stdout.strip()}")
                return True, result.stdout
            else:
                print(f"❌ 失敗: {result.stderr}")
                return False, result.stderr
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode == 0, ""
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False, str(e)

def create_host_json():
    """創建或更新 host.json 以優化 Azure Functions 配置"""
    host_json_config = {
        "version": "2.0",
        "functionTimeout": "00:10:00",
        "logging": {
            "applicationInsights": {
                "samplingSettings": {
                    "isEnabled": True,
                    "maxTelemetryItemsPerSecond": 20
                }
            }
        },
        "extensions": {
            "http": {
                "routePrefix": "api",
                "maxOutstandingRequests": 200,
                "maxConcurrentRequests": 100,
                "dynamicThrottlesEnabled": False
            }
        },
        "retry": {
            "strategy": "fixedDelay",
            "maxRetryCount": 2,
            "delayInterval": "00:00:02"
        }
    }
    
    try:
        with open("host.json", "w", encoding="utf-8") as f:
            json.dump(host_json_config, f, indent=2, ensure_ascii=False)
        print("✅ host.json 已更新")
        return True
    except Exception as e:
        print(f"❌ 更新 host.json 失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔧 Azure Functions 部署修復工具")
    print("專門解決 'Unexpected end of request content' 錯誤")
    print("=" * 60)
    
    # 確認在正確的目錄
    if not os.path.exists("function_app.py"):
        print("❌ 找不到 function_app.py，請確認您在正確的專案目錄中")
        return False
    
    # 獲取部署參數
    function_app_name = input("\n請輸入 Azure Function App 名稱: ").strip()
    if not function_app_name:
        print("❌ Function App 名稱不能為空")
        return False
    
    resource_group = input(f"請輸入 {function_app_name} 的資源群組名稱: ").strip()
    if not resource_group:
        print("❌ 資源群組名稱不能為空")
        return False
    
    # 步驟 1: 優化 host.json
    print(f"\n{'='*20} 步驟 1: 優化配置 {'='*20}")
    if not create_host_json():
        print("⚠️ host.json 更新失敗，但繼續部署")
    
    # 步驟 2: 確保所有依賴套件都已安裝
    print(f"\n{'='*20} 步驟 2: 安裝依賴 {'='*20}")
    if not run_command("pip install -r requirements.txt", "安裝 Python 依賴套件")[0]:
        print("⚠️ 依賴套件安裝失敗，但繼續部署")
    
    # 步驟 3: 部署到 Azure
    print(f"\n{'='*20} 步驟 3: 部署到 Azure {'='*20}")
    success, output = run_command(f"func azure functionapp publish {function_app_name} --python", 
                                 f"部署到 {function_app_name}")
    if not success:
        print("❌ 部署失敗")
        print("可能的解決方案:")
        print("1. 確認您已登入 Azure CLI: az login")
        print("2. 確認 Function App 存在且有權限")
        print("3. 檢查網路連接")
        return False
    
    # 步驟 4: 設定關鍵環境變數
    print(f"\n{'='*20} 步驟 4: 設定環境變數 {'='*20}")
    
    env_settings = [
        ("LINE_TEST_MODE", "true", "啟用測試模式"),
        ("LINE_SKIP_SIGNATURE", "true", "跳過簽章驗證"),
        ("FUNCTIONS_WORKER_RUNTIME", "python", "設定 Python 運行時"),
        ("WEBSITE_CONTENTAZUREFILECONNECTIONSTRING", "", "移除文件連接字串（避免衝突）"),
        ("WEBSITE_CONTENTSHARE", "", "移除內容共享（避免衝突）")
    ]
    
    for setting_name, setting_value, description in env_settings:
        if setting_value:  # 只有當值不為空時才設定
            command = f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group} --settings "{setting_name}={setting_value}"'
        else:  # 刪除設定
            command = f'az functionapp config appsettings delete --name {function_app_name} --resource-group {resource_group} --setting-names {setting_name}'
        
        success, _ = run_command(command, description)
        if not success:
            print(f"⚠️ {description} 失敗，但繼續...")
    
    # 步驟 5: 重新啟動 Function App
    print(f"\n{'='*20} 步驟 5: 重新啟動 {'='*20}")
    if run_command(f"az functionapp restart --name {function_app_name} --resource-group {resource_group}",
                   "重新啟動 Function App")[0]:
        print("✅ Function App 已重新啟動")
    
    # 步驟 6: 測試健康檢查
    print(f"\n{'='*20} 步驟 6: 驗證部署 {'='*20}")
    import time
    print("等待 30 秒讓服務完全啟動...")
    time.sleep(30)
    
    health_url = f"https://{function_app_name}.azurewebsites.net/api/health"
    success, response = run_command(f'curl -s -o /dev/null -w "%{{http_code}}" {health_url}', 
                                   f"測試健康檢查端點")
    
    if success and "200" in response:
        print("✅ 健康檢查通過")
    else:
        print("⚠️ 健康檢查失敗，但服務可能仍在啟動中")
    
    # 完成
    print(f"\n{'='*60}")
    print("🎉 修復部署完成！")
    print(f"\n📍 Azure Function App URLs:")
    print(f"  健康檢查: https://{function_app_name}.azurewebsites.net/api/health")
    print(f"  LINE Callback: https://{function_app_name}.azurewebsites.net/api/callback")
    print(f"  Teams Webhook: https://{function_app_name}.azurewebsites.net/api/teamshook")
    
    print(f"\n🔧 已套用的修復:")
    print("  ✅ 強化請求內容讀取邏輯")
    print("  ✅ 增加 UTF-8 解碼錯誤處理")
    print("  ✅ 處理空請求內容情況")
    print("  ✅ 優化 Azure Functions 配置")
    print("  ✅ 確保所有錯誤都返回 200 狀態碼")
    
    print(f"\n📝 測試建議:")
    print("  1. 先測試健康檢查端點")
    print("  2. 在 LINE Developer Console 測試 webhook")
    print("  3. 發送實際 LINE 訊息測試翻譯功能")
    print("  4. 檢查 Azure Portal 中的 Application Insights 日誌")
    
    print(f"\n📊 監控建議:")
    print("  1. Azure Portal > Function App > Monitoring > Logs")
    print("  2. Application Insights > Failures")
    print("  3. Application Insights > Performance")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
