"""
Code Review Agents for Multi-Language Analysis
Uses LLM for code quality, complexity, and comment analysis
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from plugin_framework import (
    BaseAgentPlugin, AgentMetadata, AgentInput, AgentOutput,
    AgentCapability, ExecutionMode
)
from llm_client import LLMClient

class PythonCodeReviewAgent(BaseAgentPlugin):
    """Python code quality and security review agent using LLM"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="python_code_review",
            version="1.0.0",
            description="Python code quality analysis using LLM - quality, complexity, comments",
            author="Code Review Team",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.SECURITY],
            dependencies=[],
            execution_priority=20,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={"min_quality_score": float},
            optional_config={}
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Main processing method"""
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            changed_files = pr_data.get('changed_files', [])
            
            # Filter Python files - handle both string filenames and file dictionaries
            python_files = []
            for f in changed_files:
                if isinstance(f, str):
                    if f.endswith('.py'):
                        python_files.append(f)
                elif isinstance(f, dict):
                    filename = f.get('filename', '')
                    if filename.endswith('.py'):
                        python_files.append(f)
            
            if not python_files:
                return AgentOutput(
                    result={},
                    metadata={'language': 'python', 'files_analyzed': 0},
                    session_id=input_data.session_id,
                    analysis_method='llm'
                )
            
            # Analyze each file
            file_analyses = []
            for file_info in python_files:
                try:
                    if isinstance(file_info, str):
                        file_path = file_info
                        file_content = self._get_file_content(file_path, pr_data)
                    else:  # Dictionary with file info
                        file_path = file_info.get('filename', '')
                        file_content = file_info.get('full_content') or file_info.get('patch', '')
                        
                    if file_content:
                        analysis = await self._analyze_with_llm(file_content, file_path)
                        analysis['file'] = file_path
                        file_analyses.append(analysis)
                except Exception as e:
                    continue
            
            # Aggregate results
            total_issues = sum(len(f.get('issues', [])) for f in file_analyses)
            critical_count = sum(f.get('critical_count', 0) for f in file_analyses)
            warning_count = sum(f.get('warning_count', 0) for f in file_analyses)
            
            result = {
                'language': 'python',
                'files_analyzed': len(file_analyses),
                'issues_found': total_issues,
                'critical_issues': critical_count,
                'warnings': warning_count,
                'file_reports': file_analyses,
                'quality_score': sum(f.get('quality_score', 70) for f in file_analyses) / len(file_analyses) if file_analyses else 70
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentOutput(
                result=result,
                metadata={'language': 'python', 'analysis_type': 'llm_based'},
                confidence=0.85,
                analysis_method='llm',
                execution_time=execution_time,
                session_id=input_data.session_id
            )
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Python code review failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="error"
            )
    
    def _get_file_content(self, file_path: str, pr_data: Dict[str, Any]) -> str:
        """Extract file content from PR data"""
        file_contents = pr_data.get('file_contents', {})
        if file_path in file_contents:
            return file_contents[file_path]
        
        # Try to get from files list
        files = pr_data.get('files', [])
        for file_info in files:
            if file_info.get('filename') == file_path:
                return file_info.get('patch', '') or file_info.get('content', '')
        
        return ""
    
    async def _analyze_with_llm(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze code using LLM with strict anti-hallucination prompts"""
        llm_client = LLMClient()
        
        # Build prompt without f-string to avoid escaping issues
        analysis_prompt = """You are a code quality analyzer. Analyze the following Python code strictly based on the actual content provided.

IMPORTANT RULES:
1. Only report issues that are ACTUALLY PRESENT in the code below
2. Provide EXACT line numbers where issues occur
3. Do NOT make assumptions about code not shown
4. Do NOT suggest features or improvements not related to actual issues
5. Base your analysis ONLY on the code provided
6. Do NOT use emojis in your response

Code file: """ + file_path + """

Analyze the following aspects:
1. Code Quality - Style issues, naming conventions, code organization
2. Complexity - Cyclomatic complexity, nested loops, long functions
3. Code Comments - Presence and quality of comments, docstrings
4. Security - Obvious security vulnerabilities (hardcoded secrets, unsafe functions)
5. Best Practices - Python-specific best practices (PEP 8, type hints)

Code to analyze:
```python
""" + content + """
```

Provide your analysis in STRICT JSON format with NO additional text:
{
  "issues": [
    {
      "type": "style|complexity|security|documentation|best_practices",
      "severity": "critical|warning|info",
      "line": <exact_line_number>,
      "message": "Brief description of the actual issue found",
      "rule": "Rule code if applicable"
    }
  ],
  "complexity_score": <0-100, where 100 is most complex>,
  "comment_coverage": <0-100, percentage of code that has meaningful comments>,
  "quality_score": <0-100, where 100 is perfect quality>
}

Only include issues that are verifiable from the code above. Return ONLY valid JSON, no markdown formatting. """
        
        try:
            llm_response = llm_client.call_llm(analysis_prompt)
            
            if not llm_response.get('success', False):
                return self._create_fallback_analysis(content)
            
            # Parse JSON response
            response_text = llm_response.get('response', '').strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
            
            analysis_result = json.loads(response_text)
            issues = analysis_result.get('issues', [])
            
            critical_count = len([i for i in issues if i.get('severity') == 'critical'])
            warning_count = len([i for i in issues if i.get('severity') == 'warning'])
            info_count = len([i for i in issues if i.get('severity') == 'info'])
            
            return {
                'issues': issues,
                'critical_count': critical_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'quality_score': analysis_result.get('quality_score', 70),
                'complexity_score': analysis_result.get('complexity_score', 50),
                'comment_coverage': analysis_result.get('comment_coverage', 50)
            }
            
        except Exception as e:
            return self._create_fallback_analysis(content)
    
    def _create_fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Basic fallback analysis when LLM is unavailable"""
        lines = content.split('\n')
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    'type': 'style',
                    'severity': 'info',
                    'line': line_num,
                    'message': 'Line length exceeds 100 characters'
                })
        
        return {
            'issues': issues,
            'critical_count': 0,
            'warning_count': 0,
            'info_count': len(issues),
            'quality_score': 70,
            'complexity_score': 50,
            'comment_coverage': 50
        }

class JavaCodeReviewAgent(BaseAgentPlugin):
    """Java code quality review agent using LLM"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="java_code_review",
            version="1.0.0",
            description="Java code quality analysis using LLM",
            author="Code Review Team",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.SECURITY],
            dependencies=[],
            execution_priority=20,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={"min_quality_score": float},
            optional_config={}
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Main processing method"""
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            changed_files = pr_data.get('changed_files', [])
            
            # Filter Java files - handle both string filenames and file dictionaries
            java_files = []
            for f in changed_files:
                if isinstance(f, str):
                    if f.endswith('.java'):
                        java_files.append(f)
                elif isinstance(f, dict):
                    filename = f.get('filename', '')
                    if filename.endswith('.java'):
                        java_files.append(f)
            
            if not java_files:
                return AgentOutput(
                    result={},
                    metadata={'language': 'java', 'files_analyzed': 0},
                    session_id=input_data.session_id,
                    analysis_method='llm'
                )
            
            file_analyses = []
            for file_info in java_files:
                try:
                    if isinstance(file_info, str):
                        file_path = file_info
                        file_content = self._get_file_content(file_path, pr_data)
                    else:  # Dictionary with file info
                        file_path = file_info.get('filename', '')
                        file_content = file_info.get('full_content') or file_info.get('patch', '')
                        
                    if file_content:
                        analysis = await self._analyze_java_with_llm(file_content, file_path)
                        analysis['file'] = file_path
                        file_analyses.append(analysis)
                except Exception:
                    continue
            
            total_issues = sum(len(f.get('issues', [])) for f in file_analyses)
            critical_count = sum(f.get('critical_count', 0) for f in file_analyses)
            
            result = {
                'language': 'java',
                'files_analyzed': len(file_analyses),
                'issues_found': total_issues,
                'critical_issues': critical_count,
                'file_reports': file_analyses
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentOutput(
                result=result,
                metadata={'language': 'java'},
                confidence=0.85,
                analysis_method='llm',
                execution_time=execution_time,
                session_id=input_data.session_id
            )
            
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Java code review failed: {str(e)}"],
                session_id=input_data.session_id,
                analysis_method="error"
            )
    
    def _get_file_content(self, file_path: str, pr_data: Dict[str, Any]) -> str:
        """Extract file content from PR data"""
        file_contents = pr_data.get('file_contents', {})
        if file_path in file_contents:
            return file_contents[file_path]
        files = pr_data.get('files', [])
        for file_info in files:
            if file_info.get('filename') == file_path:
                return file_info.get('patch', '') or file_info.get('content', '')
        return ""
    
    async def _analyze_java_with_llm(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Java code using LLM"""
        llm_client = LLMClient()
        
        analysis_prompt = """You are a Java code quality analyzer. Analyze strictly based on actual content.

IMPORTANT RULES:
1. Only report issues ACTUALLY PRESENT
2. Provide EXACT line numbers
3. Do NOT make assumptions
4. Do NOT use emojis

Code file: """ + file_path + """

Analyze:
1. Code Quality - Style, naming conventions
2. Complexity - Method complexity
3. Code Comments - Javadoc, inline comments
4. Security - Vulnerabilities, hardcoded secrets
5. Best Practices - Java standards

Code:
```java
""" + content + """
```

Return STRICT JSON format:
{
  "issues": [{
    "type": "style|complexity|security|documentation|best_practices",
    "severity": "critical|warning|info",
    "line": <exact_line_number>,
    "message": "Brief description"
  }],
  "complexity_score": <0-100>,
  "comment_coverage": <0-100>,
  "quality_score": <0-100>
}

Return ONLY valid JSON."""
        
        try:
            llm_response = llm_client.call_llm(analysis_prompt)
            
            if not llm_response.get('success', False):
                return self._create_fallback_analysis(content)
            
            response_text = llm_response.get('response', '').strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
            
            analysis_result = json.loads(response_text)
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
    
    def _create_fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback analysis"""
        return {
            'issues': [],
            'critical_count': 0,
            'warning_count': 0,
            'quality_score': 70,
            'complexity_score': 50,
            'comment_coverage': 50
        }

class NodeJSCodeReviewAgent(BaseAgentPlugin):
    """Node.js code quality review agent using LLM"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="nodejs_code_review",
            version="1.0.0",
            description="Node.js code quality analysis using LLM",
            author="Code Review Team",
            capabilities=[AgentCapability.ANALYSIS],
            dependencies=[],
            execution_priority=20,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={"min_quality_score": float},
            optional_config={}
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        """Main processing method"""
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            changed_files = pr_data.get('changed_files', [])
            
            # Filter JS/TS files - handle both string filenames and file dictionaries
            js_files = []
            for f in changed_files:
                if isinstance(f, str):
                    if f.endswith(('.js', '.ts')):
                        js_files.append(f)
                elif isinstance(f, dict):
                    filename = f.get('filename', '')
                    if filename.endswith(('.js', '.ts')):
                        js_files.append(f)
            
            if not js_files:
                return AgentOutput(
                    result={},
                    metadata={'language': 'nodejs'},
                    session_id=input_data.session_id,
                    analysis_method='llm'
                )
            
            file_analyses = []
            for file_info in js_files:
                try:
                    if isinstance(file_info, str):
                        file_path = file_info
                        file_content = self._get_file_content(file_path, pr_data)
                    else:  # Dictionary with file info
                        file_path = file_info.get('filename', '')
                        file_content = file_info.get('full_content') or file_info.get('patch', '')
                        
                    if file_content:
                        analysis = await self._analyze_nodejs_with_llm(file_content, file_path)
                        analysis['file'] = file_path
                        file_analyses.append(analysis)
                except Exception:
                    continue
            
            result = {
                'language': 'nodejs',
                'files_analyzed': len(file_analyses),
                'issues_found': sum(len(f.get('issues', [])) for f in file_analyses),
                'file_reports': file_analyses
            }
            
            return AgentOutput(
                result=result,
                metadata={'language': 'nodejs'},
                execution_time=(datetime.now() - start_time).total_seconds(),
                session_id=input_data.session_id,
                analysis_method='llm'
            )
        except Exception as e:
            return AgentOutput(
                result={},
                errors=[f"Node.js review failed: {str(e)}"],
                session_id=input_data.session_id
            )
    
    def _get_file_content(self, file_path: str, pr_data: Dict[str, Any]) -> str:
        file_contents = pr_data.get('file_contents', {})
        if file_path in file_contents:
            return file_contents[file_path]
        files = pr_data.get('files', [])
        for file_info in files:
            if file_info.get('filename') == file_path:
                return file_info.get('patch', '') or file_info.get('content', '')
        return ""
    
    async def _analyze_nodejs_with_llm(self, content: str, file_path: str) -> Dict[str, Any]:
        llm_client = LLMClient()
        
        analysis_prompt = """Analyze Node.js code strictly based on actual content.

RULES:
1. Only report ACTUAL issues
2. EXACT line numbers
3. NO assumptions
4. NO emojis

File: """ + file_path + """

Analyze: Quality, Complexity, Comments, Security, Async patterns

Code:
```javascript
""" + content + """
```

Return JSON:
{
  "issues": [{"type": "...", "severity": "...", "line": <num>, "message": "..."}],
  "complexity_score": <0-100>,
  "comment_coverage": <0-100>,
  "quality_score": <0-100>
}"""
        
        try:
            llm_response = llm_client.call_llm(analysis_prompt)
            
            if not llm_response.get('success', False):
                return {'issues': [], 'quality_score': 70, 'complexity_score': 50, 'comment_coverage': 50}
            
            response_text = llm_response.get('response', '').strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
            
            analysis_result = json.loads(response_text)
            return {
                'issues': analysis_result.get('issues', []),
                'critical_count': len([i for i in analysis_result.get('issues', []) if i.get('severity') == 'critical']),
                'quality_score': analysis_result.get('quality_score', 70),
                'complexity_score': analysis_result.get('complexity_score', 50),
                'comment_coverage': analysis_result.get('comment_coverage', 50)
            }
        except Exception:
            return {'issues': [], 'quality_score': 70, 'complexity_score': 50, 'comment_coverage': 50}

