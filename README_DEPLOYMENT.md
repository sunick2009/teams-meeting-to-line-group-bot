# Azure Function 整併部署指南

## 概述

這個專案將 Teams Webhook 和 Translation Bot 整併為單一 Azure Function，提供以下功能：
- Teams 會議通知轉發到 LINE
- LINE 訊息雙向翻譯（中英文）

## 專案結構

```
teams-meeting-to-line-group-bot/
├── app_unified.py          # 主要應用程式（整併版）
├── __init__.py            # Azure Function 入口點
├── function.json          # Function 配置
├── host.json             # Host 配置
├── requirements.txt       # 相依套件
├── local.settings.json.example  # 環境變數範例
└── README_DEPLOYMENT.md   # 此檔案
```

## 環境變數設定

### 必要環境變數

| 變數名稱 | 描述 | 範例 |
|---------|------|------|
| `LINE_ACCESS_TOKEN` | LINE Bot 存取權杖 | `your_line_access_token` |
| `LINE_CHANNEL_SECRET` | LINE Bot 頻道密鑰 | `your_line_channel_secret` |
| `TARGET_ID` | LINE 目標群組或用戶 ID | `C1234567890abcdef...` |
| `FLOW_VERIFY_TOKEN` | Teams Flow 驗證權杖 | `your_verify_token` |
| `OPENAI_API_KEY` | OpenAI API 金鑰 | `sk-...` |

### 可選環境變數

| 變數名稱 | 描述 | 預設值 |
|---------|------|--------|
| `OPENAI_MODEL` | OpenAI 模型名稱 | `gpt-4.1` |

## 本地開發設定

1. **建立虛擬環境**：
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **安裝相依套件**：
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數**：
   ```bash
   cp local.settings.json.example local.settings.json
   # 編輯 local.settings.json 填入實際值
   ```

4. **本地測試**：
   ```bash
   # 直接運行 Flask 應用
   python app_unified.py --port 8000 --debug
   
   # 或使用 Azure Functions Core Tools
   func start
   ```

## Azure 部署步驟

### 1. 準備 Azure 資源

```bash
# 建立資源群組
az group create --name rg-teams-line-bot --location "East Asia"

# 建立儲存體帳戶
az storage account create --name stteamslinebot --resource-group rg-teams-line-bot --sku Standard_LRS

# 建立 Function App
az functionapp create \
  --resource-group rg-teams-line-bot \
  --name teams-line-bot-function \
  --storage-account stteamslinebot \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4
```

### 2. 設定環境變數

```bash
# 設定應用程式設定
az functionapp config appsettings set \
  --name teams-line-bot-function \
  --resource-group rg-teams-line-bot \
  --settings \
    "LINE_ACCESS_TOKEN=your_line_access_token" \
    "LINE_CHANNEL_SECRET=your_line_channel_secret" \
    "TARGET_ID=your_target_id" \
    "FLOW_VERIFY_TOKEN=your_verify_token" \
    "OPENAI_API_KEY=your_openai_api_key" \
    "OPENAI_MODEL=gpt-4o"
```

### 3. 部署程式碼

```bash
# 使用 Azure Functions Core Tools
func azure functionapp publish teams-line-bot-function

# 或使用 VS Code Azure Functions 擴充功能
# 或使用 Azure DevOps / GitHub Actions
```

## API 端點

部署後，您的 Function 將提供以下端點：

- **健康檢查**: `GET /api/health`
- **Teams Webhook**: `POST /api/teamshook?token=your_verify_token`
- **LINE Bot Callback**: `POST /api/callback`

## 安全性考量

### 1. 環境變數保護
- 所有敏感資訊都透過環境變數管理
- 使用 Azure Key Vault 存儲機密資訊（推薦）

### 2. 權杖驗證
- Teams Webhook 需要 `FLOW_VERIFY_TOKEN` 驗證
- LINE Bot 使用 HMAC 簽章驗證

### 3. 網路安全
- 建議設定 Azure Application Gateway 或 Front Door
- 啟用 HTTPS Only
- 考慮使用 IP 白名單

### 4. 錯誤處理
- 統一錯誤處理，避免洩露敏感資訊
- 完整的日誌記錄以便除錯

## 監控與日誌

### Application Insights
```bash
# 啟用 Application Insights
az monitor app-insights component create \
  --app teams-line-bot-insights \
  --location "East Asia" \
  --resource-group rg-teams-line-bot

# 連結到 Function App
az functionapp config appsettings set \
  --name teams-line-bot-function \
  --resource-group rg-teams-line-bot \
  --settings "APPINSIGHTS_INSTRUMENTATIONKEY=your_instrumentation_key"
```

### 日誌檢視
- Azure Portal > Function App > 監視 > 日誌
- Application Insights > 查詢
- 即時日誌串流

## 成本優化

1. **消費方案**: 使用 Consumption Plan 降低成本
2. **冷啟動**: 考慮使用 Premium Plan 或 Dedicated Plan 避免冷啟動
3. **資源限制**: 設定適當的 timeout 和 memory 限制

## 疑難排解

### 常見問題

1. **環境變數未設定**
   - 檢查 Azure Function App 的應用程式設定
   - 確保所有必要變數都已設定

2. **LINE Bot 簽章驗證失敗**
   - 檢查 `LINE_CHANNEL_SECRET` 是否正確
   - 確認 Webhook URL 設定正確

3. **Teams Webhook 權杖錯誤**
   - 檢查 `FLOW_VERIFY_TOKEN` 設定
   - 確認 Teams Flow 中的 URL 參數

4. **OpenAI API 錯誤**
   - 檢查 `OPENAI_API_KEY` 是否有效
   - 確認 API 配額和使用限制

### 除錯步驟

1. 檢查 Application Insights 日誌
2. 使用 Postman 或 curl 測試端點
3. 檢查環境變數設定
4. 驗證網路連線性

## 維護與更新

1. **定期更新相依套件**: 檢查 `requirements.txt` 中的套件版本
2. **監控 API 使用量**: 追蹤 OpenAI 和 LINE API 的使用情況
3. **備份設定**: 定期備份環境變數和配置
4. **測試**: 在 staging 環境測試更新

## 進階功能

### 1. 多環境部署
- 開發環境: `dev-teams-line-bot`
- 測試環境: `test-teams-line-bot`
- 生產環境: `prod-teams-line-bot`

### 2. CI/CD 管道
```yaml
# GitHub Actions 範例
name: Deploy to Azure Functions
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Deploy to Azure Functions
      uses: Azure/functions-action@v1
      with:
        app-name: teams-line-bot-function
        package: .
```

### 3. 效能監控
- 設定警示規則
- 監控執行時間和記憶體使用
- 追蹤錯誤率和成功率
