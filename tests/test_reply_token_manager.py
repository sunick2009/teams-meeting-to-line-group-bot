# test_reply_token_fix.py - Reply Token 修復測試套件
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List
import uuid

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReplyTokenFixTester:
    """Reply Token 修復功能測試器"""
    
    def __init__(self, base_url: str = "http://localhost:7071"):
        """
        初始化測試器
        
        Args:
            base_url: Azure Functions 的基礎 URL
        """
        self.base_url = base_url
        self.test_results = []
    
    def test_health_check(self) -> bool:
        """測試健康檢查端點和 Reply Token 管理器統計"""
        logger.info("🔍 測試健康檢查端點...")
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 健康檢查成功，狀態: {data.get('status')}")
                
                # 檢查 Reply Token 管理器統計
                reply_token_stats = data.get('reply_token_manager', {})
                if reply_token_stats:
                    logger.info(f"📊 Reply Token 統計:")
                    logger.info(f"   - 活躍 tokens: {reply_token_stats.get('active_tokens_count', 0)}")
                    logger.info(f"   - Token 生命週期: {reply_token_stats.get('token_lifetime_minutes', 0)} 分鐘")
                    logger.info(f"   - 最舊 token 年齡: {reply_token_stats.get('oldest_token_age_minutes', 0)} 分鐘")
                else:
                    logger.warning("⚠️ 未找到 Reply Token 管理器統計資訊")
                
                self.test_results.append({"test": "health_check", "status": "pass", "data": data})
                return True
            else:
                logger.error(f"❌ 健康檢查失敗，狀態碼: {response.status_code}")
                self.test_results.append({"test": "health_check", "status": "fail", "error": f"Status {response.status_code}"})
                return False
                
        except Exception as e:
            logger.error(f"❌ 健康檢查異常: {e}")
            self.test_results.append({"test": "health_check", "status": "error", "error": str(e)})
            return False
    
    def test_line_webhook_with_duplicate_tokens(self) -> bool:
        """測試 LINE Webhook 重複 Reply Token 處理"""
        logger.info("🔍 測試 LINE Webhook 重複 Reply Token 處理...")
        
        # 創建模擬的 LINE Webhook 事件
        test_reply_token = f"test_token_{int(time.time())}"
        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "mode": "active",
                    "timestamp": int(time.time() * 1000),
                    "source": {
                        "type": "user",
                        "userId": "test_user_123"
                    },
                    "webhookEventId": str(uuid.uuid4()),
                    "deliveryContext": {
                        "isRedelivery": False
                    },
                    "message": {
                        "id": str(uuid.uuid4()),
                        "type": "text",
                        "text": "Hello test message"
                    },
                    "replyToken": test_reply_token
                }
            ]
        }
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Line-Signature": "test_signature"
            }
            
            # 第一次發送 - 應該成功處理
            logger.info(f"📤 發送第一次 Webhook 請求 (Reply Token: {test_reply_token[:10]}...)")
            response1 = requests.post(
                f"{self.base_url}/api/callback",
                json=webhook_payload,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"📥 第一次回應狀態: {response1.status_code}")
            
            # 立即發送第二次 - 應該跳過處理（模擬重複投遞）
            logger.info(f"📤 發送第二次 Webhook 請求 (相同 Reply Token)")
            response2 = requests.post(
                f"{self.base_url}/api/callback",
                json=webhook_payload,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"📥 第二次回應狀態: {response2.status_code}")
            
            # 兩次都應該返回 200，但第二次應該在日誌中顯示跳過處理
            if response1.status_code == 200 and response2.status_code == 200:
                logger.info("✅ 重複 Reply Token 測試通過")
                self.test_results.append({
                    "test": "duplicate_reply_token", 
                    "status": "pass",
                    "first_response": response1.status_code,
                    "second_response": response2.status_code
                })
                return True
            else:
                logger.error(f"❌ 重複 Reply Token 測試失敗")
                self.test_results.append({
                    "test": "duplicate_reply_token", 
                    "status": "fail",
                    "first_response": response1.status_code,
                    "second_response": response2.status_code
                })
                return False
                
        except Exception as e:
            logger.error(f"❌ 重複 Reply Token 測試異常: {e}")
            self.test_results.append({"test": "duplicate_reply_token", "status": "error", "error": str(e)})
            return False
    
    def test_line_webhook_with_test_token(self) -> bool:
        """測試 LINE Webhook 假 Reply Token 處理"""
        logger.info("🔍 測試 LINE Webhook 假 Reply Token 處理...")
        
        # 使用測試用的假 token
        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "mode": "active",
                    "timestamp": int(time.time() * 1000),
                    "source": {
                        "type": "user",
                        "userId": "test_user_123"
                    },
                    "webhookEventId": str(uuid.uuid4()),
                    "deliveryContext": {
                        "isRedelivery": False
                    },
                    "message": {
                        "id": str(uuid.uuid4()),
                        "type": "text",
                        "text": "Test message with fake token"
                    },
                    "replyToken": "test_reply_token"  # 假的測試 token
                }
            ]
        }
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Line-Signature": "test_signature"
            }
            
            logger.info(f"📤 發送假 Reply Token Webhook 請求")
            response = requests.post(
                f"{self.base_url}/api/callback",
                json=webhook_payload,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"📥 假 Reply Token 回應狀態: {response.status_code}")
            
            # 應該返回 200，但在日誌中顯示跳過 LINE API 呼叫
            if response.status_code == 200:
                logger.info("✅ 假 Reply Token 測試通過")
                self.test_results.append({
                    "test": "fake_reply_token", 
                    "status": "pass",
                    "response": response.status_code
                })
                return True
            else:
                logger.error(f"❌ 假 Reply Token 測試失敗")
                self.test_results.append({
                    "test": "fake_reply_token", 
                    "status": "fail",
                    "response": response.status_code
                })
                return False
                
        except Exception as e:
            logger.error(f"❌ 假 Reply Token 測試異常: {e}")
            self.test_results.append({"test": "fake_reply_token", "status": "error", "error": str(e)})
            return False
    
    def test_line_webhook_redelivery_detection(self) -> bool:
        """測試 LINE Webhook 重複投遞檢測"""
        logger.info("🔍 測試 LINE Webhook 重複投遞檢測...")
        
        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "mode": "active",
                    "timestamp": int(time.time() * 1000),
                    "source": {
                        "type": "user",
                        "userId": "test_user_123"
                    },
                    "webhookEventId": str(uuid.uuid4()),
                    "deliveryContext": {
                        "isRedelivery": True  # 標記為重複投遞
                    },
                    "message": {
                        "id": str(uuid.uuid4()),
                        "type": "text",
                        "text": "Redelivery test message"
                    },
                    "replyToken": f"redelivery_token_{int(time.time())}"
                }
            ]
        }
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Line-Signature": "test_signature"
            }
            
            logger.info(f"📤 發送重複投遞 Webhook 請求")
            response = requests.post(
                f"{self.base_url}/api/callback",
                json=webhook_payload,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"📥 重複投遞回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ 重複投遞檢測測試通過")
                self.test_results.append({
                    "test": "redelivery_detection", 
                    "status": "pass",
                    "response": response.status_code
                })
                return True
            else:
                logger.error(f"❌ 重複投遞檢測測試失敗")
                self.test_results.append({
                    "test": "redelivery_detection", 
                    "status": "fail",
                    "response": response.status_code
                })
                return False
                
        except Exception as e:
            logger.error(f"❌ 重複投遞檢測測試異常: {e}")
            self.test_results.append({"test": "redelivery_detection", "status": "error", "error": str(e)})
            return False
    
    def test_reply_token_manager_directly(self) -> bool:
        """直接測試 Reply Token 管理器功能"""
        logger.info("🔍 直接測試 Reply Token 管理器...")
        
        try:
            from reply_token_manager import reply_token_manager
            
            # 測試基本功能
            test_token = f"direct_test_token_{int(time.time())}"
            
            # 檢查初始狀態
            assert not reply_token_manager.is_token_used(test_token), "新 token 不應該被標記為已使用"
            
            # 標記為已使用
            assert reply_token_manager.mark_token_used(test_token, "test_request"), "應該能成功標記 token"
            
            # 檢查是否已使用
            assert reply_token_manager.is_token_used(test_token), "Token 應該被標記為已使用"
            
            # 嘗試重複標記
            assert not reply_token_manager.mark_token_used(test_token, "test_request"), "不應該能重複標記相同 token"
            
            # 測試假 token 檢測
            assert reply_token_manager.is_test_token("test_reply_token"), "應該檢測到測試 token"
            assert reply_token_manager.is_test_token("mock_reply_token"), "應該檢測到模擬 token"
            assert not reply_token_manager.is_test_token("real_token_123"), "不應該誤判真實 token"
            
            # 獲取統計資訊
            stats = reply_token_manager.get_stats()
            assert "active_tokens_count" in stats, "統計資訊應該包含活躍 token 計數"
            assert "token_lifetime_minutes" in stats, "統計資訊應該包含生命週期"
            
            logger.info("✅ Reply Token 管理器直接測試通過")
            logger.info(f"📊 當前統計: {stats}")
            
            self.test_results.append({
                "test": "reply_token_manager_direct", 
                "status": "pass",
                "stats": stats
            })
            return True
            
        except Exception as e:
            logger.error(f"❌ Reply Token 管理器直接測試失敗: {e}")
            self.test_results.append({"test": "reply_token_manager_direct", "status": "error", "error": str(e)})
            return False
    
    def run_all_tests(self) -> Dict:
        """執行所有測試"""
        logger.info("🚀 開始執行 Reply Token 修復測試套件...")
        
        tests = [
            ("Reply Token 管理器直接測試", self.test_reply_token_manager_directly),
            ("健康檢查測試", self.test_health_check),
            ("重複 Reply Token 測試", self.test_line_webhook_with_duplicate_tokens),
            ("假 Reply Token 測試", self.test_line_webhook_with_test_token),
            ("重複投遞檢測測試", self.test_line_webhook_redelivery_detection),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"執行測試: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} 通過")
                else:
                    logger.error(f"❌ {test_name} 失敗")
            except Exception as e:
                logger.error(f"💥 {test_name} 發生異常: {e}")
            
            time.sleep(1)  # 測試間隔
        
        # 生成測試報告
        summary = {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": f"{(passed/total)*100:.1f}%",
            "timestamp": datetime.utcnow().isoformat(),
            "detailed_results": self.test_results
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 測試完成！")
        logger.info(f"{'='*60}")
        logger.info(f"📊 總測試數: {total}")
        logger.info(f"✅ 通過測試: {passed}")
        logger.info(f"❌ 失敗測試: {total - passed}")
        logger.info(f"📈 成功率: {summary['success_rate']}")
        
        return summary

def main():
    """主函數"""
    logger.info("🧪 Reply Token 修復測試套件")
    logger.info("=" * 60)
    
    # 確認 Azure Functions 是否運行
    tester = ReplyTokenFixTester()
    
    # 執行所有測試
    results = tester.run_all_tests()
    
    # 保存測試結果
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n📄 測試結果已保存到 test_results.json")
    
    return results

if __name__ == "__main__":
    main()
