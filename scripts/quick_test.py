# quick_test.py - 快速測試 Reply Token 修復
import sys
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import():
    """測試模組匯入"""
    logger.info("🔍 測試模組匯入...")
    
    try:
        from reply_token_manager import reply_token_manager
        logger.info("✅ reply_token_manager 匯入成功")
        
        # 測試基本功能
        stats = reply_token_manager.get_stats()
        logger.info(f"📊 Reply Token 統計: {stats}")
        
        # 測試假 token 檢測
        test_tokens = [
            ("test_reply_token", True),
            ("mock_reply_token", True),
            ("real_token_123", False),
            ("test_abc123", True)
        ]
        
        for token, expected in test_tokens:
            result = reply_token_manager.is_test_token(token)
            status = "✅" if result == expected else "❌"
            logger.info(f"{status} Token '{token}' -> 測試token: {result} (預期: {expected})")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ 匯入失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        return False

def test_function_app():
    """測試 function_app 匯入"""
    logger.info("🔍 測試 function_app 匯入...")
    
    try:
        import function_app
        logger.info("✅ function_app 匯入成功")
        return True
    except Exception as e:
        logger.error(f"❌ function_app 匯入失敗: {e}")
        return False

def test_reply_token_manager_functionality():
    """測試 Reply Token 管理器核心功能"""
    logger.info("🔍 測試 Reply Token 管理器核心功能...")
    
    try:
        from reply_token_manager import reply_token_manager
        
        # 測試 token 使用追蹤
        test_token = "test_token_12345"
        
        # 初始狀態：未使用
        if reply_token_manager.is_token_used(test_token):
            logger.error(f"❌ 新 token 不應該被標記為已使用")
            return False
        
        # 標記為已使用
        if not reply_token_manager.mark_token_used(test_token, "test_request"):
            logger.error(f"❌ 無法標記 token 為已使用")
            return False
        
        # 檢查是否已使用
        if not reply_token_manager.is_token_used(test_token):
            logger.error(f"❌ Token 應該被標記為已使用")
            return False
        
        # 嘗試重複標記
        if reply_token_manager.mark_token_used(test_token, "test_request"):
            logger.error(f"❌ 不應該能重複標記相同 token")
            return False
        
        logger.info("✅ Reply Token 管理器核心功能測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ Reply Token 管理器測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始快速測試...")
    logger.info("=" * 50)
    
    tests = [
        ("模組匯入", test_import),
        ("Function App 匯入", test_function_app),
        ("Reply Token 管理器功能", test_reply_token_manager_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 執行: {test_name}")
        logger.info("-" * 30)
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} - 通過")
            else:
                logger.error(f"❌ {test_name} - 失敗")
        except Exception as e:
            logger.error(f"💥 {test_name} - 異常: {e}")
    
    logger.info("=" * 50)
    logger.info(f"🎯 測試完成")
    logger.info(f"📊 結果: {passed}/{total} 通過 ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 所有測試通過！Reply Token 修復已就緒")
        return 0
    else:
        logger.error("⚠️ 部分測試失敗，請檢查錯誤訊息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
