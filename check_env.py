#!/usr/bin/env python3
# check_env.py - 檢查環境變數是否正確設定

import os

def check_env_vars():
    """檢查必要的環境變數"""
    required_vars = {
        "LINE_ACCESS_TOKEN": "LINE Bot 的 Access Token",
        "TARGET_ID": "LINE 群組或使用者 ID",
        "FLOW_VERIFY_TOKEN": "Power Automate 驗證 Token"
    }
    
    print("檢查環境變數設定：")
    print("=" * 50)
    
    all_ok = True
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # 隱藏敏感資訊，只顯示前幾個字元
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"✓ {var_name}: {masked_value} ({description})")
        else:
            print(f"✗ {var_name}: 未設定 ({description})")
            all_ok = False
    
    print("=" * 50)
    if all_ok:
        print("✓ 所有環境變數都已正確設定")
    else:
        print("✗ 有環境變數未設定，請檢查 .env 檔案或系統環境變數")
        print("\n建議：")
        print("1. 建立 .env 檔案並設定變數")
        print("2. 或在系統中設定環境變數")
        print("3. 或在 PowerShell 中使用 $env:變數名稱='值' 來設定")

if __name__ == "__main__":
    check_env_vars()
