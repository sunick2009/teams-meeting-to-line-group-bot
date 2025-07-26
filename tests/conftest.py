"""
pytest 配置和測試 fixtures
提供測試中需要的共用設定和模擬物件
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# 測試用的環境變數
TEST_ENV_VARS = {
    "LINE_ACCESS_TOKEN": "test_line_access_token_12345",
    "LINE_CHANNEL_SECRET": "test_line_channel_secret_12345", 
    "TARGET_ID": "test_target_id_12345",
    "FLOW_VERIFY_TOKEN": "test_verify_token_12345",
    "OPENAI_API_KEY": "test_openai_api_key_12345",
    "OPENAI_MODEL": "gpt-4o",
    "SKIP_SIGNATURE_VALIDATION": "true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test"
}

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """設定測試環境變數"""
    with patch.dict(os.environ, TEST_ENV_VARS):
        yield

@pytest.fixture
def mock_line_api():
    """模擬 LINE Bot API"""
    mock_api = Mock()
    mock_api.push_message = Mock()
    mock_api.reply_message = Mock()
    return mock_api

@pytest.fixture 
def mock_openai_client():
    """模擬 OpenAI 客戶端"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Mocked translation result"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def sample_teams_webhook():
    """範例 Teams webhook 資料"""
    return {
        "attachments": [
            {
                "name": "Test Meeting",
                "content": json.dumps({
                    "meetingJoinUrl": "https://teams.microsoft.com/l/meetup-join/test"
                })
            }
        ],
        "body": {
            "content": "<p>會議時間: 2025-01-26 14:00</p>"
        }
    }

@pytest.fixture
def sample_line_webhook():
    """範例 LINE webhook 資料"""
    return {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {
                    "type": "user",
                    "userId": "test_user_id"
                },
                "message": {
                    "type": "text",
                    "text": "Hello, this is a test message"
                }
            }
        ]
    }

@pytest.fixture
def mock_azure_function_request():
    """模擬 Azure Function 請求物件"""
    mock_req = Mock()
    mock_req.method = "POST"
    mock_req.headers = {
        "Content-Type": "application/json",
        "X-Line-Signature": "test_signature"
    }
    return mock_req

@pytest.fixture
def mock_webhook_logger():
    """模擬 webhook logger"""
    mock_logger = Mock()
    mock_logger.log_webhook.return_value = {"request_id": "test_request_id"}
    return mock_logger

@pytest.fixture
def mock_reply_token_manager():
    """模擬 reply token 管理器"""
    mock_manager = Mock()
    mock_manager.is_token_used.return_value = False
    mock_manager.mark_token_used.return_value = None
    mock_manager.get_stats.return_value = {
        "active_tokens_count": 0,
        "token_lifetime_minutes": 60,
        "oldest_token_age_minutes": 0
    }
    return mock_manager

# pytest 標記
pytest_plugins = []

def pytest_configure(config):
    """pytest 配置"""
    config.addinivalue_line("markers", "integration: 整合測試")
    config.addinivalue_line("markers", "unit: 單元測試") 
    config.addinivalue_line("markers", "webhook: Webhook 相關測試")
    config.addinivalue_line("markers", "azure: Azure Functions 測試")
    config.addinivalue_line("markers", "slow: 較慢的測試")

def pytest_collection_modifyitems(config, items):
    """修改測試項目，添加標記"""
    for item in items:
        # 根據檔案名稱自動添加標記
        if "webhook" in item.nodeid:
            item.add_marker(pytest.mark.webhook)
        if "azure" in item.nodeid:
            item.add_marker(pytest.mark.azure)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
