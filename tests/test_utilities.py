"""
Unit Tests for Utilities

Tests for utility functions and data structures.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utilities.data_structures import (
    RiskLevel, QualityClassification, PRData, RepositoryMetrics,
    CodeReviewResult, AnalysisResult
)
from src.utilities.config_utils import setup_logging, validate_environment
from src.utilities.formatting_utils import format_repository_metrics

class TestDataStructures(unittest.TestCase):
    """Test cases for data structures"""
    
    def test_risk_level_enum(self):
        """Test RiskLevel enum values"""

        self.assertEqual(RiskLevel.LOW.value, "LOW")
        self.assertEqual(RiskLevel.MEDIUM.value, "MEDIUM")
        self.assertEqual(RiskLevel.HIGH.value, "HIGH")
        self.assertEqual(RiskLevel.CRITICAL.value, "critical")
    
    def test_quality_classification_enum(self):
        """Test QualityClassification enum values"""
        self.assertEqual(QualityClassification.EXCELLENT.value, "excellent")
        self.assertEqual(QualityClassification.GOOD.value, "good")
        self.assertEqual(QualityClassification.ACCEPTABLE.value, "acceptable")
        self.assertEqual(QualityClassification.NEEDS_IMPROVEMENT.value, "needs_improvement")
        self.assertEqual(QualityClassification.POOR.value, "poor")
    
    def test_pr_data_creation(self):
        """Test PRData dataclass creation"""
        pr_data = PRData(
            number=123,
            title="Test PR",
            state="open",
            author="testuser",
            created_at="2024-01-01",
            updated_at="2024-01-02",
            files=[],
            additions=10,
            deletions=5,
            comments=[]
        )
        
        self.assertEqual(pr_data.number, 123)
        self.assertEqual(pr_data.title, "Test PR")
        self.assertEqual(pr_data.state, "open")
        self.assertEqual(pr_data.additions, 10)
    
    def test_repository_metrics_creation(self):
        """Test RepositoryMetrics dataclass creation"""
        metrics = RepositoryMetrics(
            total_files=100,
            total_lines=5000,
            programming_languages={'Python': 60, 'JavaScript': 40},
            largest_files=[],
            complexity_metrics={}
        )
        
        self.assertEqual(metrics.total_files, 100)
        self.assertEqual(metrics.total_lines, 5000)
        self.assertIn('Python', metrics.programming_languages)
    
    def test_code_review_result_creation(self):
        """Test CodeReviewResult creation"""
        result = CodeReviewResult(
            agent_name="python_agent",
            issues_found=5,
            critical_issues=1,
            warnings=4,
            recommendations=["Fix issue 1", "Improve code 2"]
        )
        
        self.assertEqual(result.agent_name, "python_agent")
        self.assertEqual(result.issues_found, 5)
        self.assertEqual(len(result.recommendations), 2)
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation"""
        result = AnalysisResult(
            repository_url="https://github.com/user/repo.git",
            classification=QualityClassification.GOOD,
            risk_level=RiskLevel.LOW,
            pr_analysis=None,
            code_review_results={},
            risk_assessment=None,
            recommendations=[]
        )
        
        self.assertEqual(result.repository_url, "https://github.com/user/repo.git")
        self.assertEqual(result.classification, QualityClassification.GOOD)
        self.assertEqual(result.risk_level, RiskLevel.LOW)

class TestConfigUtils(unittest.TestCase):
    """Test cases for configuration utilities"""
    
    def test_setup_logging_info_level(self):
        """Test logging setup with INFO level"""
        try:
            setup_logging("INFO")
            # If no exception, test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"setup_logging raised exception: {e}")
    
    def test_setup_logging_debug_level(self):
        """Test logging setup with DEBUG level"""
        try:
            setup_logging("DEBUG")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"setup_logging raised exception: {e}")
    
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level"""
        with self.assertRaises(ValueError):
            setup_logging("INVALID")

class TestFormattingUtils(unittest.TestCase):
    """Test cases for formatting utilities"""
    
    def test_format_repository_metrics_basic(self):
        """Test basic repository metrics formatting"""
        metrics = RepositoryMetrics(
            total_files=50,
            total_lines=2500,
            programming_languages={'Python': 70, 'JavaScript': 30},
            largest_files=[],
            complexity_metrics={}
        )
        
        formatted = format_repository_metrics(metrics)
        
        self.assertIsInstance(formatted, str)
        self.assertIn('50', formatted)  # total files
        self.assertIn('2500', formatted)  # total lines
    
    def test_format_repository_metrics_with_languages(self):
        """Test repository metrics formatting with language breakdown"""
        metrics = RepositoryMetrics(
            total_files=100,
            total_lines=10000,
            programming_languages={
                'Python': 50,
                'JavaScript': 30,
                'Java': 20
            },
            largest_files=[],
            complexity_metrics={}
        )
        
        formatted = format_repository_metrics(metrics)
        
        self.assertIn('Python', formatted)
        self.assertIn('JavaScript', formatted)
        self.assertIn('Java', formatted)
    
    def test_format_repository_metrics_empty(self):
        """Test formatting empty repository metrics"""
        metrics = RepositoryMetrics(
            total_files=0,
            total_lines=0,
            programming_languages={},
            largest_files=[],
            complexity_metrics={}
        )
        
        formatted = format_repository_metrics(metrics)
        
        self.assertIsInstance(formatted, str)
        self.assertIn('0', formatted)

class TestDataStructureEdgeCases(unittest.TestCase):
    """Test edge cases for data structures"""
    
    def test_pr_data_with_minimal_fields(self):
        """Test PRData with only required fields"""
        pr_data = PRData(
            number=1,
            title="Minimal PR",
            state="open",
            author="user",
            created_at="2024-01-01",
            updated_at="2024-01-01",
            files=[],
            additions=0,
            deletions=0,
            comments=[]
        )
        
        self.assertEqual(pr_data.number, 1)
        self.assertEqual(pr_data.additions, 0)
    
    def test_analysis_result_with_no_recommendations(self):
        """Test AnalysisResult with empty recommendations"""
        result = AnalysisResult(
            repository_url="https://github.com/test/repo.git",
            classification=QualityClassification.EXCELLENT,
            risk_level=RiskLevel.LOW,
            pr_analysis=None,
            code_review_results={},
            risk_assessment=None,
            recommendations=[]
        )
        
        self.assertEqual(len(result.recommendations), 0)
        self.assertEqual(result.classification, QualityClassification.EXCELLENT)
    
    def test_code_review_result_no_issues(self):
        """Test CodeReviewResult with no issues"""
        result = CodeReviewResult(
            agent_name="test_agent",
            issues_found=0,
            critical_issues=0,
            warnings=0,
            recommendations=[]
        )
        
        self.assertEqual(result.issues_found, 0)
        self.assertEqual(result.critical_issues, 0)
        self.assertEqual(len(result.recommendations), 0)

if __name__ == '__main__':
    unittest.main()
