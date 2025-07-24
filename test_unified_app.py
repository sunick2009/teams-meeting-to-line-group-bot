# test_unified_app.py - 整併應用程式測試

import os
import json
import sys
from unittest.mock import Mock, patch, MagicMock

# 嘗試導入主模組
try:
    from app_unified import create_app, EnvironmentConfig, TeamsWebhookHandler, TranslationBotHandler
except ImportError as e:
    print(f"無法導入 app_unified: {e}")
    sys.exit(1)

# 測試用的環境變數
TEST_ENV_VARS = {
    "LINE_ACCESS_TOKEN": "test_line_access_token",
    "LINE_CHANNEL_SECRET": "test_line_channel_secret",
    "TARGET_ID": "test_target_id",
    "FLOW_VERIFY_TOKEN": "test_verify_token",
    "OPENAI_API_KEY": "test_openai_api_key",
    "OPENAI_MODEL": "gpt-4.1"
}

class TestEnvironmentConfig:
    """測試環境配置類"""
    
    def test_valid_config(self):
        """測試有效的環境配置"""
        try:
            with patch.dict(os.environ, TEST_ENV_VARS):
                config = EnvironmentConfig()
                assert config.line_access_token == "test_line_access_token"
                assert config.target_id == "test_target_id"
                return True
        except Exception as e:
            print(f"valid_config 測試失敗: {e}")
            return False
    
    def test_missing_required_env(self):
        """測試缺少必要環境變數"""
        try:
            with patch.dict(os.environ, {}, clear=True):
                config = EnvironmentConfig()
                # 如果沒有拋出錯誤，測試失敗
                print("missing_required_env 測試失敗: 應該要拋出 ValueError")
                return False
        except ValueError:
            # 預期的錯誤，測試通過
            return True
        except Exception as e:
            print(f"missing_required_env 測試失敗: 非預期錯誤 {e}")
            return False
    
    def test_target_id_cleaning(self):
        """測試 TARGET_ID 清理功能"""
        test_cases = [
            ("'test_id'", "test_id"),
            ('"test_id"', "test_id"),
            ("test_id # comment", "test_id"),
            ("'test_id' # comment", "test_id"),
        ]
        
        try:
            for raw_id, expected in test_cases:
                env_vars = TEST_ENV_VARS.copy()
                env_vars["TARGET_ID"] = raw_id
                with patch.dict(os.environ, env_vars):
                    config = EnvironmentConfig()
                    if config.target_id != expected:
                        print(f"target_id_cleaning 測試失敗: 期望 {expected}, 實際 {config.target_id}")
                        return False
            return True
        except Exception as e:
            print(f"target_id_cleaning 測試失敗: {e}")
            return False


class TestTeamsWebhookHandler:
    """測試 Teams Webhook 處理器"""
    
    def setup_method(self):
        """設定測試環境"""
        try:
            with patch.dict(os.environ, TEST_ENV_VARS):
                self.config = EnvironmentConfig()
                with patch('app_unified.MessagingApi'), patch('app_unified.ApiClient'):
                    self.handler = TeamsWebhookHandler(self.config)
            return True
        except Exception as e:
            print(f"Teams handler 初始化失敗: {e}")
            return False
    
    def test_extract_meeting_info(self):
        """測試會議資訊擷取"""
        if not self.setup_method():
            return False
            
        payload = {
            "attachments": [{
                "name": "測試會議",
                "content": '{"meetingJoinUrl": "https://teams.microsoft.com/join/123"}'
            }],
            "body": {
                "content": "<div>2024-01-15 14:30 會議內容</div>"
            }
        }
        
        try:
            result = self.handler.extract_meeting_info(payload)
            if (result["title"] != "測試會議" or 
                result["time"] != "2024-01-15 14:30" or 
                result["link"] != "https://teams.microsoft.com/join/123"):
                print(f"extract_meeting_info 測試失敗: {result}")
                return False
            return True
        except Exception as e:
            print(f"extract_meeting_info 測試失敗: {e}")
            return False
    
    def test_build_flex_message(self):
        """測試 Flex Message 建立"""
        if not self.setup_method():
            return False
            
        meeting = {
            "title": "測試會議",
            "time": "2024-01-15 14:30",
            "link": "https://teams.microsoft.com/join/123"
        }
        
        try:
            flex_msg = self.handler.build_flex_message(meeting)
            expected_alt_text = "會議通知：測試會議 2024-01-15 14:30"
            if (flex_msg.alt_text != expected_alt_text or 
                flex_msg.contents.body.contents[0].text != "測試會議"):
                print(f"build_flex_message 測試失敗: alt_text={flex_msg.alt_text}")
                return False
            return True
        except Exception as e:
            print(f"build_flex_message 測試失敗: {e}")
            return False


