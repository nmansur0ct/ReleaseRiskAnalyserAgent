"""
Summary Generator for Risk Agent Analyzer

Generates executive summaries and AI-powered insights.
"""

import logging
from typing import Dict, Any, List

class SummaryGenerator:
    """Generates various types of summaries for analysis results"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize summary generator"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def generate_executive_summary(self, analysis_results: List[Any]) -> str:
        """Generate executive summary using AI"""
        try:
            from ..integration.llm_client import get_llm_response
            
            # Create summary prompt
            prompt = self._create_executive_prompt(analysis_results)
            
            # Get LLM response
            response = get_llm_response(prompt)
            return response.get('response', 'Summary generation failed') if isinstance(response, dict) else str(response)
            
        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {e}")
            return "Executive summary generation failed due to technical issues."
    
    def _create_executive_prompt(self, analysis_results: List[Any]) -> str:
        """Create prompt for executive summary"""
        total_repos = len(analysis_results)
        
        return f"""
Generate a professional executive summary for a comprehensive code analysis of {total_repos} repositories.

Provide insights on:
1. Overall code quality assessment
2. Security posture and risks
3. Compliance status
4. Recommendations for improvement
5. Strategic next steps

Make it suitable for C-level executives and technical leadership.
"""
