"""
Enhanced Pydantic models for LangGraph-based Risk Analyzer.

This module extends the basic models with additional fields for sophisticated
agent orchestration, confidence tracking, and workflow state management.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Union, Any
from datetime import datetime
from enum import Enum
import uuid

class AnalysisMode(str, Enum):
    """Analysis execution modes."""
    HEURISTIC = "heuristic"
    LLM = "llm"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"

class ConfidenceLevel(str, Enum):
    """Confidence levels for analysis results."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class AgentStatus(str, Enum):
    """Status of individual agents in the workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowStage(str, Enum):
    """Stages of the analysis workflow."""
    INPUT_VALIDATION = "input_validation"
    CHANGE_ANALYSIS = "change_analysis"
    POLICY_EVALUATION = "policy_evaluation"
    RISK_ASSESSMENT = "risk_assessment"
    DECISION_ENGINE = "decision_engine"
    QUALITY_ASSURANCE = "quality_assurance"
    COMPLETED = "completed"
    FAILED = "failed"

class PRInput(BaseModel):
    """Enhanced PR input with metadata and validation."""
    title: str = Field(..., description="PR title", min_length=1, max_length=200)
    body: str = Field(..., description="PR description")
    files: List[str] = Field(default_factory=list, description="Modified files")
    
    # Enhanced metadata
    author: Optional[str] = Field(None, description="PR author")
    branch: Optional[str] = Field(None, description="Source branch")
    target_branch: Optional[str] = Field("main", description="Target branch")
    labels: List[str] = Field(default_factory=list, description="PR labels")
    reviewers: List[str] = Field(default_factory=list, description="Assigned reviewers")
    timestamp: datetime = Field(default_factory=datetime.now, description="PR creation time")
    
    # File analysis
    file_changes: Dict[str, int] = Field(default_factory=dict, description="Lines changed per file")
    file_types: List[str] = Field(default_factory=list, description="File extensions involved")
    
    @validator('files')
    def validate_files(cls, v):
        """Ensure file paths are reasonable."""
        for file_path in v:
            if len(file_path) > 500:
                raise ValueError(f"File path too long: {file_path[:50]}...")
        return v

class AgentExecution(BaseModel):
    """Tracks individual agent execution details."""
    agent_name: str = Field(..., description="Name of the agent")
    status: AgentStatus = Field(AgentStatus.PENDING, description="Agent execution status")
    start_time: Optional[datetime] = Field(None, description="Agent start time")
    end_time: Optional[datetime] = Field(None, description="Agent completion time")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    confidence: float = Field(0.0, ge=0, le=1, description="Agent confidence in results")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific metadata")
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate execution duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class ChangePattern(BaseModel):
    """Detected change patterns with confidence metrics."""
    pattern_type: str = Field(..., description="Type of change pattern")
    confidence: float = Field(..., ge=0, le=1, description="Pattern detection confidence")
    evidence: List[str] = Field(..., description="Evidence supporting pattern")
    risk_weight: float = Field(..., ge=0, description="Risk weight for this pattern")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested mitigations")

class EnhancedSummary(BaseModel):
    """Enhanced change summary with detailed analysis."""
    highlights: List[str] = Field(..., description="Key change highlights")
    modules_touched: List[str] = Field(..., description="Affected modules")
    risk_notes: List[str] = Field(..., description="Risk indicators")
    change_size: Literal["small", "medium", "large"] = Field(..., description="Change size")
    
    # Enhanced analysis
    change_patterns: List[ChangePattern] = Field(default_factory=list, description="Detected patterns")
    dependencies_affected: List[str] = Field(default_factory=list, description="Affected dependencies")
    business_impact: Literal["low", "medium", "high"] = Field("low", description="Business impact level")
    technical_complexity: Literal["low", "medium", "high"] = Field("low", description="Technical complexity")
    confidence_score: float = Field(..., ge=0, le=1, description="Analysis confidence")
    
    # Agent metadata
    agent_execution: AgentExecution = Field(..., description="Agent execution details")

class PolicyViolation(BaseModel):
    """Detailed policy violation with remediation guidance."""
    policy_name: str = Field(..., description="Name of violated policy")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Violation severity")
    description: str = Field(..., description="Violation description")
    evidence: List[str] = Field(..., description="Evidence of violation")
    remediation: str = Field(..., description="Suggested remediation")
    auto_fixable: bool = Field(False, description="Can be automatically fixed")
    impact_assessment: str = Field(..., description="Impact if not addressed")
    compliance_frameworks: List[str] = Field(default_factory=list, description="Affected compliance frameworks")

class RiskComponent(BaseModel):
    """Individual risk component with detailed breakdown."""
    component_name: str = Field(..., description="Risk component name")
    base_score: int = Field(..., ge=0, le=100, description="Base risk score")
    adjusted_score: int = Field(..., ge=0, le=100, description="Adjusted risk score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in score")
    factors: List[str] = Field(..., description="Contributing factors")
    mitigation_suggestions: List[str] = Field(default_factory=list, description="Mitigation suggestions")
    weight: float = Field(1.0, ge=0, description="Component weight in final score")
    
    @validator('adjusted_score')
    def validate_adjusted_score(cls, v, values):
        """Ensure adjusted score is reasonable relative to base score."""
        base_score = values.get('base_score', 0)
        if v > base_score * 2:
            raise ValueError("Adjusted score cannot be more than double the base score")
        return v

class EnhancedPolicyFindings(BaseModel):
    """Enhanced policy findings with detailed violation tracking."""
    violations: List[PolicyViolation] = Field(default_factory=list, description="Detailed violations")
    compliance_score: float = Field(1.0, ge=0, le=1, description="Overall compliance score")
    
    # Risk components
    risk_components: List[RiskComponent] = Field(default_factory=list, description="Risk component breakdown")
    
    # Traditional boolean flags (for backward compatibility)
    missing_tests: bool = Field(False, description="Tests missing for code changes")
    secret_like: bool = Field(False, description="Potential secret exposure detected")
    risky_modules: List[str] = Field(default_factory=list, description="Risky modules touched")
    db_migration_detected: bool = Field(False, description="Database migration detected")
    unapproved_modules: List[str] = Field(default_factory=list, description="Unapproved modules used")
    docs_updated: bool = Field(False, description="Documentation updated")
    change_size: Literal["small", "medium", "large"] = Field("small", description="Change size category")
    
    # Agent metadata
    agent_execution: AgentExecution = Field(..., description="Agent execution details")
    
    @property
    def critical_violations(self) -> List[PolicyViolation]:
        """Get only critical violations."""
        return [v for v in self.violations if v.severity == "critical"]
    
    @property
    def total_risk_score(self) -> int:
        """Calculate total risk score from components."""
        return int(min(sum(comp.adjusted_score * comp.weight for comp in self.risk_components), 100))

class DecisionContext(BaseModel):
    """Context information for decision making with stakeholder considerations."""
    decision_factors: List[str] = Field(..., description="Key decision factors")
    alternative_paths: List[str] = Field(default_factory=list, description="Alternative actions")
    stakeholder_impact: Dict[str, str] = Field(default_factory=dict, description="Impact on stakeholders")
    rollback_plan: Optional[str] = Field(None, description="Rollback strategy")
    monitoring_requirements: List[str] = Field(default_factory=list, description="Required monitoring")
    communication_plan: List[str] = Field(default_factory=list, description="Communication requirements")

class EnhancedDecision(BaseModel):
    """Enhanced decision with comprehensive context and explainability."""
    go: bool = Field(..., description="Go/No-Go decision")
    risk_score: int = Field(..., ge=0, le=100, description="Final risk score")
    confidence: float = Field(..., ge=0, le=1, description="Decision confidence")
    rationale: str = Field(..., description="Primary decision rationale")
    detailed_reasoning: List[str] = Field(..., description="Detailed reasoning steps")
    
    # Enhanced decision context
    context: DecisionContext = Field(..., description="Decision context")
    risk_tolerance: Literal["low", "medium", "high"] = Field("medium", description="Applied risk tolerance")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    conditions_for_approval: List[str] = Field(default_factory=list, description="Conditions for Go decision")
    
    # Agent metadata
    agent_execution: AgentExecution = Field(..., description="Agent execution details")
    
    @validator('risk_score')
    def validate_risk_score_consistency(cls, v, values):
        """Ensure risk score aligns with decision."""
        go_decision = values.get('go')
        confidence = values.get('confidence', 0.5)
        
        # High-confidence decisions should be consistent
        if confidence > 0.8:
            if go_decision and v >= 70:
                raise ValueError("High confidence Go decision with high risk score needs justification")
            if not go_decision and v < 50:
                raise ValueError("High confidence No-Go decision with low risk score seems inconsistent")
        
        return v

class WorkflowState(BaseModel):
    """Complete workflow state for LangGraph orchestration."""
    # Workflow metadata
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique workflow ID")
    current_stage: WorkflowStage = Field(WorkflowStage.INPUT_VALIDATION, description="Current workflow stage")
    analysis_mode: AnalysisMode = Field(AnalysisMode.HYBRID, description="Analysis mode")
    start_time: datetime = Field(default_factory=datetime.now, description="Workflow start time")
    
    # Input data
    pr_input: PRInput = Field(..., description="Original PR input")
    
    # Agent outputs (optional until populated)
    summary: Optional[EnhancedSummary] = Field(None, description="Change summary from summarizer")
    policy_findings: Optional[EnhancedPolicyFindings] = Field(None, description="Policy findings from validator")
    decision: Optional[EnhancedDecision] = Field(None, description="Final decision from decision agent")
    
    # Workflow control and monitoring
    agent_executions: Dict[str, AgentExecution] = Field(default_factory=dict, description="Agent execution tracking")
    overall_confidence: float = Field(0.0, ge=0, le=1, description="Overall workflow confidence")
    errors: List[str] = Field(default_factory=list, description="Workflow-level errors")
    warnings: List[str] = Field(default_factory=list, description="Workflow-level warnings")
    retry_count: int = Field(0, ge=0, description="Number of retries attempted")
    max_retries: int = Field(3, ge=0, description="Maximum allowed retries")
    
    # Parallel processing results
    concurrent_analyses: Dict[str, Any] = Field(default_factory=dict, description="Results from parallel processing")
    
    # Quality metrics
    quality_score: float = Field(0.0, ge=0, le=1, description="Overall quality score")
    completeness_score: float = Field(0.0, ge=0, le=1, description="Analysis completeness score")
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.current_stage in [WorkflowStage.COMPLETED, WorkflowStage.FAILED]
    
    @property
    def has_critical_errors(self) -> bool:
        """Check if there are critical errors."""
        return any("critical" in error.lower() for error in self.errors)
    
    @property
    def should_retry(self) -> bool:
        """Determine if workflow should be retried."""
        return (
            not self.is_completed and
            self.retry_count < self.max_retries and
            not self.has_critical_errors and
            self.overall_confidence < 0.5
        )
    
    def add_agent_execution(self, agent_name: str) -> AgentExecution:
        """Add and track a new agent execution."""
        execution = AgentExecution(
            agent_name=agent_name,
            status=AgentStatus.PENDING,
            start_time=datetime.now(),
            end_time=None,
            execution_time=None,
            confidence=0.0
        )
        self.agent_executions[agent_name] = execution
        return execution
    
    def complete_agent_execution(self, agent_name: str, status: AgentStatus, confidence: float = 0.0):
        """Mark an agent execution as completed."""
        if agent_name in self.agent_executions:
            execution = self.agent_executions[agent_name]
            execution.status = status
            execution.end_time = datetime.now()
            execution.confidence = confidence
            execution.execution_time = execution.duration

class FinalAnalysisResult(BaseModel):
    """Final comprehensive analysis result."""
    # Workflow metadata
    workflow_id: str = Field(..., description="Workflow identifier")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis completion time")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    analysis_mode: AnalysisMode = Field(..., description="Analysis mode used")
    
    # Core results
    summary: EnhancedSummary = Field(..., description="Change summary")
    policy_findings: EnhancedPolicyFindings = Field(..., description="Policy evaluation results")
    decision: EnhancedDecision = Field(..., description="Final decision")
    
    # Quality and confidence metrics
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall analysis confidence")
    quality_score: float = Field(..., ge=0, le=1, description="Analysis quality score")
    completeness_score: float = Field(..., ge=0, le=1, description="Analysis completeness")
    
    # Workflow execution details
    agent_executions: Dict[str, AgentExecution] = Field(..., description="Agent execution details")
    workflow_path: List[str] = Field(..., description="Executed workflow path")
    fallback_used: bool = Field(False, description="Whether fallback logic was used")
    
    # Diagnostics
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence analysis."""
        return self.overall_confidence >= 0.8
    
    @property
    def requires_human_review(self) -> bool:
        """Check if human review is recommended."""
        return (
            self.overall_confidence < 0.7 or
            self.decision.risk_score > 80 or
            any(v.severity == "critical" for v in self.policy_findings.violations) or
            self.fallback_used
        )
    
    @property
    def decision_summary(self) -> str:
        """Get a concise decision summary."""
        status = "GO" if self.decision.go else "NO-GO"
        confidence_level = "High" if self.is_high_confidence else "Medium" if self.overall_confidence >= 0.5 else "Low"
        return f"{status} (Risk: {self.decision.risk_score}/100, Confidence: {confidence_level})"