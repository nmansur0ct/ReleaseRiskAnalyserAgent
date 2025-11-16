"""
Environment Configuration Manager
Handles loading configuration from .env files and environment variables
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None
    logging.warning("python-dotenv not available. Install with: pip install python-dotenv")

class EnvironmentConfig:
    """Manages environment configuration for the Risk Analyzer framework"""
    
    def __init__(self, env_file_path: Optional[str] = None):
        """
        Initialize environment configuration
        
        Args:
            env_file_path: Optional path to .env file. If None, searches for .env in project root
        """
        self.logger = logging.getLogger(__name__)
        self._config_cache = {}
        
        # Determine .env file path
        if env_file_path:
            self.env_file = Path(env_file_path)
        else:
            # Search for .env file in current directory and parent directories
            current_dir = Path.cwd()
            self.env_file = current_dir / '.env'
            
            # If not found in current directory, check project root
            if not self.env_file.exists():
                project_root = self._find_project_root()
                if project_root:
                    self.env_file = project_root / '.env'
        
        self._load_environment()
    
    def _find_project_root(self) -> Optional[Path]:
        """Find project root by looking for common project files"""
        current = Path.cwd()
        
        # Look for project indicators
        indicators = ['requirements.txt', 'pyproject.toml', 'setup.py', '.git', 'src']
        
        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent
        
        return None
    
    def _load_environment(self):
        """Load environment variables from .env file if available"""
        if DOTENV_AVAILABLE and load_dotenv and self.env_file.exists():
            load_dotenv(self.env_file)
            self.logger.info(f"Loaded environment configuration from {self.env_file}")
        elif self.env_file.exists():
            self.logger.warning(f"Found .env file at {self.env_file} but python-dotenv not installed")
        else:
            self.logger.info("No .env file found, using system environment variables")
    
    def get(self, key: str, default: Any = None, config_type: type = str) -> Any:
        """
        Get configuration value from environment
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            config_type: Type to cast the value to
        
        Returns:
            Configuration value cast to specified type
        """
        # Check cache first
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Get from environment
        value = os.getenv(key, default)
        
        # Type conversion
        if value is not None and config_type != str:
            try:
                if config_type == bool:
                    value = str(value).lower() in ('true', '1', 'yes', 'on')
                elif config_type == int:
                    value = int(value)
                elif config_type == float:
                    value = float(value)
                # Add more type conversions as needed
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to convert {key}={value} to {config_type}: {e}")
                value = default
        
        # Cache the result
        self._config_cache[key] = value
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM-specific configuration"""
        return {
            'provider': self.get('LLM_PROVIDER', 'walmart_llm_gateway'),
            'fallback_provider': self.get('FALLBACK_LLM_PROVIDER', 'openai'),
            'walmart_llm_gateway_url': self.get('WALMART_LLM_GATEWAY_URL'),
            'walmart_llm_gateway_key': self.get('WALMART_LLM_GATEWAY_KEY'),
            'walmart_llm_model': self.get('WALMART_LLM_MODEL', 'gpt-4'),
            'openai_api_key': self.get('OPENAI_API_KEY'),
            'openai_model': self.get('OPENAI_MODEL', 'gpt-4'),
            'anthropic_api_key': self.get('ANTHROPIC_API_KEY'),
            'anthropic_model': self.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229'),
            'timeout_seconds': self.get('LLM_TIMEOUT_SECONDS', 60, int),
            'max_retries': self.get('LLM_MAX_RETRIES', 3, int)
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification-specific configuration"""
        return {
            'slack_webhook_url': self.get('SLACK_WEBHOOK_URL'),
            'email_smtp_server': self.get('EMAIL_SMTP_SERVER', 'smtp.company.com'),
            'email_from_address': self.get('EMAIL_FROM_ADDRESS', 'noreply@company.com')
        }
    

    def get_git_config(self) -> Dict[str, Any]:
        """Get Git integration configuration"""
        return {
            'provider': self.get('GIT_PROVIDER', 'github'),
            'access_token': self.get('GIT_ACCESS_TOKEN'),
            'default_repo_url': self.get('GIT_DEFAULT_REPO_URL'),
            'api_base_url': self.get('GIT_API_BASE_URL', 'https://api.github.com'),
            'pr_state': self.get('PR_STATE', 'open'),
            'pr_limit_per_repo': self.get('PR_LIMIT_PER_REPO', 10, config_type=int)
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration"""
        return {
            'database_url': self.get('DATABASE_URL')
        }
    
    def get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics-specific configuration"""
        return {
            'endpoint': self.get('METRICS_ENDPOINT', 'http://metrics.internal:8080'),
            'enabled': self.get('ENABLE_METRICS', True, bool)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging-specific configuration"""
        return {
            'level': self.get('LOG_LEVEL', 'INFO'),
            'debug': self.get('ENABLE_DEBUG', False, bool)
        }
    
    def merge_with_yaml_config(self, yaml_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge environment configuration with YAML configuration
        Environment variables take precedence over YAML values
        
        Args:
            yaml_config: Configuration loaded from YAML file
        
        Returns:
            Merged configuration with environment overrides
        """
        merged_config = yaml_config.copy()
        
        # Override LLM provider in plugin configurations
        llm_config = self.get_llm_config()
        
        if 'plugins' in merged_config:
            for plugin_name, plugin_config in merged_config['plugins'].items():
                if isinstance(plugin_config, dict) and 'config' in plugin_config:
                    config_section = plugin_config['config']
                    
                    # Override LLM provider
                    if 'llm_provider' in config_section and llm_config['provider']:
                        config_section['llm_provider'] = llm_config['provider']
                    
                    # Override fallback provider
                    if 'fallback_provider' in config_section and llm_config['fallback_provider']:
                        config_section['fallback_provider'] = llm_config['fallback_provider']
                    
                    # Override timeout if specified
                    if 'timeout_seconds' in config_section and llm_config['timeout_seconds']:
                        config_section['timeout_seconds'] = llm_config['timeout_seconds']
        
        # Override notification settings
        notification_config = self.get_notification_config()
        if 'plugins' in merged_config and 'notification_agent' in merged_config['plugins']:
            notification_plugin = merged_config['plugins']['notification_agent']
            if 'config' in notification_plugin:
                config_section = notification_plugin['config']
                
                # Override Slack webhook
                if 'slack_config' in config_section and notification_config['slack_webhook_url']:
                    config_section['slack_config']['webhook_url'] = notification_config['slack_webhook_url']
                
                # Override email settings
                if 'email_config' in config_section:
                    if notification_config['email_smtp_server']:
                        config_section['email_config']['smtp_server'] = notification_config['email_smtp_server']
                    if notification_config['email_from_address']:
                        config_section['email_config']['from_address'] = notification_config['email_from_address']
        
        # Override global configuration
        if 'global_config' in merged_config:
            global_config = merged_config['global_config']
            
            # Override logging
            logging_config = self.get_logging_config()
            if logging_config['level']:
                global_config['log_level'] = logging_config['level']
            
            # Override metrics
            metrics_config = self.get_metrics_config()
            if metrics_config['endpoint']:
                global_config['metrics_endpoint'] = metrics_config['endpoint']
            global_config['enable_metrics'] = metrics_config['enabled']
        
        return merged_config
    
    def validate_llm_config(self) -> bool:
        """
        Validate that required LLM configuration is present
        
        Returns:
            True if LLM configuration is valid, False otherwise
        """
        llm_config = self.get_llm_config()
        
        if llm_config['provider'] == 'openai':
            if not llm_config['openai_api_key']:
                self.logger.error("OPENAI_API_KEY is required when using OpenAI provider")
                return False
        elif llm_config['provider'] == 'anthropic':
            if not llm_config['anthropic_api_key']:
                self.logger.error("ANTHROPIC_API_KEY is required when using Anthropic provider")
                return False
        
        return True
    
    def reload(self):
        """Reload environment configuration and clear cache"""
        self._config_cache.clear()
        self._load_environment()
        self.logger.info("Environment configuration reloaded")

# Global instance for easy access
_env_config = None

def get_env_config() -> EnvironmentConfig:
    """Get the global environment configuration instance"""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfig()
    return _env_config

def reload_env_config():
    """Reload the global environment configuration"""
    global _env_config
    if _env_config:
        _env_config.reload()
    else:
        _env_config = EnvironmentConfig()