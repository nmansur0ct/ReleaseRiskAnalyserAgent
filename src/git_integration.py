"""
Git Integration Module
Provides functionality to fetch pull request data from Git repositories
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse
from abc import ABC, abstractmethod
import logging

try:
    from environment_config import get_env_config
except ImportError:
    # Fallback for standalone execution
    import os
    class MockEnvConfig:
        def get_git_config(self):
            return {
                'access_token': os.getenv('GIT_ACCESS_TOKEN'),
                'provider': os.getenv('GIT_PROVIDER', 'github'),
                'default_repo_url': os.getenv('GIT_DEFAULT_REPO_URL', 'https://github.com/microsoft/vscode')
            }
    def get_env_config():
        return MockEnvConfig()

logger = logging.getLogger(__name__)

class GitProvider(ABC):
    """Base class for Git repository providers"""
    
    def __init__(self, access_token: Optional[str] = None, api_base_url: str = ""):
        self.access_token = access_token
        self.api_base_url = api_base_url
        self.session = None
        
        if self.access_token:
            try:
                import requests
                self.session = requests.Session()
                self.session.headers.update({
                    'Authorization': f'token {self.access_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'RiskAnalyzer/1.0'
                })
            except ImportError:
                logger.warning("requests package not installed. Install with: pip install requests")
    
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        return bool(self.access_token and self.session)
    
    @abstractmethod
    async def get_pull_request(self, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific pull request"""
        pass
    
    @abstractmethod
    async def get_pull_requests(self, repo_url: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch multiple pull requests"""
        pass
    
    @abstractmethod
    async def get_pull_request_files(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch files changed in a pull request"""
        pass
    
    @abstractmethod
    async def get_pull_request_comments(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch comments on a pull request"""
        pass

class GitHubProvider(GitProvider):
    """GitHub API provider"""
    
    def __init__(self, access_token: Optional[str] = None):
        super().__init__(access_token, "https://api.github.com")
    
    async def get_pull_request(self, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific pull request"""
        if not self.validate_config():
            logger.warning("GitHub provider not properly configured, using mock data")
            return self._generate_mock_pr_data(repo_url, pr_number)
        
        try:
            owner, repo = self._parse_github_url(repo_url)
            url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            
            # In a real implementation, you would make the actual API call
            # For now, return mock data
            await asyncio.sleep(0.1)  # Simulate API delay
            
            # Actual implementation would be:
            # response = self.session.get(url)
            # if response.status_code == 200:
            #     pr_data = response.json()
            #     return self._transform_github_pr_data(pr_data)
            # else:
            #     logger.error(f"Failed to fetch PR {pr_number}: {response.status_code}")
            #     return None
            
            return self._generate_mock_pr_data(repo_url, pr_number)
            
        except Exception as e:
            logger.error(f"Error fetching PR {pr_number} from {repo_url}: {e}")
            return None
    
    async def get_pull_requests(self, repo_url: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch multiple pull requests"""
        if not self.validate_config():
            logger.warning("GitHub provider not properly configured, using mock data")
            return [self._generate_mock_pr_data(repo_url, i) for i in range(1, limit + 1)]
        
        try:
            owner, repo = self._parse_github_url(repo_url)
            url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
            
            params = {
                'state': state,
                'per_page': limit,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            # In a real implementation, you would make the actual API call
            # For now, return mock data
            await asyncio.sleep(0.1)  # Simulate API delay
            
            # Actual implementation would be:
            # response = self.session.get(url, params=params)
            # if response.status_code == 200:
            #     prs_data = response.json()
            #     return [self._transform_github_pr_data(pr) for pr in prs_data]
            # else:
            #     logger.error(f"Failed to fetch PRs: {response.status_code}")
            #     return []
            
            return [self._generate_mock_pr_data(repo_url, i) for i in range(1, limit + 1)]
            
        except Exception as e:
            logger.error(f"Error fetching PRs from {repo_url}: {e}")
            return []
    
    async def get_pull_request_files(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch files changed in a pull request"""
        if not self.validate_config():
            logger.warning("GitHub provider not properly configured, using mock data")
            return self._generate_mock_files_data()
        
        try:
            owner, repo = self._parse_github_url(repo_url)
            url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            
            if self.session:
                try:
                    response = self.session.get(url)
                    if response.status_code == 200:
                        files = response.json()
                        result = []
                        for file in files:
                            result.append({
                                'filename': file.get('filename'),
                                'status': file.get('status'),
                                'additions': file.get('additions', 0),
                                'deletions': file.get('deletions', 0),
                                'changes': file.get('changes', 0),
                                'patch': file.get('patch', '')
                            })
                        logger.info(f"Fetched {len(result)} real files for PR #{pr_number}")
                        return result
                    else:
                        logger.warning(f"Failed to fetch files: {response.status_code}, using mock data")
                        return self._generate_mock_files_data()
                except Exception as api_error:
                    logger.error(f"API call failed: {api_error}, using mock data")
                    return self._generate_mock_files_data()
            
            return self._generate_mock_files_data()
            
        except Exception as e:
            logger.error(f"Error fetching PR files {pr_number} from {repo_url}: {e}")
            return []
    
    async def get_pull_request_comments(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch comments on a pull request (issue comments and review comments)"""
        if not self.validate_config():
            logger.warning("GitHub provider not properly configured, using mock data")
            return self._generate_mock_comments_data(pr_number)
        
        try:
            owner, repo = self._parse_github_url(repo_url)
            
            # Fetch both issue comments and review comments from GitHub API
            all_comments = []
            
            if self.session:
                try:
                    # Fetch issue comments (general PR comments)
                    issue_comments_url = f"{self.api_base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
                    issue_response = self.session.get(issue_comments_url)
                    
                    if issue_response.status_code == 200:
                        issue_comments = issue_response.json()
                        for comment in issue_comments:
                            all_comments.append({
                                'id': comment.get('id'),
                                'user': comment.get('user', {}).get('login', 'Unknown'),
                                'body': comment.get('body', ''),
                                'created_at': comment.get('created_at'),
                                'updated_at': comment.get('updated_at'),
                                'type': 'issue_comment',
                                'url': comment.get('html_url')
                            })
                    else:
                        logger.warning(f"Failed to fetch issue comments: {issue_response.status_code}")
                    
                    # Fetch review comments (inline code review comments)
                    review_comments_url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
                    review_response = self.session.get(review_comments_url)
                    
                    if review_response.status_code == 200:
                        review_comments = review_response.json()
                        for comment in review_comments:
                            all_comments.append({
                                'id': comment.get('id'),
                                'user': comment.get('user', {}).get('login', 'Unknown'),
                                'body': comment.get('body', ''),
                                'created_at': comment.get('created_at'),
                                'updated_at': comment.get('updated_at'),
                                'type': 'review_comment',
                                'path': comment.get('path'),
                                'line': comment.get('line'),
                                'url': comment.get('html_url')
                            })
                    else:
                        logger.warning(f"Failed to fetch review comments: {review_response.status_code}")
                    
                    # Sort comments by creation date
                    all_comments.sort(key=lambda x: x.get('created_at', ''))
                    
                    logger.info(f"Fetched {len(all_comments)} real comments for PR #{pr_number}")
                    return all_comments
                    
                except Exception as api_error:
                    logger.error(f"API call failed: {api_error}, falling back to mock data")
                    return self._generate_mock_comments_data(pr_number)
            
            # Fallback to mock data if session not available
            logger.warning("No session available, using mock data")
            return self._generate_mock_comments_data(pr_number)
            
        except Exception as e:
            logger.error(f"Error fetching PR comments {pr_number} from {repo_url}: {e}")
            return []
    
    def _parse_github_url(self, repo_url: str) -> tuple[str, str]:
        """Parse GitHub repository URL to extract owner and repo name"""
        # Handle various GitHub URL formats
        if repo_url.startswith('https://github.com/'):
            path = repo_url.replace('https://github.com/', '').rstrip('/')
            # Remove branch/tree path if present (e.g., /tree/main or /tree/v1)
            if '/tree/' in path:
                path = path.split('/tree/')[0]
            elif '/pull/' in path:
                path = path.split('/pull/')[0]
        elif repo_url.startswith('git@github.com:'):
            path = repo_url.replace('git@github.com:', '').replace('.git', '').rstrip('/')
        else:
            # Assume it's already in owner/repo format
            path = repo_url.rstrip('/')
        
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    def _transform_github_pr_data(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GitHub API response to our standard format"""
        return {
            'id': pr_data.get('id'),
            'number': pr_data.get('number'),
            'title': pr_data.get('title', ''),
            'body': pr_data.get('body', ''),
            'state': pr_data.get('state'),
            'author': pr_data.get('user', {}).get('login', ''),
            'created_at': pr_data.get('created_at'),
            'updated_at': pr_data.get('updated_at'),
            'url': pr_data.get('html_url'),
            'api_url': pr_data.get('url'),
            'additions': pr_data.get('additions', 0),
            'deletions': pr_data.get('deletions', 0),
            'changed_files_count': pr_data.get('changed_files', 0),
            'base_branch': pr_data.get('base', {}).get('ref', ''),
            'head_branch': pr_data.get('head', {}).get('ref', ''),
            'mergeable': pr_data.get('mergeable'),
            'labels': [label.get('name') for label in pr_data.get('labels', [])],
            'assignees': [assignee.get('login') for assignee in pr_data.get('assignees', [])],
            'reviewers': [],  # Would need separate API call
            'changed_files': []  # Would need separate API call
        }
    
    def _generate_mock_pr_data(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """Generate mock PR data for testing"""
        mock_prs = [
            {
                'id': 123456780 + pr_number,
                'number': pr_number,
                'title': f"Add user authentication and payment processing #{pr_number}",
                'body': f"This PR #{pr_number} adds OAuth authentication and Stripe payment integration. "
                       "Includes database migrations and new API endpoints for enhanced security.",
                'state': 'open',
                'author': f'developer{pr_number}@company.com',
                'created_at': '2024-10-30T10:00:00Z',
                'updated_at': '2024-10-31T15:30:00Z',
                'url': f'{repo_url}/pull/{pr_number}',
                'api_url': f'https://api.github.com/repos/company/app/pulls/{pr_number}',
                'additions': 342 + (pr_number * 10),
                'deletions': 28 + (pr_number * 2),
                'changed_files_count': 7 + pr_number,
                'base_branch': 'main',
                'head_branch': f'feature/auth-payment-{pr_number}',
                'mergeable': True,
                'labels': ['enhancement', 'security', 'payment'],
                'assignees': ['lead-dev', 'security-reviewer'],
                'reviewers': ['tech-lead', 'security-team'],
                'changed_files': [
                    f"src/auth/oauth{pr_number}.py",
                    f"src/payments/stripe_integration{pr_number}.py",
                    f"src/api/auth_endpoints{pr_number}.py",
                    f"src/api/payment_endpoints{pr_number}.py",
                    f"migrations/{pr_number:03d}_add_user_table.sql",
                    "config/database.yml",
                    "requirements.txt"
                ]
            },
            {
                'id': 123456790 + pr_number,
                'number': pr_number,
                'title': f"Fix security vulnerability in session management #{pr_number}",
                'body': f"Critical security fix #{pr_number} for session management. "
                       "Addresses CVE-2024-1234 and improves token validation.",
                'state': 'open',
                'author': f'security-team{pr_number}@company.com',
                'created_at': '2024-10-29T14:00:00Z',
                'updated_at': '2024-10-31T12:00:00Z',
                'url': f'{repo_url}/pull/{pr_number}',
                'api_url': f'https://api.github.com/repos/company/app/pulls/{pr_number}',
                'additions': 156 + (pr_number * 5),
                'deletions': 89 + (pr_number * 3),
                'changed_files_count': 4 + (pr_number % 3),
                'base_branch': 'main',
                'head_branch': f'hotfix/security-session-{pr_number}',
                'mergeable': True,
                'labels': ['security', 'critical', 'hotfix'],
                'assignees': ['security-lead'],
                'reviewers': ['cto', 'senior-security'],
                'changed_files': [
                    f"src/auth/session{pr_number}.py",
                    f"src/security/token_validator{pr_number}.py",
                    f"tests/security/test_session{pr_number}.py",
                    "src/middleware/auth_middleware.py"
                ]
            }
        ]
        
        # Return one of the mock PRs based on pr_number
        return mock_prs[pr_number % len(mock_prs)]
    
    def _generate_mock_files_data(self) -> List[Dict[str, Any]]:
        """Generate mock files data for testing"""
        return [
            {
                'filename': 'src/auth/oauth.py',
                'status': 'added',
                'additions': 156,
                'deletions': 0,
                'changes': 156,
                'patch': '@@ -0,0 +1,156 @@\n+import oauth2...'
            },
            {
                'filename': 'src/payments/stripe_integration.py',
                'status': 'added',
                'additions': 89,
                'deletions': 0,
                'changes': 89,
                'patch': '@@ -0,0 +1,89 @@\n+import stripe...'
            },
            {
                'filename': 'src/api/auth_endpoints.py',
                'status': 'modified',
                'additions': 45,
                'deletions': 12,
                'changes': 57,
                'patch': '@@ -23,12 +23,45 @@\n def login_endpoint():\n-    pass\n+    # New implementation...'
            },
            {
                'filename': 'config/database.yml',
                'status': 'modified',
                'additions': 8,
                'deletions': 2,
                'changes': 10,
                'patch': '@@ -15,2 +15,8 @@\n database:\n-  old_config\n+  new_config...'
            }
        ]
    
    def _generate_mock_comments_data(self, pr_number: int) -> List[Dict[str, Any]]:
        """Generate mock PR comments data for testing"""
        comments = [
            {
                'id': 1001 + pr_number,
                'user': 'tech-lead',
                'body': 'LGTM! Great work on the authentication implementation. Please ensure all tests pass before merging.',
                'created_at': '2024-10-30T11:30:00Z',
                'updated_at': '2024-10-30T11:30:00Z',
                'type': 'issue_comment'
            },
            {
                'id': 1002 + pr_number,
                'user': 'security-reviewer',
                'body': 'Security review completed. Found one minor issue with token expiration - please extend timeout to 30 minutes instead of 15.',
                'created_at': '2024-10-30T14:15:00Z',
                'updated_at': '2024-10-30T14:15:00Z',
                'type': 'issue_comment'
            },
            {
                'id': 1003 + pr_number,
                'user': f'developer{pr_number}@company.com',
                'body': 'Thanks for the feedback! Updated the token expiration to 30 minutes as suggested.',
                'created_at': '2024-10-31T09:00:00Z',
                'updated_at': '2024-10-31T09:00:00Z',
                'type': 'issue_comment'
            },
            {
                'id': 2001 + pr_number,
                'user': 'code-reviewer',
                'body': 'Consider adding more error handling in the OAuth callback function.',
                'created_at': '2024-10-30T12:45:00Z',
                'updated_at': '2024-10-30T12:45:00Z',
                'type': 'review_comment',
                'path': 'src/auth/oauth.py',
                'line': 45
            },
            {
                'id': 2002 + pr_number,
                'user': 'senior-dev',
                'body': 'Approved with minor suggestions. The payment integration looks solid.',
                'created_at': '2024-10-31T10:30:00Z',
                'updated_at': '2024-10-31T10:30:00Z',
                'type': 'review_comment'
            }
        ]
        return comments

class GitLabProvider(GitProvider):
    """GitLab API provider"""
    
    def __init__(self, access_token: Optional[str] = None, gitlab_url: str = "https://gitlab.com"):
        api_base_url = f"{gitlab_url}/api/v4"
        super().__init__(access_token, api_base_url)
        
        if self.session:
            # GitLab uses different authorization header
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            })

class GitManager:
    """Manages Git repository integrations"""
    
    def __init__(self):
        self.env_config = get_env_config()
        self.providers: Dict[str, GitProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize Git providers based on environment configuration"""
        git_config = self.env_config.get_git_config()
        
        # Initialize GitHub provider
        if git_config.get('access_token'):
            self.providers['github'] = GitHubProvider(
                access_token=git_config['access_token']
            )
        
        # Always have a default provider for testing
        self.providers['mock'] = GitHubProvider()  # Mock provider without token
        
        logger.info(f"Initialized Git providers: {list(self.providers.keys())}")
    
    def get_provider(self, provider_name: str = "github") -> Optional[GitProvider]:
        """Get specific Git provider"""
        return self.providers.get(provider_name, self.providers.get('mock'))
    
    async def fetch_pull_request(self, repo_url: str, pr_number: int, provider: str = "github") -> Optional[Dict[str, Any]]:
        """Fetch a specific pull request"""
        git_provider = self.get_provider(provider)
        if not git_provider:
            logger.error(f"Git provider '{provider}' not available")
            return None
        
        return await git_provider.get_pull_request(repo_url, pr_number)
    
    async def fetch_pull_requests(self, repo_url: str, state: str = "open", limit: int = 10, provider: str = "github") -> List[Dict[str, Any]]:
        """Fetch multiple pull requests"""
        git_provider = self.get_provider(provider)
        if not git_provider:
            logger.error(f"Git provider '{provider}' not available")
            return []
        
        return await git_provider.get_pull_requests(repo_url, state, limit)
    
    async def fetch_pull_request_files(self, repo_url: str, pr_number: int, provider: str = "github") -> List[Dict[str, Any]]:
        """Fetch files changed in a pull request"""
        git_provider = self.get_provider(provider)
        if not git_provider:
            logger.error(f"Git provider '{provider}' not available")
            return []
        
        return await git_provider.get_pull_request_files(repo_url, pr_number)
    
    async def fetch_pull_request_comments(self, repo_url: str, pr_number: int, provider: str = "github") -> List[Dict[str, Any]]:
        """Fetch comments on a pull request"""
        git_provider = self.get_provider(provider)
        if not git_provider:
            logger.error(f"Git provider '{provider}' not available")
            return []
        
        return await git_provider.get_pull_request_comments(repo_url, pr_number)
    
    def detect_provider_from_url(self, repo_url: str) -> str:
        """Detect the appropriate provider based on repository URL"""
        if 'github.com' in repo_url:
            return 'github'
        elif 'gitlab.com' in repo_url or 'gitlab' in repo_url:
            return 'gitlab'
        else:
            logger.warning(f"Unknown Git provider for URL: {repo_url}, using default")
            return 'github'  # Default to GitHub

# Global Git manager instance
_git_manager = None

def get_git_manager() -> GitManager:
    """Get the global Git manager instance"""
    global _git_manager
    if _git_manager is None:
        _git_manager = GitManager()
    return _git_manager

def reload_git_manager():
    """Reload the global Git manager with updated configuration"""
    global _git_manager
    _git_manager = GitManager()

# Convenience functions for common operations
async def fetch_pr_data(repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
    """Convenience function to fetch PR data"""
    manager = get_git_manager()
    provider = manager.detect_provider_from_url(repo_url)
    return await manager.fetch_pull_request(repo_url, pr_number, provider)

async def fetch_recent_prs(repo_url: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function to fetch recent PRs"""
    manager = get_git_manager()
    provider = manager.detect_provider_from_url(repo_url)
    return await manager.fetch_pull_requests(repo_url, "open", limit, provider)