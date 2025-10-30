"""
LLM-Enhanced Release Risk Analyzer Demo
Demonstrates LLM-first analysis with heuristic fallback for all three agents.
"""

import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Mock LLM interface for demonstration
class MockLLMClient:
    """Mock LLM client for demonstration purposes."""
    
    async def generate_response(self, prompt: str, timeout: int = 30) -> str:
        """Simulate LLM response generation."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        # Parse prompt to determine response type
        if "Analyze this pull request" in prompt:
            return json.dumps({
                "change_type": "feature",
                "complexity": "medium",
                "modules_affected": ["user_service", "auth_module"],
                "risk_indicators": ["api_changes", "authentication_modification"],
                "summary": "Feature addition with authentication changes",
                "potential_impacts": ["user_experience", "security"],
                "security_risks": ["auth"],
                "confidence": 0.85
            })
        elif "Analyze this change for policy compliance" in prompt:
            return json.dumps({
                "compliance_status": "requires_review",
                "policy_violations": [
                    {
                        "policy": "security_file_changes",
                        "violation_type": "Authentication files modified",
                        "severity": "high",
                        "evidence": "auth_module files changed",
                        "recommendation": "Security team review required"
                    }
                ],
                "compliance_checks": [
                    {
                        "check": "security_policy_compliance",
                        "status": "warning",
                        "details": "Authentication changes detected"
                    }
                ],
                "risk_level": "medium",
                "approval_required": True,
                "required_reviewers": ["security_team"],
                "confidence": 0.9,
                "reasoning": "Authentication changes require security review"
            })
        elif "Analyze this change and make a release decision" in prompt:
            return json.dumps({
                "recommended_decision": "conditional_approve",
                "confidence_level": 0.8,
                "risk_assessment": {
                    "overall_risk": "medium",
                    "risk_factors": ["authentication_changes", "policy_review_required"],
                    "mitigation_strategies": ["security_review", "staged_rollout"]
                },
                "decision_rationale": {
                    "primary_concerns": ["Security implications of auth changes"],
                    "positive_indicators": ["Good test coverage", "Clear documentation"],
                    "risk_trade_offs": "Feature value vs security risk acceptable with conditions",
                    "business_impact": "Positive user experience improvement"
                },
                "conditions": [
                    {
                        "condition": "Security team approval",
                        "required_actions": ["Security review", "Penetration testing"],
                        "responsible_party": "security_team",
                        "timeline": "48 hours"
                    }
                ],
                "escalation_triggers": [],
                "monitoring_requirements": ["security_monitoring", "auth_failure_tracking"],
                "rollback_plan": {
                    "required": True,
                    "complexity": "medium",
                    "strategy": "feature_flag_rollback"
                },
                "stakeholder_communication": {
                    "required_notifications": ["security_team", "product_team"],
                    "key_messages": ["Auth enhancement requires security validation"]
                }
            })
        else:
            return '{"error": "Unknown prompt type"}'

class AnalysisMode(Enum):
    """Analysis execution modes."""
    LLM_FIRST = "llm_first"
    HEURISTIC_ONLY = "heuristic_only"
    HYBRID = "hybrid"

@dataclass
class RiskAnalysisState:
    """Enhanced state for LLM-powered workflow."""
    pr_title: str
    pr_body: str
    pr_files: List[str]
    change_summary: Dict[str, Any] = None
    policy_validation: Dict[str, Any] = None
    final_decision: Dict[str, Any] = None
    current_agent: str = None
    confidence: float = 1.0
    analysis_mode: AnalysisMode = AnalysisMode.LLM_FIRST

class BaseLLMAgent:
    """Enhanced base agent with LLM integration capabilities."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.llm_client = MockLLMClient()
        self.llm_timeout = config.get("llm_timeout", 30)
        self.fallback_threshold = config.get("fallback_threshold", 0.5)
    
    async def process(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Main processing pipeline with LLM integration."""
        
        try:
            # Determine analysis mode
            if state.analysis_mode == AnalysisMode.LLM_FIRST:
                result = await self._llm_analysis(state)
            elif state.analysis_mode == AnalysisMode.HEURISTIC_ONLY:
                result = await self._heuristic_analysis(state)
            else:  # HYBRID
                result = await self._hybrid_analysis(state)
            
            # Validate result quality
            if not self._validate_result(result):
                print(f"[{self.agent_id}] Result validation failed, using fallback")
                result = await self._heuristic_analysis(state)
            
            # Apply results to state
            return await self._apply_analysis_result(state, result)
            
        except Exception as e:
            print(f"[{self.agent_id}] Analysis failed: {e}, falling back to heuristic")
            result = await self._heuristic_analysis(state)
            return await self._apply_analysis_result(state, result)
    
    async def _execute_llm_with_timeout(self, prompt: str) -> str:
        """Execute LLM request with timeout protection."""
        try:
            return await asyncio.wait_for(
                self.llm_client.generate_response(prompt),
                timeout=self.llm_timeout
            )
        except asyncio.TimeoutError:
            print(f"[{self.agent_id}] LLM timeout after {self.llm_timeout}s")
            return None
        except Exception as e:
            print(f"[{self.agent_id}] LLM error: {e}")
            return None
    
    async def _hybrid_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Hybrid analysis combining LLM and heuristic methods."""
        
        # Try LLM first
        llm_result = None
        try:
            llm_result = await self._llm_analysis(state)
            if llm_result.get("llm_confidence", 0) >= self.fallback_threshold:
                print(f"[{self.agent_id}] Using LLM analysis (confidence: {llm_result.get('llm_confidence')})")
                return llm_result
        except Exception as e:
            print(f"[{self.agent_id}] LLM analysis failed: {e}")
        
        # Fallback to heuristic
        print(f"[{self.agent_id}] Falling back to heuristic analysis")
        heuristic_result = await self._heuristic_analysis(state)
        
        # Enhance heuristic with any successful LLM insights
        if llm_result:
            heuristic_result["llm_insights"] = llm_result
            heuristic_result["analysis_method"] = "hybrid"
        
        return heuristic_result
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate analysis result quality."""
        required_fields = self._get_required_result_fields()
        
        # Check required fields
        for field in required_fields:
            if field not in result:
                return False
        
        # Check confidence threshold
        confidence = result.get("llm_confidence", 0)
        if confidence < 0.3:  # Minimum confidence threshold
            return False
        
        return True
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """LLM-powered analysis (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _llm_analysis")
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Heuristic fallback analysis (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _heuristic_analysis")
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply analysis results to state (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _apply_analysis_result")
    
    def _get_required_result_fields(self) -> List[str]:
        """Get required fields for result validation (to be implemented by subclasses)."""
        return ["analysis_method"]

class LLMChangeLogSummarizerAgent(BaseLLMAgent):
    """LLM-enhanced Change Log Summarizer Agent."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("change_log_summarizer", config)
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """LLM-powered change analysis."""
        
        file_list = ", ".join(state.pr_files[:15])
        if len(state.pr_files) > 15:
            file_list += f" ... and {len(state.pr_files) - 15} more files"
        
        prompt = f"""
        Analyze this pull request and provide a structured summary:
        
        PR Title: {state.pr_title}
        PR Description: {state.pr_body}
        Changed Files: {file_list}
        
        Please provide analysis in JSON format with change_type, complexity, modules_affected, 
        risk_indicators, summary, potential_impacts, security_risks, and confidence (0.0-1.0).
        
        Focus on identifying core business logic changes, security modifications, 
        infrastructure changes, API modifications, and database schema changes.
        """
        
        response = await self._execute_llm_with_timeout(prompt)
        if not response:
            raise ValueError("LLM analysis failed")
        
        try:
            result_data = json.loads(response)
        except json.JSONDecodeError:
            result_data = {"change_type": "unknown", "complexity": "medium", "confidence": 0.3}
        
        # Enhance with file analysis
        file_analysis = self._analyze_file_patterns(state.pr_files)
        
        return {
            "change_type": result_data.get("change_type", "unknown"),
            "complexity": result_data.get("complexity", "medium"),
            "modules_touched": result_data.get("modules_affected", file_analysis["modules"]),
            "risk_notes": result_data.get("risk_indicators", []),
            "semantic_summary": result_data.get("summary", "LLM analysis completed"),
            "potential_impacts": result_data.get("potential_impacts", []),
            "security_risks": result_data.get("security_risks", []),
            "llm_confidence": result_data.get("confidence", 0.7),
            "analysis_method": "llm",
            "file_analysis": file_analysis
        }
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Heuristic fallback analysis."""
        
        file_analysis = self._analyze_file_patterns(state.pr_files)
        content_analysis = self._analyze_content_keywords(state.pr_title, state.pr_body)
        complexity = self._assess_complexity_heuristic(state.pr_files, state.pr_body)
        
        return {
            "change_type": content_analysis["change_type"],
            "complexity": complexity,
            "modules_touched": file_analysis["modules"],
            "risk_notes": content_analysis["risk_indicators"],
            "semantic_summary": f"Heuristic analysis: {content_analysis['summary']}",
            "potential_impacts": content_analysis["impacts"],
            "security_risks": content_analysis["security_keywords"],
            "llm_confidence": 0.6,
            "analysis_method": "heuristic",
            "file_analysis": file_analysis
        }
    
    def _analyze_file_patterns(self, files: List[str]) -> Dict[str, Any]:
        """Analyze file patterns to identify modules."""
        modules = set()
        file_types = {}
        
        for file_path in files:
            if "/" in file_path:
                module = file_path.split("/")[0]
                modules.add(module)
            
            if "." in file_path:
                ext = file_path.split(".")[-1]
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return {"modules": list(modules), "file_types": file_types}
    
    def _analyze_content_keywords(self, title: str, body: str) -> Dict[str, Any]:
        """Analyze content for semantic keywords."""
        combined_text = f"{title} {body}".lower()
        
        change_patterns = {
            "feature": ["add", "implement", "create", "new"],
            "bugfix": ["fix", "bug", "issue", "resolve"],
            "refactor": ["refactor", "cleanup", "reorganize"],
            "security": ["security", "auth", "permission"],
        }
        
        detected_type = "unknown"
        for change_type, keywords in change_patterns.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_type = change_type
                break
        
        security_keywords = []
        for pattern in ["password", "token", "secret", "auth"]:
            if pattern in combined_text:
                security_keywords.append(pattern)
        
        return {
            "change_type": detected_type,
            "summary": f"{detected_type.title()} change detected",
            "security_keywords": security_keywords,
            "impacts": ["core_functionality"],
            "risk_indicators": security_keywords
        }
    
    def _assess_complexity_heuristic(self, files: List[str], body: str) -> str:
        """Assess complexity using heuristics."""
        file_count = len(files)
        
        if file_count <= 3:
            return "low"
        elif file_count <= 10:
            return "medium"
        else:
            return "high"
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply summarizer results to state."""
        
        complexity_mapping = {"low": "small", "medium": "medium", "high": "large"}
        
        state.change_summary = {
            "highlights": [state.pr_title],
            "modules_touched": result["modules_touched"],
            "risk_notes": result["risk_notes"],
            "change_size": complexity_mapping.get(result["complexity"], "medium"),
            "semantic_summary": result["semantic_summary"],
            "change_type": result["change_type"],
            "potential_impacts": result["potential_impacts"],
            "security_risks": result["security_risks"],
            "analysis_method": result["analysis_method"],
            "llm_confidence": result["llm_confidence"]
        }
        
        state.current_agent = self.agent_id
        state.confidence = result["llm_confidence"]
        return state
    
    def _get_required_result_fields(self) -> List[str]:
        """Required fields for validation."""
        return ["change_type", "complexity", "modules_touched", "analysis_method", "llm_confidence"]

class LLMPolicyValidatorAgent(BaseLLMAgent):
    """LLM-enhanced Policy Validator Agent."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("policy_validator", config)
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """LLM-powered policy compliance analysis."""
        
        change_summary = state.change_summary or {}
        summary_text = f"""
        Change Type: {change_summary.get('change_type', 'unknown')}
        Size: {change_summary.get('change_size', 'unknown')}
        Modules: {', '.join(change_summary.get('modules_touched', []))}
        Security Risks: {', '.join(change_summary.get('security_risks', []))}
        Summary: {change_summary.get('semantic_summary', '')}
        """
        
        file_list = ", ".join(state.pr_files[:10])
        policies_text = """
        SECURITY POLICIES:
        - No secrets, passwords, API keys in code
        - Security changes require security team approval
        
        QUALITY POLICIES:
        - Minimum 80% test coverage required
        - API changes must include documentation
        
        PROCESS POLICIES:
        - High-risk changes require lead developer approval
        - Database changes require DBA approval
        """
        
        prompt = f"""
        Analyze this change for policy compliance:
        
        Change Summary: {summary_text}
        Files Changed: {file_list}
        Organizational Policies: {policies_text}
        
        Provide compliance analysis in JSON format with compliance_status, policy_violations,
        compliance_checks, risk_level, approval_required, required_reviewers, confidence, and reasoning.
        """
        
        response = await self._execute_llm_with_timeout(prompt)
        if not response:
            raise ValueError("LLM compliance analysis failed")
        
        try:
            result_data = json.loads(response)
        except json.JSONDecodeError:
            result_data = {"compliance_status": "requires_review", "confidence": 0.3}
        
        # Enhance with rule-based validation
        rule_validation = self._perform_rule_based_validation(state)
        
        return {
            "compliance_status": result_data.get("compliance_status", "requires_review"),
            "policy_violations": result_data.get("policy_violations", []),
            "compliance_checks": result_data.get("compliance_checks", []),
            "risk_level": result_data.get("risk_level", "medium"),
            "approval_required": result_data.get("approval_required", True),
            "required_reviewers": result_data.get("required_reviewers", []),
            "reasoning": result_data.get("reasoning", "LLM analysis completed"),
            "llm_confidence": result_data.get("confidence", 0.7),
            "analysis_method": "llm",
            "rule_validation": rule_validation
        }
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Rule-based fallback validation."""
        
        rule_validation = self._perform_rule_based_validation(state)
        
        # Determine compliance status
        critical_violations = [v for v in rule_validation["violations"] if v["severity"] == "critical"]
        high_violations = [v for v in rule_validation["violations"] if v["severity"] == "high"]
        
        if critical_violations:
            compliance_status = "non_compliant"
            risk_level = "critical"
        elif high_violations:
            compliance_status = "requires_review"
            risk_level = "high"
        elif rule_validation["violations"]:
            compliance_status = "requires_review"
            risk_level = "medium"
        else:
            compliance_status = "compliant"
            risk_level = "low"
        
        required_reviewers = self._determine_required_reviewers(state, rule_validation)
        
        return {
            "compliance_status": compliance_status,
            "policy_violations": rule_validation["violations"],
            "compliance_checks": rule_validation["checks"],
            "risk_level": risk_level,
            "approval_required": len(required_reviewers) > 0,
            "required_reviewers": required_reviewers,
            "reasoning": f"Rule-based validation: {len(rule_validation['violations'])} violations found",
            "llm_confidence": 0.8,
            "analysis_method": "heuristic",
            "rule_validation": rule_validation
        }
    
    def _perform_rule_based_validation(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Perform rule-based policy validation."""
        violations = []
        checks = []
        
        # Security checks
        content = f"{state.pr_title} {state.pr_body}".lower()
        for pattern in ["password", "secret", "token"]:
            if pattern in content:
                violations.append({
                    "policy": "no_secrets_in_code",
                    "violation_type": f"Potential {pattern} in PR content",
                    "severity": "critical",
                    "evidence": f"Pattern '{pattern}' found",
                    "recommendation": "Remove sensitive information"
                })
        
        # Test coverage check
        test_files = [f for f in state.pr_files if "test" in f.lower()]
        source_files = [f for f in state.pr_files if f.endswith(('.py', '.js', '.java'))]
        
        if source_files and not test_files:
            violations.append({
                "policy": "test_coverage",
                "violation_type": "No test files found",
                "severity": "medium",
                "evidence": f"{len(source_files)} source files, no tests",
                "recommendation": "Add test coverage"
            })
        
        checks.append({
            "check": "security_policy_compliance",
            "status": "pass" if not any("critical" == v["severity"] for v in violations) else "fail",
            "details": f"Security validation completed"
        })
        
        return {"violations": violations, "checks": checks}
    
    def _determine_required_reviewers(self, state: RiskAnalysisState, rule_validation: Dict[str, Any]) -> List[str]:
        """Determine required reviewers."""
        reviewers = set()
        
        # Security violations
        security_violations = [v for v in rule_validation["violations"] if "security" in v["policy"]]
        if security_violations:
            reviewers.add("security_team")
        
        # Large changes
        if len(state.pr_files) > 20:
            reviewers.add("lead_developer")
        
        return list(reviewers)
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply validation results to state."""
        
        state.policy_validation = {
            "compliance_status": result["compliance_status"],
            "violations": result["policy_violations"],
            "risk_level": result["risk_level"],
            "approval_required": result["approval_required"],
            "required_reviewers": result["required_reviewers"],
            "reasoning": result["reasoning"],
            "analysis_method": result["analysis_method"],
            "llm_confidence": result["llm_confidence"]
        }
        
        state.current_agent = self.agent_id
        state.confidence = min(state.confidence, result["llm_confidence"])
        return state
    
    def _get_required_result_fields(self) -> List[str]:
        """Required fields for validation."""
        return ["compliance_status", "risk_level", "analysis_method", "llm_confidence"]

class LLMReleaseDecisionAgent(BaseLLMAgent):
    """LLM-enhanced Release Decision Agent."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("release_decision", config)
        self.decision_thresholds = config.get("decision_thresholds", {
            "auto_approve": 30, "conditional_approve": 50, "auto_reject": 80
        })
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """LLM-powered release decision analysis."""
        
        change_summary = self._format_change_summary(state)
        policy_validation = self._format_policy_validation(state)
        organizational_context = """
        ORGANIZATIONAL CONTEXT:
        - Release Frequency: Weekly releases with hotfix capability
        - Risk Tolerance: Medium - balanced innovation with stability
        - Quality Standards: High - comprehensive testing required
        - Business Criticality: High availability system (99.9% SLA)
        """
        
        prompt = f"""
        Analyze this change and make a release decision:
        
        CHANGE SUMMARY:
        {change_summary}
        
        POLICY VALIDATION:
        {policy_validation}
        
        ORGANIZATIONAL CONTEXT:
        {organizational_context}
        
        Provide decision analysis in JSON format with recommended_decision, confidence_level,
        risk_assessment, decision_rationale, conditions, and monitoring_requirements.
        """
        
        response = await self._execute_llm_with_timeout(prompt)
        if not response:
            raise ValueError("LLM decision analysis failed")
        
        try:
            result_data = json.loads(response)
        except json.JSONDecodeError:
            result_data = {"recommended_decision": "conditional_approve", "confidence_level": 0.3}
        
        return {
            "decision": result_data.get("recommended_decision", "conditional_approve"),
            "confidence": result_data.get("confidence_level", 0.7),
            "risk_assessment": result_data.get("risk_assessment", {}),
            "rationale": result_data.get("decision_rationale", {}),
            "conditions": result_data.get("conditions", []),
            "monitoring_requirements": result_data.get("monitoring_requirements", []),
            "rollback_plan": result_data.get("rollback_plan", {}),
            "analysis_method": "llm",
            "llm_confidence": result_data.get("confidence_level", 0.7)
        }
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Quantitative fallback decision."""
        
        risk_score = self._calculate_risk_score(state)
        decision = self._apply_decision_thresholds(risk_score)
        
        return {
            "decision": decision,
            "confidence": 0.8,
            "risk_assessment": {
                "overall_risk": self._score_to_risk_level(risk_score),
                "risk_factors": self._identify_risk_factors(state)
            },
            "rationale": {
                "primary_concerns": self._identify_primary_concerns(state),
                "risk_trade_offs": f"Risk score {risk_score} vs thresholds"
            },
            "conditions": self._generate_conditions(state),
            "monitoring_requirements": ["standard_monitoring"],
            "rollback_plan": {"required": risk_score > 50},
            "analysis_method": "heuristic",
            "llm_confidence": 0.8
        }
    
    def _format_change_summary(self, state: RiskAnalysisState) -> str:
        """Format change summary for LLM."""
        summary = state.change_summary or {}
        return f"""
        Change Type: {summary.get('change_type', 'unknown')}
        Size: {summary.get('change_size', 'unknown')}
        Modules: {', '.join(summary.get('modules_touched', []))}
        Security Risks: {', '.join(summary.get('security_risks', []))}
        Summary: {summary.get('semantic_summary', '')}
        """
    
    def _format_policy_validation(self, state: RiskAnalysisState) -> str:
        """Format policy validation for LLM."""
        validation = state.policy_validation or {}
        return f"""
        Compliance Status: {validation.get('compliance_status', 'unknown')}
        Risk Level: {validation.get('risk_level', 'unknown')}
        Violations: {len(validation.get('violations', []))}
        Required Reviewers: {', '.join(validation.get('required_reviewers', []))}
        """
    
    def _calculate_risk_score(self, state: RiskAnalysisState) -> int:
        """Calculate quantitative risk score."""
        score = 0
        
        # Policy violations
        policy_validation = state.policy_validation or {}
        violations = policy_validation.get("violations", [])
        for violation in violations:
            severity_scores = {"low": 5, "medium": 15, "high": 30, "critical": 50}
            score += severity_scores.get(violation.get("severity", "medium"), 15)
        
        # Change size
        change_summary = state.change_summary or {}
        size_scores = {"small": 5, "medium": 15, "large": 30}
        score += size_scores.get(change_summary.get("change_size", "medium"), 15)
        
        # File count
        file_count = len(state.pr_files)
        if file_count > 20:
            score += 20
        elif file_count > 10:
            score += 10
        
        return min(100, score)
    
    def _apply_decision_thresholds(self, risk_score: int) -> str:
        """Apply threshold-based decisions."""
        if risk_score >= self.decision_thresholds["auto_reject"]:
            return "reject"
        elif risk_score >= self.decision_thresholds["conditional_approve"]:
            return "conditional_approve"
        else:
            return "approve"
    
    def _score_to_risk_level(self, score: int) -> str:
        """Convert score to risk level."""
        if score >= 80:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"
    
    def _identify_risk_factors(self, state: RiskAnalysisState) -> List[str]:
        """Identify key risk factors."""
        factors = []
        
        policy_validation = state.policy_validation or {}
        if policy_validation.get("violations"):
            factors.append("policy_violations")
        
        change_summary = state.change_summary or {}
        if change_summary.get("security_risks"):
            factors.append("security_implications")
        
        return factors
    
    def _identify_primary_concerns(self, state: RiskAnalysisState) -> List[str]:
        """Identify primary concerns."""
        concerns = []
        
        policy_validation = state.policy_validation or {}
        violations = policy_validation.get("violations", [])
        
        for violation in violations[:3]:
            concerns.append(f"{violation.get('policy', 'unknown')}: {violation.get('violation_type', 'unknown')}")
        
        return concerns
    
    def _generate_conditions(self, state: RiskAnalysisState) -> List[Dict[str, Any]]:
        """Generate conditions for approval."""
        conditions = []
        
        policy_validation = state.policy_validation or {}
        if policy_validation.get("required_reviewers"):
            conditions.append({
                "condition": "Required reviewer approval",
                "required_actions": ["Review and approval"],
                "responsible_party": ", ".join(policy_validation.get("required_reviewers", [])),
                "timeline": "48 hours"
            })
        
        return conditions
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply decision results to state."""
        
        state.final_decision = {
            "decision": result["decision"],
            "confidence": result["confidence"],
            "risk_assessment": result["risk_assessment"],
            "rationale": result["rationale"],
            "conditions": result["conditions"],
            "monitoring_requirements": result["monitoring_requirements"],
            "rollback_plan": result["rollback_plan"],
            "analysis_method": result["analysis_method"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        state.current_agent = self.agent_id
        state.confidence = min(state.confidence, result["confidence"])
        return state
    
    def _get_required_result_fields(self) -> List[str]:
        """Required fields for validation."""
        return ["decision", "confidence", "analysis_method", "llm_confidence"]

async def run_llm_enhanced_demo():
    """Run the LLM-enhanced release risk analysis demo."""
    
    print("🤖 LLM-Enhanced Release Risk Analyzer Demo")
    print("=" * 60)
    
    # Test scenarios with different analysis modes
    scenarios = [
        {
            "name": "Feature PR with Auth Changes (LLM-First)",
            "state": RiskAnalysisState(
                pr_title="Add OAuth2 integration for user authentication",
                pr_body="Implements OAuth2 authentication flow with secure token handling",
                pr_files=["src/auth/oauth2.py", "src/user/service.py", "tests/auth/test_oauth2.py"],
                analysis_mode=AnalysisMode.LLM_FIRST
            )
        },
        {
            "name": "Large Refactor (Heuristic Only)",
            "state": RiskAnalysisState(
                pr_title="Major refactor of payment processing",
                pr_body="Refactors payment processing for better maintainability",
                pr_files=[f"src/payment/module_{i}.py" for i in range(15)],
                analysis_mode=AnalysisMode.HEURISTIC_ONLY
            )
        },
        {
            "name": "Security Update (Hybrid Mode)",
            "state": RiskAnalysisState(
                pr_title="Security patch for password encryption",
                pr_body="Updates password hashing to use bcrypt with higher cost",
                pr_files=["src/auth/password.py", "src/security/crypto.py"],
                analysis_mode=AnalysisMode.HYBRID
            )
        }
    ]
    
    # Initialize agents
    config = {
        "llm_timeout": 30,
        "fallback_threshold": 0.5,
        "decision_thresholds": {"auto_approve": 30, "conditional_approve": 50, "auto_reject": 80}
    }
    
    summarizer = LLMChangeLogSummarizerAgent(config)
    validator = LLMPolicyValidatorAgent(config)
    decision_agent = LLMReleaseDecisionAgent(config)
    
    # Process each scenario
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Analysis Mode: {scenario['state'].analysis_mode.value}")
        print("-" * 50)
        
        state = scenario["state"]
        
        try:
            # Agent 1: Change Log Summarizer
            print("🔍 Change Log Summarizer Agent...")
            state = await summarizer.process(state)
            print(f"   ✅ Analysis complete ({state.change_summary['analysis_method']})")
            print(f"   📊 Change: {state.change_summary['change_type']}, "
                  f"Size: {state.change_summary['change_size']}, "
                  f"Confidence: {state.change_summary['llm_confidence']:.2f}")
            
            # Agent 2: Policy Validator
            print("\n✅ Policy Validator Agent...")
            state = await validator.process(state)
            print(f"   ✅ Validation complete ({state.policy_validation['analysis_method']})")
            print(f"   📊 Status: {state.policy_validation['compliance_status']}, "
                  f"Risk: {state.policy_validation['risk_level']}, "
                  f"Violations: {len(state.policy_validation['violations'])}")
            
            # Agent 3: Release Decision
            print("\n🎯 Release Decision Agent...")
            state = await decision_agent.process(state)
            print(f"   ✅ Decision complete ({state.final_decision['analysis_method']})")
            print(f"   📊 Decision: {state.final_decision['decision']}, "
                  f"Confidence: {state.final_decision['confidence']:.2f}")
            
            # Final summary
            print(f"\n📋 Final Decision Summary:")
            print(f"   🎯 Decision: {state.final_decision['decision'].upper()}")
            print(f"   🎯 Overall Risk: {state.final_decision['risk_assessment'].get('overall_risk', 'unknown')}")
            print(f"   🎯 Conditions: {len(state.final_decision['conditions'])} required")
            print(f"   🎯 Confidence: {state.confidence:.2f}")
            
            if state.final_decision['conditions']:
                print(f"   📝 Conditions:")
                for condition in state.final_decision['conditions']:
                    print(f"      - {condition.get('condition', 'Unknown condition')}")
        
        except Exception as e:
            print(f"   ❌ Error processing scenario: {e}")
    
    print(f"\n✅ LLM-Enhanced Demo Complete")
    print(f"🔧 All agents successfully demonstrated LLM-first analysis with fallback capabilities")

if __name__ == "__main__":
    asyncio.run(run_llm_enhanced_demo())