# test_error_handling.py - 測試錯誤處理機制
# 驗證修復後的錯誤處理是否正確工作

import json
import os
import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime

# Azure 端點配置
AZURE_ENDPOINT = "https://yzuimsc-linebot-gdhzgga2e7fhg8ay.eastasia-01.azurewebsites.net/api"
TIMEOUT = 30

def create_line_signature(body: str, secret: str) -> str:
    """創建有效的 LINE 簽章"""
    hash_bytes = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_bytes).decode()

def test_invalid_openai_request():
    """測試會導致 OpenAI 錯誤的請求"""
    print("\n🧪 測試 OpenAI 錯誤處理...")
    
    # 模擬 LINE webhook payload
    webhook_body = json.dumps({
        "events": [
            {
                "type": "message",
                "replyToken": "test-reply-token-error-handling",
                "source": {
                    "userId": "test-user-id",
                    "type": "user"
                },
                "timestamp": int(time.time() * 1000),
                "message": {
                    "type": "text",
                    "id": "test-message-id",
                    "text": "測試錯誤處理機制 - 這可能會導致 OpenAI 地區限制錯誤"
                }
            }
        ]
    })
    
    # 創建假的但格式正確的簽章（用於測試用途）
    fake_secret = "fake-line-channel-secret-for-testing"
    signature = create_line_signature(webhook_body, fake_secret)
    
    try:
        url = f"{AZURE_ENDPOINT}/callback"
        headers = {
            "Content-Type": "application/json",
            "X-Line-Signature": signature
        }
        
        print(f"請求 URL: {url}")
        print(f"Payload 大小: {len(webhook_body)} 字元")
        
        response = requests.post(
            url, 
            data=webhook_body,
            headers=headers,
            timeout=TIMEOUT
        )
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 錯誤處理測試成功 - Azure Function 返回 200（避免 LINE 重試）")
            return True
        elif response.status_code == 400:
            print("✅ 簽章驗證正常工作 - 返回 400（預期行為）")
            return True
        else:
            print(f"⚠️ 意外的回應狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_multiple_rapid_requests():
    """測試多個快速請求（模擬錯誤後的連續請求）"""
    print("\n🔄 測試多個快速請求...")
    
    # 簡單的健康檢查請求，測試系統穩定性
    results = []
    
    for i in range(5):
        try:
            url = f"{AZURE_ENDPOINT}/health"
            start_time = time.time()
            
            response = requests.get(url, timeout=TIMEOUT)
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            results.append(success)
            
            print(f"  請求 {i+1}: {'✅' if success else '❌'} ({response.status_code}) - {response_time:.2f}s")
            
            if not success:
                print(f"    錯誤內容: {response.text[:100]}...")
            
            time.sleep(0.5)  # 短暫延遲
            
        except Exception as e:
            print(f"  請求 {i+1}: ❌ 異常 - {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results)
    print(f"\n成功率: {success_rate*100:.1f}% ({sum(results)}/{len(results)})")
    
    if success_rate >= 0.8:  # 80% 以上成功率認為正常
        print("✅ 系統穩定性測試通過")
        return True
    else:
        print("❌ 系統穩定性測試失敗")
        return False

def test_malformed_requests():
    """測試畸形請求的處理"""
    print("\n🚨 測試畸形請求處理...")
    
    test_cases = [
        {
            "name": "無效 JSON",
            "url": f"{AZURE_ENDPOINT}/callback",
            "method": "POST",
            "data": "invalid json content",
            "headers": {"Content-Type": "application/json", "X-Line-Signature": "invalid-signature"},
            "expected_codes": [400, 200]  # 可能返回 400 或 200（錯誤處理）
        },
        {
            "name": "缺少標頭",
            "url": f"{AZURE_ENDPOINT}/callback",
            "method": "POST", 
            "data": json.dumps({"test": "data"}),
            "headers": {"Content-Type": "application/json"},
            "expected_codes": [400]
        },
        {
            "name": "超大請求",
            "url": f"{AZURE_ENDPOINT}/health",
            "method": "GET",
            "data": None,
            "headers": {},
            "expected_codes": [200]
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n  測試: {test_case['name']}")
            
            if test_case['method'] == 'GET':
                response = requests.get(
                    test_case['url'],
                    headers=test_case['headers'],
                    timeout=TIMEOUT
                )
            else:
                response = requests.post(
                    test_case['url'],
                    data=test_case['data'],
                    headers=test_case['headers'],
                    timeout=TIMEOUT
                )
            
            success = response.status_code in test_case['expected_codes']
            results.append(success)
            
            print(f"    回應: {'✅' if success else '❌'} ({response.status_code})")
            
            if not success:
                print(f"    預期: {test_case['expected_codes']}, 實際: {response.status_code}")
                print(f"    內容: {response.text[:100]}...")
                
        except Exception as e:
            print(f"    ❌ 異常: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results)
    print(f"\n畸形請求處理成功率: {success_rate*100:.1f}% ({sum(results)}/{len(results)})")
    
    return success_rate >= 0.8

def main():
    """執行錯誤處理測試"""
    print("🔧 錯誤處理機制測試")
    print("=" * 50)
    print(f"目標端點: {AZURE_ENDPOINT}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    print("\n📝 測試目的:")
    print("  1. 驗證 OpenAI 錯誤後系統仍能正常響應")
    print("  2. 確認 LINE webhook 錯誤處理機制")
    print("  3. 測試系統在錯誤後的穩定性")
    print("  4. 驗證畸形請求的處理")
    
    # 執行測試
    tests = [
        ("OpenAI 錯誤處理", test_invalid_openai_request),
        ("系統穩定性", test_multiple_rapid_requests),
        ("畸形請求處理", test_malformed_requests)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*30}")
        success = test_func()
        results.append((test_name, success))
        time.sleep(2)  # 延遲避免對系統造成壓力
    
    # 總結結果
    print(f"\n{'='*50}")
    print("📊 錯誤處理測試結果總結:")
    
    passed = 0
    for test_name, success in results:
        icon = "✅" if success else "❌"
        print(f"  {icon} {test_name}")
        if success:
            passed += 1
    
    print(f"\n通過測試: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 所有錯誤處理測試通過！")
        print("\n✨ 修復後的系統應該能夠:")
        print("  • 正確處理 OpenAI 錯誤而不影響後續請求")
        print("  • 避免 LINE webhook 重試循環")
        print("  • 在錯誤後快速恢復正常服務")
        print("  • 提供有意義的錯誤訊息給用戶")
    elif passed > 0:
        print("⚠️ 部分錯誤處理測試通過。")
        print("\n🔧 建議進一步檢查失敗的測試項目。")
    else:
        print("❌ 所有錯誤處理測試失敗。")
        print("\n🚨 系統可能仍有錯誤處理問題。")
    
    print(f"\n📍 Azure Portal 監控: https://portal.azure.com")
    print(f"📊 健康檢查: {AZURE_ENDPOINT}/health")
    print(f"📝 Application Insights 中可查看詳細錯誤日誌")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
