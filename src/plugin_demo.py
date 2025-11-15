"""
Complete Plugin Framework Demonstration
Shows how to use the modular plugin system with configuration
"""

import asyncio
import json
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from plugin_framework import (
    WorkflowOrchestrator, AgentPluginRegistry, ConfigurationManager, AgentInput
)
from example_plugins import (
    ChangeLogSummarizerPlugin,
    SecurityAnalyzerPlugin,
    NotificationAgentPlugin,
    CustomCompliancePlugin
)

# Simple state class for the demo
class SimpleRiskAnalysisState:
    """Simple state object for demonstration"""
    def __init__(self):
        self.analysis_results = {}
        self.validation_results = {}
        self.decision_results = {}
        self.confidence_levels = {}
        self.analysis_methods = {}

import asyncio
import json
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from plugin_framework import (
    PluginFramework, ConfigurationManager, AgentInput
)
from example_plugins import (
    ChangeLogSummarizerPlugin,
    SecurityAnalyzerPlugin,
    NotificationAgentPlugin,
    CustomCompliancePlugin
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PluginFrameworkDemo:
    """Demonstration of the complete plugin framework"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the demo with configuration"""
        self.config_path = config_path or "config/basic_config.yaml"
        self.config_manager = None
        self.registry = None
        self.orchestrator = None
        
    async def initialize(self):
        """Initialize the plugin framework"""
        try:
            # Load configuration
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            
            # Initialize components
            self.config_manager = ConfigurationManager(self.config_path)
            await self.config_manager.load_config()
            self.registry = AgentPluginRegistry()
            self.orchestrator = WorkflowOrchestrator(self.registry, self.config_manager)
            
            # Register built-in plugins
            await self._register_plugins()
            
            logger.info("Plugin framework initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize framework: {e}")
            raise
    
    async def _register_plugins(self):
        """Register all available plugins"""
        # Get plugin configurations from the config
        plugins_config = self.config_manager.config.get('plugins', {})
        
        plugins = [
            ChangeLogSummarizerPlugin(plugins_config.get('change_log_summarizer', {}).get('config', {})),
            SecurityAnalyzerPlugin(plugins_config.get('security_analyzer', {}).get('config', {})),
            NotificationAgentPlugin(plugins_config.get('notification_agent', {}).get('config', {})),
            CustomCompliancePlugin(plugins_config.get('custom_compliance_checker', {}).get('config', {}))
        ]
        
        for plugin in plugins:
            await self.registry.register_agent(plugin)
            logger.info(f"Registered plugin: {plugin.get_metadata().name}")
    
    async def run_analysis(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete risk analysis on PR data"""
        session_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create input
        input_data = AgentInput(
            data=pr_data,
            session_id=session_id
        )
        
        logger.info(f"Starting analysis for session: {session_id}")
        
        try:
            # Create state
            state = SimpleRiskAnalysisState()
            
            # Execute workflow
            results = await self.orchestrator.execute_workflow(input_data, state)
            
            # Package results with additional info
            return {
                'agent_results': results,
                'workflow_info': {
                    'name': self.config_manager.config.get('workflow', {}).get('name', 'Unknown'),
                    'status': 'completed',
                    'total_execution_time': sum(r.execution_time for r in results.values() if hasattr(r, 'execution_time'))
                }
            }
            
            logger.info(f"Analysis completed successfully for session: {session_id}")
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed for session {session_id}: {e}")
            raise
    
    def print_results(self, results: Dict[str, Any]):
        """Print analysis results in a formatted way"""
        print("\n" + "="*80)
        print("🔍 RELEASE RISK ANALYSIS RESULTS")
        print("="*80)
        
        # Workflow info
        workflow_info = results.get('workflow_info', {})
        print(f"\n📋 Workflow: {workflow_info.get('name', 'Unknown')}")
        print(f"⏱️  Execution Time: {workflow_info.get('total_execution_time', 0):.2f}s")
        print(f"🔄 Status: {workflow_info.get('status', 'Unknown')}")
        
        # Agent results
        agent_results = results.get('agent_results', {})
        
        if 'change_log_summarizer' in agent_results:
            self._print_change_summary(agent_results['change_log_summarizer'])
        
        if 'security_analyzer' in agent_results:
            self._print_security_analysis(agent_results['security_analyzer'])
        
        if 'custom_compliance_checker' in agent_results:
            self._print_compliance_results(agent_results['custom_compliance_checker'])
        
        if 'notification_agent' in agent_results:
            self._print_notification_results(agent_results['notification_agent'])
        
        # Overall metrics
        self._print_overall_metrics(results)
        
        print("\n" + "="*80)
    
    def _print_change_summary(self, result: Dict[str, Any]):
        """Print change log summary results"""
        print(f"\n📝 CHANGE LOG ANALYSIS")
        print("-" * 40)
        
        summary_data = result.get('result', {})
        print(f"Summary: {summary_data.get('summary', 'No summary available')}")
        print(f"Change Size: {summary_data.get('change_size', 'Unknown').upper()}")
        
        modules = summary_data.get('affected_modules', [])
        if modules:
            print(f"Affected Modules: {', '.join(modules)}")
        
        risk_indicators = summary_data.get('risk_indicators', [])
        if risk_indicators:
            print(f"Risk Indicators: {', '.join(risk_indicators)}")
        
        print(f"Confidence: {result.get('confidence', 0):.1%}")
        print(f"Method: {result.get('analysis_method', 'Unknown')}")
    
    def _print_security_analysis(self, result: Dict[str, Any]):
        """Print security analysis results"""
        print(f"\n🔒 SECURITY ANALYSIS")
        print("-" * 40)
        
        security_data = result.get('result', {})
        security_score = security_data.get('security_score', 0)
        findings = security_data.get('security_findings', [])
        
        # Security score with color coding
        if security_score >= 75:
            status = "🔴 HIGH RISK"
        elif security_score >= 50:
            status = "🟡 MEDIUM RISK"
        elif security_score >= 25:
            status = "🟠 LOW RISK"
        else:
            status = "🟢 MINIMAL RISK"
        
        print(f"Security Score: {security_score} - {status}")
        print(f"Recommendation: {security_data.get('recommendation', 'No recommendation')}")
        
        if findings:
            print(f"\nFindings ({len(findings)}):")
            for i, finding in enumerate(findings[:5], 1):  # Show first 5
                severity = finding.get('severity', 'unknown').upper()
                message = finding.get('message', 'No message')
                print(f"  {i}. [{severity}] {message}")
            
            if len(findings) > 5:
                print(f"  ... and {len(findings) - 5} more findings")
    
    def _print_compliance_results(self, result: Dict[str, Any]):
        """Print compliance check results"""
        print(f"\n⚖️  COMPLIANCE ANALYSIS")
        print("-" * 40)
        
        compliance_data = result.get('result', {})
        overall_compliant = compliance_data.get('overall_compliant', False)
        compliance_results = compliance_data.get('compliance_results', {})
        
        status = "✅ COMPLIANT" if overall_compliant else "❌ NON-COMPLIANT"
        print(f"Overall Status: {status}")
        
        if compliance_results:
            print("\nStandard Compliance:")
            for standard, standard_result in compliance_results.items():
                compliant = standard_result.get('compliant', False)
                issues = standard_result.get('issues', [])
                
                standard_status = "✅" if compliant else "❌"
                print(f"  {standard_status} {standard}")
                
                if issues:
                    for issue in issues[:2]:  # Show first 2 issues
                        print(f"    • {issue}")
    
    def _print_notification_results(self, result: Dict[str, Any]):
        """Print notification results"""
        print(f"\n📢 NOTIFICATIONS")
        print("-" * 40)
        
        notification_data = result.get('result', {})
        notifications_sent = notification_data.get('notifications_sent', [])
        channels_used = notification_data.get('channels_used', [])
        
        if notifications_sent:
            print(f"Notifications Sent: {len(notifications_sent)}")
            for notification in notifications_sent:
                print(f"  • {notification}")
        else:
            print("No notifications sent")
        
        if channels_used:
            print(f"Channels: {', '.join(channels_used)}")
    
    def _print_overall_metrics(self, results: Dict[str, Any]):
        """Print overall workflow metrics"""
        print(f"\n📊 WORKFLOW METRICS")
        print("-" * 40)
        
        workflow_info = results.get('workflow_info', {})
        agent_results = results.get('agent_results', {})
        
        # Execution statistics
        total_agents = len(agent_results)
        successful_agents = len([r for r in agent_results.values() 
                               if not r.get('errors')])
        
        print(f"Agents Executed: {successful_agents}/{total_agents}")
        print(f"Total Execution Time: {workflow_info.get('total_execution_time', 0):.2f}s")
        
        # Average confidence
        confidences = [r.get('confidence', 0) for r in agent_results.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        print(f"Average Confidence: {avg_confidence:.1%}")
        
        # Error summary
        errors = []
        for agent_result in agent_results.values():
            errors.extend(agent_result.get('errors', []))
        
        if errors:
            print(f"Errors Encountered: {len(errors)}")
            for error in errors[:3]:  # Show first 3
                print(f"  • {error}")

async def main():
    """Main demonstration function"""
    print("🚀 Starting Plugin Framework Demonstration")
    
    # Sample PR data for testing
    sample_pr_data = {
        "title": "Add user authentication and payment processing",
        "body": "This PR adds OAuth authentication and Stripe payment integration. "
                "Includes database migrations and new API endpoints.",
        "changed_files": [
            "src/auth/oauth.py",
            "src/payments/stripe_integration.py",
            "src/api/auth_endpoints.py",
            "src/api/payment_endpoints.py",
            "migrations/001_add_user_table.sql",
            "config/database.yml",
            "requirements.txt"
        ],
        "additions": 342,
        "deletions": 28,
        "url": "https://github.com/company/app/pull/123",
        "author": "developer@company.com",
        "created_at": "2024-01-15T10:30:00Z"
    }
    
    # Initialize demo
    demo = PluginFrameworkDemo("config/basic_config.yaml")
    
    try:
        # Initialize framework
        await demo.initialize()
        
        # Run analysis
        print("\n🔄 Running risk analysis...")
        results = await demo.run_analysis(sample_pr_data)
        
        # Display results
        demo.print_results(results)
        
        # Show configuration flexibility
        print("\n\n🔧 CONFIGURATION FLEXIBILITY DEMO")
        print("="*80)
        print("The framework supports multiple configuration files:")
        print("• config/basic_config.yaml - Simple setup")
        print("• config/enterprise_config.yaml - Full enterprise features")
        print("• config/development_config.yaml - Development environment")
        print("\nTo switch configurations, change the config_path parameter")
        
        # Show plugin addition demo
        print("\n\n🔌 PLUGIN ADDITION DEMO")
        print("="*80)
        print("Adding a new plugin is simple:")
        print("1. Create a class inheriting from BaseAgentPlugin")
        print("2. Implement get_metadata() and process() methods")
        print("3. Register the plugin with the framework")
        print("4. Add configuration in YAML file")
        print("\nSee example_plugins.py for reference implementations")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())