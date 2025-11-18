"""
Example Test with Enhanced Reporting

Demonstrates how to use test decorators for detailed reporting.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_config import TestConfig
from tests.test_decorators import test_scenario, test_case, integration_test, performance_test

@test_scenario(
    scenario_name="Code Review Report Generation",
    description="Tests the comprehensive reporter's ability to generate various report formats and sections",
    category="Unit Tests - Reporting"
)
class TestReportGenerationExample(unittest.TestCase):
    """Example test class with enhanced metadata for reporting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = {"repository": "test-repo", "prs": 5}
    
    @test_case(
        name="Generate Basic Report Header",
        description="Verify that the report header contains all required information including title, timestamp, and repository details",
        expected_result="Report header should be generated with COMPREHENSIVE CODE REVIEW title, current timestamp, and repository information formatted correctly"
    )
    def test_report_header_generation(self):
        """Test basic report header generation"""
        # This would contain actual test logic
        header = "COMPREHENSIVE CODE REVIEW"
        self.assertIn("COMPREHENSIVE CODE REVIEW", header)
    
    @test_case(
        name="Calculate Summary Statistics",
        description="Calculate aggregate statistics across multiple analysis results including total PRs, issues, and quality metrics",
        expected_result="Summary statistics should correctly aggregate: total_prs=8, total_issues=8, critical_issues=3, major_issues=5 from two analysis results"
    )
    def test_summary_statistics_calculation(self):
        """Test calculation of summary statistics"""
        # Mock data
        stats = {
            'total_prs': 8,
            'total_issues': 8,
            'critical_issues': 3,
            'major_issues': 5
        }
        
        self.assertEqual(stats['total_prs'], 8)
        self.assertEqual(stats['total_issues'], 8)
        self.assertEqual(stats['critical_issues'], 3)
    
    @test_case(
        name="Parse JSON Agent Response",
        description="Parse a valid JSON response from an agent containing issues array and quality score",
        expected_result="Response should be parsed into a dictionary with 'issues' key containing 1 issue and 'quality_score' of 75"
    )
    @performance_test(max_execution_time_ms=100)
    def test_json_response_parsing(self):
        """Test parsing JSON agent response with performance constraint"""
        import json
        response_text = '{"issues": [{"severity": "critical", "message": "Test issue"}], "quality_score": 75}'
        parsed = json.loads(response_text)
        
        self.assertIsInstance(parsed, dict)
        self.assertIn('issues', parsed)
        self.assertEqual(len(parsed['issues']), 1)
        self.assertEqual(parsed['quality_score'], 75)
    
    @test_case(
        name="Format Agent Findings Table",
        description="Format agent findings with multiple severity levels (critical and warning) into a readable table structure",
        expected_result="Table should contain formatted rows for each issue with severity, line number, message, and type. Should include both 'critical' and 'warning' issues from Python agent"
    )
    def test_agent_findings_formatting(self):
        """Test formatting of agent findings into table"""
        findings = {
            'python': {
                'issues': [
                    {'severity': 'critical', 'line': 10, 'message': 'Critical issue', 'type': 'security'},
                    {'severity': 'warning', 'line': 20, 'message': 'Warning issue', 'type': 'style'}
                ]
            }
        }
        
        # Simulate table formatting
        table = str(findings)
        self.assertIn('critical', table.lower())
        self.assertIn('warning', table.lower())
    
    @test_case(
        name="Handle Empty Findings",
        description="Handle edge case where no issues are found in the code review",
        expected_result="Table should display 'No issues found' message when findings dictionary is empty"
    )
    def test_empty_findings_handling(self):
        """Test handling of empty findings"""
        findings = {}
        
        if not findings:
            message = "No issues found"
            self.assertEqual(message, "No issues found")

@test_scenario(
    scenario_name="End-to-End Repository Analysis",
    description="Integration tests for complete repository analysis workflows",
    category="Integration Tests"
)
class TestRepositoryAnalysisExample(unittest.TestCase):
    """Example integration test class"""
    
    @test_case(
        name="Single Repository Analysis Workflow",
        description="Execute complete analysis workflow for a single repository including PR discovery, code review, risk assessment, and report generation",
        expected_result="Complete AnalysisResult object with: repository URL, repository name, risk level (LOW/MEDIUM/HIGH), quality classification (GOOD/OK/BAD), at least 1 PR analyzed, valid repository metrics"
    )
    @integration_test(dependencies=["Git API", "LLM Service"], requires_external_service=True)
    def test_single_repo_workflow(self):
        """Test complete single repository analysis"""
        # ::: Code Generated by Copilot [550e8400-e29b-41d4-a716-446655440008]. This comment will be removed automatically after the file is saved :::
        # Use actual repository URL from config
        repo_url = TestConfig.DEFAULT_REPO_URL
        
        # Mock result
        result = {
            'repository_url': repo_url,
            'prs_analyzed': 1,
            'risk_level': 'MEDIUM',
            'quality': 'OK'
        }
        
        self.assertEqual(result['prs_analyzed'], 1)
        self.assertIn(result['risk_level'], ['LOW', 'MEDIUM', 'HIGH'])
    
    @test_case(
        name="Multi-Language Code Review",
        description="Execute code review across multiple programming languages (Python, Java, JavaScript, React) in a single PR",
        expected_result="Code review results should contain entries for each detected language agent (python_agent, java_agent, nodejs_agent, reactjs_agent) with language-specific analysis points and quality scores"
    )
    @integration_test(dependencies=["LLM Service"], requires_external_service=False)
    def test_multi_language_review(self):
        """Test multi-language code review integration"""
        languages_detected = ['Python', 'Java', 'JavaScript', 'React']
        
        self.assertGreater(len(languages_detected), 0)
        self.assertIn('Python', languages_detected)

if __name__ == '__main__':
    # Run with enhanced reporting
    from tests.run_tests_with_reports import run_tests_with_detailed_reports
    
    run_tests_with_detailed_reports(
        test_pattern='test_example_with_metadata.py',
        output_dir='reports/examples',
        report_name='example_test_execution',
        verbose=True
    )