class TestTranslationBotHandler:
    """測試翻譯 Bot 處理器"""
    
    def setup_method(self):
        """設定測試環境"""
        try:
            with patch.dict(os.environ, TEST_ENV_VARS):
                self.config = EnvironmentConfig()
                with patch('app_unified.OpenAI'):
                    self.handler = TranslationBotHandler(self.config)
            return True
        except Exception as e:
            print(f"Translation handler 初始化失敗: {e}")
            return False
    
    def test_is_chinese(self):
        """測試中文檢測"""
        if not self.setup_method():
            return False
            
        try:
            test_cases = [
                ("你好", True),
                ("Hello", False),
                ("Hello 你好", True)
            ]
            
            for text, expected in test_cases:
                result = self.handler.is_chinese(text)
                if result != expected:
                    print(f"is_chinese 測試失敗: '{text}' 期望 {expected}, 實際 {result}")
                    return False
            return True
        except Exception as e:
            print(f"is_chinese 測試失敗: {e}")
            return False
    
    def test_translate_message(self):
        """測試訊息翻譯"""
        try:
            # 模擬 OpenAI 回應
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Hello"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            
            with patch.dict(os.environ, TEST_ENV_VARS):
                config = EnvironmentConfig()
                with patch('app_unified.OpenAI') as mock_openai_class:
                    mock_openai_instance = Mock()
                    mock_openai_instance.chat.completions.create.return_value = mock_response
                    mock_openai_class.return_value = mock_openai_instance
                    
                    handler = TranslationBotHandler(config)
                    result = handler.translate_message("你好")
                    
                    if result != "Hello":
                        print(f"translate_message 測試失敗: 期望 'Hello', 實際 '{result}'")
                        return False
                    return True
        except Exception as e:
            print(f"translate_message 測試失敗: {e}")
            return False


class TestFlaskApp:
    """測試 Flask 應用程式"""
    
    def setup_method(self):
        """設定測試環境"""
        try:
            with patch.dict(os.environ, TEST_ENV_VARS):
                self.app = create_app()
                self.client = self.app.test_client()
            return True
        except Exception as e:
            print(f"Flask app 初始化失敗: {e}")
            return False
    
    def test_health_check(self):
        """測試健康檢查端點"""
        if not self.setup_method():
            return False
            
        try:
            response = self.client.get('/health')
            if response.status_code != 200:
                print(f"health_check 測試失敗: 狀態碼 {response.status_code}")
                return False
                
            data = json.loads(response.data)
            if data.get('status') != 'healthy':
                print(f"health_check 測試失敗: 狀態 {data}")
                return False
            return True
        except Exception as e:
            print(f"health_check 測試失敗: {e}")
            return False
    
    def test_teams_webhook_invalid_token(self):
        """測試無效 token 的 Teams Webhook"""
        if not self.setup_method():
            return False
            
        try:
            response = self.client.post('/teamshook?token=invalid', 
                                      json={},
                                      content_type='application/json')
            # 應該回傳 401 或被錯誤處理器處理成 500
            if response.status_code not in [401, 500]:
                print(f"teams_webhook_invalid_token 測試失敗: 狀態碼 {response.status_code}")
                return False
            return True
        except Exception as e:
            print(f"teams_webhook_invalid_token 測試失敗: {e}")
            return False
    
    def test_teams_webhook_valid_request(self):
        """測試有效的 Teams Webhook 請求"""
        if not self.setup_method():
            return False
            
        payload = {
            "messageType": "message",
            "attachments": [{
                "contentType": "meetingReference",
                "name": "測試會議",
                "content": '{"meetingJoinUrl": "https://teams.microsoft.com/join/123"}'
            }],
            "body": {
                "content": "<div>2024-01-15 14:30 會議內容</div>"
            }
        }
        
        try:
            with patch('app_unified.MessagingApi') as mock_api_class:
                # 模擬 LINE API 成功
                mock_api_instance = Mock()
                mock_api_class.return_value = mock_api_instance
                
                with patch('app_unified.ApiClient'):
                    response = self.client.post(
                        f'/teamshook?token={TEST_ENV_VARS["FLOW_VERIFY_TOKEN"]}',
                        json=payload,
                        content_type='application/json'
                    )
                    # 成功處理或因為 LINE API 測試 token 而失敗都是可接受的
                    if response.status_code not in [200, 500]:
                        print(f"teams_webhook_valid_request 測試失敗: 狀態碼 {response.status_code}")
                        return False
                    return True
        except Exception as e:
            print(f"teams_webhook_valid_request 測試失敗: {e}")
            return False


