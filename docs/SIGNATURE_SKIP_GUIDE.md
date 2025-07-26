# LINE Bot 簽章跳過測試指南

## 修改說明

為了測試 LINE callback 功能，我們添加了跳過簽章檢查的選項。這允許您在不需要正確 LINE 簽章的情況下測試翻譯功能。

## 主要修改

### 1. 環境變數設定
- 添加了 `SKIP_SIGNATURE_CHECK` 環境變數（預設為 `true`）
- 在 Azure Function App 設定中，您可以設定此變數為 `false` 來啟用正常的簽章檢查

### 2. 測試模式功能
當 `skip_signature_check = true` 時：
- 跳過 LINE 簽章驗證
- 直接解析 JSON 內容
- 實際執行翻譯功能（僅記錄結果，不回傳到 LINE）
- 提供詳細的除錯日誌

### 3. 健康檢查改善
- 添加了測試模式狀態資訊
- 顯示當前的 `skip_signature_check` 設定

## 測試步驟

### 1. 檢查健康狀態
```bash
curl https://your-function-app.azurewebsites.net/api/health
```

查看回應中的 `test_mode` 欄位：
```json
{
  "test_mode": {
    "skip_signature_check": true,
    "skip_signature_check_env": "true"
  }
}
```

### 2. 測試 LINE Callback
發送一個模擬的 LINE webhook 請求：

```bash
curl -X POST https://your-function-app.azurewebsites.net/api/callback \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: test-signature" \
  -d '{
    "events": [
      {
        "type": "message",
        "message": {
          "type": "text",
          "text": "Hello, world!"
        },
        "replyToken": "test-reply-token"
      }
    ]
  }'
```

### 3. 檢查日誌
在 Azure Function App 的日誌中，您應該看到類似以下的輸出：

```
[request-id] 測試模式：解析 JSON 內容
[request-id] 測試模式：找到 1 個事件
[request-id] 事件 1: type=message
[request-id] 訊息類型: text
[request-id] 收到文字訊息: Hello, world!
[request-id] 翻譯結果: 哈囉，世界！...
[request-id] 測試模式：翻譯成功（實際環境會回傳給 LINE）
```

## 恢復正常模式

當您準備好使用真實的 LINE 簽章時：
1. 在 Azure Function App 設定中將 `SKIP_SIGNATURE_CHECK` 設為 `false`
2. 確保您的 LINE Channel Secret 設定正確
3. 重新部署或重啟 Function App

## 疑難排解

### 如果看到 "解析到 0 個事件"
- 檢查是否已正確設定 `SKIP_SIGNATURE_CHECK=true`
- 確認請求的 JSON 格式正確
- 檢查 `events` 陣列是否存在且包含正確的訊息結構

### 如果翻譯失敗
- 檢查 `OPENAI_API_KEY` 是否正確設定
- 確認 OpenAI API 配額是否足夠
- 檢查網路連線是否正常

## 注意事項

⚠️ **安全提醒**: 在生產環境中必須啟用簽章檢查 (`SKIP_SIGNATURE_CHECK=false`)，以確保只有 LINE 平台能夠呼叫您的 webhook。

✅ **測試建議**: 使用此測試模式驗證翻譯功能正常運作後，再設定真實的 LINE Bot webhook URL。
