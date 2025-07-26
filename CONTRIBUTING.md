# 貢獻指南

感謝您考慮為 Teams Meeting to LINE Group Bot 專案做出貢獻！

## 如何貢獻

### 回報 Bug

如果您發現 Bug，請建立一個 Issue 並包含以下資訊：

1. **問題描述** - 清楚描述問題
2. **重現步驟** - 詳細的重現步驟
3. **預期行為** - 描述您期待的正確行為
4. **實際行為** - 描述實際發生的情況
5. **環境資訊** - 作業系統、Python 版本、相依套件版本
6. **日誌資訊** - 相關的錯誤日誌

### 建議新功能

如果您有新功能建議，請建立一個 Feature Request Issue：

1. **功能描述** - 詳細描述建議的功能
2. **使用案例** - 說明這個功能的使用場景
3. **實作建議** - 如果有想法，可以描述實作方式

### 提交 Pull Request

1. **Fork 專案**
   ```bash
   git clone https://github.com/your-username/teams-meeting-to-line-group-bot.git
   cd teams-meeting-to-line-group-bot
   ```

2. **建立功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **設定開發環境**
   ```bash
   pip install -r requirements.txt
   cp local.settings.json.example local.settings.json
   # 編輯 local.settings.json 設定測試環境變數
   ```

4. **進行開發**
   - 遵循現有的程式碼風格
   - 新增適當的測試
   - 更新相關文件

5. **執行測試**
   ```bash
   python -m pytest tests/ -v
   ```

6. **提交變更**
   ```bash
   git add .
   git commit -m "Add: 描述您的變更"
   git push origin feature/your-feature-name
   ```

7. **建立 Pull Request**
   - 提供清楚的標題和描述
   - 參考相關的 Issue
   - 確保所有測試都通過

## 開發指南

### 程式碼風格

- 使用 Python PEP 8 風格指南
- 函數和類別需要適當的文件字串
- 變數和函數名稱使用描述性命名

### 測試

- 為新功能編寫測試
- 確保測試覆蓋率維持在合理水準
- 使用 pytest 框架

### 提交訊息格式

使用以下格式：

```
類型: 簡短描述

詳細描述（如果需要）

相關 Issue: #123
```

類型可以是：
- `Add`: 新增功能
- `Fix`: 修復 Bug
- `Update`: 更新現有功能
- `Docs`: 文件變更
- `Test`: 測試相關
- `Refactor`: 重構程式碼

### 分支命名

- `feature/feature-name` - 新功能
- `bugfix/bug-description` - Bug 修復
- `docs/documentation-update` - 文件更新

## 開發環境設定

### 必要工具

- Python 3.8+
- Azure Functions Core Tools
- Azure CLI
- Git

### 環境變數

複製 `local.settings.json.example` 並設定以下變數：

```json
{
  "IsEncrypted": false,
  "Values": {
    "LINE_ACCESS_TOKEN": "測試用的 LINE Bot Token",
    "LINE_CHANNEL_SECRET": "測試用的 LINE Channel Secret",
    "TARGET_ID": "測試用的 LINE 群組或用戶 ID",
    "FLOW_VERIFY_TOKEN": "測試用的驗證 Token",
    "OPENAI_API_KEY": "OpenAI API 金鑰",
    "OPENAI_MODEL": "gpt-4o",
    "SKIP_SIGNATURE_VALIDATION": "true"
  }
}
```

### 本地測試

```bash
# 安裝相依套件
pip install -r requirements.txt

# 執行測試
python -m pytest tests/ -v

# 啟動本地開發伺服器
func start
```

## 專案結構

```
├── function_app.py           # 主要應用程式
├── app_unified.py           # 統一應用程式（向後相容）
├── reply_token_manager.py   # Reply Token 管理
├── webhook_logger.py        # Webhook 日誌
├── requirements.txt         # Python 相依套件
├── host.json               # Azure Function 設定
├── tests/                  # 測試檔案
├── scripts/                # 輔助腳本
├── docs/                   # 文件
└── README.md               # 專案說明
```

## 程式碼審查

所有的 Pull Request 都會經過程式碼審查：

1. **功能正確性** - 確保功能按預期工作
2. **程式碼品質** - 遵循最佳實作和風格指南
3. **測試覆蓋** - 適當的測試覆蓋
4. **文件更新** - 相關文件是否更新
5. **向後相容** - 是否影響現有功能

## 尋求幫助

如果您需要幫助：

1. 查看現有的 Issues 和 Discussions
2. 閱讀 `docs/` 目錄中的文件
3. 建立新的 Issue 尋求協助

## 行為準則

- 尊重所有參與者
- 建設性的反饋
- 保持友善和專業
- 協助新手貢獻者

感謝您的貢獻！🎉
