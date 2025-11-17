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
    async def get_pull_requests(self, repo_url: str) -> List[Dict[str, Any]]:
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
    """GitHub API provider with support for GitHub Enterprise"""
    
    def __init__(self, access_token: Optional[str] = None):
        # Default to public GitHub API
        api_base_url = "https://api.github.com"
        super().__init__(access_token, api_base_url)
    
    def _get_api_base_url_for_repo(self, repo_url: str) -> str:
        """Determine the correct API base URL based on the repository URL"""
        parsed_url = urlparse(repo_url.strip())
        
        if parsed_url.hostname:
            hostname = parsed_url.hostname.lower()
            
            # Handle Walmart GitHub Enterprise
            if 'walmart.com' in hostname or 'gecgithub01' in hostname:
                # For Walmart GitHub Enterprise, use the same hostname with /api/v3
                return f"https://{parsed_url.hostname}/api/v3"
            
            # Handle other GitHub Enterprise instances
            elif hostname != 'github.com' and 'github' in hostname:
                return f"https://{parsed_url.hostname}/api/v3"
                
        # Default to public GitHub
        return "https://api.github.com"
    
    def _check_repository_access(self, owner: str, repo: str, api_base_url: str):
        """Check if we can access the repository and provide helpful debugging info"""
        if not self.session:
            logger.error("No session available for repository access check")
            return
            
        try:
            # Try to get basic repository information
            repo_url = f"{api_base_url}/repos/{owner}/{repo}"
            logger.info(f"Checking repository access: {repo_url}")
            
            response = self.session.get(repo_url)
            
            if response.status_code == 200:
                repo_info = response.json()
                logger.info(f"Repository exists: {repo_info.get('full_name')}")
                logger.info(f"Repository is private: {repo_info.get('private', False)}")
                logger.info(f"Repository default branch: {repo_info.get('default_branch')}")
            elif response.status_code == 404:
                logger.error(f"Repository not found: {owner}/{repo}")
                logger.error("Possible causes:")
                logger.error("1. Repository name is incorrect")
                logger.error("2. Repository is private and token lacks access")
                logger.error("3. Repository is in a different organization")
                logger.error("4. URL format issue - browser URLs with /tree/branch are supported but repository must exist")
                
                # Try to list repositories the user has access to
                user_repos_url = f"{api_base_url}/user/repos"
                user_response = self.session.get(user_repos_url, params={'per_page': 100})
                if user_response.status_code == 200:
                    repos = user_response.json()
                    logger.info(f"Token has access to {len(repos)} repositories")
                    
                    # Look for similar repository names
                    similar_repos = [r['full_name'] for r in repos if repo.lower() in r['name'].lower() or 'risk' in r['name'].lower()]
                    if similar_repos:
                        logger.info(f"Similar repositories found: {similar_repos}")
                        logger.info("Try using one of the similar repositories above instead")
                else:
                    logger.error(f"Could not list user repositories: {user_response.status_code}")
                    
            elif response.status_code == 403:
                logger.error(f"Access forbidden to repository: {owner}/{repo}")
                logger.error("Token may not have sufficient permissions")
            else:
                logger.error(f"Unexpected response checking repository: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error checking repository access: {e}")
    

    async def get_pull_request(self, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific pull request"""
        if not self.validate_config():
            logger.error("GitHub provider not properly configured. Missing access token.")
            return None
        
        try:
            owner, repo, _ = self._parse_github_url(repo_url)
            api_base_url = self._get_api_base_url_for_repo(repo_url)
            url = f"{api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            
            if self.session:
                try:
                    response = self.session.get(url)
                    if response.status_code == 200:
                        pr_data = response.json()
                        return self._transform_github_pr_data(pr_data)
                    else:
                        logger.error(f"Failed to fetch PR {pr_number}: {response.status_code} - {response.text}")
                        return None
                except Exception as api_error:
                    logger.error(f"API call failed for PR {pr_number}: {api_error}")
                    return None

            logger.error("Session not available for GitHub provider.")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching PR {pr_number} from {repo_url}: {e}")
            return None
    

    async def get_pull_requests(self, repo_url: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch multiple pull requests, with fallback to all open PRs if branch-specific search fails."""
        if not self.validate_config():
            logger.error("GitHub provider not properly configured. Missing access token.")
            return []

        try:
            owner, repo, branch = self._parse_github_url(repo_url)
            api_base_url = self._get_api_base_url_for_repo(repo_url)
            url = f"{api_base_url}/repos/{owner}/{repo}/pulls"
            
            params = {
                'state': state,
                'per_page': limit,
                'sort': 'updated',
                'direction': 'desc'
            }
            if branch:
                params['base'] = branch

            logger.info(f"Attempting to fetch PRs from {url} with params: {params}")

            if self.session:
                try:
                    response = self.session.get(url, params=params)
                    if response.status_code == 200:
                        prs_data = response.json()
                        logger.info(f"Found {len(prs_data)} PRs for branch '{branch}'.")
                        # If no PRs are found for the specific branch, try fetching all open PRs as a fallback
                        if not prs_data and branch:
                            logger.warning(f"No PRs found for base branch '{branch}'. Falling back to fetch all open PRs.")
                            fallback_params = {
                                'state': state, 'per_page': limit, 'sort': 'updated', 'direction': 'desc'
                            }
                            logger.info(f"Fallback attempt: Fetching PRs from {url} with params: {fallback_params}")
                            fallback_response = self.session.get(url, params=fallback_params)
                            if fallback_response.status_code == 200:
                                prs_data = fallback_response.json()
                                logger.info(f"Fallback successful: Found {len(prs_data)} total open PRs.")
                            else:
                                logger.error(f"Fallback fetch failed: {fallback_response.status_code} - {fallback_response.text}")
                                # Try to get repository info to verify access
                                self._check_repository_access(owner, repo, api_base_url)

                        return [self._transform_github_pr_data(pr) for pr in prs_data]
                    else:
                        logger.error(f"Failed to fetch PRs: {response.status_code} - {response.text}")
                        logger.error(f"Request URL was: {url}")
                        logger.error(f"Request params were: {params}")
                        # Try to get repository info to verify access
                        self._check_repository_access(owner, repo, api_base_url)
                        return []
                except Exception as api_error:
                    logger.error(f"API call failed for PRs: {api_error}")
                    return []
            
            logger.error("Session not available for GitHub provider.")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching PRs from {repo_url}: {e}")
            return []
    

    async def get_pull_request_files(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch files changed in a pull request"""
        if not self.validate_config():
            logger.error("GitHub provider not properly configured. Missing access token.")
            return []
        
        try:
            owner, repo, _ = self._parse_github_url(repo_url)
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
                        logger.error(f"Failed to fetch files: {response.status_code} - {response.text}")
                        return []
                except Exception as api_error:
                    logger.error(f"API call failed for PR files: {api_error}")
                    return []
            
            logger.error("Session not available for GitHub provider.")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching PR files {pr_number} from {repo_url}: {e}")
            return []
    

    async def get_pull_request_comments(self, repo_url: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch comments on a pull request (issue comments and review comments)"""
        if not self.validate_config():
            logger.error("GitHub provider not properly configured. Missing access token.")
            return []
        
        try:
            owner, repo, _ = self._parse_github_url(repo_url)
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
                        logger.warning(f"Failed to fetch issue comments: {issue_response.status_code} - {issue_response.text}")
                    
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
                        logger.warning(f"Failed to fetch review comments: {review_response.status_code} - {review_response.text}")
                    
                    all_comments.sort(key=lambda x: x.get('created_at', ''))
                    logger.info(f"Fetched {len(all_comments)} real comments for PR #{pr_number}")
                    return all_comments
                    
                except Exception as api_error:
                    logger.error(f"API call failed for PR comments: {api_error}")
                    return []
            
            logger.error("Session not available for GitHub provider.")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching PR comments {pr_number} from {repo_url}: {e}")
            return []

    async def get_repository_files(self, repo_url: str, branch: str = None, file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch all files from repository for comprehensive code review"""
        if not self.validate_config():
            logger.error("GitHub provider not properly configured. Missing access token.")
            return []
        
        try:
            owner, repo, parsed_branch = self._parse_github_url(repo_url)
            target_branch = branch or parsed_branch or "main"
            
            # Set default file extensions if not provided
            if not file_extensions:
                file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs']
            
            api_base_url = self._get_api_base_url_for_repo(repo_url)
            url = f"{api_base_url}/repos/{owner}/{repo}/git/trees/{target_branch}?recursive=1"
            
            if self.session:
                try:
                    response = self.session.get(url)
                    if response.status_code == 200:
                        tree_data = response.json()
                        files = []
                        
                        for item in tree_data.get('tree', []):
                            if item.get('type') == 'blob':  # Only files, not directories
                                filename = item.get('path', '')
                                
                                # Filter by file extensions
                                if any(filename.endswith(ext) for ext in file_extensions):
                                    # Get file content
                                    content_url = f"{api_base_url}/repos/{owner}/{repo}/contents/{filename}?ref={target_branch}"
                                    content_response = self.session.get(content_url)
                                    
                                    file_info = {
                                        'filename': filename,
                                        'status': 'existing',
                                        'additions': 0,  # Not applicable for existing files
                                        'deletions': 0,  # Not applicable for existing files  
                                        'changes': 0,    # Not applicable for existing files
                                        'patch': '',     # Will be populated with actual content
                                        'size': item.get('size', 0),
                                        'sha': item.get('sha', ''),
                                        'full_content': ''
                                    }
                                    
                                    if content_response.status_code == 200:
                                        content_data = content_response.json()
                                        if content_data.get('encoding') == 'base64':
                                            import base64
                                            try:
                                                file_content = base64.b64decode(content_data.get('content', '')).decode('utf-8')
                                                file_info['full_content'] = file_content
                                                # For compatibility with PR review, put content in patch field too
                                                file_info['patch'] = file_content
                                            except Exception as decode_error:
                                                logger.warning(f"Could not decode file {filename}: {decode_error}")
                                                file_info['full_content'] = f"# Could not decode file: {decode_error}"
                                                file_info['patch'] = f"# Could not decode file: {decode_error}"
                                    
                                    files.append(file_info)
                                    
                                    # Limit to avoid API rate limits and large responses
                                    if len(files) >= 50:  # Configurable limit
                                        logger.warning(f"Reached file limit (50), stopping repository scan")
                                        break
                        
                        logger.info(f"Fetched {len(files)} repository files for full code review")
                        return files
                    else:
                        logger.error(f"Failed to fetch repository tree: {response.status_code} - {response.text}")
                        return []
                except Exception as api_error:
                    logger.error(f"API call failed for repository files: {api_error}")
                    return []
            
            logger.error("Session not available for GitHub provider.")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching repository files from {repo_url}: {e}")
            return []
    

    async def get_pull_requests(self, repo_url: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch multiple pull requests with specified state (open, closed, all)."""
        if not self.validate_config():
            logger.error("GitHub provider not properly configured. Missing access token.")
            return []

        try:
            # Use provided parameters, fallback to config if not provided
            git_config = get_env_config().get_git_config()
            if state == "open" and git_config.get('pr_state'):
                state = git_config.get('pr_state', state)
            if limit == 10 and git_config.get('pr_limit_per_repo'):
                limit = git_config.get('pr_limit_per_repo', limit)

            owner, repo, branch = self._parse_github_url(repo_url)
            api_base_url = self._get_api_base_url_for_repo(repo_url)
            url = f"{api_base_url}/repos/{owner}/{repo}/pulls"
            
            base_params = {
                'state': state,
                'per_page': limit,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            if self.session:
                prs_data = []
                # 1. Try fetching PRs with the branch as the 'base'
                if branch:
                    params = base_params.copy()
                    params['base'] = branch
                    logger.info(f"Attempt 1: Fetching PRs with base='{branch}' from {url}")
                    try:
                        response = self.session.get(url, params=params)
                        if response.status_code == 200:
                            prs_data = response.json()
                            logger.info(f"Found {len(prs_data)} PRs with base branch '{branch}'.")
                        else:
                            logger.warning(f"Could not fetch PRs with base='{branch}': {response.status_code}")
                    except Exception as api_error:
                        logger.error(f"API call failed for base branch search: {api_error}")

                # 2. If no PRs found, try fetching with the branch as the 'head'
                if not prs_data and branch:
                    params = base_params.copy()
                    params['head'] = f'{owner}:{branch}'
                    logger.info(f"Attempt 2: No PRs found with base='{branch}'. Fetching with head='{owner}:{branch}'.")
                    try:
                        response = self.session.get(url, params=params)
                        if response.status_code == 200:
                            prs_data = response.json()
                            logger.info(f"Found {len(prs_data)} PRs with head branch '{owner}:{branch}'.")
                        else:
                             logger.warning(f"Could not fetch PRs with head='{owner}:{branch}': {response.status_code}")
                    except Exception as api_error:
                        logger.error(f"API call failed for head branch search: {api_error}")

                # 3. If still no PRs, fall back to all open PRs
                if not prs_data:
                    logger.warning(f"No PRs found for branch '{branch}'. Falling back to fetch all PRs based on state: {state}.")
                    logger.info(f"Fallback attempt: Fetching all PRs from {url}")
                    try:
                        response = self.session.get(url, params=base_params)
                        if response.status_code == 200:
                            prs_data = response.json()
                            logger.info(f"Fallback successful: Found {len(prs_data)} total PRs with state '{state}'.")
                        else:
                            logger.error(f"Fallback fetch failed: {response.status_code} - {response.text}")
                            logger.error(f"Fallback URL was: {url}")
                            logger.error(f"Fallback params were: {base_params}")
                            # Check repository access to provide helpful debugging
                            self._check_repository_access(owner, repo, api_base_url)
                    except Exception as api_error:
                        logger.error(f"API call failed for fallback search: {api_error}")

                return [self._transform_github_pr_data(pr) for pr in prs_data]
            
            logger.error("Session not available for GitHub provider.")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching PRs from {repo_url}: {e}")
            return []
    def _parse_github_url(self, repo_url: str) -> tuple[str, str, Optional[str]]:
        """Parse GitHub repository URL to extract owner, repo name, and branch."""
        
        # Normalize URL by removing trailing slashes and .git suffix
        cleaned_url = repo_url.strip().rstrip('/').removesuffix('.git')
        
        # Use urlparse to handle different URL structures
        parsed_url = urlparse(cleaned_url)
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        if not path_parts or len(path_parts) < 2:
            # Fallback for owner/repo format
            if len(repo_url.split('/')) == 2:
                owner, repo = repo_url.split('/')
                return owner, repo, None
            raise ValueError(f"Invalid GitHub repository URL format: {repo_url}")
            
        owner = path_parts[0]
        repo = path_parts[1]
        
        # Remove .git suffix from repository name if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        branch = None
        
        # Check for branch information in the path, e.g., /tree/v1
        if len(path_parts) > 3 and path_parts[2] == 'tree':
            branch = path_parts[3]
            
        return owner, repo, branch
    
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
    
    async def fetch_repository_files(self, repo_url: str, branch: str = None, file_extensions: List[str] = None, provider: str = "github") -> List[Dict[str, Any]]:
        """Fetch all files from repository for comprehensive code review"""
        git_provider = self.get_provider(provider)
        if not git_provider:
            logger.error(f"Git provider '{provider}' not available")
            return []
        
        return await git_provider.get_repository_files(repo_url, branch, file_extensions)
    
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

async def fetch_recent_prs(repo_url: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function to fetch recent PRs with specified state and limit"""
    manager = get_git_manager()
    provider = manager.detect_provider_from_url(repo_url)
    return await manager.fetch_pull_requests(repo_url, state, limit, provider)