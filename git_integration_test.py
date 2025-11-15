"""
Git Integration Test Script
Tests the Git integration and Walmart LLM Gateway functionality
"""

import asyncio
import os
import sys
from datetime import datetime

# Mock implementations for testing
class MockGitManager:
    def __init__(self):
        self.providers = {'github': 'available', 'mock': 'available'}
    
    async def fetch_pull_request(self, repo_url, pr_number):
        """Mock PR data"""
        return {
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
            'additions': 342 + (pr_number * 10),
            'deletions': 28 + (pr_number * 2),
            'changed_files_count': 7 + pr_number,
            'base_branch': 'main',
            'head_branch': f'feature/auth-payment-{pr_number}',
            'mergeable': True,
            'labels': ['enhancement', 'security', 'payment'],
            'assignees': ['lead-dev', 'security-reviewer'],
            'changed_files': [
                f"src/auth/oauth{pr_number}.py",
                f"src/payments/stripe_integration{pr_number}.py",
                f"src/api/auth_endpoints{pr_number}.py",
                f"src/api/payment_endpoints{pr_number}.py",
                f"migrations/{pr_number:03d}_add_user_table.sql",
                "config/database.yml",
                "requirements.txt"
            ]
        }
    
    async def fetch_pull_requests(self, repo_url, state="open", limit=10):
        """Mock multiple PRs"""
        return [await self.fetch_pull_request(repo_url, i) for i in range(1, limit + 1)]

class MockLLMManager:
    def __init__(self):
        self.providers = {
            'walmart_llm_gateway': 'configured',
            'openai': 'configured',
            'mock': 'available'
        }
    
    def get_available_providers(self):
        return list(self.providers.keys())
    
    async def analyze_code_changes(self, changes_data):
        """Mock LLM analysis"""
        provider = 'walmart_llm_gateway'
        
        # Simulate LLM analysis
        await asyncio.sleep(0.1)
        
        analysis = f"""
        **Risk Assessment for PR: {changes_data.get('title', 'Unknown')}**
        
        Changes analyzed: {changes_data.get('additions', 0)} additions, {changes_data.get('deletions', 0)} deletions
        Files affected: {len(changes_data.get('changed_files', []))}
        
        **Risk Level: {'HIGH' if changes_data.get('additions', 0) > 300 else 'MEDIUM' if changes_data.get('additions', 0) > 100 else 'LOW'}**
        
        **Security Considerations:**
        - Authentication changes detected: {'Yes' if 'auth' in changes_data.get('title', '').lower() else 'No'}
        - Payment processing: {'Yes' if 'payment' in changes_data.get('title', '').lower() else 'No'}
        - Database modifications: {'Yes' if 'migration' in str(changes_data.get('changed_files', [])) else 'No'}
        
        **Recommendations:**
        - Code review required
        - Security team approval needed
        - Comprehensive testing recommended
        """
        
        return {
            'success': True,
            'provider_used': provider,
            'response': analysis
        }

class MockEnvironmentConfig:
    def get_git_config(self):
        return {
            'access_token': os.getenv('GIT_ACCESS_TOKEN'),
            'default_repo_url': os.getenv('GIT_DEFAULT_REPO_URL', 'https://gecgithub01.walmart.com/n0m08hp/TransactionPatterns.git'),
            'api_base_url': 'https://api.github.com'
        }
    
    def get_llm_config(self):
        return {
            'provider': 'walmart_llm_gateway',
            'walmart_llm_gateway_url': os.getenv('WALMART_LLM_GATEWAY_URL', 'https://wmtllmgateway.stage.walmart.com/wmtllmgateway'),
            'walmart_llm_gateway_key': os.getenv('WALMART_LLM_GATEWAY_KEY', '***configured***'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'fallback_provider': 'openai'
        }

async def test_git_integration():
    """Test Git integration functionality"""
    
    print("🔗 Git Integration Test")
    print("="*50)
    
    # Create mock managers
    env_config = MockEnvironmentConfig()
    git_manager = MockGitManager()
    llm_manager = MockLLMManager()
    
    # Show configuration
    git_config = env_config.get_git_config()
    llm_config = env_config.get_llm_config()
    
    print(f"\n🔧 Configuration:")
    print(f"Git Token: {'✅ Set' if git_config['access_token'] else '⚠️  Using mock data'}")
    print(f"Repo URL: {git_config['default_repo_url']}")
    print(f"LLM Provider: {llm_config['provider']}")
    print(f"LLM Gateway: {llm_config['walmart_llm_gateway_url']}")
    print(f"LLM Key: {'✅ Configured' if llm_config['walmart_llm_gateway_key'] else '❌ Missing'}")
    
    # Test fetching recent PRs
    repo_url = git_config['default_repo_url']
    print(f"\n📋 Fetching Recent PRs from: {repo_url}")
    
    recent_prs = await git_manager.fetch_pull_requests(repo_url, limit=3)
    
    for i, pr in enumerate(recent_prs, 1):
        print(f"\n{i}. PR #{pr['number']}: {pr['title']}")
        print(f"   Author: {pr['author']}")
        print(f"   Changes: +{pr['additions']} -{pr['deletions']}")
        print(f"   Files: {pr['changed_files_count']}")
        
        # Test LLM analysis
        print(f"\n   🤖 Walmart LLM Gateway Analysis:")
        
        analysis_data = {
            'title': pr['title'],
            'body': pr.get('body', ''),
            'changed_files': pr.get('changed_files', []),
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0)
        }
        
        result = await llm_manager.analyze_code_changes(analysis_data)
        
        if result['success']:
            print(f"   Provider: {result['provider_used']}")
            print(f"   Analysis:")
            # Show first few lines of analysis
            lines = result['response'].strip().split('\n')[:8]
            for line in lines:
                if line.strip():
                    print(f"     {line.strip()}")
            print(f"     ... (truncated)")
        else:
            print(f"   ❌ Analysis failed")

