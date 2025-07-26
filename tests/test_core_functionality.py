"""
核心功能測試
測試 function_app.py 的主要功能，包括 webhook 處理、翻譯功能等
"""

import pytest
import json
import azure.functions as func
from unittest.mock import Mock, patch, MagicMock
from function_app import app


class TestCoreApplication:
    """應用程式核心功能測試"""

    def test_health_endpoint(self):
        """測試健康檢查端點"""
        # 建立模擬請求
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='http://localhost:7071/api/health',
            headers={}
        )

        # 執行函數
        response = app.function_name(req)

        # 驗證回應
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data['status'] == 'healthy'
        assert data['service'] == 'Teams to LINE Bot'

    @patch('function_app.webhook_logger')
    def test_teams_webhook_basic(self, mock_logger, sample_teams_webhook):
        """測試基本 Teams webhook 處理"""
        mock_logger.log_webhook.return_value = {"request_id": "test_123"}

        # 準備請求
        req = func.HttpRequest(
            method='POST',
            body=json.dumps(sample_teams_webhook).encode(),
            url='http://localhost:7071/api/teams_webhook',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test_token'
            }
        )

        with patch('function_app.send_to_line') as mock_send:
            mock_send.return_value = True
            response = app.function_name(req)

        assert response.status_code == 200
        mock_send.assert_called_once()

    @patch('function_app.webhook_logger')
    @patch('function_app.reply_token_manager')
    @patch('function_app.MessagingApi')
    def test_line_webhook_text_message(self, mock_messaging_api, mock_token_manager, 
                                     mock_logger, sample_line_webhook):
        """測試 LINE text message 處理"""
        # 設定模擬
        mock_logger.log_webhook.return_value = {"request_id": "test_456"}
        mock_token_manager.is_token_used.return_value = False
        mock_api_instance = Mock()
        mock_messaging_api.return_value = mock_api_instance

        # 準備請求
        req = func.HttpRequest(
            method='POST',
            body=json.dumps(sample_line_webhook).encode(),
            url='http://localhost:7071/api/line_webhook',
            headers={
                'Content-Type': 'application/json',
                'X-Line-Signature': 'test_signature'
            }
        )

        with patch('function_app.WebhookParser') as mock_parser:
            mock_event = Mock()
            mock_event.reply_token = "test_reply_token"
            mock_event.message.text = "Hello world"
            mock_parser.return_value.parse.return_value = [mock_event]

            with patch.dict('os.environ', {'SKIP_SIGNATURE_VALIDATION': 'true'}):
                response = app.function_name(req)

        assert response.status_code == 200


class TestTranslationFeatures:
    """翻譯功能測試"""

    @patch('function_app.OpenAI')
    def test_translation_with_openai(self, mock_openai_class):
        """測試 OpenAI 翻譯功能"""
        # 設定模擬回應
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # 直接測試翻譯函數 (如果有的話)
        # 這裡需要根據實際的函數結構調整
        pass

    def test_url_preservation_in_translation(self):
        """測試翻譯時 URL 的保留"""
        test_text = "請查看這個網站 https://example.com 了解更多資訊"
        
        # 這裡應該測試翻譯函數確實保留了 URL
        # 實際實作需要根據 function_app.py 的結構
        pass


class TestWebhookSecurity:
    """Webhook 安全性測試"""

    def test_line_signature_validation_enabled(self):
        """測試 LINE 簽章驗證啟用時的行為"""
        req = func.HttpRequest(
            method='POST',
            body=b'{"test": "data"}',
            url='http://localhost:7071/api/line_webhook',
            headers={
                'Content-Type': 'application/json'
                # 故意不包含 X-Line-Signature
            }
        )

        with patch.dict('os.environ', {'SKIP_SIGNATURE_VALIDATION': 'false'}):
            response = app.function_name(req)

        # 應該因為缺少簽章而回傳錯誤
        assert response.status_code in [400, 401, 403]

    def test_teams_webhook_token_validation(self):
        """測試 Teams webhook token 驗證"""
        req = func.HttpRequest(
            method='POST',
            body=b'{"test": "data"}',
            url='http://localhost:7071/api/teams_webhook',
            headers={
                'Content-Type': 'application/json'
                # 故意不包含正確的 Authorization header
            }
        )

        response = app.function_name(req)
        
        # 應該因為缺少或錯誤的 token 而回傳錯誤
        assert response.status_code in [401, 403]


class TestErrorHandling:
    """錯誤處理測試"""

    def test_invalid_json_request(self):
        """測試無效 JSON 請求的處理"""
        req = func.HttpRequest(
            method='POST',
            body=b'invalid json content',
            url='http://localhost:7071/api/teams_webhook',
            headers={'Content-Type': 'application/json'}
        )

        response = app.function_name(req)
        assert response.status_code == 400

    def test_unsupported_http_method(self):
        """測試不支援的 HTTP 方法"""
        req = func.HttpRequest(
            method='PUT',
            body=b'',
            url='http://localhost:7071/api/health',
            headers={}
        )

        response = app.function_name(req)
        assert response.status_code == 405

    def test_unknown_endpoint(self):
        """測試未知端點"""
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='http://localhost:7071/api/unknown_endpoint',
            headers={}
        )

        response = app.function_name(req)
        assert response.status_code == 404


@pytest.mark.integration
class TestIntegration:
    """整合測試"""

    @pytest.mark.slow
    def test_full_teams_to_line_flow(self, sample_teams_webhook):
        """測試完整的 Teams 到 LINE 流程"""
        # 這是一個較慢的整合測試
        # 測試從接收 Teams webhook 到發送 LINE 訊息的完整流程
        pass

    @pytest.mark.slow  
    def test_full_line_translation_flow(self, sample_line_webhook):
        """測試完整的 LINE 翻譯流程"""
        # 測試從接收 LINE 訊息到回覆翻譯結果的完整流程
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
