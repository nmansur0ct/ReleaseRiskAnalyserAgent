"""
Unit Tests for Comprehensive Reporter

Tests for report generation and formatting.
"""

import unittest
import os
import tempfile
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.comprehensive_reporter import ComprehensiveReporter
from src.utilities.data_structures import AnalysisResult, QualityClassification, RiskLevel

class TestComprehensiveReporter(unittest.TestCase):
    """Test cases for ComprehensiveReporter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test reports
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            "output_dir": self.test_dir
        }
        self.reporter = ComprehensiveReporter(self.config)
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test reporter initialization"""
        self.assertIsNotNone(self.reporter)
        self.assertEqual(self.reporter.output_dir, self.test_dir)
    
    def test_add_header(self):
        """Test adding report header"""
        content = []
        self.reporter._add_header(content)
        
        self.assertGreater(len(content), 0)
        self.assertIn("COMPREHENSIVE CODE REVIEW", ' '.join(content))
    
    def test_calculate_summary_stats(self):
        """Test calculating summary statistics"""
        analysis_results = [
            Mock(
                classification=QualityClassification.HIGH_QUALITY,
                risk_level=RiskLevel.LOW,
                pr_analysis=Mock(total_prs=5),
                code_review_results={'python_agent': Mock(result={'issues_found': 3, 'critical_issues': 1, 'warnings': 2})}
            ),
            Mock(
                classification=QualityClassification.MEDIUM_QUALITY,
                risk_level=RiskLevel.MEDIUM,
                pr_analysis=Mock(total_prs=3),
                code_review_results={'java_agent': Mock(result={'issues_found': 5, 'critical_issues': 2, 'warnings': 3})}
            )
        ]
        
        stats = self.reporter._calculate_summary_stats(analysis_results)
        
        self.assertEqual(stats['total_prs'], 8)
        self.assertEqual(stats['total_issues'], 8)
        self.assertEqual(stats['critical_issues'], 3)
        self.assertEqual(stats['major_issues'], 5)
    
    def test_parse_agent_response_json(self):
        """Test parsing JSON agent response"""
        response_text = '{"issues": [{"severity": "critical", "message": "Test issue"}], "quality_score": 75}'
        
        parsed = self.reporter._parse_agent_response(response_text)
        
        self.assertIsInstance(parsed, dict)
        self.assertIn('issues', parsed)
        self.assertEqual(len(parsed['issues']), 1)
    
    def test_parse_agent_response_ast(self):
        """Test parsing Python literal agent response"""
        response_text = "{'issues': [{'severity': 'warning'}], 'quality_score': 80}"
        
        parsed = self.reporter._parse_agent_response(response_text)
        
        self.assertIsInstance(parsed, dict)
        self.assertIn('issues', parsed)
    
    def test_parse_agent_response_invalid(self):
        """Test parsing invalid agent response"""
        response_text = "not valid json or python literal"
        
        parsed = self.reporter._parse_agent_response(response_text)
        
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed, {})
    
    def test_format_agent_findings_table(self):
        """Test formatting agent findings as table"""
        findings = {
            'python': {
                'issues': [
                    {'severity': 'critical', 'line': 10, 'message': 'Critical issue', 'type': 'security'},
                    {'severity': 'warning', 'line': 20, 'message': 'Warning issue', 'type': 'style'}
                ]
            }
        }
        
        table = self.reporter._format_agent_findings_table(findings)
        
        self.assertIsInstance(table, str)
        self.assertIn('critical', table.lower())
        self.assertIn('warning', table.lower())
        self.assertIn('Critical issue', table)
    
    def test_format_agent_findings_table_empty(self):
        """Test formatting empty findings"""
        findings = {}
        
        table = self.reporter._format_agent_findings_table(findings)
        
        self.assertIn('No issues found', table)
    
    def test_generate_comprehensive_report_single_repo(self):
        """Test generating report for single repository"""
        analysis_result = Mock(
            classification=QualityClassification.HIGH_QUALITY,
            risk_level=RiskLevel.LOW,
            repository_url='https://github.com/user/repo.git',
            pr_analysis=Mock(total_prs=5, open_prs=2, closed_prs=3),
            code_review_results={
                'python_agent': Mock(result={
                    'issues_found': 2,
                    'critical_issues': 0,
                    'warnings': 2,
                    'file_reports': []
                })
            },
            risk_assessment=Mock(overall_risk=RiskLevel.LOW),
            recommendations=[]
        )
        
        async def run_test():
            report_path = await self.reporter.generate_comprehensive_report(
                [analysis_result],
                ['https://github.com/user/repo.git']
            )
            
            self.assertTrue(os.path.exists(report_path))
            self.assertTrue(report_path.endswith('.txt'))
            
            # Verify report content
            with open(report_path, 'r') as f:
                content = f.read()
                self.assertIn('COMPREHENSIVE CODE REVIEW', content)
                self.assertIn('repo.git', content)
        
        asyncio.run(run_test())
    
    def test_generate_comprehensive_report_multiple_repos(self):
        """Test generating report for multiple repositories"""
        analysis_results = [
            Mock(
                classification=QualityClassification.HIGH_QUALITY,
                risk_level=RiskLevel.LOW,
                repository_url='https://github.com/user/repo1.git',
                pr_analysis=Mock(total_prs=3),
                code_review_results={},
                risk_assessment=Mock(overall_risk=RiskLevel.LOW),
                recommendations=[]
            ),
            Mock(
                classification=QualityClassification.MEDIUM_QUALITY,
                risk_level=RiskLevel.MEDIUM,
                repository_url='https://github.com/user/repo2.git',
                pr_analysis=Mock(total_prs=5),
                code_review_results={},
                risk_assessment=Mock(overall_risk=RiskLevel.MEDIUM),
                recommendations=[]
            )
        ]
        
        async def run_test():
            report_path = await self.reporter.generate_comprehensive_report(
                analysis_results,
                ['https://github.com/user/repo1.git', 'https://github.com/user/repo2.git']
            )
            
            self.assertTrue(os.path.exists(report_path))
            self.assertIn('multi_repo', report_path)
            
            # Verify multiple repos in content
            with open(report_path, 'r') as f:
                content = f.read()
                self.assertIn('repo1', content)
                self.assertIn('repo2', content)
        
        asyncio.run(run_test())

