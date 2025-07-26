#!/usr/bin/env python3
# debug_env.py - 診斷環境變數設定

import os
import sys

def check_environment():
    """檢查所有必要的環境變數"""
    
    required_vars = [
        "LINE_ACCESS_TOKEN",
        "LINE_CHANNEL_SECRET", 
        "TARGET_ID",
        "FLOW_VERIFY_TOKEN",
        "OPENAI_API_KEY"
    ]
    
    optional_vars = [
        "OPENAI_MODEL",
        "AzureWebJobsStorage",
        "FUNCTIONS_WORKER_RUNTIME"
    ]
    
    print("=== 環境變數診斷報告 ===\n")
    
    # 檢查必要變數
    print("必要環境變數:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: 已設定 (長度: {len(value)})")
        else:
            print(f"✗ {var}: 未設定")
            missing_vars.append(var)
    
    print(f"\n選用環境變數:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"- {var}: 未設定")
    
    print(f"\n=== 診斷結果 ===")
    if missing_vars:
        print(f"❌ 缺少 {len(missing_vars)} 個必要環境變數: {', '.join(missing_vars)}")
        print("\n建議解決方案:")
        print("1. 檢查 Azure Function App 的 'Configuration' > 'Application settings'")
        print("2. 確保所有必要的環境變數都已正確設定")
        print("3. 重新部署應用程式")
        return False
    else:
        print("✅ 所有必要的環境變數都已設定")
        return True

def test_imports():
    """測試所有必要的套件導入"""
    print("\n=== 套件導入測試 ===")
    
    packages = [
        ("azure.functions", "Azure Functions"),
        ("linebot.v3", "LINE Bot SDK"),
        ("openai", "OpenAI"),
        ("bs4", "BeautifulSoup4"),
        ("flask", "Flask")
    ]
    
    failed_imports = []
    for package, name in packages:
        try:
            __import__(package)
            print(f"✓ {name}: 導入成功")
        except ImportError as e:
            print(f"✗ {name}: 導入失敗 - {e}")
            failed_imports.append(name)
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} 個套件導入失敗: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ 所有套件導入成功")
        return True

if __name__ == "__main__":
    print("開始診斷...")
    
    env_ok = check_environment()
    import_ok = test_imports()
    
    print(f"\n=== 總結 ===")
    if env_ok and import_ok:
        print("✅ 所有檢查都通過，應用程式應該可以正常運行")
        sys.exit(0)
    else:
        print("❌ 發現問題，請根據上述建議進行修復")
        sys.exit(1)
