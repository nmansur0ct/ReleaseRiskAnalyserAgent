"""
Risk Agent Analyzer - Professional Grade Repository Analysis Framework

A comprehensive, modular framework for analyzing code repositories with:
- Multi-repository analysis capabilities
- AI-powered code review and risk assessment  
- Comprehensive reporting with detailed sections
- Professional-grade architecture with separated concerns

Main Components:
- analysis/: Core analysis functionality (code review, PR analysis, risk assessment)
- reporting/: Comprehensive report generation and formatting
- orchestration/: Workflow management and coordination
- utilities/: Common utilities and data structures

Usage:
    # Import from root level, not from src package
    from risk_analyzer import RiskAgentAnalyzer
    
    analyzer = RiskAgentAnalyzer()
    await analyzer.analyze_repositories(repo_urls, config)
"""

__version__ = "2.0.0"
__author__ = "Risk Agent Analyzer Team"
__description__ = "Professional-grade multi-repository analysis framework"

# Note: Main entry point is at root level (risk_analyzer.py)
# Import utilities and data structures for package access
from .utilities.config_utils import load_configuration, setup_logging, validate_environment
from .utilities.data_structures import (
    AnalysisResult, 
    PRData, 
    CodeReviewResult,
    RepositoryMetrics,
    RiskLevel,
    QualityClassification
)

# Main exports (excluding RiskAgentAnalyzer which is at root level)
__all__ = [
    'load_configuration',
    'setup_logging', 
    'validate_environment',
    'AnalysisResult',
    'PRData',
    'CodeReviewResult',
    'RepositoryMetrics', 
    'RiskLevel',
    'QualityClassification'
]