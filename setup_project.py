#!/usr/bin/env python3
"""
專案設置腳本
用於快速設置開發環境和檢查專案配置
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(text):
    """列印標題"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_step(step, text):
    """列印步驟"""
    print(f"\n[步驟 {step}] {text}")

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print(f"❌ Python 版本不支援: {version.major}.{version.minor}")
        print("需要 Python 3.8 或更新版本")
        return False
    print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_file_exists(filepath, required=True):
    """檢查檔案是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {filepath}")
        return True
    else:
        status = "❌" if required else "⚠️"
        print(f"{status} {filepath} (缺失)")
        return not required

def setup_environment():
    """設置環境變數檔案"""
    example_file = "local.settings.json.example"
    target_file = "local.settings.json"
    
    if not os.path.exists(target_file) and os.path.exists(example_file):
        try:
            import shutil
            shutil.copy(example_file, target_file)
            print(f"✅ 已複製 {example_file} 到 {target_file}")
            print("⚠️  請編輯 local.settings.json 設定您的環境變數")
            return True
        except Exception as e:
            print(f"❌ 複製檔案失敗: {e}")
            return False
    elif os.path.exists(target_file):
        print(f"✅ {target_file} 已存在")
        return True
    else:
        print(f"❌ 找不到 {example_file}")
        return False

def install_dependencies():
    """安裝相依套件"""
    try:
        print("正在安裝相依套件...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 相依套件安裝完成")
            return True
        else:
            print(f"❌ 安裝失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 安裝過程出錯: {e}")
        return False

def run_tests():
    """執行測試"""
    try:
        print("正在執行測試...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 所有測試通過")
            return True
        else:
            print(f"❌ 測試失敗:\n{result.stdout}\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 測試執行出錯: {e}")
        return False

def check_azure_tools():
    """檢查 Azure 工具"""
    tools = {
        "func": "Azure Functions Core Tools",
        "az": "Azure CLI"
    }
    
    results = {}
    for tool, name in tools.items():
        try:
            result = subprocess.run([tool, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"✅ {name}: {version}")
                results[tool] = True
            else:
                print(f"❌ {name}: 未安裝")
                results[tool] = False
        except FileNotFoundError:
            print(f"❌ {name}: 未安裝")
            results[tool] = False
    
    return results

def main():
    """主函數"""
    print_header("Teams Meeting to LINE Group Bot - 專案設置")
    
    # 檢查當前目錄
    if not os.path.exists("function_app.py"):
        print("❌ 請在專案根目錄執行此腳本")
        sys.exit(1)
    
    # 步驟 1: 檢查 Python 版本
    print_step(1, "檢查 Python 版本")
    if not check_python_version():
        sys.exit(1)
    
    # 步驟 2: 檢查核心檔案
    print_step(2, "檢查專案檔案")
    core_files = [
        "function_app.py",
        "requirements.txt",
        "host.json",
        "local.settings.json.example"
    ]
    
    all_files_exist = True
    for file in core_files:
        if not check_file_exists(file):
            all_files_exist = False
    
    if not all_files_exist:
        print("❌ 缺少必要檔案，請檢查專案完整性")
        sys.exit(1)
    
    # 步驟 3: 設置環境變數
    print_step(3, "設置環境變數檔案")
    setup_environment()
    
    # 步驟 4: 安裝相依套件
    print_step(4, "安裝相依套件")
    if not install_dependencies():
        print("⚠️  相依套件安裝失敗，請手動執行: pip install -r requirements.txt")
    
    # 步驟 5: 檢查 Azure 工具
    print_step(5, "檢查 Azure 工具")
    azure_tools = check_azure_tools()
    
    # 步驟 6: 執行測試
    print_step(6, "執行測試")
    if not run_tests():
        print("⚠️  測試失敗，請檢查配置後重新執行")
    
    # 完成
    print_header("設置完成")
    print("\n🎉 專案設置完成！")
    print("\n下一步:")
    print("1. 編輯 local.settings.json 設定您的環境變數")
    print("2. 執行 func start 啟動本地開發伺服器")
    print("3. 查看 docs/ 目錄了解詳細文件")
    
    if not azure_tools.get("func", False):
        print("\n⚠️  建議安裝 Azure Functions Core Tools:")
        print("   npm install -g azure-functions-core-tools@4 --unsafe-perm true")
    
    if not azure_tools.get("az", False):
        print("\n⚠️  建議安裝 Azure CLI:")
        print("   https://docs.microsoft.com/zh-tw/cli/azure/install-azure-cli")

if __name__ == "__main__":
    main()
