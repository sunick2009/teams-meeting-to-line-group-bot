# 快速開始指南

## 🚀 快速部署到 Azure Cloud Function

### 1. 環境準備
```bash
# 安裝相依套件
pip install -r requirements.txt

# 複製環境變數範例檔案
copy local.settings.json.example local.settings.json
```

### 2. 設定環境變數
編輯 `local.settings.json`：
```json
{
  "IsEncrypted": false,
  "Values": {
    "LINE_ACCESS_TOKEN": "你的LINE Bot存取權杖",
    "LINE_CHANNEL_SECRET": "你的LINE Bot頻道密鑰", 
    "TARGET_ID": "LINE群組或用戶ID",
    "FLOW_VERIFY_TOKEN": "Teams Flow驗證權杖",
    "OPENAI_API_KEY": "你的OpenAI API金鑰",
    "OPENAI_MODEL": "gpt-4o"
  }
}
```

### 3. 本地測試
```bash
# 執行測試
python test_unified_app.py

# 本地運行
python app_unified.py --port 8000 --debug
```

### 4. Azure 部署
```bash
# 建立 Azure 資源
az functionapp create --name your-function-name --resource-group your-rg

# 設定環境變數
az functionapp config appsettings set --name your-function-name --settings "LINE_ACCESS_TOKEN=..."

# 部署
func azure functionapp publish your-function-name
```

## 📋 API 端點

部署完成後，您的 Function 將提供：

- **健康檢查**: `GET https://your-function.azurewebsites.net/api/health`
- **Teams Webhook**: `POST https://your-function.azurewebsites.net/api/teamshook?token=verify_token`
- **LINE Bot**: `POST https://your-function.azurewebsites.net/api/callback`

## 🔧 功能驗證

### Teams 會議通知
1. 在 Teams Flow 中設定 Webhook URL
2. 創建會議並測試通知

### LINE 翻譯功能  
1. 在 LINE Developers Console 設定 Webhook URL
2. 向 Bot 發送中文或英文訊息測試翻譯

## 📚 文件參考

- **完整部署指南**: `README_DEPLOYMENT.md`
- **遷移指南**: `MIGRATION_GUIDE.md`
- **整併總結**: `INTEGRATION_SUMMARY.md`

## 🆘 問題排除

### 測試失敗
```bash
python test_unified_app.py
```
應該顯示「🎉 所有測試都通過！」

### 部署問題
檢查 `README_DEPLOYMENT.md` 中的疑難排解章節

### 功能異常
1. 檢查環境變數設定
2. 查看 Azure Function 日誌
3. 驗證 API 金鑰有效性
