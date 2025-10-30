"""
Basic tests for the Release Risk Analyzer.

These tests verify the core functionality of the three agents
and the overall orchestration logic.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models import PRInput
from src.orchestrator import ReleaseRiskAnalyzer

class TestReleaseRiskAnalyzer:
    """Test the main analyzer orchestration."""
    
    def test_basic_analysis(self):
        """Test basic analysis flow with simple PR."""
        analyzer = ReleaseRiskAnalyzer()
        
        pr_input = PRInput(
            title="Simple bug fix",
            body="Fix null pointer exception in user service",
            files=["src/user_service.py", "tests/test_user_service.py"]
        )
        
        result = analyzer.analyze(pr_input)
        
        # Should have all required components
        assert result.summary is not None
        assert result.validator_output is not None
        assert result.decision is not None
        
        # Should be low risk with tests included
        assert result.decision.risk_score < 70
        assert result.decision.go is True
    
    def test_secret_detection_auto_block(self):
        """Test that secret exposure triggers auto No-Go."""
        analyzer = ReleaseRiskAnalyzer()
        
        pr_input = PRInput(
            title="Update API key",
            body="New API key: AKIAEXAMPLEKEY123456",
            files=["config/api.py"]
        )
        
        result = analyzer.analyze(pr_input)
        
        # Should be auto No-Go with max risk
        assert result.decision.go is False
        assert result.decision.risk_score == 100
        assert "secret" in result.decision.rationale.lower()
    
    def test_missing_tests_in_risky_modules(self):
        """Test penalty for missing tests in risky modules.""" 
        analyzer = ReleaseRiskAnalyzer()
        
        pr_input = PRInput(
            title="Update payment processing",
            body="Refactor payment validation logic",
            files=["payments/validator.py", "gateway/router.py"]
        )
        
        result = analyzer.analyze(pr_input)
        
        # Should have high risk due to missing tests + risky modules
        assert result.decision.risk_score >= 60  # Base 50 + conditional bump
        assert result.validator_output.findings.missing_tests is True
        assert len(result.validator_output.findings.risky_modules) > 0
    
    def test_db_migration_without_docs(self):
        """Test penalty for DB migration without documentation."""
        analyzer = ReleaseRiskAnalyzer()
        
        pr_input = PRInput(
            title="Add user index migration", 
            body="Adds index on user_id column for performance",
            files=["migrations/add_user_index.sql", "models/user.py"]
        )
        
        result = analyzer.analyze(pr_input)
        
        # Should detect DB migration
        assert result.validator_output.findings.db_migration_detected is True
        # Should not have docs updated  
        assert result.validator_output.findings.docs_updated is False
        # Should have additional penalty
        assert result.decision.risk_score > result.validator_output.base_risk

if __name__ == "__main__":
    pytest.main([__file__])