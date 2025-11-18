"""
Repository Orchestrator for Risk Agent Analyzer

Main orchestration component that coordinates the entire analysis workflow.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utilities.data_structures import AnalysisResult, PRData, RepositoryMetrics
from ..analysis.code_review_orchestrator import CodeReviewOrchestrator
from ..analysis.pr_analyzer import PRAnalyzer
from ..analysis.risk_assessor import RiskAssessor
from ..reporting.comprehensive_reporter import ComprehensiveReporter
from ..utilities.formatting_utils import (
    print_framework_header, print_repository_header, format_pr_summary, 
    format_repository_metrics, format_time_duration
)

class RepositoryOrchestrator:
    """Orchestrates the complete repository analysis workflow"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the repository orchestrator"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.code_review_orchestrator = CodeReviewOrchestrator(config)
        self.pr_analyzer = PRAnalyzer(config)
        self.risk_assessor = RiskAssessor(config)
        self.comprehensive_reporter = ComprehensiveReporter(config)
    
    async def analyze_repositories(self, repo_urls: List[str]) -> List[AnalysisResult]:
        """Analyze multiple repositories and generate comprehensive report"""
        print_framework_header(
            repo_urls, 
            self.config.get('pr_limit', 10),
            self.config.get('output_dir', '../reports'),
            self.config.get('pr_state', 'open')
        )
        
        all_results = []
        
        # Process each repository
        for i, repo_url in enumerate(repo_urls, 1):
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            print_repository_header(i, len(repo_urls), repo_name)
            
            try:
                result = await self._analyze_single_repository(repo_url, i, len(repo_urls))
                all_results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze repository {repo_url}: {e}")
                # Create minimal result for failed analysis
                all_results.append(AnalysisResult(
                    repository_url=repo_url,
                    repository_name=repo_name,
                    default_branch="unknown",
                    analysis_timestamp=datetime.now()
                ))
        
        # Generate comprehensive report
        report_path = await self.comprehensive_reporter.generate_comprehensive_report(
            all_results, repo_urls
        )
        
        print("\\nMULTI-REPOSITORY ANALYSIS COMPLETE!")
        print("=" * 80)
        
        return all_results
    
    async def _analyze_single_repository(self, repo_url: str, repo_index: int, total_repos: int) -> AnalysisResult:
        """Analyze a single repository comprehensively"""
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        # Fetch repository data
        print("\\nGit Integration - PR Fetching")
        print("=" * 60)
        print(f"Analyzing repository: {repo_url}")
        
        prs, repository_stats = await self._fetch_repository_data(repo_url)
        
        # Initialize result object
        result = AnalysisResult(
            repository_url=repo_url,
            repository_name=repo_name,
            default_branch="main",  # Could be detected from git integration
            analysis_timestamp=datetime.now(),
            prs=prs,
            repository_stats=repository_stats
        )
        
        if not prs:
            # Handle no PRs scenario
            print(f"\\nNO OPEN PULL REQUESTS FOUND IN {repo_name.upper()} REPOSITORY")
            print("=" * 60)
            await self._handle_no_prs_scenario(result)
        else:
            # Analyze PRs
            print(f"\\nFOUND {len(prs)} OPEN PRS FROM {repo_name.upper()} REPOSITORY")
            await self._analyze_repository_prs(result)
        
        return result
    
    async def _fetch_repository_data(self, repo_url: str) -> tuple:
        """Fetch repository data including PRs and metadata"""
        try:
            # Import git integration functions
            from ..integration.git_integration import fetch_recent_prs, get_git_manager
            
            # Fetch PRs using existing function
            prs_list = await fetch_recent_prs(
                repo_url,
                state=self.config.get('pr_state', 'open'),
                limit=self.config.get('pr_limit', 10)
            )
            
            # Convert to expected format
            pr_data = {
                'prs': prs_list,
                'repository_stats': {}
            }
            
            # Convert to PRData objects
            prs = []
            if pr_data and 'prs' in pr_data:
                for pr in pr_data['prs']:
                    # Handle files_changed which might be a list or int
                    files_changed_raw = pr.get('changed_files', 0)
                    if isinstance(files_changed_raw, list):
                        files_changed = len(files_changed_raw)
                    elif isinstance(files_changed_raw, (int, float)):
                        files_changed = int(files_changed_raw)
                    else:
                        files_changed = 0
                    
                    # Handle additions/deletions safely
                    additions = pr.get('additions', 0)
                    deletions = pr.get('deletions', 0)
                    
                    if not isinstance(additions, (int, float)):
                        additions = 0
                    if not isinstance(deletions, (int, float)):
                        deletions = 0
                    
                    prs.append(PRData(
                        number=pr.get('number', 0),
                        title=pr.get('title', 'N/A'),
                        state=pr.get('state', 'unknown'),
                        author=pr.get('user', {}).get('login', 'Unknown'),
                        created_at=pr.get('created_at', ''),
                        updated_at=pr.get('updated_at', ''),
                        base_branch=pr.get('base', {}).get('ref', 'N/A'),
                        head_branch=pr.get('head', {}).get('ref', 'N/A'),
                        files_changed=files_changed,
                        additions=int(additions),
                        deletions=int(deletions),
                        url=pr.get('html_url', 'N/A'),
                        description=pr.get('body'),
                        comments=pr.get('comments', []),
                        files=pr.get('files', [])
                    ))
            
            # Get repository statistics (if available)
            repository_stats = RepositoryMetrics()
            if pr_data and 'repository_stats' in pr_data:
                stats = pr_data['repository_stats']
                repository_stats.total_files = stats.get('total_files', 0)
                repository_stats.total_lines = stats.get('total_lines', 0)
                repository_stats.file_types = stats.get('file_types', [])
                repository_stats.languages = stats.get('languages', [])
            
            return prs, repository_stats
            
        except Exception as e:
            self.logger.error(f"Failed to fetch repository data: {e}")
            return [], RepositoryMetrics()
    
    async def _analyze_repository_prs(self, result: AnalysisResult) -> None:
        """Analyze all PRs in a repository"""
        print("Analyzing each PR with comprehensive LLM evaluation...")
        
        pr_results = []
        
        # Analyze each PR
        for i, pr in enumerate(result.prs, 1):
            try:

                # Convert PRData back to dict for analysis
                pr_dict = {
                    'number': pr.number,
                    'title': pr.title,
                    'state': pr.state,
                    'user': {'login': pr.author},
                    'created_at': pr.created_at,
                    'updated_at': pr.updated_at,
                    'base': {
                        'ref': pr.base_branch,
                        'repo': {
                            'html_url': result.repository_url,
                            'clone_url': result.repository_url
                        }
                    },
                    'head': {'ref': pr.head_branch},
                    'changed_files': pr.files_changed,  # Now guaranteed to be int
                    'additions': pr.additions,  # Now guaranteed to be int
                    'deletions': pr.deletions,  # Now guaranteed to be int
                    'html_url': pr.url,
                    'body': pr.description,
                    'comments': pr.comments,
                    'files': pr.files,
                    'repository_url': result.repository_url  # Add repository URL for easy access
                }
                
                # Execute code review
                print("\\nEXECUTING CODE REVIEW AGENTS...")
                print("-" * 60)
                code_review_results = await self.code_review_orchestrator.execute_code_review(
                    pr_dict, f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Store code review results
                result.code_review_results.extend(code_review_results.values())
                
                # Analyze with plugins
                pr_analysis = await self.pr_analyzer.analyze_pr(
                    pr_dict, result.repository_url, i, len(result.prs)
                )
                pr_results.append(pr_analysis)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze PR #{pr.number}: {e}")
        
        # Generate overall assessment
        await self._generate_overall_assessment(result, pr_results)
    
    async def _handle_no_prs_scenario(self, result: AnalysisResult) -> None:
        """Handle repositories with no PRs by doing full code review"""
        print("Repository Analysis Summary:")
        print(f"   Repository: {result.repository_url}")
        print(f"   PR State Filter: {self.config.get('pr_state', 'open').upper()}")
        print("   Total PRs Found: 0")
        
        # Suggest performing full repository code review
        print("\\nRECOMMENDATIONS:")
        print("  - Consider switching to full repository analysis mode")
        print("  - Check if repository has PRs in different states")
        print("  - Verify repository access permissions")
        
        # Generate AI summary for no-PR scenario
        try:
            from ..integration.llm_client import get_llm_response
            
            prompt = f"""
Analyze a repository with no pull requests found.

Repository: {result.repository_url}
Analysis mode: {self.config.get('pr_state', 'open')} PRs

Provide recommendations for:
1. Alternative analysis approaches
2. Possible reasons for no PRs
3. Next steps for comprehensive code review
"""
            
            response = get_llm_response(prompt)
            ai_summary = response.get('response', 'No summary available') if isinstance(response, dict) else str(response)
            result.ai_summary = ai_summary
            
            print("\\nGENERATE LLM-POWERED SUMMARY FOR NO-PR SCENARIO")
            print("=" * 60)
            print("  LLM is analyzing the no-PR scenario...")
            print("\\n  AI-Generated Summary:")
            print("-" * 40)
            print(f"  {ai_summary}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI summary: {e}")
    
    async def _generate_overall_assessment(self, result: AnalysisResult, pr_results: List[Dict[str, Any]]) -> None:
        """Generate overall repository assessment"""
        print("\\n OVERALL REPOSITORY ASSESSMENT")
        print("=" * 80)
        print(f" Repository: {result.repository_name}")
        print(f" Total PRs Analyzed: {len(result.prs)}")
        
        # Aggregate assessments
        assessment_metrics = self.risk_assessor.aggregate_pr_assessments(pr_results)
        
        print("\\n" + format_repository_metrics(
            assessment_metrics['approved'],
            assessment_metrics['conditional'], 
            assessment_metrics['rejected'],
            assessment_metrics['low_risk'],
            assessment_metrics['medium_risk'],
            assessment_metrics['high_risk'],
            assessment_metrics['avg_confidence'],
            assessment_metrics['avg_score']
        ))
        
        # Calculate issue totals from code review results
        total_issues = sum(cr.issues_found for cr in result.code_review_results)
        critical_issues = sum(cr.critical_issues for cr in result.code_review_results)
        major_issues = sum(cr.major_issues for cr in result.code_review_results) 
        minor_issues = sum(cr.minor_issues for cr in result.code_review_results)
        
        # Update result with totals
        result.total_issues = total_issues
        result.critical_issues = critical_issues
        result.major_issues = major_issues
        result.minor_issues = minor_issues
        
        # Determine quality classification and risk level
        result.quality_classification = self.risk_assessor.assess_repository_quality(
            total_issues, critical_issues, major_issues, minor_issues
        )
        result.risk_level = self.risk_assessor.determine_repository_risk_level(
            critical_issues, major_issues, total_issues
        )
        
        # Generate AI summary
        await self._generate_ai_repository_summary(result, pr_results, assessment_metrics)
    
    async def _generate_ai_repository_summary(self, result: AnalysisResult, 
                                            pr_results: List[Dict[str, Any]],
                                            metrics: Dict[str, Any]) -> None:
        """Generate AI-powered repository summary"""
        try:
            print(f"\\n Generating comprehensive LLM summary for repository {result.repository_name}...")
            
            from ..integration.llm_client import get_llm_response
            
            prompt = f"""
Generate an executive summary for repository analysis:

Repository: {result.repository_name}
Total PRs: {len(result.prs)}
Approved: {metrics['approved']}
Conditional: {metrics['conditional']}
Rejected: {metrics['rejected']}
Average Confidence: {metrics['avg_confidence']:.1f}%
Average Score: {metrics['avg_score']:.1f}/100

Risk Distribution:
- Low: {metrics['low_risk']} PRs
- Medium: {metrics['medium_risk']} PRs  
- High: {metrics['high_risk']} PRs

Provide a professional assessment covering:
1. Overall repository health
2. Release readiness  
3. Key risks
4. Data-driven recommendations
5. Next steps

Focus on actionable insights for technical leadership.
"""
            
            response = get_llm_response(prompt)
            ai_summary = response.get('response', 'Summary generation failed') if isinstance(response, dict) else str(response)
            result.ai_summary = ai_summary
            
            print("\\n EXECUTIVE REPOSITORY ASSESSMENT")
            print("=" * 60)
            print(f" Generated by: AI Agent (LLM)")
            print(f" Repository: {result.repository_name}")
            print(f"\\n   {ai_summary}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate repository summary: {e}")
            result.ai_summary = "AI summary generation failed due to technical issues."