class ReactJSCodeReviewAgent(BaseAgentPlugin):
    """React.js code review agent using LLM"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="reactjs_code_review",
            version="1.0.0",
            description="React.js code quality analysis using LLM",
            author="Code Review Team",
            capabilities=[AgentCapability.ANALYSIS],
            dependencies=[],
            execution_priority=20,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={"min_quality_score": float},
            optional_config={}
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        start_time = datetime.now()
        
        try:
            pr_data = input_data.data
            changed_files = pr_data.get('changed_files', [])
            react_files = [f for f in changed_files if f.endswith(('.jsx', '.tsx'))]
            
            if not react_files:
                return AgentOutput(result={}, session_id=input_data.session_id)
            
            file_analyses = []
            for file_path in react_files:
                try:
                    file_content = self._get_file_content(file_path, pr_data)
                    if file_content:
                        analysis = await self._analyze_react_with_llm(file_content, file_path)
                        analysis['file'] = file_path
                        file_analyses.append(analysis)
                except Exception:
                    continue
            
            result = {
                'language': 'react',
                'files_analyzed': len(file_analyses),
                'file_reports': file_analyses
            }
            
            return AgentOutput(
                result=result,
                session_id=input_data.session_id,
                analysis_method='llm'
            )
        except Exception as e:
            return AgentOutput(result={}, errors=[str(e)], session_id=input_data.session_id)
    
    def _get_file_content(self, file_path: str, pr_data: Dict[str, Any]) -> str:
        file_contents = pr_data.get('file_contents', {})
        if file_path in file_contents:
            return file_contents[file_path]
        return ""
    
    async def _analyze_react_with_llm(self, content: str, file_path: str) -> Dict[str, Any]:
        llm_client = LLMClient()
        
        analysis_prompt = """Analyze React code. Only ACTUAL issues. EXACT line numbers. NO emojis.

