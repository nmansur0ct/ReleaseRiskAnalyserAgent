"""
Code Review Orchestrator for Risk Agent Analyzer

Manages the execution and coordination of code review agents.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..utilities.data_structures import CodeReviewResult, PRData
from ..agents.code_review_agents import (
    PythonCodeReviewAgent,
    JavaCodeReviewAgent, 
    NodeJSCodeReviewAgent,
    ReactJSCodeReviewAgent,
    BigQueryReviewAgent,
    AzureSQLReviewAgent,
    PostgreSQLReviewAgent,
    CosmosDBReviewAgent
)
from ..agents.code_review_agents import AgentInput

class CodeReviewOrchestrator:
    """Orchestrates code review agent execution"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the code review orchestrator"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all code review agents"""
        default_config = {
            "min_quality_score": self.config.get("min_quality_score", 70.0),
            "cost_threshold": self.config.get("cost_threshold", 1000.0)
        }
        
        return {
            'python_agent': PythonCodeReviewAgent(),
            'java_agent': JavaCodeReviewAgent(),
            'nodejs_agent': NodeJSCodeReviewAgent(),
            'react_agent': ReactJSCodeReviewAgent(),
            'bigquery_agent': BigQueryReviewAgent(),
            'azuresql_agent': AzureSQLReviewAgent(),
            'postgresql_agent': PostgreSQLReviewAgent(),
            'cosmosdb_agent': CosmosDBReviewAgent()
        }
    

    async def execute_code_review(self, pr_data: Dict[str, Any], session_id: str) -> Dict[str, CodeReviewResult]:
        """Execute code review agents on PR data"""
        print("  Full repository code review mode enabled...")
        

        # Get repository files for full code review
        try:
            from ..integration.git_integration import get_git_manager
            git_manager = get_git_manager()
            
            # Extract repository information from PR data
            repo_url = None
            branch = None
            
            # Try multiple ways to get repository URL
            if 'repository_url' in pr_data:
                repo_url = pr_data['repository_url']
            elif 'base' in pr_data and isinstance(pr_data['base'], dict):
                if 'repo' in pr_data['base'] and isinstance(pr_data['base']['repo'], dict):
                    repo_url = pr_data['base']['repo'].get('clone_url') or pr_data['base']['repo'].get('html_url')
                branch = pr_data['base'].get('ref', 'main')
            
            if not repo_url and 'html_url' in pr_data:
                # Extract repo URL from PR URL
                pr_url = pr_data['html_url']
                if '/pull/' in pr_url:
                    repo_url = pr_url.split('/pull/')[0]
                elif '/pulls/' in pr_url:
                    repo_url = pr_url.split('/pulls/')[0]
                    
            if not branch:
                branch = 'main'  # Default branch
            
            if repo_url:
                self.logger.info(f"Fetching repository files from: {repo_url} (branch: {branch})")
                
                # Define file extensions for code review
                file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.sql', '.json', '.yaml', '.yml']
                

                # Fetch repository files
                repository_files = await git_manager.fetch_repository_files(repo_url, branch, file_extensions)
                self.logger.info(f"Fetched {len(repository_files)} repository files for full code review")
                
                # Add repository files to PR data for comprehensive analysis
                if 'files' not in pr_data:
                    pr_data['files'] = []
                pr_data['files'].extend(repository_files)
                print(f"  Added {len(repository_files)} repository files to code review (total: {len(pr_data['files'])} files)")
            else:
                self.logger.warning("Could not extract repository URL from PR data for file fetching")
                print("  Warning: Could not extract repository URL - using PR files only")
                
        except Exception as e:
            self.logger.error(f"Failed to fetch repository files: {e}")
            print(f"  Warning: Could not fetch repository files for comprehensive review: {e}")
        
        # Execute agents
        print("  Executing code review agents...")
        

        try:
            agent_input = AgentInput(pr_data, session_id)
            
            # Execute all agents in parallel
            agent_tasks = []
            for agent_name, agent in self.agents.items():
                agent_tasks.append(self._execute_single_agent(agent_name, agent, agent_input))
            
            # Wait for all agents to complete
            results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Process results into CodeReviewResult objects
            code_review_results = {}
            total_issues = 0
            critical_issues = 0
            

            for agent_name, result in zip(self.agents.keys(), results):
                if isinstance(result, Exception):
                    code_review_results[agent_name] = CodeReviewResult(
                        agent_name=agent_name,
                        files_analyzed=0,
                        issues_found=0,
                        critical_issues=0,
                        major_issues=0,
                        minor_issues=0,
                        response="",
                        error=str(result)
                    )
                elif hasattr(result, 'result') and hasattr(result, 'metadata'):
                    # Handle AgentOutput objects
                    result_data = result.result or {}
                    files_analyzed = result_data.get('files_analyzed', 0)
                    issues_found = result_data.get('issues_found', 0)
                    critical_count = result_data.get('critical_issues', 0)
                    
                    code_review_results[agent_name] = CodeReviewResult(
                        agent_name=agent_name,
                        files_analyzed=files_analyzed,
                        issues_found=issues_found,
                        critical_issues=critical_count,
                        major_issues=0,  # Could be extracted from response
                        minor_issues=0,  # Could be extracted from response
                        response=str(result_data),
                        execution_time=getattr(result, 'execution_time', 0.0)
                    )
                    
                    total_issues += issues_found
                    critical_issues += critical_count
                elif isinstance(result, dict):
                    # Extract metrics from agent response
                    issues_found = self._extract_issues_count(result.get('response', ''))
                    critical_count = self._extract_critical_count(result.get('response', ''))
                    
                    # Ensure files_analyzed is always an integer
                    files_analyzed = result.get('files_analyzed', 0)
                    if isinstance(files_analyzed, list):
                        files_analyzed = len(files_analyzed)
                    elif not isinstance(files_analyzed, int):
                        files_analyzed = 0
                    
                    code_review_results[agent_name] = CodeReviewResult(
                        agent_name=agent_name,
                        files_analyzed=files_analyzed,
                        issues_found=issues_found,
                        critical_issues=critical_count,
                        major_issues=0,  # Could be extracted from response
                        minor_issues=0,  # Could be extracted from response
                        response=result.get('response', ''),
                        execution_time=result.get('execution_time', 0.0)
                    )
                    
                    total_issues += issues_found
                    critical_issues += critical_count
                else:
                    # Handle non-dict results
                    code_review_results[agent_name] = CodeReviewResult(
                        agent_name=agent_name,
                        files_analyzed=0,
                        issues_found=0,
                        critical_issues=0,
                        major_issues=0,
                        minor_issues=0,
                        response=str(result),
                        execution_time=0.0
                    )
            
            print(f"  Code Review Complete: {len(pr_data.get('files', []))} files, {total_issues} issues ({critical_issues} critical)")
            return code_review_results
            
        except Exception as e:
            self.logger.error(f"Code review execution failed: {e}")
            return {}
    
    async def _execute_single_agent(self, agent_name: str, agent: Any, agent_input: AgentInput):
        """Execute a single code review agent"""

        start_time = datetime.now()
        try:
            result = await agent.process(agent_input, None)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Check if result is an AgentOutput object
            if hasattr(result, 'result') and hasattr(result, 'execution_time'):
                # Update execution time if not already set
                if not result.execution_time or result.execution_time == 0:
                    result.execution_time = execution_time
                return result
            elif isinstance(result, dict):
                result['execution_time'] = execution_time
                return result
            else:
                return {
                    'response': str(result),
                    'execution_time': execution_time,
                    'files_analyzed': 0
                }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                'error': str(e),
                'execution_time': execution_time,
                'files_analyzed': 0
            }
    
    def _extract_issues_count(self, response: str) -> int:
        """Extract total issues count from agent response"""
        # Simple heuristic - count occurrences of issue-related keywords
        if not response:
            return 0
        
        response_lower = response.lower()
        issue_indicators = ['error', 'warning', 'issue', 'problem', 'concern', 'violation']
        
        count = 0
        for indicator in issue_indicators:
            count += response_lower.count(indicator)
        
        return min(count, 50)  # Cap at reasonable limit
    
    def _extract_critical_count(self, response: str) -> int:
        """Extract critical issues count from agent response"""
        if not response:
            return 0
        
        response_lower = response.lower()
        critical_indicators = ['critical', 'severe', 'high priority', 'security']
        
        count = 0
        for indicator in critical_indicators:
            count += response_lower.count(indicator)
        
        return min(count, 10)  # Cap at reasonable limit