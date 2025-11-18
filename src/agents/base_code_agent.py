"""
Base Code Review Agent

Provides common functionality for all code review agents to eliminate duplication.
"""

import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
from abc import abstractmethod

from ..integration.llm_client import LLMClient
from .code_review_agents import (
    BaseAgentPlugin, AgentMetadata, AgentInput, AgentOutput,
    AgentCapability, ExecutionMode
)

class BaseCodeReviewAgent(BaseAgentPlugin):
    """Base class for all code review agents with common functionality"""
    
    def __init__(self):
        """Initialize base code review agent"""
        self.llm_client = LLMClient()
    
    @abstractmethod
    def get_language_name(self) -> str:
        """Return the language name (python, java, nodejs, etc.)"""
        pass
    
    @abstractmethod
    def get_file_extensions(self) -> Tuple[str, ...]:
        """Return tuple of file extensions for this language"""
        pass
    
    @abstractmethod
    def get_language_specific_analysis_points(self) -> str:
        """Return language-specific analysis points for LLM prompt"""
        pass
    
    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata - can be overridden if needed"""
        return AgentMetadata(
            name=f"{self.get_language_name()}_code_review",
            version="1.0.0",
            description=f"{self.get_language_name().title()} code quality analysis using LLM",
            author="Code Review Team",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.SECURITY],
            dependencies=[],
            execution_priority=20,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Main processing method - common across all agents"""
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            changed_files = pr_data.get('files', [])
            
            # Filter files by extension
            filtered_files = self._filter_files_by_extension(changed_files)
            
            if not filtered_files:
                return AgentOutput(
                    result={},
                    metadata={'language': self.get_language_name(), 'files_analyzed': 0},
                    session_id=input_data.session_id,
                    analysis_method='llm'
                )
            
            # Analyze each file
            file_analyses = []
            for file_info in filtered_files:
                try:
                    file_path = self._extract_file_path(file_info)
                    file_content = self._get_file_content(file_path, pr_data)
                    
                    if file_content:
                        analysis = await self._analyze_with_llm(file_content, file_path)
                        analysis['file'] = file_path
                        file_analyses.append(analysis)
                except Exception:
                    continue
            
            # Aggregate results
            result = self._aggregate_results(file_analyses)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentOutput(
                result=result,
                metadata={'language': self.get_language_name(), 'analysis_type': 'llm_based'},
                confidence=0.85,
                analysis_method='llm',
                execution_time=execution_time,
                session_id=input_data.session_id
            )
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"{self.get_language_name().title()} code review failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="error"
            )
    
    def _filter_files_by_extension(self, changed_files: List) -> List:
        """Filter files by language-specific extensions"""
        extensions = self.get_file_extensions()
        filtered_files = []
        
        for f in changed_files:
            if isinstance(f, str):
                if f.endswith(extensions):
                    filtered_files.append(f)
            elif isinstance(f, dict):
                filename = f.get('filename', '')
                if filename.endswith(extensions):
                    filtered_files.append(f)
        
        return filtered_files
    
    def _extract_file_path(self, file_info) -> str:
        """Extract file path from file info (string or dict)"""
        if isinstance(file_info, str):
            return file_info
        return file_info.get('filename', '')
    
    def _get_file_content(self, file_path: str, pr_data: Dict[str, Any]) -> str:
        """Extract file content from PR data - common implementation"""
        # Try file_contents dictionary first
        file_contents = pr_data.get('file_contents', {})
        if file_path in file_contents:
            return file_contents[file_path]
        
        # Try to get from files list
        files = pr_data.get('files', [])
        for file_info in files:
            if file_info.get('filename') == file_path:
                # Try full_content first (for repository files), then patch (for PR files)
                return (file_info.get('full_content', '') or 
                       file_info.get('patch', '') or 
                       file_info.get('content', ''))
        
        return ""
    
    async def _analyze_with_llm(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze code using LLM with strict anti-hallucination prompts"""
        analysis_prompt = self._build_analysis_prompt(content, file_path)
        
        try:
            llm_response = self.llm_client.call_llm(analysis_prompt)
            
            if not llm_response.get('success', False):
                return self._create_fallback_analysis(content)
            
            # Parse JSON response
            response_text = self._extract_json_from_response(llm_response.get('response', '').strip())
            analysis_result = json.loads(response_text)
            
            # Process issues and calculate metrics
            issues = analysis_result.get('issues', [])
            
            return {
                'issues': issues,
                'critical_count': len([i for i in issues if i.get('severity') == 'critical']),
                'warning_count': len([i for i in issues if i.get('severity') == 'warning']),
                'quality_score': analysis_result.get('quality_score', 70),
                'complexity_score': analysis_result.get('complexity_score', 50),
                'comment_coverage': analysis_result.get('comment_coverage', 50)
            }
        except Exception:
            return self._create_fallback_analysis(content)
    
    def _build_analysis_prompt(self, content: str, file_path: str) -> str:
        """Build LLM analysis prompt"""
        lang_name = self.get_language_name().title()
        lang_specific_points = self.get_language_specific_analysis_points()
        
        return f"""You are a code quality analyzer. Analyze the following {lang_name} code strictly based on the actual content provided.

IMPORTANT RULES:
1. Only report issues that are ACTUALLY PRESENT in the code below
2. Provide EXACT line numbers where issues occur
3. Do NOT make assumptions about code not shown
4. Do NOT suggest features or improvements not related to actual issues
5. Base your analysis ONLY on the code provided
6. Do NOT use emojis in your response

Code file: {file_path}

Analyze the following aspects:
1. Code Quality - Style issues, naming conventions, code organization
2. Complexity - Cyclomatic complexity, nested loops, long functions
3. Code Comments - Presence and quality of comments, docstrings
4. Security - Obvious security vulnerabilities (hardcoded secrets, unsafe functions)
5. Best Practices - {lang_specific_points}

Code to analyze:
```
{content}
```

Provide your analysis in STRICT JSON format with NO additional text:
{{
  "issues": [
    {{
      "type": "style|complexity|security|documentation|best_practices",
      "severity": "critical|warning|info",
      "line": <exact_line_number>,
      "message": "Brief description of the actual issue found",
      "rule": "Rule code if applicable"
    }}
  ],
  "complexity_score": <0-100, where 100 is most complex>,
  "comment_coverage": <0-100, percentage of code that has meaningful comments>,
  "quality_score": <0-100, where 100 is perfect quality>
}}

Only include issues that are verifiable from the code above. Return ONLY valid JSON, no markdown formatting."""
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from LLM response (handle markdown code blocks)"""
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()
        return response_text
    
    def _create_fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Create fallback analysis when LLM fails"""
        return {
            'issues': [],
            'critical_count': 0,
            'warning_count': 0,
            'quality_score': 70,
            'complexity_score': 50,
            'comment_coverage': 50
        }
    
    def _aggregate_results(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple file analyses"""
        if not file_analyses:
            return {
                'language': self.get_language_name(),
                'files_analyzed': 0,
                'issues_found': 0,
                'critical_issues': 0,
                'warnings': 0,
                'file_reports': [],
                'quality_score': 70
            }
        
        total_issues = sum(len(f.get('issues', [])) for f in file_analyses)
        critical_count = sum(f.get('critical_count', 0) for f in file_analyses)
        warning_count = sum(f.get('warning_count', 0) for f in file_analyses)
        avg_quality_score = sum(f.get('quality_score', 70) for f in file_analyses) / len(file_analyses)
        
        return {
            'language': self.get_language_name(),
            'files_analyzed': len(file_analyses),
            'issues_found': total_issues,
            'critical_issues': critical_count,
            'warnings': warning_count,
            'file_reports': file_analyses,
            'quality_score': avg_quality_score
        }
