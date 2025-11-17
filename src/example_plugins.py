"""
Example Agent Plugins demonstrating the modular plugin framework
"""

import asyncio
import re
from typing import Dict, Any, List
from datetime import datetime

from .plugin_framework import (
    BaseAgentPlugin, AgentMetadata, AgentInput, AgentOutput,
    AgentCapability, ExecutionMode
)
from .llm_client import LLMClient

# Compatibility wrapper for the old get_llm_manager function
def get_agent_llm_manager():
    """Compatibility wrapper that returns an LLMClient instance"""
    return LLMClient()

def analyze_code_changes(changes, provider=None):
    """Simplified code changes analysis using LLM client"""
    llm_client = LLMClient()
    prompt = f"""
    You are an Agent doing analysis of the following code changes for risk assessment:
    
    Files changed: {changes.get('changed_files', [])}
    Additions: {changes.get('additions', 0)}
    Deletions: {changes.get('deletions', 0)}
    Title: {changes.get('title', '')}
    Description: {changes.get('body', '')}
    
    As an Agent, please provide:
    1. Risk level (low/medium/high)
    2. Affected modules
    3. Potential security concerns
    4. Deployment recommendations
    
    Return your analysis in a structured format.
    """
    
    result = llm_client.call_llm(prompt)
    if result.get('success'):
        return {'content': result.get('response', '')}
    else:
        return {'content': 'Analysis failed'}

