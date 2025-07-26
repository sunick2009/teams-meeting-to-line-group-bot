# LINE Callback 測試模式指南

## 概述

為了測試 LINE Bot 功能而不需要真實的 LINE 簽章驗證，我們加入了測試模式功能。在測試模式下，系統會跳過簽章驗證，允許您直接發送模擬的 LINE webhook 事件來測試翻譯功能。

## 測試模式環境變數

### 本地測試

在 `local.settings.json` 中加入以下環境變數：

```json
{
  "IsEncrypted": false,
  "Values": {
    // ... 其他環境變數 ...
    "LINE_TEST_MODE": "true",
    "LINE_SKIP_SIGNATURE": "true"
  }
}
```

### Azure 部署測試

使用 Azure CLI 設定環境變數：

```bash
# 啟用測試模式
az functionapp config appsettings set --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP --settings "LINE_TEST_MODE=true"
az functionapp config appsettings set --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP --settings "LINE_SKIP_SIGNATURE=true"

# 重新啟動 Function App
az functionapp restart --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP
```

或使用提供的腳本：
```bash
python enable_test_mode_azure.py
```

## 測試模式功能

### 1. 簽章驗證跳過
- `LINE_TEST_MODE=true` 或 `LINE_SKIP_SIGNATURE=true` 時，系統會跳過 LINE 簽章驗證
- 不需要 `X-Line-Signature` 標頭
- 可以直接發送 JSON 格式的測試資料

### 2. 事件解析增強
- 測試模式下，系統會直接解析 JSON 內容而不使用 LINE SDK parser
- 創建模擬的事件物件來處理翻譯請求
- 支援文字訊息的翻譯測試

### 3. 詳細日誌記錄
- 測試模式下會記錄更詳細的請求內容（前 200 字元）
- 明確標示測試模式狀態
- 提供完整的錯誤堆疊資訊

## 執行測試

### 自動測試

```bash
# 本地測試（需要先啟動 Azure Functions）
func host start

# 在另一個終端執行測試
python test_with_skip_signature.py
```

### 手動測試

使用提供的測試腳本：
```bash
python test_function_app_unified.py
```

選擇測試端點，然後腳本會自動執行以下測試：
1. 健康檢查
2. Teams Webhook
3. LINE Callback（包含測試模式）
4. 未知端點處理

### 測試 payload 範例

#### 英文翻譯測試
```json
{
  "destination": "test_destination",
  "events": [
    {
      "type": "message",
      "mode": "active",
      "timestamp": 1643723400000,
      "source": {
        "type": "user",
        "userId": "test_user_id"
      },
      "replyToken": "test_reply_token_12345",
      "message": {
        "id": "test_message_id",
        "type": "text",
        "text": "Hello, this is a test message for translation!"
      }
    }
  ]
}
```

#### 中文翻譯測試
```json
{
  "destination": "test_destination",
  "events": [
    {
      "type": "message",
      "mode": "active",
      "timestamp": 1643723400000,
      "source": {
        "type": "user",
        "userId": "test_user_id"
      },
      "replyToken": "test_reply_token_67890",
      "message": {
        "id": "test_message_id_2",
        "type": "text",
        "text": "你好，這是一個測試中文翻譯的訊息。"
      }
    }
  ]
}
```

## 測試端點

### 本地測試
- 健康檢查: `http://localhost:7071/api/health`
- LINE Callback: `http://localhost:7071/api/callback`

### Azure 測試
- 健康檢查: `https://YOUR_FUNCTION_APP.azurewebsites.net/api/health`
- LINE Callback: `https://YOUR_FUNCTION_APP.azurewebsites.net/api/callback`

## 健康檢查中的測試模式資訊

健康檢查端點 (`/api/health`) 會顯示測試模式狀態：

```json
{
  "status": "healthy",
  "service": "unified-bot",
  "test_mode": {
    "enabled": true,
    "signature_skip": true,
    "warning": "⚠️ 測試模式已啟用 - 僅供開發測試使用"
  }
  // ... 其他健康檢查資訊
}
```

## 日誌分析

### 正常運作的日誌範例

```
[request_id] ⚠️ 測試模式已啟用 - 將跳過簽章驗證
[request_id] 收到內容大小: 234 字元
[request_id] 請求內容: {"destination":"test_destination","events":[{"type":"message"...
[request_id] 測試模式: 跳過簽章驗證
[request_id] 測試模式: 直接解析 JSON 事件
[request_id] 測試模式: 從 JSON 解析到 1 個原始事件
[request_id] 測試模式: 創建模擬事件 - Hello, this is a test message...
[request_id] 解析到 1 個事件
[request_id] 處理事件 1/1: MockMessageEvent
[request_id] 收到文字訊息: Hello, this is a test message for translation!
[request_id] 翻譯方向: 英文 -> 繁體中文
[request_id] 開始 OpenAI 翻譯請求
[request_id] 翻譯完成，長度: 28
[request_id] 翻譯回覆發送成功
[request_id] LINE callback 處理完成
```

## 安全性注意事項

⚠️ **重要警告**：
- 測試模式會跳過所有簽章驗證，這會讓您的端點不安全
- 僅在開發和測試環境中使用測試模式
- 完成測試後，請務必停用測試模式並恢復簽章驗證
- 生產環境中絕對不要啟用測試模式

## 停用測試模式

### 本地環境
從 `local.settings.json` 中移除或設為 `false`：
```json
{
  "LINE_TEST_MODE": "false",
  "LINE_SKIP_SIGNATURE": "false"
}
```

### Azure 環境
```bash
# 移除測試模式環境變數
az functionapp config appsettings delete --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP --setting-names "LINE_TEST_MODE"
az functionapp config appsettings delete --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP --setting-names "LINE_SKIP_SIGNATURE"

# 重新啟動 Function App
az functionapp restart --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP
```

或使用腳本：
```bash
python enable_test_mode_azure.py
# 選擇選項 2 來停用測試模式
```

## 疑難排解

### 常見問題

1. **仍然出現簽章驗證錯誤**
   - 確認環境變數是否正確設定
   - 檢查 Function App 是否已重新啟動
   - 查看健康檢查端點確認測試模式狀態

2. **解析到 0 個事件**
   - 檢查 JSON 格式是否正確
   - 確認 `events` 陣列包含有效的訊息事件
   - 查看日誌確認是否正確進入測試模式

3. **翻譯功能不工作**
   - 檢查 OpenAI API 金鑰是否正確設定
   - 確認網路連線是否正常
   - 查看翻譯相關的錯誤日誌

### 檢查清單

- [ ] 測試模式環境變數已設定
- [ ] Function App 已重新啟動（Azure 部署）
- [ ] 健康檢查顯示測試模式已啟用
- [ ] 測試 payload 格式正確
- [ ] 所有必要的環境變數已設定
- [ ] 網路連線正常

## 相關檔案

- `function_app.py` - 主要的 Function App 程式碼
- `test_function_app_unified.py` - 統一測試腳本
- `test_with_skip_signature.py` - 啟用測試模式的執行器
- `enable_test_mode_azure.py` - Azure 測試模式管理器
- `local.settings.json` - 本地環境設定
