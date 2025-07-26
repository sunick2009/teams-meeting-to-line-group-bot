# enable_test_mode_azure.py - 在 Azure Function App 中啟用測試模式
import subprocess
import sys
import os

def run_az_command(command):
    """執行 Azure CLI 命令"""
    try:
        print(f"執行命令: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 命令執行成功")
            if result.stdout.strip():
                print(f"輸出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ 命令執行失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 執行命令時發生錯誤: {e}")
        return False

def enable_test_mode():
    """在 Azure Function App 中啟用測試模式"""
    
    # 從環境變數或用戶輸入獲取 Function App 名稱
    function_app_name = os.getenv("AZURE_FUNCTION_APP_NAME")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    
    if not function_app_name:
        function_app_name = input("請輸入 Azure Function App 名稱: ").strip()
    
    if not resource_group:
        resource_group = input("請輸入資源群組名稱: ").strip()
    
    if not function_app_name or not resource_group:
        print("❌ 缺少必要的參數")
        return False
    
    print(f"\n🔧 在 {function_app_name} 中啟用測試模式...")
    
    # 設定測試模式環境變數
    commands = [
        f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group} --settings "LINE_TEST_MODE=true"',
        f'az functionapp config appsettings set --name {function_app_name} --resource-group {resource_group} --settings "LINE_SKIP_SIGNATURE=true"'
    ]
    
    success = True
    for command in commands:
        if not run_az_command(command):
            success = False
    
    if success:
        print("\n✅ 測試模式已在 Azure Function App 中啟用")
        print("⚠️ 警告: 這將跳過 LINE 簽章驗證，僅供測試使用")
        print("\n重新部署或重新啟動 Function App 以套用變更:")
        print(f"az functionapp restart --name {function_app_name} --resource-group {resource_group}")
    else:
        print("\n❌ 啟用測試模式失敗")
    
    return success

def disable_test_mode():
    """在 Azure Function App 中停用測試模式"""
    
    function_app_name = os.getenv("AZURE_FUNCTION_APP_NAME")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    
    if not function_app_name:
        function_app_name = input("請輸入 Azure Function App 名稱: ").strip()
    
    if not resource_group:
        resource_group = input("請輸入資源群組名稱: ").strip()
    
    if not function_app_name or not resource_group:
        print("❌ 缺少必要的參數")
        return False
    
    print(f"\n🔧 在 {function_app_name} 中停用測試模式...")
    
    # 移除測試模式環境變數
    commands = [
        f'az functionapp config appsettings delete --name {function_app_name} --resource-group {resource_group} --setting-names "LINE_TEST_MODE"',
        f'az functionapp config appsettings delete --name {function_app_name} --resource-group {resource_group} --setting-names "LINE_SKIP_SIGNATURE"'
    ]
    
    success = True
    for command in commands:
        # 這些命令可能會失敗（如果變數不存在），這是正常的
        run_az_command(command)
    
    print("\n✅ 測試模式已停用")
    print("🔒 簽章驗證已恢復正常")
    print("\n重新部署或重新啟動 Function App 以套用變更:")
    print(f"az functionapp restart --name {function_app_name} --resource-group {resource_group}")
    
    return True

def main():
    """主函數"""
    print("🛠️ Azure Function App 測試模式管理器")
    print("=" * 50)
    
    while True:
        print("\n請選擇操作:")
        print("1. 啟用測試模式 (跳過簽章驗證)")
        print("2. 停用測試模式 (恢復簽章驗證)")
        print("3. 退出")
        
        try:
            choice = input("\n請輸入選擇 (1/2/3): ").strip()
        except KeyboardInterrupt:
            print("\n操作已取消")
            return False
        
        if choice == "1":
            return enable_test_mode()
        elif choice == "2":
            return disable_test_mode()
        elif choice == "3":
            print("再見！")
            return True
        else:
            print("無效選擇，請重新輸入")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
