"""
Risk Agent Analyzer - Main Application Entry Point

Professional-grade multi-repository analysis framework with comprehensive reporting.
Refactored from monolithic simple_demo.py into modular packages.
"""

import asyncio
import argparse
import sys
import logging
from typing import List

from src.utilities.config_utils import setup_logging, validate_environment, load_configuration
from src.orchestration.repository_orchestrator import RepositoryOrchestrator

class RiskAgentAnalyzer:
    """Main application class for Risk Agent Analyzer"""
    
    def __init__(self):
        """Initialize the Risk Agent Analyzer"""
        self.logger = logging.getLogger(__name__)
        
    async def analyze_repositories(self, repo_urls: List[str], config: dict) -> None:
        """Analyze repositories with comprehensive reporting"""
        try:
            # Initialize repository orchestrator
            orchestrator = RepositoryOrchestrator(config)
            
            # Execute analysis
            results = await orchestrator.analyze_repositories(repo_urls)
            
            self.logger.info(f"Analysis completed for {len(repo_urls)} repositories")
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Multi-Repository Pull Request Analysis Framework",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  # Analyze single repository
  python risk_analyzer.py https://github.com/user/repo.git
  
  # Analyze multiple repositories with custom settings
  python risk_analyzer.py repo1.git repo2.git --pr-limit 5 --pr-state closed
  
  # Full repository analysis mode
  python risk_analyzer.py repo.git --output-dir ./custom_reports
        """
    )
    
    parser.add_argument(
        'repo_urls',
        nargs='+',
        help='Repository URLs to analyze (space-separated)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='../reports',
        help='Directory to save analysis reports (default: ../reports)'
    )
    
    parser.add_argument(
        '--pr-state',
        choices=['open', 'closed', 'all'],
        default='open',
        help='PR state filter (default: open)'
    )
    
    parser.add_argument(
        '--pr-limit',
        type=int,
        default=10,
        help='Maximum number of PRs to analyze per repository (default: 10)'
    )
    
    parser.add_argument(
        '--include-comments',
        action='store_true',
        default=True,
        help='Include PR comments in analysis (default: True)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser

async def main():
    """Main entry point for the Risk Agent Analyzer"""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_configuration()
        
        # Override with command line arguments
        config.update({
            'output_dir': args.output_dir,
            'pr_state': args.pr_state,
            'pr_limit': args.pr_limit,
            'include_comments': args.include_comments
        })
        
        logger.info("Configuration loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize and run analyzer
    try:
        analyzer = RiskAgentAnalyzer()
        await analyzer.analyze_repositories(args.repo_urls, config)
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    """Run the Risk Agent Analyzer"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)