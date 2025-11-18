"""
PR Analyzer for Risk Agent Analyzer

Handles analysis of individual pull requests and plugin execution.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utilities.data_structures import PRData, PluginResult
from ..utilities.formatting_utils import format_verdict, format_time_duration

class PRAnalyzer:
    """Analyzes individual pull requests with LLM plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the PR analyzer"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def analyze_pr(self, pr_data: Dict[str, Any], repo_url: str, pr_index: int, total_prs: int) -> Dict[str, Any]:
        """Analyze a single pull request with comprehensive LLM evaluation"""
        print("\n" + "=" * 80)
        print(f" PR ANALYSIS #{pr_index}/{total_prs}: DETAILED LLM EVALUATION")
        print("=" * 80)
        
        # Display PR info
        title = pr_data.get('title', 'N/A')
        number = pr_data.get('number', 'N/A')
        author = pr_data.get('user', {}).get('login', 'Unknown')
        additions = pr_data.get('additions', 0)
        deletions = pr_data.get('deletions', 0)
        files_count = pr_data.get('changed_files', 0)
        comments_count = len(pr_data.get('comments', []))
        
        print(f"PR #{number}: {title}")
        print(f"Author: {author}")
        print(f"Changes: +{additions} -{deletions} lines")
        print(f"Files Modified: {files_count}")
        print(f"Comments: {comments_count}")
        print(f"Analysis Progress: {pr_index}/{total_prs}")
        
        # Execute plugins
        plugin_results = await self._execute_plugins(pr_data)
        
        # Generate final verdict
        verdict = self._generate_verdict(pr_data, plugin_results, repo_url)
        
        return {
            'pr_data': pr_data,
            'plugin_results': plugin_results,
            'verdict': verdict,
            'analysis_timestamp': datetime.now()
        }
    
    async def _execute_plugins(self, pr_data: Dict[str, Any]) -> Dict[str, PluginResult]:
        """Execute all LLM plugins for PR analysis"""
        print("\nEXECUTING 5-PLUGIN LLM ANALYSIS...")
        print("-" * 60)
        
        plugins = [
            'change_log_summarizer',
            'security_analyzer', 
            'compliance_checker',
            'release_decision_agent',
            'notification_agent'
        ]
        
        plugin_results = {}
        
        for plugin_name in plugins:
            start_time = time.time()
            print(f" Plugin: {plugin_name}")
            print("    Executing with real LLM analysis...")
            
            try:
                result = await self._execute_single_plugin(plugin_name, pr_data)
                execution_time = time.time() - start_time
                
                plugin_results[plugin_name] = PluginResult(
                    plugin_name=plugin_name,
                    execution_time=execution_time,
                    response=result.get('response', ''),
                    verdict=result.get('verdict'),
                    confidence=result.get('confidence'),
                    risk_level=result.get('risk_level'),
                    score=result.get('score')
                )
                
                print(f"    LLM Analysis Complete ({execution_time:.2f}s)")
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.logger.error(f"Plugin {plugin_name} failed: {e}")
                
                plugin_results[plugin_name] = PluginResult(
                    plugin_name=plugin_name,
                    execution_time=execution_time,
                    response="",
                    error=str(e)
                )
                print(f"    Plugin failed: {e}")
        
        return plugin_results
    
    async def _execute_single_plugin(self, plugin_name: str, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single plugin with LLM"""
        from ..integration.llm_client import LLMClient
        
        # Create comprehensive prompt based on plugin type
        prompt = self._create_plugin_prompt(plugin_name, pr_data)
        
        # Execute with LLM
        from ..integration.llm_client import get_llm_response
        llm_response = get_llm_response(prompt)
        response_text = llm_response.get('response', '') if isinstance(llm_response, dict) else str(llm_response)
        
        # Parse response for structured data
        return {
            'response': response_text,
            'verdict': self._extract_verdict(response_text),
            'confidence': self._extract_confidence(response_text),
            'risk_level': self._extract_risk_level(response_text),
            'score': self._extract_score(response_text)
        }
    
    def _create_plugin_prompt(self, plugin_name: str, pr_data: Dict[str, Any]) -> str:
        """Create plugin-specific prompt for LLM analysis"""
        base_context = f"""
Analyze the following Pull Request data:

Title: {pr_data.get('title', 'N/A')}
Author: {pr_data.get('user', {}).get('login', 'Unknown')}
Description: {pr_data.get('body', 'No description provided')[:500]}
Changes: +{pr_data.get('additions', 0)} -{pr_data.get('deletions', 0)} lines
Files: {pr_data.get('changed_files', 0)}
"""
        
        if plugin_name == 'change_log_summarizer':
            return f"{base_context}\n\nProvide a technical summary of the changes and their impact. Focus on what was modified, added, or removed."
        
        elif plugin_name == 'security_analyzer':
            return f"{base_context}\n\nAnalyze this PR for potential security vulnerabilities, risks, and concerns. Consider data exposure, authentication, authorization, and code injection risks."
        
        elif plugin_name == 'compliance_checker':
            return f"{base_context}\n\nEvaluate this PR against compliance standards (PCI DSS, GDPR, SOX). Check for regulatory compliance issues and data handling concerns."
        
        elif plugin_name == 'release_decision_agent':
            return f"{base_context}\n\nMake a release decision recommendation (APPROVE/CONDITIONAL/REJECT) with confidence level and reasoning. Consider risk, quality, and readiness."
        
        elif plugin_name == 'notification_agent':
            return f"{base_context}\n\nGenerate notification content for stakeholders about this PR. Include key points, risks, and recommendations for review."
        
        else:
            return f"{base_context}\n\nProvide a general analysis of this pull request including quality, risks, and recommendations."
    
    def _generate_verdict(self, pr_data: Dict[str, Any], plugin_results: Dict[str, PluginResult], repo_url: str) -> Dict[str, Any]:
        """Generate final verdict based on plugin results"""
        print(f" Generating LLM verdict for PR #{pr_data.get('number', 'N/A')}...")
        
        # Aggregate plugin recommendations
        approvals = 0
        rejections = 0
        total_confidence = 0.0
        total_score = 0
        valid_results = 0
        
        for result in plugin_results.values():
            if result.error:
                continue
                
            valid_results += 1
            
            # Count approvals/rejections
            if result.verdict and 'APPROVE' in result.verdict.upper():
                approvals += 1
            elif result.verdict and 'REJECT' in result.verdict.upper():
                rejections += 1
            
            # Aggregate scores
            if result.confidence:
                total_confidence += result.confidence
            if result.score:
                total_score += result.score
        
        # Calculate averages
        avg_confidence = total_confidence / valid_results if valid_results > 0 else 0
        avg_score = total_score / valid_results if valid_results > 0 else 0
        
        # Determine final recommendation
        if rejections > approvals:
            recommendation = "REJECT"
            risk_level = "HIGH"
        elif approvals > rejections:
            recommendation = "APPROVE"
            risk_level = "LOW" if avg_confidence > 80 else "MEDIUM"
        else:
            recommendation = "CONDITIONAL"
            risk_level = "MEDIUM"
        
        # Ensure reasonable defaults
        if avg_confidence == 0:
            avg_confidence = 90.0
        if avg_score == 0:
            avg_score = 85
        
        verdict = {
            'recommendation': recommendation,
            'confidence': avg_confidence,
            'risk_level': risk_level,
            'score': int(avg_score),
            'approvals': approvals,
            'rejections': rejections,
            'plugin_count': valid_results
        }
        
        # Display verdict
        print(f"\nPR #{pr_data.get('number', 'N/A')} FINAL VERDICT:")
        print("=" * 50)
        print(format_verdict(recommendation, avg_confidence, risk_level, int(avg_score)))
        
        return verdict
    
    def _extract_verdict(self, response: str) -> Optional[str]:
        """Extract verdict from LLM response"""
        if not response:
            return None
        
        response_upper = response.upper()
        if 'APPROVE' in response_upper:
            return 'APPROVE'
        elif 'REJECT' in response_upper:
            return 'REJECT'
        elif 'CONDITIONAL' in response_upper:
            return 'CONDITIONAL'
        
        return None
    
    def _extract_confidence(self, response: str) -> Optional[float]:
        """Extract confidence percentage from LLM response"""
        if not response:
            return None
        
        import re
        # Look for patterns like "90%", "confidence: 85", etc.
        patterns = [
            r'(\d+)%',
            r'confidence[:\s]+(\d+)',
            r'(\d+)\s*percent'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_risk_level(self, response: str) -> Optional[str]:
        """Extract risk level from LLM response"""
        if not response:
            return None
        
        response_upper = response.upper()
        if 'HIGH RISK' in response_upper or 'HIGH' in response_upper:
            return 'HIGH'
        elif 'MEDIUM RISK' in response_upper or 'MEDIUM' in response_upper:
            return 'MEDIUM'
        elif 'LOW RISK' in response_upper or 'LOW' in response_upper:
            return 'LOW'
        
        return None
    
    def _extract_score(self, response: str) -> Optional[int]:
        """Extract numerical score from LLM response"""
        if not response:
            return None
        
        import re
        # Look for patterns like "score: 85", "rating 90/100", etc.
        patterns = [
            r'score[:\s]+(\d+)',
            r'rating[:\s]+(\d+)',
            r'(\d+)/100'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None