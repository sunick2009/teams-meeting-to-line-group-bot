# deploy_test_mode.py - 快速部署測試模式到 Azure
import subprocess
import sys
import os

def run_command(command, description):
    """執行命令並顯示結果"""
    print(f"\n🔧 {description}...")
    print(f"執行: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 成功")
            if result.stdout.strip():
                print(f"輸出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ 失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 Azure Function App 測試模式部署器")
    print("=" * 50)
    
    # 檢查必要工具
    print("\n📋 檢查必要工具...")
    if not run_command("func --version", "檢查 Azure Functions Core Tools"):
        print("❌ 請安裝 Azure Functions Core Tools")
        print("下載地址: https://github.com/Azure/azure-functions-core-tools")
        return False
    
    if not run_command("az --version", "檢查 Azure CLI"):
        print("❌ 請安裝 Azure CLI")
        print("下載地址: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return False
    
    # 獲取部署參數
    function_app_name = input("\n請輸入 Azure Function App 名稱: ").strip()
    if not function_app_name:
        print("❌ Function App 名稱不能為空")
        return False
    
    # 確認部署
    print(f"\n⚠️ 即將執行以下操作:")
    print(f"1. 在本地啟用測試模式")
    print(f"2. 部署到 Azure Function App: {function_app_name}")
    print(f"3. 在 Azure 中設定測試模式環境變數")
    
    confirm = input("\n是否繼續？(y/N): ").strip().lower()
    if confirm != 'y':
        print("部署已取消")
        return True
    
    # 步驟 1: 確保本地設定正確
    print(f"\n{'='*20} 步驟 1: 本地設定 {'='*20}")
    
    local_settings_path = "local.settings.json"
    if os.path.exists(local_settings_path):
        print("✅ 本地設定檔已存在")
    else:
        print("⚠️ 本地設定檔不存在，請確認您在正確的專案目錄中")
    
    # 步驟 2: 部署到 Azure
    print(f"\n{'='*20} 步驟 2: 部署到 Azure {'='*20}")
    
    if not run_command(f"func azure functionapp publish {function_app_name}", 
                      f"部署到 {function_app_name}"):
        print("❌ 部署失敗")
        return False
    
    # 步驟 3: 設定 Azure 環境變數
    print(f"\n{'='*20} 步驟 3: 設定測試模式 {'='*20}")
    
    # 詢問資源群組
    resource_group = input(f"請輸入 {function_app_name} 的資源群組名稱: ").strip()
    if not resource_group:
        print("❌ 資源群組名稱不能為空")
        return False
    
    # 設定測試模式環境變數
    commands = [
        f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group} --settings "LINE_TEST_MODE=true"',
        f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group} --settings "LINE_SKIP_SIGNATURE=true"'
    ]
    
    for i, command in enumerate(commands, 1):
        if not run_command(command, f"設定測試模式環境變數 {i}/2"):
            print("⚠️ 環境變數設定失敗，但部署可能仍然成功")
    
    # 重新啟動 Function App
    if run_command(f"az functionapp restart --name {function_app_name} --resource-group {resource_group}",
                   "重新啟動 Function App"):
        print("✅ Function App 已重新啟動")
    
    # 完成
    print(f"\n{'='*50}")
    print("🎉 部署完成！")
    print(f"\n📍 Azure Function App URL:")
    print(f"  健康檢查: https://{function_app_name}.azurewebsites.net/api/health")
    print(f"  LINE Callback: https://{function_app_name}.azurewebsites.net/api/callback")
    print(f"  Teams Webhook: https://{function_app_name}.azurewebsites.net/api/teamshook")
    
    print(f"\n🧪 測試模式已啟用:")
    print("  ⚠️ LINE 簽章驗證已跳過")
    print("  ⚠️ 僅供開發測試使用")
    
    print(f"\n📝 後續步驟:")
    print("  1. 使用健康檢查 URL 確認服務狀態")
    print("  2. 執行 test_function_app_unified.py 測試功能")
    print("  3. 完成測試後記得停用測試模式")
    
    print(f"\n🔒 停用測試模式:")
    print(f"  python enable_test_mode_azure.py")
    print(f"  (選擇選項 2 來停用測試模式)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
