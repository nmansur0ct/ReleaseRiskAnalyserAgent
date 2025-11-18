"""
Data structures for Risk Agent Analyzer

Defines common data classes and types used throughout the application.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"

class QualityClassification(Enum):
    """Quality classification enumeration"""
    GOOD = "GOOD"
    OK = "OK"
    BAD = "BAD"

@dataclass
class PRData:
    """Pull request data structure"""
    number: int
    title: str
    state: str
    author: str
    created_at: str
    updated_at: str
    base_branch: str
    head_branch: str
    files_changed: int
    additions: int
    deletions: int
    url: str
    description: Optional[str] = None
    comments: List[Dict[str, Any]] = field(default_factory=list)
    files: List[Dict[str, Any]] = field(default_factory=list)

@dataclass 
class RepositoryMetrics:
    """Repository metrics data structure"""
    total_files: int = 0
    total_lines: int = 0
    file_types: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    branches: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class CodeReviewResult:
    """Code review analysis result"""
    agent_name: str
    files_analyzed: int
    issues_found: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    response: str
    execution_time: float = 0.0
    error: Optional[str] = None

@dataclass
class AnalysisResult:
    """Complete analysis result for a repository"""
    repository_url: str
    repository_name: str
    default_branch: str
    analysis_timestamp: datetime
    prs: List[PRData] = field(default_factory=list)
    repository_stats: Optional[RepositoryMetrics] = None
    code_review_results: List[CodeReviewResult] = field(default_factory=list)
    total_issues: int = 0
    critical_issues: int = 0
    major_issues: int = 0
    minor_issues: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    quality_classification: QualityClassification = QualityClassification.GOOD
    ai_summary: Optional[str] = None
    
    
@dataclass
class PluginResult:
    """Plugin execution result"""
    plugin_name: str
    execution_time: float
    response: str
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    risk_level: Optional[str] = None
    score: Optional[int] = None
    error: Optional[str] = None