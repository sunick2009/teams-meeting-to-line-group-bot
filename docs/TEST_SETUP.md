# 測試環境設定說明

## 設定環境變數進行測試

為了正確測試 Teams webhook，您需要設定以下環境變數：

### 方法一：在命令列中設定環境變數（推薦）

**Windows PowerShell:**
```powershell
$env:FLOW_VERIFY_TOKEN = "您的_FLOW_VERIFY_TOKEN"
$env:LINE_CHANNEL_SECRET = "您的_LINE_CHANNEL_SECRET"
python test_webhooks_final.py
```

**Windows Command Prompt:**
```cmd
set FLOW_VERIFY_TOKEN=您的_FLOW_VERIFY_TOKEN
set LINE_CHANNEL_SECRET=您的_LINE_CHANNEL_SECRET
python test_webhooks_final.py
```

**macOS/Linux:**
```bash
export FLOW_VERIFY_TOKEN="您的_FLOW_VERIFY_TOKEN"
export LINE_CHANNEL_SECRET="您的_LINE_CHANNEL_SECRET"
python test_webhooks_final.py
```

### 方法二：創建 .env 檔案

創建一個名為 `.env` 的檔案在專案根目錄：

```env
FLOW_VERIFY_TOKEN=您的_FLOW_VERIFY_TOKEN
LINE_CHANNEL_SECRET=您的_LINE_CHANNEL_SECRET
```

然後修改測試腳本載入 .env 檔案。

### 方法三：直接修改測試腳本

直接在 `test_webhooks_final.py` 中修改這些行：

```python
TEAMS_VERIFY_TOKEN = "您的實際_FLOW_VERIFY_TOKEN"
LINE_CHANNEL_SECRET = "您的實際_LINE_CHANNEL_SECRET"
```

## 如何取得這些值

### FLOW_VERIFY_TOKEN
這是您在 Microsoft Power Automate 或 Teams 設定中配置的驗證 token。

### LINE_CHANNEL_SECRET
這是在 LINE Developers Console 中建立 LINE Bot 時取得的 Channel Secret。

## 測試預期結果

設定正確的環境變數後：
- Teams webhook 應該返回 200 狀態碼
- LINE callback 應該返回 200 狀態碼
- 健康檢查應該返回 200 狀態碼

如果沒有設定環境變數，測試腳本會使用預設值，並顯示相應的警告訊息。
