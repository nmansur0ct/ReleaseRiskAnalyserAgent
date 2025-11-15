"""
Git Integration Demo
Demonstrates fetching pull request data from Git repositories and analyzing them
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from environment_config import get_env_config
    from llm_integration import get_llm_manager, analyze_code_changes
    from git_integration import get_git_manager
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    MODULES_AVAILABLE = False
    # Mock functions for fallback
    def mock_get_env_config():
        class MockConfig:
            def get_llm_config(self):
                return {'provider': 'mock'}
            def get_git_config(self):
                return {'access_token': None}
        return MockConfig()
    
    def mock_get_llm_manager():
        class MockLLMManager:
            def get_available_providers(self):
                return ['mock']
        return MockLLMManager()
    
    def mock_get_git_manager():
        class MockGitManager:
            @property
            def providers(self):
                return {'github': None, 'mock': None}
            def get_provider(self, name):
                return None
        return MockGitManager()
    
    async def mock_analyze_code_changes(pr_data):
        return {
            'success': True,
            'provider_used': 'mock',
            'response': 'Mock analysis: This is a simulated LLM analysis of the pull request changes.',
            'errors': []
        }
    
    get_env_config = mock_get_env_config
    get_llm_manager = mock_get_llm_manager  
    get_git_manager = mock_get_git_manager
    analyze_code_changes = mock_analyze_code_changes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demonstrate_git_integration():
    """Demonstrate Git integration capabilities"""
    
    print(" Git Integration Demonstration")
    print("="*80)
    
    if not MODULES_AVAILABLE:
        print(" Required modules not available. Please check your installation.")
        return
    
    # Show environment configuration
    env_config = get_env_config()
    git_config = env_config.get_git_config()
    llm_config = env_config.get_llm_config()
    
    print(f"\n Configuration Status:")
    print(f"Git Access Token: {' Configured' if git_config['access_token'] else '  Not configured (using mock data)'}")
    print(f"Default Repo URL: {git_config.get('default_repo_url', 'Not set')}")
    print(f"LLM Provider: {llm_config['provider']}")
    print(f"LLM Gateway URL: {llm_config.get('walmart_llm_gateway_url', 'Not configured')}")
    
    # Initialize managers
    git_manager = get_git_manager()
    llm_manager = get_llm_manager()
    
    print(f"\n Available Providers:")
    print(f"Git Providers: {list(git_manager.providers.keys())}")
    print(f"LLM Providers: {llm_manager.get_available_providers()}")
    
    # Demo repository URL (can be changed via environment variable)
    demo_repo_url = git_config.get('default_repo_url') or "https://gecgithub01.walmart.com/n0m08hp/TransactionPatterns.git"
    
    print(f"\n  Demo Repository: {demo_repo_url}")
    print("-" * 60)
    
    # Fetch recent pull requests
    print("\n Fetching Recent Pull Requests...")
    try:
        git_manager = get_git_manager()
        git_provider = git_manager.get_provider("github")
        if git_provider:
            recent_prs = await git_provider.get_pull_requests(demo_repo_url, limit=5)
        else:
            recent_prs = []
        
        if recent_prs:
            print(f"Found {len(recent_prs)} recent pull requests:")
            
            for i, pr in enumerate(recent_prs[:3], 1):  # Show first 3 PRs
                print(f"\n{i}. PR #{pr['number']}: {pr['title']}")
                print(f"   Author: {pr['author']}")
                print(f"   Changes: +{pr['additions']} -{pr['deletions']}")
                print(f"   Files: {len(pr.get('changed_files', []))}")
                print(f"   URL: {pr['url']}")
                
                # Analyze with LLM
                await analyze_pr_with_llm(pr, llm_manager)
        else:
            print("No pull requests found or access token not configured.")
            
    except Exception as e:
        logger.error(f"Error fetching PRs: {e}")
        print(f" Error fetching pull requests: {e}")

async def analyze_pr_with_llm(pr_data: Dict[str, Any], llm_manager) -> None:
    """Analyze a pull request using LLM"""
    print(f"\n    LLM Analysis:")
    
    if not MODULES_AVAILABLE or not analyze_code_changes:
        print("     LLM analysis not available")
        return
    
    try:
        # Prepare PR data for analysis
        analysis_data = {
            'title': pr_data['title'],
            'body': pr_data.get('body', ''),
            'changed_files': pr_data.get('changed_files', []),
            'additions': pr_data.get('additions', 0),
            'deletions': pr_data.get('deletions', 0),
            'labels': pr_data.get('labels', [])
        }
        
        # Analyze using LLM with fallback
        result = await analyze_code_changes(analysis_data)
        
        if result['success']:
            print(f"   Provider: {result['provider_used']}")
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"     Analysis failed: {result.get('errors', ['Unknown error'])}")
            
    except Exception as e:
        print(f"    LLM analysis error: {e}")

async def demonstrate_specific_pr_analysis():
    """Demonstrate analyzing a specific PR"""
    
    print("\n\n Specific PR Analysis Demo")
    print("="*80)
    
    if not MODULES_AVAILABLE:
        print(" Required modules not available")
        return
    
    # Demo with a specific PR
    demo_repo = "https://gecgithub01.walmart.com/n0m08hp/TransactionPatterns.git"
    demo_pr_number = 1  # This will use mock data
    
    print(f"\n Fetching PR #{demo_pr_number} from {demo_repo}")
    
    try:
        git_manager = get_git_manager()
        git_provider = git_manager.get_provider("github")
        if git_provider:
            pr_data = await git_provider.get_pull_request(demo_repo, demo_pr_number)
        else:
            # Create mock data for demonstration
            pr_data = {
                'title': f'Mock PR #{demo_pr_number}: Add new risk analysis feature',
                'author': 'developer@example.com',
                'state': 'open',
                'additions': 156,
                'deletions': 23,
                'changed_files': ['src/risk_analyzer.py', 'tests/test_risk.py'],
                'labels': ['enhancement', 'security']
            }
        
        if pr_data:
            print(f"\n PR Details:")
            print(f"Title: {pr_data['title']}")
            print(f"Author: {pr_data['author']}")
            print(f"State: {pr_data['state']}")
            print(f"Changes: +{pr_data['additions']} -{pr_data['deletions']}")
            print(f"Files changed: {len(pr_data.get('changed_files', []))}")
            print(f"Labels: {', '.join(pr_data.get('labels', []))}")
            
            if pr_data.get('changed_files'):
                print(f"\n Changed Files:")
                for file in pr_data['changed_files'][:5]:  # Show first 5 files
                    print(f"   - {file}")
                if len(pr_data['changed_files']) > 5:
                    print(f"   ... and {len(pr_data['changed_files']) - 5} more files")
            
            # Comprehensive analysis
            await run_comprehensive_analysis(pr_data)
            
        else:
            print(" Failed to fetch PR data")
            
    except Exception as e:
        logger.error(f"Error in specific PR analysis: {e}")
        print(f" Error: {e}")

async def run_comprehensive_analysis(pr_data: Dict[str, Any]):
    """Run comprehensive analysis on PR data"""
    
    print(f"\n Comprehensive Risk Analysis")
    print("-" * 40)
    
    try:
        # Simulate the plugin framework analysis
        await simulate_plugin_analysis("change_log_summarizer", pr_data)
        await simulate_plugin_analysis("security_analyzer", pr_data) 
        await simulate_plugin_analysis("compliance_checker", pr_data)
        await simulate_plugin_analysis("release_decision_agent", pr_data)
        
    except Exception as e:
        print(f" Analysis error: {e}")

async def simulate_plugin_analysis(plugin_name: str, pr_data: Dict[str, Any]):
    """Simulate plugin-based analysis"""
    
    await asyncio.sleep(0.1)  # Simulate processing time
    
    if plugin_name == "change_log_summarizer":
        print(f" {plugin_name.replace('_', ' ').title()}")
        print(f"   Summary: Analyzed {pr_data['changed_files_count']} files")
        print(f"   Risk Level: {'HIGH' if pr_data['additions'] > 300 else 'MEDIUM' if pr_data['additions'] > 100 else 'LOW'}")
        print(f"   Impact: {len(pr_data.get('changed_files', []))} modules affected")
        
    elif plugin_name == "security_analyzer":
        security_score = min(100, max(0, 100 - (pr_data['additions'] // 10)))
        print(f" {plugin_name.replace('_', ' ').title()}")
        print(f"   Security Score: {security_score}/100")
        
        # Check for security-related changes
        security_indicators = []
        content = f"{pr_data['title']} {pr_data.get('body', '')}".lower()
        if any(word in content for word in ['auth', 'password', 'token', 'security']):
            security_indicators.append("Authentication changes detected")
        if any(word in content for word in ['api', 'endpoint', 'route']):
            security_indicators.append("API changes detected")
            
        if security_indicators:
            print(f"   Findings: {', '.join(security_indicators)}")
        else:
            print(f"   Findings: No obvious security concerns")
            
    elif plugin_name == "compliance_checker":
        labels = pr_data.get('labels', [])
        compliant = not any(label in ['breaking-change', 'experimental'] for label in labels)
        
        print(f" {plugin_name.replace('_', ' ').title()}")
        print(f"   Status: {' COMPLIANT' if compliant else ' NON-COMPLIANT'}")
        print(f"   Checks: Code review required, Documentation updated")
        
    elif plugin_name == "release_decision_agent":
        # Simple decision logic based on size and security
        risk_factors = []
        if pr_data['additions'] > 500:
            risk_factors.append("Large change size")
        if pr_data['changed_files_count'] > 10:
            risk_factors.append("Many files affected")
        
        approved = len(risk_factors) == 0
        
        print(f" {plugin_name.replace('_', ' ').title()}")
        print(f"   Decision: {' APPROVED' if approved else '  REVIEW REQUIRED'}")
        if risk_factors:
            print(f"   Concerns: {', '.join(risk_factors)}")
        print(f"   Recommendation: {'Ready for merge' if approved else 'Manual review needed'}")

async def main():
    """Main demo function"""
    
    print(" Enhanced Git Integration & LLM Analysis Demo")
    print("="*80)
    
    try:
        # Run Git integration demo
        await demonstrate_git_integration()
        
        # Run specific PR analysis
        await demonstrate_specific_pr_analysis()
        
        print(f"\n Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f" Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())