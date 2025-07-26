# 文件索引

這裡包含了專案的所有文件和指南。

## 📚 主要文件

### 快速開始
- [QUICK_START.md](QUICK_START.md) - 快速部署指南
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 詳細部署說明

### 開發指南
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - 測試指南
- [TEST_SETUP.md](TEST_SETUP.md) - 測試環境設定
- [FUNCTION_APP_UNIFIED_GUIDE.md](FUNCTION_APP_UNIFIED_GUIDE.md) - 統一應用程式指南

### 特殊功能設定
- [LINE_TEST_MODE_GUIDE.md](LINE_TEST_MODE_GUIDE.md) - LINE 測試模式
- [SIGNATURE_SKIP_GUIDE.md](SIGNATURE_SKIP_GUIDE.md) - 簽章跳過設定

### 範例檔案
- [real_line_webhook_example.json](real_line_webhook_example.json) - LINE Webhook 範例

## 📖 閱讀順序建議

### 新用戶
1. [QUICK_START.md](QUICK_START.md) - 了解如何快速開始
2. [TESTING_GUIDE.md](TESTING_GUIDE.md) - 測試功能

### 開發者
1. [FUNCTION_APP_UNIFIED_GUIDE.md](FUNCTION_APP_UNIFIED_GUIDE.md) - 應用程式架構
2. [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 遷移說明
3. [LINE_TEST_MODE_GUIDE.md](LINE_TEST_MODE_GUIDE.md) - 測試模式設定

### 維護人員
1. [TESTING_GUIDE.md](TESTING_GUIDE.md) - 測試策略


## 🔧 快速參考

### 本地開發
```bash
# 複製環境變數範例
cp ../local.settings.json.example ../local.settings.json

# 安裝相依套件
pip install -r ../requirements.txt

# 啟動本地伺服器
func host start
```

### 快速測試
```bash
# 執行完整測試
python -m pytest ../tests/ -v

# 檢查健康狀態
curl http://localhost:7071/api/health
```

### 部署檢查
```bash
# 檢查環境設定
python ../check_environment.py

# 驗證部署狀態
python ../verify_deployment.py
```

1. [FUNCTION_APP_UNIFIED_GUIDE.md](FUNCTION_APP_UNIFIED_GUIDE.md) - 應用程式結構
2. [TEST_SETUP.md](TEST_SETUP.md) - 設定開發環境

## 🔧 實用工具

### 環境設定
```bash
# 複製環境變數範例
cp ../local.settings.json.example ../local.settings.json

# 安裝相依套件
pip install -r ../requirements.txt
```

### 快速測試
```bash
# 執行完整測試
python -m pytest ../tests/ -v

# 執行特定測試
python ../tests/test_function_app_unified.py
```

### 部署準備
```bash
# 檢查環境
python ../scripts/check_environment.py

# 準備部署
python ../scripts/prepare_deployment.py
```