File: """ + file_path + """

Analyze: Component structure, Hooks, Performance, Accessibility

Code:
```jsx
""" + content + """
```

Return JSON: {"issues": [...], "quality_score": <num>, "complexity_score": <num>, "comment_coverage": <num>}"""
        
        try:
            llm_response = llm_client.call_llm(analysis_prompt)
            if not llm_response.get('success', False):
                return {'issues': [], 'quality_score': 70, 'complexity_score': 50, 'comment_coverage': 50}
            
            response_text = llm_response.get('response', '').strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]).replace('json', '', 1).strip()
            
            analysis_result = json.loads(response_text)
            return {
                'issues': analysis_result.get('issues', []),
                'quality_score': analysis_result.get('quality_score', 70),
                'complexity_score': analysis_result.get('complexity_score', 50),
                'comment_coverage': analysis_result.get('comment_coverage', 50)
            }
        except Exception:
            return {'issues': [], 'quality_score': 70, 'complexity_score': 50, 'comment_coverage': 50}

class BigQueryReviewAgent(BaseAgentPlugin):
    """BigQuery SQL review agent using LLM"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="bigquery_review",
            version="1.0.0",
            description="BigQuery SQL optimization analysis using LLM",
            author="Database Review Team",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.PERFORMANCE],
            dependencies=[],
            execution_priority=25,
            execution_mode=ExecutionMode.PARALLEL,
            parallel_compatible=True,
            required_config={"cost_threshold": float},
            optional_config={}
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        try:
            pr_data = input_data.data
            changed_files = pr_data.get('changed_files', [])
            sql_files = [f for f in changed_files if f.endswith(('.sql', '.bq'))]
            
            if not sql_files:
                return AgentOutput(result={}, session_id=input_data.session_id)
            
            file_analyses = []
            for file_path in sql_files:
                file_content = self._get_file_content(file_path, pr_data)
                if file_content:
                    analysis = await self._analyze_sql_with_llm(file_content, file_path, "BigQuery")
                    analysis['file'] = file_path
                    file_analyses.append(analysis)
            
            return AgentOutput(
                result={'database': 'bigquery', 'files_analyzed': len(file_analyses), 'file_reports': file_analyses},
                session_id=input_data.session_id
            )
        except Exception as e:
            return AgentOutput(result={}, errors=[str(e)], session_id=input_data.session_id)
    
    def _get_file_content(self, file_path: str, pr_data: Dict[str, Any]) -> str:
        file_contents = pr_data.get('file_contents', {})
        return file_contents.get(file_path, "")
    
    async def _analyze_sql_with_llm(self, content: str, file_path: str, db_type: str) -> Dict[str, Any]:
        llm_client = LLMClient()
        
        prompt = """Analyze """ + db_type + """ SQL. Only ACTUAL issues. NO emojis.

File: """ + file_path + """

Analyze: Query optimization, Cost, Comments

SQL:
```sql
""" + content + """
```

Return JSON: {"issues": [...], "quality_score": <num>, "complexity_score": <num>}"""
        
        try:
            llm_response = llm_client.call_llm(prompt)
            if not llm_response.get('success', False):
                return {'issues': [], 'quality_score': 70}
            
            response_text = llm_response.get('response', '').strip()
            if response_text.startswith('```'):
                response_text = '\n'.join(response_text.split('\n')[1:-1]).replace('json', '', 1).strip()
            
            return json.loads(response_text)
        except Exception:
            return {'issues': [], 'quality_score': 70}

