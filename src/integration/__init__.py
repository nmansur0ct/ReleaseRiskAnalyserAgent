"""
Integration Package

External system integrations for LLM, Git, and environment configuration.
"""

from .llm_client import LLMClient, get_llm_response
from .git_integration import (
    get_git_manager,
    fetch_recent_prs,
    fetch_pr_data,
    GitManager,
    GitProvider,
    GitHubProvider,
    GitLabProvider
)
from .environment_config import get_env_config

__all__ = [
    "LLMClient",
    "get_llm_response", 
    "get_git_manager",
    "fetch_recent_prs",
    "fetch_pr_data",
    "GitManager",
    "GitProvider",
    "GitHubProvider",
    "GitLabProvider",
    "get_env_config"
]