class TestReportSections(unittest.TestCase):
    """Test individual report sections"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.config = {"output_dir": self.test_dir}
        self.reporter = ComprehensiveReporter(self.config)
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_add_metadata_section(self):
        """Test adding metadata section"""
        content = []
        analysis_results = [
            Mock(classification=QualityClassification.HIGH_QUALITY)
        ]
        
        self.reporter._add_metadata_section(content, analysis_results)
        
        self.assertGreater(len(content), 0)
        content_str = '\n'.join(content)
        self.assertIn('Generated', content_str)
    
    def test_add_repository_information_section(self):
        """Test adding repository information section"""
        content = []
        analysis_results = [
            Mock(
                repository_url='https://github.com/user/repo.git',
                repository_metrics=Mock(
                    total_files=100,
                    total_lines=5000,
                    programming_languages={'Python': 60, 'JavaScript': 40}
                )
            )
        ]
        repo_urls = ['https://github.com/user/repo.git']
        
        self.reporter._add_repository_information_section(content, analysis_results, repo_urls)
        
        self.assertGreater(len(content), 0)
        content_str = '\n'.join(content)
        self.assertIn('REPOSITORY INFORMATION', content_str)
    
    def test_add_pull_request_section(self):
        """Test adding pull request section"""
        content = []
        analysis_results = [
            Mock(
                pr_analysis=Mock(
                    total_prs=10,
                    open_prs=5,
                    closed_prs=5,
                    pr_summaries=[]
                )
            )
        ]
        
        self.reporter._add_pull_request_section(content, analysis_results)
        
        content_str = '\n'.join(content)
        self.assertIn('PULL REQUEST ANALYSIS', content_str)
    
    def test_add_code_review_section(self):
        """Test adding code review section"""
        content = []
        analysis_results = [
            Mock(
                code_review_results={
                    'python_agent': Mock(result={
                        'issues_found': 5,
                        'critical_issues': 1,
                        'file_reports': []
                    })
                }
            )
        ]
        
        self.reporter._add_code_review_section(content, analysis_results)
        
        content_str = '\n'.join(content)
        self.assertIn('CODE REVIEW', content_str)
    
    def test_add_quality_assessment_section(self):
        """Test adding quality assessment section"""
        content = []
        analysis_results = [
            Mock(
                classification=QualityClassification.HIGH_QUALITY,
                risk_level=RiskLevel.LOW,
                risk_assessment=Mock(
                    overall_risk=RiskLevel.LOW,
                    risk_factors=[]
                ),
                recommendations=['Recommendation 1', 'Recommendation 2']
            )
        ]
        
        self.reporter._add_quality_assessment_section(content, analysis_results)
        
        content_str = '\n'.join(content)
        self.assertIn('QUALITY ASSESSMENT', content_str)
        self.assertIn('Recommendation 1', content_str)

if __name__ == '__main__':
    unittest.main()
