"""
Webhook 端點測試
測試 Teams 和 LINE 的 webhook 處理功能
"""

import pytest
import json
import hmac
import hashlib
import base64
import azure.functions as func
from unittest.mock import Mock, patch


class TestWebhookEndpoints:
    """Webhook 端點測試"""

    def test_health_endpoint_basic(self):
        """測試健康檢查端點基本功能"""
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='http://localhost:7071/api/health',
            headers={}
        )
        
        from function_app import app
        response = app.function_name(req)
        
        assert response.status_code == 200
        data = json.loads(response.get_body())
        assert data['status'] == 'healthy'

    @patch('function_app.webhook_logger')
    def test_teams_webhook_valid_request(self, mock_logger, sample_teams_webhook):
        """測試有效的 Teams webhook 請求"""
        mock_logger.log_webhook.return_value = {"request_id": "test_123"}
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps(sample_teams_webhook).encode(),
            url='http://localhost:7071/api/teams_webhook',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test_verify_token_12345'
            }
        )
        
        with patch('function_app.send_to_line') as mock_send:
            mock_send.return_value = True
            from function_app import app
            response = app.function_name(req)
        
        assert response.status_code == 200
        assert mock_send.called

    def test_teams_webhook_invalid_token(self, sample_teams_webhook):
        """測試無效 token 的 Teams webhook 請求"""
        req = func.HttpRequest(
            method='POST',
            body=json.dumps(sample_teams_webhook).encode(),
            url='http://localhost:7071/api/teams_webhook',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer invalid_token'
            }
        )
        
        from function_app import app
        response = app.function_name(req)
        
        assert response.status_code in [401, 403]

    @patch('function_app.webhook_logger')
    @patch('function_app.reply_token_manager')
    def test_line_webhook_valid_signature(self, mock_token_manager, mock_logger, sample_line_webhook):
        """測試有效簽章的 LINE webhook 請求"""
        mock_logger.log_webhook.return_value = {"request_id": "test_456"}
        mock_token_manager.is_token_used.return_value = False
        
        body = json.dumps(sample_line_webhook)
        signature = self._generate_line_signature(body, "test_line_channel_secret_12345")
        
        req = func.HttpRequest(
            method='POST',
            body=body.encode(),
            url='http://localhost:7071/api/line_webhook',
            headers={
                'Content-Type': 'application/json',
                'X-Line-Signature': signature
            }
        )
        
        with patch('function_app.WebhookParser') as mock_parser:
            mock_event = Mock()
            mock_event.reply_token = "test_reply_token"
            mock_event.message.text = "Test message"
            mock_parser.return_value.parse.return_value = [mock_event]
            
            with patch.dict('os.environ', {'SKIP_SIGNATURE_VALIDATION': 'false'}):
                from function_app import app
                response = app.function_name(req)
        
        assert response.status_code == 200

    def test_line_webhook_invalid_signature(self, sample_line_webhook):
        """測試無效簽章的 LINE webhook 請求"""
        body = json.dumps(sample_line_webhook)
        
        req = func.HttpRequest(
            method='POST',
            body=body.encode(),
            url='http://localhost:7071/api/line_webhook',
            headers={
                'Content-Type': 'application/json',
                'X-Line-Signature': 'invalid_signature'
            }
        )
        
        with patch.dict('os.environ', {'SKIP_SIGNATURE_VALIDATION': 'false'}):
            from function_app import app
            response = app.function_name(req)
        
        assert response.status_code in [400, 401, 403]

    def _generate_line_signature(self, body: str, channel_secret: str) -> str:
        """生成 LINE webhook 簽章"""
        hash_bytes = hmac.new(
            channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(hash_bytes).decode('utf-8')


class TestWebhookSecurity:
    """Webhook 安全性測試"""

    def test_missing_content_type(self):
        """測試缺少 Content-Type header"""
        req = func.HttpRequest(
            method='POST',
            body=b'{"test": "data"}',
            url='http://localhost:7071/api/teams_webhook',
            headers={}
        )
        
        from function_app import app
        response = app.function_name(req)
        
        assert response.status_code == 400

    def test_wrong_http_method(self):
        """測試錯誤的 HTTP 方法"""
        req = func.HttpRequest(
            method='GET',
            body=b'',
            url='http://localhost:7071/api/teams_webhook',
            headers={}
        )
        
        from function_app import app
        response = app.function_name(req)
        
        assert response.status_code == 405

    def test_malformed_json(self):
        """測試格式錯誤的 JSON"""
        req = func.HttpRequest(
            method='POST',
            body=b'{"invalid": json}',
            url='http://localhost:7071/api/teams_webhook',
            headers={'Content-Type': 'application/json'}
        )
        
        from function_app import app
        response = app.function_name(req)
        
        assert response.status_code == 400


@pytest.mark.integration
class TestWebhookIntegration:
    """Webhook 整合測試"""

    @pytest.mark.slow
    @patch('function_app.MessagingApi')
    def test_teams_to_line_full_flow(self, mock_messaging_api, sample_teams_webhook):
        """測試完整的 Teams 到 LINE 流程"""
        mock_api = Mock()
        mock_messaging_api.return_value = mock_api
        
        req = func.HttpRequest(
            method='POST',
            body=json.dumps(sample_teams_webhook).encode(),
            url='http://localhost:7071/api/teams_webhook',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test_verify_token_12345'
            }
        )
        
        from function_app import app
        response = app.function_name(req)
        
        assert response.status_code == 200
        # 驗證 LINE API 被調用
        mock_api.push_message.assert_called()

    @pytest.mark.slow 
    @patch('function_app.OpenAI')
    def test_line_translation_full_flow(self, mock_openai, sample_line_webhook):
        """測試完整的 LINE 翻譯流程"""
        # 設定 OpenAI 模擬回應
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello, this is a test message"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        body = json.dumps(sample_line_webhook)
        
        req = func.HttpRequest(
            method='POST',
            body=body.encode(),
            url='http://localhost:7071/api/line_webhook',
            headers={
                'Content-Type': 'application/json',
                'X-Line-Signature': 'test_signature'
            }
        )
        
        with patch.dict('os.environ', {'SKIP_SIGNATURE_VALIDATION': 'true'}):
            with patch('function_app.WebhookParser') as mock_parser:
                mock_event = Mock()
                mock_event.reply_token = "test_reply_token"
                mock_event.message.text = "你好世界"
                mock_parser.return_value.parse.return_value = [mock_event]
                
                from function_app import app
                response = app.function_name(req)
        
        assert response.status_code == 200