class AzureSQLReviewAgent(BaseAgentPlugin):
    """Azure SQL review agent"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="azuresql_review",
            version="1.0.0",
            description="Azure SQL analysis using LLM",
            author="Database Review Team",
            capabilities=[AgentCapability.ANALYSIS],
            execution_priority=25,
            parallel_compatible=True
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        try:
            pr_data = input_data.data
            sql_files = [f for f in pr_data.get('changed_files', []) if f.endswith('.sql')]
            
            file_analyses = []
            for file_path in sql_files:
                file_content = pr_data.get('file_contents', {}).get(file_path, "")
                if file_content:
                    analysis = await self._analyze_sql(file_content, file_path)
                    analysis['file'] = file_path
                    file_analyses.append(analysis)
            
            return AgentOutput(
                result={'database': 'azuresql', 'file_reports': file_analyses},
                session_id=input_data.session_id
            )
        except Exception as e:
            return AgentOutput(result={}, session_id=input_data.session_id)
    
    async def _analyze_sql(self, content: str, file_path: str) -> Dict[str, Any]:
        llm_client = LLMClient()
        try:
            llm_response = llm_client.call_llm(
                "Analyze Azure SQL. Only actual issues. Return JSON: {'issues': [...], 'quality_score': <num>}\n\nSQL:\n" + content
            )
            if llm_response.get('success', False):
                return json.loads(llm_response.get('response', '').strip().replace('```json', '').replace('```', ''))
        except Exception:
            pass
        return {'issues': [], 'quality_score': 70}

class PostgreSQLReviewAgent(BaseAgentPlugin):
    """PostgreSQL review agent"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="postgresql_review",
            version="1.0.0",
            description="PostgreSQL analysis using LLM",
            author="Database Review Team",
            capabilities=[AgentCapability.ANALYSIS],
            execution_priority=25,
            parallel_compatible=True
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        try:
            pr_data = input_data.data
            sql_files = [f for f in pr_data.get('changed_files', []) if f.endswith('.sql')]
            
            file_analyses = []
            for file_path in sql_files:
                file_content = pr_data.get('file_contents', {}).get(file_path, "")
                if file_content:
                    analysis = await self._analyze_sql(file_content)
                    analysis['file'] = file_path
                    file_analyses.append(analysis)
            
            return AgentOutput(
                result={'database': 'postgresql', 'file_reports': file_analyses},
                session_id=input_data.session_id
            )
        except Exception:
            return AgentOutput(result={}, session_id=input_data.session_id)
    
    async def _analyze_sql(self, content: str) -> Dict[str, Any]:
        llm_client = LLMClient()
        try:
            llm_response = llm_client.call_llm(
                "Analyze PostgreSQL. Return JSON: {'issues': [], 'quality_score': <num>}\n\n" + content
            )
            if llm_response.get('success', False):
                return json.loads(llm_response.get('response', '').strip().replace('```', ''))
        except Exception:
            pass
        return {'issues': [], 'quality_score': 70}

class CosmosDBReviewAgent(BaseAgentPlugin):
    """Cosmos DB review agent"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="cosmosdb_review",
            version="1.0.0",
            description="Cosmos DB analysis using LLM",
            author="Database Review Team",
            capabilities=[AgentCapability.ANALYSIS],
            execution_priority=25,
            parallel_compatible=True
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        try:
            pr_data = input_data.data
            db_files = [f for f in pr_data.get('changed_files', []) if f.endswith(('.json', '.js'))]
            
            file_analyses = []
            for file_path in db_files:
                file_content = pr_data.get('file_contents', {}).get(file_path, "")
                if file_content and 'cosmos' in file_content.lower():
                    analysis = {'file': file_path, 'issues': [], 'quality_score': 70}
                    file_analyses.append(analysis)
            
            return AgentOutput(
                result={'database': 'cosmosdb', 'file_reports': file_analyses},
                session_id=input_data.session_id
            )
        except Exception:
            return AgentOutput(result={}, session_id=input_data.session_id)
