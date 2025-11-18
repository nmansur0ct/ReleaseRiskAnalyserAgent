"""
Configuration utilities for Risk Agent Analyzer

Provides configuration loading and management functions.
"""

import logging
import sys
import os
from typing import Dict, Any

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def setup_import_path() -> None:
    """Setup Python import path for local modules"""
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

def load_configuration() -> Dict[str, Any]:
    """Load application configuration"""
    try:
        # Add src directory to path for imports
        setup_import_path()
        
        from ..integration.environment_config import get_env_config
        env_config = get_env_config()
        
        return {
            "code_review_mode": getattr(env_config, 'get_code_review_mode', lambda: 'full_repo')(),
            "pr_state": "open",
            "pr_limit": 10,
            "include_comments": True,
            "output_dir": "../reports",
            "min_quality_score": 70.0,
            "cost_threshold": 1000.0
        }
    except ImportError as e:
        print(f"Required modules not available: {e}")
        print("Please ensure environment_config and related modules are installed.")
        sys.exit(1)

def validate_environment() -> bool:
    """Validate that required environment modules are available"""
    try:
        from ..integration.environment_config import get_env_config
        from ..integration.llm_client import LLMClient
        from ..agents.code_review_agents import (
            PythonCodeReviewAgent,
            JavaCodeReviewAgent,
            NodeJSCodeReviewAgent
        )
        return True
    except ImportError as e:
        print(f"Environment validation failed: {e}")
        return False