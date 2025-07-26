# setup_port_forward.py - 設定 Port Forward 接收 LINE webhook
import subprocess
import sys
import os
import time

def check_ngrok():
    """檢查 ngrok 是否已安裝"""
    try:
        result = subprocess.run(["ngrok", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok 已安裝: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def install_ngrok_guide():
    """提供 ngrok 安裝指南"""
    print("📋 ngrok 安裝指南:")
    print("1. 前往 https://ngrok.com/download")
    print("2. 下載適合 Windows 的版本")
    print("3. 解壓縮到任意資料夾")
    print("4. 將 ngrok.exe 所在路徑加入系統 PATH")
    print("5. 註冊 ngrok 帳號並取得 authtoken")
    print("6. 執行: ngrok config add-authtoken YOUR_TOKEN")

def start_ngrok_tunnel():
    """啟動 ngrok 隧道"""
    print("🚀 啟動 ngrok 隧道...")
    print("將本地 http://localhost:7071 暴露到公網")
    
    try:
        # 啟動 ngrok (背景執行)
        process = subprocess.Popen(
            ["ngrok", "http", "7071", "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("⏳ 等待 ngrok 啟動...")
        time.sleep(3)
        
        # 檢查 ngrok 是否成功啟動
        if process.poll() is None:
            print("✅ ngrok 已啟動")
            print("\n📱 請執行以下步驟:")
            print("1. 開啟另一個終端機視窗")
            print("2. 執行: curl http://localhost:4040/api/tunnels")
            print("3. 或開啟瀏覽器前往: http://localhost:4040")
            print("4. 複製 public_url (https://xxx.ngrok.io)")
            print("5. 在 LINE Developer Console 設定 webhook URL:")
            print("   https://YOUR_NGROK_URL.ngrok.io/api/callback")
            
            print(f"\n🔄 ngrok 程序 PID: {process.pid}")
            print("要停止 ngrok，請按 Ctrl+C 或執行: taskkill /F /PID", process.pid)
            
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ ngrok 啟動失敗")
            print(f"錯誤: {stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ 找不到 ngrok 執行檔")
        install_ngrok_guide()
        return None
    except Exception as e:
        print(f"❌ 啟動 ngrok 時發生錯誤: {e}")
        return None

def get_ngrok_url():
    """取得 ngrok 公開 URL"""
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    public_url = tunnel.get('public_url')
                    print(f"🌐 ngrok 公開 URL: {public_url}")
                    print(f"📝 LINE webhook URL: {public_url}/api/callback")
                    return public_url
        return None
    except Exception as e:
        print(f"⚠️ 無法自動取得 ngrok URL: {e}")
        print("請手動前往 http://localhost:4040 查看")
        return None

def setup_test_environment():
    """設定測試環境"""
    print("🔧 設定測試環境...")
    
    # 確保測試模式已啟用
    os.environ["LINE_TEST_MODE"] = "true"
    os.environ["LINE_SKIP_SIGNATURE"] = "true"
    
    print("✅ 測試模式已啟用")
    print("✅ 簽章驗證已跳過")

def main():
    """主函數"""
    print("🌐 LINE Webhook Port Forward 設定器")
    print("=" * 50)
    
    # 檢查 ngrok
    if not check_ngrok():
        print("❌ ngrok 未安裝")
        install_ngrok_guide()
        return False
    
    # 設定測試環境
    setup_test_environment()
    
    print("\n📋 設定步驟:")
    print("1. 確保 Azure Functions 正在運行 (func host start)")
    print("2. 啟動 ngrok 隧道")
    print("3. 在 LINE Developer Console 設定 webhook URL")
    print("4. 發送測試訊息")
    
    try:
        choice = input("\n是否要啟動 ngrok 隧道？(y/N): ").strip().lower()
    except KeyboardInterrupt:
        print("\n操作已取消")
        return False
    
    if choice == 'y':
        # 檢查 Azure Functions 是否運行
        try:
            import requests
            response = requests.get("http://localhost:7071/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Azure Functions 正在運行")
            else:
                print("⚠️ Azure Functions 可能未正常運行，請檢查")
        except:
            print("❌ 無法連接到 Azure Functions")
            print("請確認是否已執行: func host start")
            return False
        
        # 啟動 ngrok
        process = start_ngrok_tunnel()
        if process:
            time.sleep(2)
            get_ngrok_url()
            
            print("\n🎯 現在您可以:")
            print("1. 在 LINE 中發送訊息測試")
            print("2. 觀察 Azure Functions 的日誌輸出")
            print("3. 使用 Ctrl+C 停止")
            
            try:
                # 保持程式執行直到用戶中斷
                while process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ 停止 ngrok...")
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                print("✅ ngrok 已停止")
            
            return True
        else:
            return False
    else:
        print("請手動設定 port forwarding")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