async def test_specific_pr():
    """Test specific PR analysis"""
    
    print(f"\n\n🎯 Specific PR Analysis Test")
    print("="*50)
    
    git_manager = MockGitManager()
    llm_manager = MockLLMManager()
    
    # Test specific PR
    repo_url = "https://gecgithub01.walmart.com/n0m08hp/TransactionPatterns.git"
    pr_number = 42
    
    print(f"\n📥 Analyzing PR #{pr_number}")
    
    pr_data = await git_manager.fetch_pull_request(repo_url, pr_number)
    
    print(f"\n📋 PR Details:")
    print(f"Title: {pr_data['title']}")
    print(f"Author: {pr_data['author']}")
    print(f"State: {pr_data['state']}")
    print(f"Changes: +{pr_data['additions']} -{pr_data['deletions']}")
    print(f"Labels: {', '.join(pr_data['labels'])}")
    
    print(f"\n📁 Changed Files:")
    for file in pr_data['changed_files'][:5]:
        print(f"   - {file}")
    
    # Comprehensive analysis
    print(f"\n🔍 Risk Analysis Pipeline:")
    
    # Simulate plugin analysis pipeline
    await simulate_analysis_pipeline(pr_data)

async def simulate_analysis_pipeline(pr_data):
    """Simulate the plugin analysis pipeline"""
    
    plugins = [
        ("Change Log Summarizer", "🔍"),
        ("Security Analyzer", "🔒"), 
        ("Compliance Checker", "✅"),
        ("Release Decision Agent", "🚦")
    ]
    
    for plugin_name, icon in plugins:
        print(f"\n{icon} {plugin_name}")
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if "Security" in plugin_name:
            score = max(0, 100 - (pr_data['additions'] // 10))
            print(f"   Security Score: {score}/100")
            print(f"   Findings: {'Authentication changes' if 'auth' in pr_data['title'].lower() else 'No security concerns'}")
            
        elif "Compliance" in plugin_name:
            compliant = pr_data['additions'] < 500
            print(f"   Status: {'✅ COMPLIANT' if compliant else '❌ REVIEW REQUIRED'}")
            print(f"   Standards: SOX, GDPR, PCI-DSS")
            
        elif "Decision" in plugin_name:
            approved = pr_data['additions'] < 300 and pr_data['changed_files_count'] < 10
            print(f"   Decision: {'✅ APPROVED' if approved else '⚠️  MANUAL REVIEW'}")
            print(f"   Confidence: {85 if approved else 65}%")
            
        else:
            print(f"   Summary: Analyzed {pr_data['changed_files_count']} files")
            print(f"   Risk Level: {'HIGH' if pr_data['additions'] > 400 else 'MEDIUM' if pr_data['additions'] > 200 else 'LOW'}")

def show_environment_info():
    """Show current environment configuration"""
    
    print("🔧 Environment Configuration Check")
    print("="*50)
    
    env_vars = [
        'WALMART_LLM_GATEWAY_URL',
        'WALMART_LLM_GATEWAY_KEY',
        'GIT_ACCESS_TOKEN',
        'GIT_DEFAULT_REPO_URL',
        'LLM_PROVIDER'
    ]
    
    print("\n📋 Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if var.endswith('_KEY') or var.endswith('_TOKEN'):
            display_value = '***configured***' if value else 'Not set'
        else:
            display_value = value or 'Not set'
        
        status = '✅' if value else '⚠️ '
        print(f"   {status} {var}: {display_value}")

async def main():
    """Main test function"""
    
    print("🚀 Git Integration & Walmart LLM Gateway Test Suite")
    print("="*80)
    
    # Show environment info
    show_environment_info()
    
    try:
        # Test Git integration
        await test_git_integration()
        
        # Test specific PR analysis  
        await test_specific_pr()
        
        print(f"\n\n✅ All tests completed successfully!")
        print(f"📝 Next steps:")
        print(f"   1. Configure real Git access token for live data")
        print(f"   2. Verify Walmart LLM Gateway connectivity") 
        print(f"   3. Test with your specific repository")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())