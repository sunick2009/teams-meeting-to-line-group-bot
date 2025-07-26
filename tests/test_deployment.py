"""
部署和配置測試
測試 Azure Functions 部署相關的功能和配置
"""

import pytest
import os
import json
from pathlib import Path


class TestDeploymentStructure:
    """部署結構測試"""

    def test_required_files_exist(self):
        """測試必要的部署檔案是否存在"""
        required_files = [
            'function_app.py',
            'host.json',
            'requirements.txt',
            'local.settings.json.example'
        ]
        
        for file in required_files:
            assert os.path.exists(file), f"缺少必要檔案: {file}"

    def test_host_json_structure(self):
        """測試 host.json 結構正確性"""
        assert os.path.exists('host.json')
        
        with open('host.json', 'r', encoding='utf-8') as f:
            host_config = json.load(f)
        
        # 檢查基本結構
        assert 'version' in host_config
        assert 'functionTimeout' in host_config
        assert 'logging' in host_config
        
        # 檢查 Azure Functions v2 配置
        assert host_config['version'] == '2.0'

    def test_requirements_txt_content(self):
        """測試 requirements.txt 包含必要套件"""
        assert os.path.exists('requirements.txt')
        
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            requirements = f.read()
        
        required_packages = [
            'azure-functions',
            'beautifulsoup4',
            'line-bot-sdk',
            'openai'
        ]
        
        for package in required_packages:
            assert package in requirements, f"缺少必要套件: {package}"

    def test_no_legacy_v1_files(self):
        """測試不存在 Azure Functions v1 的遺留檔案"""
        legacy_patterns = [
            'HttpTrigger/',
            'function.json',
            '*/function.json'
        ]
        
        for pattern in legacy_patterns:
            files = list(Path('.').glob(pattern))
            assert len(files) == 0, f"發現遺留的 v1 檔案: {files}"


class TestEnvironmentConfiguration:
    """環境配置測試"""

    def test_example_settings_file(self):
        """測試範例設定檔案的結構"""
        assert os.path.exists('local.settings.json.example')
        
        with open('local.settings.json.example', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 檢查基本結構
        assert 'Values' in settings
        values = settings['Values']
        
        # 檢查必要的環境變數
        required_vars = [
            'LINE_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET', 
            'TARGET_ID',
            'FLOW_VERIFY_TOKEN',
            'OPENAI_API_KEY',
            'OPENAI_MODEL'
        ]
        
        for var in required_vars:
            assert var in values, f"缺少環境變數設定: {var}"

    def test_env_example_file(self):
        """測試 .env.example 檔案"""
        assert os.path.exists('.env.example')
        
        with open('.env.example', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查包含必要的環境變數
        required_vars = [
            'LINE_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET',
            'TARGET_ID', 
            'FLOW_VERIFY_TOKEN',
            'OPENAI_API_KEY'
        ]
        
        for var in required_vars:
            assert var in content, f".env.example 缺少變數: {var}"


class TestProjectStructure:
    """專案結構測試"""

    def test_documentation_exists(self):
        """測試文件目錄存在且包含基本文件"""
        assert os.path.exists('docs/'), "缺少 docs 目錄"
        assert os.path.exists('README.md'), "缺少 README.md"
        assert os.path.exists('LICENSE'), "缺少 LICENSE 檔案"

    def test_tests_directory_structure(self):
        """測試測試目錄結構"""
        assert os.path.exists('tests/'), "缺少 tests 目錄"
        assert os.path.exists('tests/__init__.py'), "缺少 tests/__init__.py"
        assert os.path.exists('tests/conftest.py'), "缺少 tests/conftest.py"
        assert os.path.exists('tests/data/'), "缺少 tests/data 目錄"

    def test_core_modules_importable(self):
        """測試核心模組可以正常匯入"""
        try:
            import function_app
            assert hasattr(function_app, 'app'), "function_app 缺少 app 物件"
        except ImportError as e:
            pytest.fail(f"無法匯入 function_app: {e}")
        
        try:
            import reply_token_manager
            assert hasattr(reply_token_manager, 'ReplyTokenManager'), "reply_token_manager 缺少主要類別"
        except ImportError as e:
            pytest.fail(f"無法匯入 reply_token_manager: {e}")
        
        try:
            import webhook_logger
            assert hasattr(webhook_logger, 'webhook_logger'), "webhook_logger 缺少主要物件"
        except ImportError as e:
            pytest.fail(f"無法匯入 webhook_logger: {e}")


class TestGitConfiguration:
    """Git 配置測試"""

    def test_gitignore_exists(self):
        """測試 .gitignore 檔案存在且包含必要規則"""
        assert os.path.exists('.gitignore')
        
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        # 檢查包含重要的忽略規則
        important_patterns = [
            '__pycache__/',
            '*.pyc',
            '.env',
            'local.settings.json',
            '*.log'
        ]
        
        for pattern in important_patterns:
            assert pattern in gitignore_content, f".gitignore 缺少規則: {pattern}"

    def test_github_templates_exist(self):
        """測試 GitHub 模板檔案存在"""
        github_files = [
            '.github/ISSUE_TEMPLATE/bug_report.md',
            '.github/ISSUE_TEMPLATE/feature_request.md',
            '.github/pull_request_template.md'
        ]
        
        for file in github_files:
            assert os.path.exists(file), f"缺少 GitHub 模板: {file}"


@pytest.mark.integration
class TestDeploymentValidation:
    """部署驗證測試"""

    def test_function_app_structure(self):
        """測試 function_app.py 的基本結構"""
        import function_app
        
        # 檢查必要的組件
        assert hasattr(function_app, 'app'), "缺少 app 物件"
        
        # 檢查路由是否正確設定
        app = function_app.app
        # 這裡需要根據實際的 Azure Functions 結構來調整測試

    @pytest.mark.slow
    def test_package_imports(self):
        """測試所有套件可以正常匯入"""
        with open('requirements.txt', 'r') as f:
            requirements = f.read().splitlines()
        
        # 過濾掉註解和空行
        packages = [
            line.split('>=')[0].split('==')[0].strip()
            for line in requirements
            if line.strip() and not line.startswith('#')
        ]
        
        # 套件名稱對應表
        package_mapping = {
            'beautifulsoup4': 'bs4',
            'line-bot-sdk': 'linebot',
            'azure-functions': 'azure.functions',
            'python-dotenv': 'dotenv'
        }
        
        failed_imports = []
        for package in packages:
            try:
                # 使用對應的匯入名稱
                import_name = package_mapping.get(package, package.replace('-', '_'))
                __import__(import_name)
            except ImportError:
                failed_imports.append(package)
        
        assert not failed_imports, f"無法匯入套件: {failed_imports}"
