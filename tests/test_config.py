"""
Test Configuration

Centralized configuration for test execution including repository URLs,
test data, and environment settings.
"""

import os

class TestConfig:
    """Central configuration for all tests"""
    
    # Repository URLs
    DEFAULT_REPO_URL = "https://gecgithub01.walmart.com/GRC/RiskAgentAnalyzer.git"
    DEFAULT_REPO_BRANCH = "v1"
    DEFAULT_REPO_TREE_URL = f"{DEFAULT_REPO_URL}/tree/{DEFAULT_REPO_BRANCH}"
    
    # Alternative repositories for multi-repo testing
    MULTI_REPO_URLS = [
        "https://gecgithub01.walmart.com/GRC/RiskAgentAnalyzer.git",
        "https://gecgithub01.walmart.com/GRC/TestRepo2.git"
    ]
    
    # Test data
    SAMPLE_PR_NUMBER = 1
    SAMPLE_AUTHOR = "test_user"
    SAMPLE_FILE_EXTENSIONS = ['.py', '.java', '.js', '.jsx']
    
    # Environment settings
    TEST_OUTPUT_DIR = os.path.join(os.getcwd(), "reports", "test_runs")
    TEMP_TEST_DIR = "/tmp/risk_analyzer_tests"
    
    # Mock PR data template
    @staticmethod
    def get_mock_pr_data(pr_number=1, repo_url=None, title="Test PR", state="open"):
        """Generate mock PR data with configurable repository"""
        if repo_url is None:
            repo_url = TestConfig.DEFAULT_REPO_URL
            
        return {
            'number': pr_number,
            'title': title,
            'state': state,
            'user': {'login': TestConfig.SAMPLE_AUTHOR},
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z',
            'base': {
                'ref': TestConfig.DEFAULT_REPO_BRANCH,
                'repo': {'clone_url': repo_url}
            },
            'head': {'ref': 'feature-branch'},
            'html_url': f"{repo_url}/pull/{pr_number}",
            'additions': 50,
            'deletions': 10,
            'changed_files': 3
        }
    
    @staticmethod
    def get_mock_file_data(filename="test.py", status="modified"):
        """Generate mock file data"""
        return {
            'filename': filename,
            'status': status,
            'additions': 30,
            'deletions': 5,
            'patch': '+def new_feature():\n+    return True',
            'full_content': 'def main():\n    pass'
        }
    
    @staticmethod
    def get_repository_urls(count=1):
        """Get repository URLs for testing"""
        if count == 1:
            return [TestConfig.DEFAULT_REPO_URL]
        else:
            return TestConfig.MULTI_REPO_URLS[:count]

# Allow override via environment variables
TEST_REPO_URL = os.getenv('TEST_REPO_URL', TestConfig.DEFAULT_REPO_URL)
TEST_REPO_BRANCH = os.getenv('TEST_REPO_BRANCH', TestConfig.DEFAULT_REPO_BRANCH)