class ChangeLogSummarizerPlugin(BaseAgentPlugin):
    """Enhanced Change Log Summarizer Agent Plugin"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="change_log_summarizer",
            version="2.0.0",
            description="Intelligent analysis and summarization of pull request changes",
            author="Risk Analyzer Team",
            capabilities=[AgentCapability.ANALYSIS],
            dependencies=[],
            execution_priority=10,  # High priority - runs first
            execution_mode=ExecutionMode.SEQUENTIAL,
            parallel_compatible=False,
            required_config={
                "llm_provider": str,
                "confidence_threshold": float
            },
            optional_config={
                "fallback_provider": str,
                "analysis_depth": str,
                "timeout_seconds": int
            }
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Process PR data and generate change summary"""
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            
            # Extract key information
            changed_files = pr_data.get('changed_files', [])
            additions = pr_data.get('additions', 0)
            deletions = pr_data.get('deletions', 0)
            title = pr_data.get('title', '')
            body = pr_data.get('body', '')
            
            # Analyze with Agent LLM if configured
            if self.config.get('llm_provider'):
                summary_result = await self._analyze_with_agent_llm(pr_data)
                if summary_result['confidence'] >= self.config.get('confidence_threshold', 0.7):
                    return self._create_output(summary_result, 'llm_primary', input_data.session_id, start_time)
            
            # Fallback to heuristic analysis
            summary_result = await self._analyze_with_heuristics(pr_data)
            return self._create_output(summary_result, 'heuristic', input_data.session_id, start_time)
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Change log analysis failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="error"
            )
    
    async def _analyze_with_agent_llm(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agent LLM-powered analysis using environment-configured provider"""
        try:
            # Use the new Agent LLM integration with environment configuration
            llm_manager = get_agent_llm_manager()
            
            # Get provider from config or use environment default
            provider = self.config.get('llm_provider')
            
            # Analyze using Agent LLM
            result = await analyze_code_changes(pr_data, provider)
            
            if result['success']:
                # Parse the Agent LLM response (assuming JSON format)
                # In a real implementation, you'd parse the actual Agent LLM response
                changed_files = pr_data.get('changed_files', [])
                additions = pr_data.get('additions', 0)
                deletions = pr_data.get('deletions', 0)
                
                # Intelligent module detection
                modules = set()
                for file_path in changed_files:
                    parts = file_path.split('/')
                    if 'src' in parts:
                        idx = parts.index('src')
                        if idx + 1 < len(parts):
                            modules.add(parts[idx + 1])
                    elif len(parts) > 1:
                        modules.add(parts[0])
                
                # Risk indicator detection
                risk_indicators = []
                content = f"{pr_data.get('title', '')} {pr_data.get('body', '')}".lower()
                
                risk_patterns = {
                    'security': ['auth', 'password', 'token', 'security', 'vulnerability'],
                    'database': ['migration', 'schema', 'sql', 'database', 'table'],
                    'api': ['endpoint', 'route', 'api', 'rest', 'graphql'],
                    'infrastructure': ['deploy', 'config', 'environment', 'docker']
                }
                
                for category, patterns in risk_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        risk_indicators.append(category)
                
                # Change size classification
                total_changes = additions + deletions
                if total_changes > 500 or len(changed_files) > 20:
                    change_size = "large"
                elif total_changes > 100 or len(changed_files) > 5:
                    change_size = "medium"
                else:
                    change_size = "small"
                
                return {
                    'summary': f"Agent LLM Analysis: You are an Agent doing change analysis on {len(changed_files)} files with {total_changes} total changes",
                    'affected_modules': list(modules),
                    'change_size': change_size,
                    'risk_indicators': risk_indicators,
                    'confidence': 0.9,  # Higher confidence for Agent LLM analysis
                    'llm_provider': result['provider_used'],
                    'llm_response': result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                }
            else:
                # Agent LLM failed, fall back to heuristic analysis
                return await self._analyze_with_heuristics(pr_data)
                
        except Exception as e:
            # Fallback to heuristic analysis on any error
            return await self._analyze_with_heuristics(pr_data)
    
    async def _analyze_with_heuristics(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Heuristic-based analysis"""
        changed_files = pr_data.get('changed_files', [])
        additions = pr_data.get('additions', 0)
        deletions = pr_data.get('deletions', 0)
        
        # Simple module extraction
        modules = []
        for file_path in changed_files:
            parts = file_path.split('/')
            if len(parts) > 1:
                modules.append(parts[0])
        
        # Basic change size
        total_changes = additions + deletions
        if total_changes > 300:
            change_size = "large"
        elif total_changes > 50:
            change_size = "medium"
        else:
            change_size = "small"
        
        return {
            'summary': f"Changed {len(changed_files)} files",
            'affected_modules': list(set(modules)),
            'change_size': change_size,
            'risk_indicators': [],
            'confidence': 0.6
        }
    
    def _create_output(self, result: Dict[str, Any], method: str, 
                      session_id: str, start_time: datetime) -> AgentOutput:
        """Create standardized output"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentOutput(
            result=result,
            confidence=result.get('confidence', 0.6),
            analysis_method=method,
            execution_time=execution_time,
            session_id=session_id
        )

class SecurityAnalyzerPlugin(BaseAgentPlugin):
    """Security-focused analysis agent plugin"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="security_analyzer",
            version="1.0.0",
            description="Advanced security analysis for code changes",
            author="Security Team",
            capabilities=[AgentCapability.SECURITY, AgentCapability.ANALYSIS],
            dependencies=["change_log_summarizer"],
            execution_priority=30,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={
                "scan_types": list
            },
            optional_config={
                "severity_threshold": str,
                "custom_patterns": dict
            }
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Perform security analysis"""
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            scan_types = self.config.get('scan_types', ['secret_detection'])
            
            security_findings = []
            
            # Secret detection
            if 'secret_detection' in scan_types:
                secrets = await self._detect_secrets(pr_data)
                security_findings.extend(secrets)
            
            # Vulnerability scanning
            if 'vulnerability_scan' in scan_types:
                vulnerabilities = await self._scan_vulnerabilities(pr_data)
                security_findings.extend(vulnerabilities)
            
            # Dependency checking
            if 'dependency_check' in scan_types:
                dependencies = await self._check_dependencies(pr_data)
                security_findings.extend(dependencies)
            
            # Calculate security score
            security_score = self._calculate_security_score(security_findings)
            
            result = {
                'security_findings': security_findings,
                'security_score': security_score,
                'scan_types_used': scan_types,
                'recommendation': self._get_security_recommendation(security_score)
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentOutput(
                result=result,
                confidence=0.9,
                analysis_method="security_analysis",
                execution_time=execution_time,
                session_id=input_data.session_id
            )
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Security analysis failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="security_analysis"
            )
    
    async def _detect_secrets(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential secrets in PR content"""
        findings = []
        content = f"{pr_data.get('title', '')} {pr_data.get('body', '')}"
        
        secret_patterns = [
            (r'password\s*[=:]\s*["\'][^"\']+["\']', 'password', 'high'),
            (r'api_key\s*[=:]\s*["\'][^"\']+["\']', 'api_key', 'high'),
            (r'secret\s*[=:]\s*["\'][^"\']+["\']', 'secret', 'high'),
            (r'token\s*[=:]\s*["\'][^"\']+["\']', 'token', 'medium'),
        ]
        
        for pattern, secret_type, severity in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append({
                    'type': 'secret_detection',
                    'secret_type': secret_type,
                    'severity': severity,
                    'location': 'pr_description',
                    'message': f"Potential {secret_type} detected"
                })
        
        return findings
    
    async def _scan_vulnerabilities(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan for known vulnerabilities"""
        # Simulated vulnerability scanning
        await asyncio.sleep(0.05)
        
        findings = []
        changed_files = pr_data.get('changed_files', [])
        
        # Check for vulnerable file patterns
        vulnerable_patterns = [
            ('*.sql', 'SQL injection risk', 'medium'),
            ('*auth*', 'Authentication changes', 'high'),
            ('*config*', 'Configuration changes', 'medium')
        ]
        
        for file_path in changed_files:
            for pattern, message, severity in vulnerable_patterns:
                if pattern.replace('*', '') in file_path.lower():
                    findings.append({
                        'type': 'vulnerability_scan',
                        'severity': severity,
                        'file': file_path,
                        'message': message
                    })
        
        return findings
    
    async def _check_dependencies(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for dependency security issues"""
        # Simulated dependency checking
        await asyncio.sleep(0.03)
        
        findings = []
        changed_files = pr_data.get('changed_files', [])
        
        # Check for dependency files
        dependency_files = ['requirements.txt', 'package.json', 'pom.xml', 'Gemfile']
        
        for file_path in changed_files:
            if any(dep_file in file_path for dep_file in dependency_files):
                findings.append({
                    'type': 'dependency_check',
                    'severity': 'low',
                    'file': file_path,
                    'message': f"Dependency file {file_path} modified - review for security updates"
                })
        
        return findings
    
    def _calculate_security_score(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate overall security score"""
        if not findings:
            return 0
        
        severity_weights = {'low': 10, 'medium': 25, 'high': 50, 'critical': 100}
        total_score = 0
        
        for finding in findings:
            severity = finding.get('severity', 'low')
            total_score += severity_weights.get(severity, 10)
        
        return min(total_score, 100)  # Cap at 100
    
    def _get_security_recommendation(self, security_score: int) -> str:
        """Get security recommendation based on score"""
        if security_score >= 75:
            return "Security review required before release"
        elif security_score >= 50:
            return "Additional security validation recommended"
        elif security_score >= 25:
            return "Monitor for security implications"
        else:
            return "No immediate security concerns"

class NotificationAgentPlugin(BaseAgentPlugin):
    """Notification agent for sending analysis results"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="notification_agent",
            version="1.0.0",
            description="Send notifications about analysis results",
            author="DevOps Team",
            capabilities=[AgentCapability.NOTIFICATION],
            dependencies=["release_decision_agent"],
            execution_priority=90,  # Low priority - runs last
            execution_mode=ExecutionMode.SEQUENTIAL,
            parallel_compatible=True,
            required_config={
                "channels": list
            },
            optional_config={
                "templates_path": str,
                "webhook_url": str,
                "slack_token": str
            }
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Send notifications about analysis results"""
        start_time = datetime.now()
        
        try:
            channels = self.config.get('channels', [])
            notifications_sent = []
            
            # Get analysis results from state
            analysis_results = getattr(state, 'analysis_results', {})
            decision_results = getattr(state, 'decision_results', {})
            
            # Prepare notification content
            notification_content = self._prepare_notification_content(
                analysis_results, decision_results, input_data
            )
            
            # Send to configured channels
            for channel in channels:
                if channel == 'slack':
                    result = await self._send_slack_notification(notification_content)
                    notifications_sent.append(f"slack: {result}")
                elif channel == 'email':
                    result = await self._send_email_notification(notification_content)
                    notifications_sent.append(f"email: {result}")
                elif channel == 'webhook':
                    result = await self._send_webhook_notification(notification_content)
                    notifications_sent.append(f"webhook: {result}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentOutput(
                result={
                    'notifications_sent': notifications_sent,
                    'channels_used': channels,
                    'notification_content': notification_content
                },
                confidence=1.0,
                analysis_method="notification",
                execution_time=execution_time,
                session_id=input_data.session_id
            )
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Notification failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="notification"
            )
    
    def _prepare_notification_content(self, analysis_results: Dict, 
                                    decision_results: Dict, 
                                    input_data: AgentInput) -> Dict[str, Any]:
        """Prepare notification content"""
        pr_data = input_data.data
        
        # Extract key information
        change_summary = analysis_results.get('change_log_summarizer', {})
        security_analysis = analysis_results.get('security_analyzer', {})
        release_decision = decision_results.get('release_decision_agent', {})
        
        return {
            'pr_title': pr_data.get('title', 'Unknown PR'),
            'pr_url': pr_data.get('url', '#'),
            'change_size': change_summary.get('change_size', 'unknown'),
            'affected_modules': change_summary.get('affected_modules', []),
            'security_score': security_analysis.get('security_score', 0),
            'decision': release_decision.get('approved', 'unknown'),
            'decision_rationale': release_decision.get('rationale', 'No rationale provided'),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _send_slack_notification(self, content: Dict[str, Any]) -> str:
        """Send Slack notification"""
        # Simulated Slack notification
        await asyncio.sleep(0.1)
        return f"Sent to Slack: {content['pr_title']}"
    
    async def _send_email_notification(self, content: Dict[str, Any]) -> str:
        """Send email notification"""
        # Simulated email notification
        await asyncio.sleep(0.1)
        return f"Sent to email: {content['pr_title']}"
    
    async def _send_webhook_notification(self, content: Dict[str, Any]) -> str:
        """Send webhook notification"""
        # Simulated webhook notification
        await asyncio.sleep(0.05)
        return f"Sent to webhook: {content['pr_title']}"

class CustomCompliancePlugin(BaseAgentPlugin):
    """Example custom compliance plugin"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="custom_compliance_checker",
            version="1.0.0",
            description="Custom compliance validation for organization-specific requirements",
            author="Compliance Team",
            capabilities=[AgentCapability.COMPLIANCE, AgentCapability.VALIDATION],
            dependencies=["change_log_summarizer"],
            execution_priority=40,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={
                "standards": list
            },
            optional_config={
                "custom_rules": dict,
                "exemption_list": list
            }
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Perform compliance validation"""
        start_time = datetime.now()
        
        try:
            standards = self.config.get('standards', [])
            compliance_results = {}
            
            # Check each compliance standard
            for standard in standards:
                if standard == 'SOX':
                    compliance_results['SOX'] = await self._check_sox_compliance(input_data)
                elif standard == 'GDPR':
                    compliance_results['GDPR'] = await self._check_gdpr_compliance(input_data)
                elif standard == 'HIPAA':
                    compliance_results['HIPAA'] = await self._check_hipaa_compliance(input_data)
            
            # Calculate overall compliance score
            overall_compliant = all(result.get('compliant', False) 
                                  for result in compliance_results.values())
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentOutput(
                result={
                    'compliance_results': compliance_results,
                    'overall_compliant': overall_compliant,
                    'standards_checked': standards
                },
                confidence=0.95,
                analysis_method="compliance_check",
                execution_time=execution_time,
                session_id=input_data.session_id
            )
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Compliance check failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="compliance_check"
            )
    
    async def _check_sox_compliance(self, input_data: AgentInput) -> Dict[str, Any]:
        """Check SOX compliance"""
        await asyncio.sleep(0.02)
        
        pr_data = input_data.data
        changed_files = pr_data.get('changed_files', [])
        
        # Check for financial data access
        financial_files = [f for f in changed_files if 'financial' in f.lower() or 'billing' in f.lower()]
        
        if financial_files:
            return {
                'compliant': False,
                'issues': ['Financial data access requires additional approval'],
                'affected_files': financial_files
            }
        
        return {'compliant': True, 'issues': []}
    
    async def _check_gdpr_compliance(self, input_data: AgentInput) -> Dict[str, Any]:
        """Check GDPR compliance"""
        await asyncio.sleep(0.02)
        
        pr_data = input_data.data
        content = f"{pr_data.get('title', '')} {pr_data.get('body', '')}".lower()
        
        # Check for personal data handling
        personal_data_keywords = ['email', 'personal', 'gdpr', 'privacy', 'data protection']
        
        if any(keyword in content for keyword in personal_data_keywords):
            return {
                'compliant': False,
                'issues': ['Personal data handling requires privacy impact assessment'],
                'recommendations': ['Conduct privacy review', 'Update data protection documentation']
            }
        
        return {'compliant': True, 'issues': []}
    
    async def _check_hipaa_compliance(self, input_data: AgentInput) -> Dict[str, Any]:
        """Check HIPAA compliance"""
        await asyncio.sleep(0.02)
        
        pr_data = input_data.data
        changed_files = pr_data.get('changed_files', [])
        
        # Check for healthcare data
        healthcare_files = [f for f in changed_files if any(term in f.lower() 
                           for term in ['health', 'medical', 'patient', 'hipaa'])]
        
        if healthcare_files:
            return {
                'compliant': False,
                'issues': ['Healthcare data changes require HIPAA compliance review'],
                'affected_files': healthcare_files
            }
        
        return {'compliant': True, 'issues': []}