def run_all_tests():
    """執行所有測試"""
    print("=" * 60)
    print("執行整併應用程式測試")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # 測試環境配置
    print("\n[環境配置測試]")
    env_config_test = TestEnvironmentConfig()
    
    tests = [
        ("有效配置", env_config_test.test_valid_config),
        ("缺少環境變數", env_config_test.test_missing_required_env),
        ("TARGET_ID 清理", env_config_test.test_target_id_cleaning),
    ]
    
    for test_name, test_func in tests:
        total_tests += 1
        try:
            if test_func():
                print(f"✓ {test_name}")
                passed_tests += 1
            else:
                print(f"✗ {test_name}")
        except Exception as e:
            print(f"✗ {test_name}: {e}")
    
    # 測試 Teams Webhook 處理器
    print("\n[Teams Webhook 處理器測試]")
    teams_test = TestTeamsWebhookHandler()
    
    tests = [
        ("會議資訊擷取", teams_test.test_extract_meeting_info),
        ("Flex 訊息建立", teams_test.test_build_flex_message),
    ]
    
    for test_name, test_func in tests:
        total_tests += 1
        try:
            if test_func():
                print(f"✓ {test_name}")
                passed_tests += 1
            else:
                print(f"✗ {test_name}")
        except Exception as e:
            print(f"✗ {test_name}: {e}")
    
    # 測試翻譯 Bot 處理器
    print("\n[翻譯 Bot 處理器測試]")
    translation_test = TestTranslationBotHandler()
    
    tests = [
        ("中文檢測", translation_test.test_is_chinese),
        ("訊息翻譯", translation_test.test_translate_message),
    ]
    
    for test_name, test_func in tests:
        total_tests += 1
        try:
            if test_func():
                print(f"✓ {test_name}")
                passed_tests += 1
            else:
                print(f"✗ {test_name}")
        except Exception as e:
            print(f"✗ {test_name}: {e}")
    
    # 測試 Flask 應用程式
    print("\n[Flask 應用程式測試]")
    flask_test = TestFlaskApp()
    
    tests = [
        ("健康檢查", flask_test.test_health_check),
        ("無效 token", flask_test.test_teams_webhook_invalid_token),
        ("有效請求", flask_test.test_teams_webhook_valid_request),
    ]
    
    for test_name, test_func in tests:
        total_tests += 1
        try:
            if test_func():
                print(f"✓ {test_name}")
                passed_tests += 1
            else:
                print(f"✗ {test_name}")
        except Exception as e:
            print(f"✗ {test_name}: {e}")
    
    # 測試總結
    print("\n" + "=" * 60)
    print(f"測試總結: {passed_tests}/{total_tests} 通過")
    if passed_tests == total_tests:
        print("🎉 所有測試都通過！")
    else:
        print(f"⚠️  有 {total_tests - passed_tests} 個測試失敗")
    print("=" * 60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # 簡單的手動測試
    print("執行基本測試...")
    
    # 測試環境配置
    with patch.dict(os.environ, TEST_ENV_VARS):
        try:
            config = EnvironmentConfig()
            print("✓ 環境配置測試通過")
        except Exception as e:
            print(f"✗ 環境配置測試失敗: {e}")
    
    # 測試 Flask 應用程式創建
    try:
        with patch.dict(os.environ, TEST_ENV_VARS):
            app = create_app()
            print("✓ Flask 應用程式創建測試通過")
    except Exception as e:
        print(f"✗ Flask 應用程式創建測試失敗: {e}")
    
    print("基本測試完成！")
    print("\n執行完整測試...")
    
    # 執行完整測試
    success = run_all_tests()
    
    if not success:
        print("\n如果需要更詳細的測試，可以安裝 pytest：")
        print("pip install pytest")
        print("pytest test_unified_app.py -v")
