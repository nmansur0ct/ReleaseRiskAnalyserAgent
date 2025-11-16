"""
LangGraph Workflow Implementation for Release Risk Analyzer.

This module implements a sophisticated multi-agent workflow using LangGraph
for orchestrating the risk analysis process with conditional routing,
error handling, and parallel processing capabilities.
"""

from typing import Dict, Any, Literal
from datetime import datetime
import asyncio
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .enhanced_models import (
    WorkflowState, 
    WorkflowStage, 
    AgentStatus, 
    AnalysisMode,
    EnhancedSummary,
    EnhancedPolicyFindings, 
    EnhancedDecision,
    FinalAnalysisResult,
    AgentExecution
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all analysis agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the agent with error handling and timing."""
        execution = state.add_agent_execution(self.name)
        execution.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"Starting {self.name} agent")
            state = await self.process(state)
            
            execution.status = AgentStatus.COMPLETED
            execution.confidence = getattr(state, f"{self.name.lower()}_confidence", 0.8)
            
            self.logger.info(f"Completed {self.name} agent successfully")
            
        except Exception as e:
            execution.status = AgentStatus.FAILED
            execution.errors.append(str(e))
            state.errors.append(f"{self.name} failed: {str(e)}")
            
            self.logger.error(f"{self.name} agent failed: {str(e)}")
            
        finally:
            state.complete_agent_execution(self.name, execution.status, execution.confidence)
        
        return state
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Override this method in concrete agents."""
        raise NotImplementedError

class InputValidationAgent(BaseAgent):
    """Validates and enriches PR input data."""
    
    def __init__(self):
        super().__init__("InputValidation")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Validate and enrich PR input."""
        # Basic validation
        if not state.pr_input.title.strip():
            raise ValueError("PR title cannot be empty")
        
        if len(state.pr_input.body) < 10:
            state.warnings.append("PR body is very short, analysis may be limited")
        
        # Enrich file metadata
        if state.pr_input.files:
            file_types = set()
            for file_path in state.pr_input.files:
                if '.' in file_path:
                    ext = file_path.split('.')[-1].lower()
                    file_types.add(ext)
            
            state.pr_input.file_types = list(file_types)
        
        # Set analysis mode based on complexity
        complexity_score = self._assess_complexity(state.pr_input)
        if complexity_score > 0.8:
            state.analysis_mode = AnalysisMode.LLM
        elif complexity_score > 0.4:
            state.analysis_mode = AnalysisMode.HYBRID
        else:
            state.analysis_mode = AnalysisMode.HEURISTIC
        
        state.current_stage = WorkflowStage.CHANGE_ANALYSIS
        return state
    
    def _assess_complexity(self, pr_input) -> float:
        """Assess PR complexity to determine optimal analysis mode."""
        score = 0.0
        
        # File count factor
        file_count = len(pr_input.files)
        if file_count > 20:
            score += 0.4
        elif file_count > 5:
            score += 0.2
        
        # Body complexity
        body_length = len(pr_input.body)
        if body_length > 1000:
            score += 0.3
        elif body_length > 300:
            score += 0.15
        
        # Complex keywords
        complex_keywords = ["refactor", "rewrite", "migration", "security", "protocol"]
        body_lower = pr_input.body.lower()
        keyword_matches = sum(1 for keyword in complex_keywords if keyword in body_lower)
        score += min(keyword_matches * 0.1, 0.3)
        
        return min(score, 1.0)

class ChangeAnalysisAgent(BaseAgent):
    """Analyzes PR changes with configurable strategies."""
    
    def __init__(self):
        super().__init__("ChangeAnalysis")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Analyze changes based on analysis mode."""
        if state.analysis_mode == AnalysisMode.LLM:
            summary = await self._analyze_with_llm(state)
        elif state.analysis_mode == AnalysisMode.HYBRID:
            summary = await self._analyze_hybrid(state)
        else:
            summary = await self._analyze_heuristic(state)
        
        state.summary = summary
        state.current_stage = WorkflowStage.POLICY_EVALUATION
        return state
    
    async def _analyze_heuristic(self, state: WorkflowState) -> EnhancedSummary:
        """Heuristic-based change analysis."""
        pr_input = state.pr_input
        
        # Extract highlights
        highlights = [pr_input.title]
        if len(pr_input.body) > 50:
            # Simple sentence extraction
            sentences = [s.strip() for s in pr_input.body.split('.') if len(s.strip()) > 20]
            highlights.extend(sentences[:3])
        
        # Determine modules touched
        modules_touched = []
        for file_path in pr_input.files:
            if '/' in file_path:
                module = file_path.split('/')[0] + '/'
                if module not in modules_touched:
                    modules_touched.append(module)
        
        # Generate risk notes
        risk_notes = []
        body_lower = pr_input.body.lower()
        
        risky_keywords = {
            "auth": "authentication changes",
            "security": "security modifications",
            "database": "database changes",
            "migration": "migration detected",
            "api": "API modifications"
        }
        
        for keyword, note in risky_keywords.items():
            if keyword in body_lower:
                risk_notes.append(note)
        
        # Determine change size
        file_count = len(pr_input.files)
        if file_count < 3:
            change_size = "small"
        elif file_count < 10:
            change_size = "medium"
        else:
            change_size = "large"
        
        return EnhancedSummary(
            highlights=highlights[:5],
            modules_touched=modules_touched,
            risk_notes=risk_notes,
            change_size=change_size,
            confidence_score=0.7,
            business_impact="medium" if risk_notes else "low",
            technical_complexity="medium" if file_count > 5 else "low",
            agent_execution=AgentExecution(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                confidence=0.7
            )
        )
    
    async def _analyze_hybrid(self, state: WorkflowState) -> EnhancedSummary:
        """Hybrid analysis combining heuristics with enhanced processing."""
        # Start with heuristic analysis
        base_summary = await self._analyze_heuristic(state)
        
        # Enhance with additional pattern detection
        base_summary.change_patterns = self._detect_change_patterns(state.pr_input)
        base_summary.confidence_score = 0.85
        
        return base_summary
    
    async def _analyze_with_llm(self, state: WorkflowState) -> EnhancedSummary:
        """LLM-based analysis (placeholder for actual LLM integration)."""
        # For demonstration, use enhanced heuristic analysis
        # In real implementation, this would call OpenAI/Anthropic/etc.
        base_summary = await self._analyze_hybrid(state)
        base_summary.confidence_score = 0.95
        
        # Simulate LLM enhancements
        base_summary.highlights = [
            "Enhanced LLM-generated summary",
            *base_summary.highlights[:3]
        ]
        
        return base_summary
    
    def _detect_change_patterns(self, pr_input) -> list:
        """Detect specific change patterns."""
        patterns = []
        body_lower = pr_input.body.lower()
        
        pattern_indicators = {
            "refactoring": ["refactor", "cleanup", "reorganize"],
            "feature_addition": ["add", "implement", "introduce"],
            "bug_fix": ["fix", "resolve", "correct"],
            "security_update": ["security", "vulnerability", "patch"],
            "performance": ["optimize", "performance", "speed"]
        }
        
        for pattern_type, keywords in pattern_indicators.items():
            matches = sum(1 for keyword in keywords if keyword in body_lower)
            if matches > 0:
                from .enhanced_models import ChangePattern
                patterns.append(ChangePattern(
                    pattern_type=pattern_type,
                    confidence=min(matches * 0.3, 1.0),
                    evidence=[f"Keyword '{kw}' found" for kw in keywords if kw in body_lower],
                    risk_weight=0.1 if pattern_type == "bug_fix" else 0.3
                ))
        
        return patterns

class PolicyEvaluationAgent(BaseAgent):
    """Evaluates governance policies with parallel processing."""
    
    def __init__(self):
        super().__init__("PolicyEvaluation")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Evaluate policies using parallel processing."""
        # Run policy checks in parallel
        policy_tasks = [
            self._check_testing_policy(state),
            self._check_security_policy(state),
            self._check_documentation_policy(state),
            self._check_compliance_policy(state)
        ]
        
        policy_results = await asyncio.gather(*policy_tasks, return_exceptions=True)
        
        # Aggregate results
        findings = await self._aggregate_policy_results(state, policy_results)
        state.policy_findings = findings
        state.current_stage = WorkflowStage.RISK_ASSESSMENT
        
        return state
    
    async def _check_testing_policy(self, state: WorkflowState) -> Dict[str, Any]:
        """Check testing requirements."""
        pr_input = state.pr_input
        
        # Check for test files
        has_tests = any("test" in file.lower() for file in pr_input.files)
        has_source_changes = any(
            file.endswith(('.py', '.js', '.ts', '.java')) 
            for file in pr_input.files
        )
        
        missing_tests = has_source_changes and not has_tests
        
        return {
            "missing_tests": missing_tests,
            "test_coverage_adequate": has_tests,
            "violations": [] if not missing_tests else [{
                "policy_name": "testing_required",
                "severity": "high",
                "description": "Source code changes require corresponding tests"
            }]
        }
    
    async def _check_security_policy(self, state: WorkflowState) -> Dict[str, Any]:
        """Check security requirements."""
        pr_input = state.pr_input
        combined_text = f"{pr_input.title} {pr_input.body}".lower()
        
        # Check for potential secrets
        secret_patterns = [
            "api_key", "secret", "password", "token", "-----begin",
            "private_key", "akia"  # AWS access key pattern
        ]
        
        secret_detected = any(pattern in combined_text for pattern in secret_patterns)
        
        # Check for risky modules
        risky_modules = ["auth", "security", "payment", "gateway"]
        modules_touched = [
            file.split('/')[0] for file in pr_input.files if '/' in file
        ]
        risky_modules_touched = [
            module for module in modules_touched 
            if any(risky in module.lower() for risky in risky_modules)
        ]
        
        violations = []
        if secret_detected:
            violations.append({
                "policy_name": "no_secrets",
                "severity": "critical",
                "description": "Potential secret or credential detected in PR content"
            })
        
        return {
            "secret_like": secret_detected,
            "risky_modules": risky_modules_touched,
            "violations": violations
        }
    
    async def _check_documentation_policy(self, state: WorkflowState) -> Dict[str, Any]:
        """Check documentation requirements."""
        pr_input = state.pr_input
        
        # Check for documentation files
        has_docs = any(
            file.lower().endswith(('.md', '.rst', '.txt')) or 'doc' in file.lower()
            for file in pr_input.files
        )
        
        # Check for docs mention in body
        docs_mentioned = "doc" in pr_input.body.lower()
        docs_updated = has_docs or docs_mentioned
        
        # Determine if docs are required
        significant_change = len(pr_input.files) > 3 or any([
            "migration" in pr_input.body.lower(),
            "breaking" in pr_input.body.lower()
        ])
        
        docs_required = significant_change and not docs_updated
        
        violations = []
        if docs_required:
            violations.append({
                "policy_name": "documentation_required",
                "severity": "medium",
                "description": "Significant changes require documentation updates"
            })
        
        return {
            "docs_updated": docs_updated,
            "violations": violations
        }
    
    async def _check_compliance_policy(self, state: WorkflowState) -> Dict[str, Any]:
        """Check compliance requirements."""
        pr_input = state.pr_input
        
        # Check for unapproved modules
        unapproved_patterns = ["experimental", "vendor", "third_party"]
        unapproved_modules = [
            file for file in pr_input.files
            if any(pattern in file.lower() for pattern in unapproved_patterns)
        ]
        
        violations = []
        if unapproved_modules:
            violations.append({
                "policy_name": "approved_modules_only",
                "severity": "high",
                "description": "Usage of unapproved modules detected"
            })
        
        return {
            "unapproved_modules": unapproved_modules,
            "violations": violations
        }
    
    async def _aggregate_policy_results(
        self, 
        state: WorkflowState, 
        results: list
    ) -> EnhancedPolicyFindings:
        """Aggregate all policy check results."""
        from .enhanced_models import PolicyViolation, RiskComponent
        
        # Collect all violations
        all_violations = []
        for result in results:
            if isinstance(result, dict) and "violations" in result:
                for violation_dict in result["violations"]:
                    all_violations.append(PolicyViolation(
                        policy_name=violation_dict["policy_name"],
                        severity=violation_dict["severity"],
                        description=violation_dict["description"],
                        evidence=["Detected during policy evaluation"],
                        remediation=f"Address {violation_dict['policy_name']} violation",
                        auto_fixable=False,
                        impact_assessment="May block release if not addressed"
                    ))
        
        # Calculate compliance score
        total_checks = len(results)
        violations_count = len(all_violations)
        compliance_score = max(0, (total_checks - violations_count) / total_checks)
        
        # Extract specific findings for backward compatibility
        missing_tests = any(
            r.get("missing_tests", False) for r in results if isinstance(r, dict)
        )
        secret_like = any(
            r.get("secret_like", False) for r in results if isinstance(r, dict)
        )
        docs_updated = any(
            r.get("docs_updated", False) for r in results if isinstance(r, dict)
        )
        
        risky_modules = []
        unapproved_modules = []
        for result in results:
            if isinstance(result, dict):
                risky_modules.extend(result.get("risky_modules", []))
                unapproved_modules.extend(result.get("unapproved_modules", []))
        
        return EnhancedPolicyFindings(
            violations=all_violations,
            compliance_score=compliance_score,
            missing_tests=missing_tests,
            secret_like=secret_like,
            risky_modules=risky_modules,
            docs_updated=docs_updated,
            unapproved_modules=unapproved_modules,
            change_size=state.summary.change_size if state.summary else "small",
            agent_execution=AgentExecution(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                confidence=0.9
            )
        )

class RiskAssessmentAgent(BaseAgent):
    """Performs advanced risk calculation."""
    
    def __init__(self):
        super().__init__("RiskAssessment")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Calculate comprehensive risk assessment."""
        # Generate detailed risk components
        risk_components = self._calculate_risk_components(state)
        
        # Update policy findings with risk components
        if state.policy_findings:
            state.policy_findings.risk_components = risk_components
        
        state.current_stage = WorkflowStage.DECISION_ENGINE
        return state
    
    def _calculate_risk_components(self, state: WorkflowState) -> list:
        """Calculate detailed risk components."""
        from .enhanced_models import RiskComponent
        
        components = []
        findings = state.policy_findings
        
        if not findings:
            return components
        
        # Testing risk
        if findings.missing_tests:
            components.append(RiskComponent(
                component_name="missing_tests",
                base_score=30,
                adjusted_score=35 if findings.risky_modules else 30,
                confidence=0.9,
                factors=["No test files found", "Source code changes detected"],
                mitigation_suggestions=["Add comprehensive test coverage", "Include unit and integration tests"]
            ))
        
        # Security risk
        if findings.secret_like:
            components.append(RiskComponent(
                component_name="security",
                base_score=100,
                adjusted_score=100,
                confidence=0.95,
                factors=["Potential secret exposure detected"],
                mitigation_suggestions=["Remove secrets from code", "Use secure credential management"]
            ))
        
        # Module risk
        if findings.risky_modules:
            components.append(RiskComponent(
                component_name="risky_modules",
                base_score=20,
                adjusted_score=25 if findings.missing_tests else 20,
                confidence=0.8,
                factors=[f"Touched risky module: {module}" for module in findings.risky_modules],
                mitigation_suggestions=["Extra review for sensitive modules", "Enhanced testing"]
            ))
        
        # Documentation risk
        if not findings.docs_updated and findings.change_size != "small":
            components.append(RiskComponent(
                component_name="documentation",
                base_score=5,
                adjusted_score=10 if findings.change_size == "large" else 5,
                confidence=0.7,
                factors=["No documentation updates", "Significant changes made"],
                mitigation_suggestions=["Update relevant documentation", "Add migration notes if needed"]
            ))
        
        return components

class DecisionEngineAgent(BaseAgent):
    """Makes final decisions with explainable reasoning."""
    
    def __init__(self):
        super().__init__("DecisionEngine")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Make final go/no-go decision."""
        decision = self._make_decision(state)
        state.decision = decision
        state.current_stage = WorkflowStage.QUALITY_ASSURANCE
        
        return state
    
    def _make_decision(self, state: WorkflowState) -> EnhancedDecision:
        """Make decision based on comprehensive analysis."""
        from .enhanced_models import EnhancedDecision, DecisionContext
        
        findings = state.policy_findings
        if not findings:
            raise ValueError("Policy findings required for decision making")
        
        # Calculate total risk score
        total_risk = findings.total_risk_score
        
        # Apply conditional bumps
        conditional_bumps = 0
        reasoning_steps = []
        
        if findings.risky_modules and findings.missing_tests:
            conditional_bumps += 15
            reasoning_steps.append("Applied +15 conditional bump for risky modules without tests")
        
        final_risk_score = min(total_risk + conditional_bumps, 100)
        
        # Determine decision
        if findings.secret_like:
            go_decision = False
            rationale = "Automatic No-Go due to potential secret exposure"
            reasoning_steps.append("Secret-like content triggers automatic rejection")
        elif final_risk_score >= 50:  # Using strict threshold from config
            go_decision = False
            rationale = f"No-Go decision due to high risk score ({final_risk_score}/100)"
            reasoning_steps.append(f"Risk score {final_risk_score} exceeds threshold of 50")
        else:
            go_decision = True
            rationale = f"Go decision with acceptable risk level ({final_risk_score}/100)"
            reasoning_steps.append(f"Risk score {final_risk_score} is within acceptable range")
        
        # Calculate confidence
        confidence = 0.9 if findings.secret_like else 0.8
        
        # Build decision context
        context = DecisionContext(
            decision_factors=[
                f"Risk score: {final_risk_score}/100",
                f"Policy violations: {len(findings.violations)}",
                f"Compliance score: {findings.compliance_score:.2f}"
            ],
            alternative_paths=[] if go_decision else [
                "Address policy violations and resubmit",
                "Request security review if needed",
                "Add missing tests and documentation"
            ],
            rollback_plan="Standard rollback procedures apply" if go_decision else None
        )
        
        return EnhancedDecision(
            go=go_decision,
            risk_score=final_risk_score,
            confidence=confidence,
            rationale=rationale,
            detailed_reasoning=reasoning_steps,
            context=context,
            recommended_actions=self._generate_recommendations(findings),
            agent_execution=AgentExecution(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                confidence=confidence
            )
        )
    
    def _generate_recommendations(self, findings) -> list:
        """Generate actionable recommendations."""
        recommendations = []
        
        if findings.missing_tests:
            recommendations.append("Add comprehensive test coverage for all code changes")
        
        if findings.risky_modules:
            recommendations.append("Request additional security review for sensitive modules")
        
        if not findings.docs_updated and findings.change_size != "small":
            recommendations.append("Update documentation to reflect changes")
        
        if findings.unapproved_modules:
            recommendations.append("Get approval for usage of experimental/vendor modules")
        
        return recommendations

class QualityAssuranceAgent(BaseAgent):
    """Validates analysis quality and consistency."""
    
    def __init__(self):
        super().__init__("QualityAssurance")
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """Perform quality assurance checks."""
        quality_issues = []
        
        # Check for consistency
        if state.decision and state.policy_findings:
            if state.decision.go and state.policy_findings.secret_like:
                quality_issues.append("Inconsistent: Go decision with secret exposure")
            
            if not state.decision.go and state.decision.risk_score < 30:
                quality_issues.append("Inconsistent: No-Go decision with low risk score")
        
        # Check completeness
        if not state.summary:
            quality_issues.append("Missing change summary")
        if not state.policy_findings:
            quality_issues.append("Missing policy findings")
        if not state.decision:
            quality_issues.append("Missing decision")
        
        # Calculate quality scores
        completeness_score = self._calculate_completeness(state)
        overall_confidence = self._calculate_overall_confidence(state)
        
        state.quality_score = max(0, 1.0 - len(quality_issues) * 0.2)
        state.completeness_score = completeness_score
        state.overall_confidence = overall_confidence
        
        # Add quality issues as warnings
        state.warnings.extend(quality_issues)
        
        state.current_stage = WorkflowStage.COMPLETED
        return state
    
    def _calculate_completeness(self, state: WorkflowState) -> float:
        """Calculate analysis completeness score."""
        components = [
            state.summary is not None,
            state.policy_findings is not None,
            state.decision is not None,
            len(state.agent_executions) >= 3
        ]
        return sum(components) / len(components)
    
    def _calculate_overall_confidence(self, state: WorkflowState) -> float:
        """Calculate overall workflow confidence."""
        confidences = []
        
        for execution in state.agent_executions.values():
            if execution.status == AgentStatus.COMPLETED:
                confidences.append(execution.confidence)
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)

# Conditional routing functions
def should_retry(state: WorkflowState) -> str:
    """Determine if workflow should be retried."""
    if state.should_retry:
        state.retry_count += 1
        return "retry"
    elif state.has_critical_errors:
        return "error"
    else:
        return "complete"

def quality_gate(state: WorkflowState) -> str:
    """Quality gate for final approval."""
    if state.quality_score >= 0.8 and state.overall_confidence >= 0.7:
        return "approved"
    elif state.retry_count < state.max_retries:
        return "retry"
    else:
        return "complete_with_warnings"

# Main workflow creation function
def create_risk_analysis_workflow() -> StateGraph:
    """Create the complete LangGraph workflow."""
    
    # Initialize agents
    input_validator = InputValidationAgent()
    change_analyzer = ChangeAnalysisAgent()
    policy_evaluator = PolicyEvaluationAgent()
    risk_assessor = RiskAssessmentAgent()
    decision_engine = DecisionEngineAgent()
    quality_assurance = QualityAssuranceAgent()
    
    # Create workflow
    workflow = StateGraph(WorkflowState)
    
    # Add agent nodes
    workflow.add_node("input_validation", input_validator.execute)
    workflow.add_node("change_analysis", change_analyzer.execute)
    workflow.add_node("policy_evaluation", policy_evaluator.execute)
    workflow.add_node("risk_assessment", risk_assessor.execute)
    workflow.add_node("decision_engine", decision_engine.execute)
    workflow.add_node("quality_assurance", quality_assurance.execute)
    
    # Set entry point
    workflow.set_entry_point("input_validation")
    
    # Define sequential flow
    workflow.add_edge("input_validation", "change_analysis")
    workflow.add_edge("change_analysis", "policy_evaluation")
    workflow.add_edge("policy_evaluation", "risk_assessment")
    workflow.add_edge("risk_assessment", "decision_engine")
    workflow.add_edge("decision_engine", "quality_assurance")
    
    # Quality gate with conditional routing
    workflow.add_conditional_edges(
        "quality_assurance",
        quality_gate,
        {
            "approved": END,
            "complete_with_warnings": END,
            "retry": "change_analysis"
        }
    )
    
    # Compile with checkpointing for state persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)