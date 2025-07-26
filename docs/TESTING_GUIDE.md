# Reply Token 修復測試指南

## 🧪 測試概述
這份指南將幫助您驗證 Reply Token 重複使用問題的修復效果。

## 📋 測試前準備

### 1. 確保 Azure Functions 運行
```powershell
# 在專案目錄中啟動 Azure Functions
cd d:\code\teams-meeting-to-line-group-bot
func host start
```

### 2. 檢查環境變數
確保以下環境變數已設定（測試模式）：
```powershell
# 設定測試模式環境變數
$env:LINE_TEST_MODE = "true"
$env:LINE_SKIP_SIGNATURE = "true"
```

## 🚀 自動化測試

### 執行完整測試套件
```powershell
# 執行自動化測試
python test_reply_token_fix.py
```

### 測試內容包括：
1. **Reply Token 管理器直接測試** - 驗證核心功能
2. **健康檢查測試** - 確認服務狀態和統計資訊
3. **重複 Reply Token 測試** - 模擬重複使用場景
4. **假 Reply Token 測試** - 測試測試模式處理
5. **重複投遞檢測測試** - 驗證重複投遞檢測

## 🔍 手動測試步驟

### 測試 1: 健康檢查
```powershell
# 測試健康檢查端點
curl http://localhost:7071/api/health
```

**預期結果：**
- 狀態碼：200
- 回應包含 `reply_token_manager` 統計資訊
- `active_tokens_count` 顯示目前追蹤的 token 數量

### 測試 2: LINE Webhook 基本功能
```powershell
# 發送測試 webhook
$headers = @{
    "Content-Type" = "application/json"
    "X-Line-Signature" = "test_signature"
}

$body = @{
    events = @(
        @{
            type = "message"
            mode = "active"
            timestamp = [long](Get-Date -UFormat %s) * 1000
            source = @{
                type = "user"
                userId = "test_user_123"
            }
            webhookEventId = [guid]::NewGuid().ToString()
            deliveryContext = @{
                isRedelivery = $false
            }
            message = @{
                id = [guid]::NewGuid().ToString()
                type = "text"
                text = "Hello test message"
            }
            replyToken = "test_unique_token_" + (Get-Date -UFormat %s)
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:7071/api/callback" -Method POST -Headers $headers -Body $body
```

### 測試 3: 重複 Reply Token 測試
```powershell
# 第一次發送
$replyToken = "duplicate_test_token_" + (Get-Date -UFormat %s)
$body = @{
    events = @(
        @{
            type = "message"
            replyToken = $replyToken
            message = @{
                type = "text"
                text = "First message"
            }
            # ... 其他必要欄位
        }
    )
} | ConvertTo-Json -Depth 10

# 發送第一次
Invoke-RestMethod -Uri "http://localhost:7071/api/callback" -Method POST -Headers $headers -Body $body

# 立即發送第二次（相同 reply token）
Invoke-RestMethod -Uri "http://localhost:7071/api/callback" -Method POST -Headers $headers -Body $body
```

**預期結果：**
- 兩次都返回 200
- 日誌顯示第二次跳過處理
- 健康檢查顯示 token 被追蹤

### 測試 4: 假 Reply Token 測試
```powershell
$body = @{
    events = @(
        @{
            type = "message"
            replyToken = "test_reply_token"  # 假的測試 token
            message = @{
                type = "text"
                text = "Test with fake token"
            }
            # ... 其他必要欄位
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:7071/api/callback" -Method POST -Headers $headers -Body $body
```

**預期結果：**
- 返回 200
- 日誌顯示跳過 LINE API 呼叫
- 沒有實際的 API 錯誤

## 📊 監控和驗證

### 1. 檢查 Azure Functions 日誌
觀察以下關鍵日誌訊息：
- `Reply token 已使用過，跳過重複回覆`
- `檢測到測試用假 reply token，跳過 LINE API 呼叫`
- `檢測到重複投遞事件`

### 2. 監控健康檢查統計
```powershell
# 定期檢查統計資訊
while ($true) {
    $health = Invoke-RestMethod -Uri "http://localhost:7071/api/health"
    Write-Host "活躍 tokens: $($health.reply_token_manager.active_tokens_count)"
    Start-Sleep 30
}
```

### 3. 檢查測試結果檔案
```powershell
# 查看自動化測試結果
Get-Content test_results.json | ConvertFrom-Json | Format-List
```

## 🔧 故障排除

### 常見問題

#### 1. Azure Functions 無法啟動
```powershell
# 檢查 Python 環境
python --version
pip list | findstr line

# 重新安裝相依性
pip install -r requirements.txt
```

#### 2. 模組匯入錯誤
```powershell
# 確認檔案存在
Test-Path reply_token_manager.py
Test-Path function_app.py

# 檢查語法錯誤
python -m py_compile reply_token_manager.py
python -m py_compile function_app.py
```

#### 3. 測試失敗
- 確認 Azure Functions 正在運行 (port 7071)
- 檢查防火牆設定
- 確認測試模式環境變數已設定

## 📈 性能測試

### 壓力測試腳本
```powershell
# 發送多個並發請求測試
1..10 | ForEach-Object -Parallel {
    $uniqueToken = "stress_test_token_" + $_ + "_" + (Get-Date -UFormat %s)
    # ... 發送請求邏輯
}
```

## ✅ 驗收標準

測試通過標準：
1. **自動化測試** - 成功率 ≥ 80%
2. **重複 Token 處理** - 正確跳過重複使用
3. **假 Token 處理** - 正確識別和跳過測試 token
4. **日誌記錄** - 詳細記錄所有 token 操作
5. **統計資訊** - 健康檢查正確顯示 token 統計
6. **無 API 錯誤** - 不再出現 "Invalid reply token" 錯誤

## 📝 測試報告範本

### 測試結果記錄
```
測試日期：2025年7月26日
測試環境：本地開發環境
Azure Functions 版本：4.x
Python 版本：3.11.x

測試結果：
✅ Reply Token 管理器功能正常
✅ 重複 token 正確處理
✅ 假 token 正確識別
✅ 日誌記錄完整
✅ 統計資訊準確

建議：
- 部署到 Azure 後重新測試
- 監控生產環境中的 token 統計
- 定期檢查日誌中的警告訊息
```

---

**注意：** 在生產環境測試前，請確保：
1. 備份現有配置
2. 在非尖峰時間進行測試
3. 準備回滾計劃
4. 監控 LINE Bot 服務狀態
