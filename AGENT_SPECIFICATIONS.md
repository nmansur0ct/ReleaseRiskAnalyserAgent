# Agent Technical Specifications

## 📋 Complete Agent Definitions and Implementation Guide

This document provides comprehensive technical specifications for each agent in the Release Risk Analyzer system, including detailed algorithms, decision trees, and implementation patterns with **LLM-first analysis and heuristic fallback**.

## 🏗️ Agent Framework Architecture

### Core Agent Interface with LLM Integration

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel
from enum import Enum
import asyncio
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate
from langchain.schema import LLMResult

class AnalysisMode(Enum):
    """Analysis mode enumeration."""
    LLM_FIRST = "llm_first"
    HEURISTIC_ONLY = "heuristic_only"
    HYBRID = "hybrid"

class BaseAgent(ABC):
    """Abstract base class for all analysis agents with LLM integration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = self.__class__.__name__
        self.llm = config.get("llm", None)  # LLM instance
        self.analysis_mode = config.get("analysis_mode", AnalysisMode.LLM_FIRST)
        self.fallback_enabled = config.get("fallback_enabled", True)
        self.llm_timeout = config.get("llm_timeout", 30)  # seconds
        
    async def process(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Process with LLM-first approach and heuristic fallback."""
        analysis_result = None
        
        try:
            if self.analysis_mode in [AnalysisMode.LLM_FIRST, AnalysisMode.HYBRID]:
                # Primary LLM analysis
                analysis_result = await self._llm_analysis(state)
                
                # Validate LLM result quality
                if not self._validate_llm_result(analysis_result):
                    if self.fallback_enabled:
                        print(f"⚠️ {self.agent_id}: LLM analysis quality low, falling back to heuristics")
                        analysis_result = await self._heuristic_analysis(state)
                    else:
                        raise ValueError("LLM analysis failed and fallback disabled")
            else:
                # Direct heuristic analysis
                analysis_result = await self._heuristic_analysis(state)
                
        except Exception as e:
            print(f"⚠️ {self.agent_id}: LLM analysis failed ({str(e)}), using fallback")
            if self.fallback_enabled:
                analysis_result = await self._heuristic_analysis(state)
            else:
                raise e
        
        # Apply results to state
        return await self._apply_analysis_result(state, analysis_result)
    
    @abstractmethod
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Perform LLM-based analysis."""
        pass
    
    @abstractmethod
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Perform heuristic-based analysis as fallback."""
        pass
    
    @abstractmethod
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply analysis result to state."""
        pass
    
    def _validate_llm_result(self, result: Dict[str, Any]) -> bool:
        """Validate quality of LLM analysis result."""
        if not result or not isinstance(result, dict):
            return False
        
        # Check for required fields
        required_fields = self._get_required_result_fields()
        return all(field in result for field in required_fields)
    
    def _get_required_result_fields(self) -> List[str]:
        """Get required fields for result validation."""
        return ["confidence", "analysis_method"]
    
    async def _execute_llm_with_timeout(self, prompt: str) -> Optional[str]:
        """Execute LLM call with timeout protection."""
        if not self.llm:
            raise ValueError("LLM not configured")
        
        try:
            # Create timeout wrapper
            result = await asyncio.wait_for(
                self._call_llm(prompt),
                timeout=self.llm_timeout
            )
            return result
        except asyncio.TimeoutError:
            print(f"⚠️ {self.agent_id}: LLM call timed out after {self.llm_timeout}s")
            return None
        except Exception as e:
            print(f"⚠️ {self.agent_id}: LLM call failed: {str(e)}")
            return None
    
    async def _call_llm(self, prompt: str) -> str:
        """Make actual LLM call."""
        # This would be implemented with your specific LLM provider
        # Example with LangChain:
        if hasattr(self.llm, 'ainvoke'):
            result = await self.llm.ainvoke(prompt)
        else:
            result = self.llm.invoke(prompt)
        return result
    
    def get_confidence_score(self, state: RiskAnalysisState) -> float:
        """Calculate confidence score for this agent's analysis."""
        base_confidence = 0.8
        
        # Boost confidence for LLM analysis
        if state.get("analysis_method") == "llm":
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def validate_input(self, state: RiskAnalysisState) -> bool:
        """Validate that required input data is present."""
        required_fields = ["pr_title", "pr_body", "pr_files"]
        return all(field in state for field in required_fields)
```

---

## 🔍 Agent 1: Change Log Summarizer Agent with LLM Analysis

### Purpose and Scope
The Change Log Summarizer Agent serves as the entry point for the analysis workflow, using **LLM-first analysis** to understand and structure pull request data into analyzable components, with heuristic fallback for reliability.

### LLM Integration Implementation

```python
class ChangeLogSummarizerAgent(BaseAgent):
    """
    LLM-powered change log analysis with heuristic fallback.
    
    Analysis Strategy:
    1. Primary: LLM semantic analysis of PR content
    2. Fallback: Heuristic pattern matching and file analysis
    3. Hybrid: LLM insights enhanced with structural analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_prompts = self._init_prompts()
    
    def _init_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize LLM prompts for different analysis tasks."""
        return {
            "summary_analysis": PromptTemplate(
                input_variables=["pr_title", "pr_body", "file_list"],
                template="""
                Analyze this pull request and provide a structured summary:
                
                PR Title: {pr_title}
                PR Description: {pr_body}
                Changed Files: {file_list}
                
                Please provide analysis in JSON format:
                {{
                    "change_type": "feature|bugfix|refactor|config|security|performance",
                    "complexity": "low|medium|high",
                    "modules_affected": ["module1", "module2"],
                    "risk_indicators": ["risk1", "risk2"],
                    "summary": "Brief description of changes",
                    "potential_impacts": ["impact1", "impact2"],
                    "confidence": 0.0-1.0
                }}
                
                Focus on identifying:
                - Core business logic changes
                - Security-related modifications
                - Infrastructure/configuration changes
                - API or interface modifications
                - Database schema changes
                
                Provide realistic confidence score based on clarity of information.
                """
            ),
            "risk_assessment": PromptTemplate(
                input_variables=["change_summary", "file_changes"],
                template="""
                Based on this change summary, assess potential risks:
                
                Change Summary: {change_summary}
                File Changes: {file_changes}
                
                Identify risks in JSON format:
                {{
                    "security_risks": ["risk1", "risk2"],
                    "stability_risks": ["risk1", "risk2"],
                    "performance_risks": ["risk1", "risk2"],
                    "compliance_risks": ["risk1", "risk2"],
                    "overall_risk_level": "low|medium|high",
                    "risk_rationale": "Explanation of risk assessment",
                    "mitigation_suggestions": ["suggestion1", "suggestion2"]
                }}
                """
            )
        }
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        LLM-powered analysis of PR changes.
        
        Process:
        1. Semantic analysis of PR content
        2. Risk pattern identification
        3. Module impact assessment
        4. Change complexity evaluation
        """
        
        # Prepare data for LLM
        file_list = ", ".join(state["pr_files"][:20])  # Limit for token efficiency
        if len(state["pr_files"]) > 20:
            file_list += f" ... and {len(state['pr_files']) - 20} more files"
        
        # Primary summary analysis
        summary_prompt = self.llm_prompts["summary_analysis"].format(
            pr_title=state["pr_title"],
            pr_body=state["pr_body"][:1000],  # Limit for token efficiency
            file_list=file_list
        )
        
        summary_result = await self._execute_llm_with_timeout(summary_prompt)
        if not summary_result:
            raise ValueError("LLM summary analysis failed")
        
        # Parse LLM response
        try:
            import json
            summary_data = json.loads(summary_result)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            summary_data = self._extract_json_from_response(summary_result)
        
        # Secondary risk assessment
        risk_prompt = self.llm_prompts["risk_assessment"].format(
            change_summary=summary_data.get("summary", ""),
            file_changes=file_list
        )
        
        risk_result = await self._execute_llm_with_timeout(risk_prompt)
        if risk_result:
            try:
                risk_data = json.loads(risk_result)
                summary_data.update(risk_data)
            except json.JSONDecodeError:
                pass  # Use summary data only
        
        # Enhance with file-based analysis
        file_analysis = self._analyze_file_patterns(state["pr_files"])
        
        return {
            "change_type": summary_data.get("change_type", "unknown"),
            "complexity": summary_data.get("complexity", "medium"),
            "modules_touched": summary_data.get("modules_affected", file_analysis["modules"]),
            "risk_notes": summary_data.get("risk_indicators", []),
            "semantic_summary": summary_data.get("summary", ""),
            "potential_impacts": summary_data.get("potential_impacts", []),
            "security_risks": summary_data.get("security_risks", []),
            "llm_confidence": summary_data.get("confidence", 0.7),
            "analysis_method": "llm",
            "file_analysis": file_analysis
        }
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Heuristic fallback analysis using pattern matching.
        
        Fallback Strategy:
        1. File pattern analysis
        2. Keyword detection in PR content
        3. Module categorization
        4. Size-based complexity assessment
        """
        
        # File pattern analysis
        file_analysis = self._analyze_file_patterns(state["pr_files"])
        
        # Content keyword analysis
        content_analysis = self._analyze_content_keywords(state["pr_title"], state["pr_body"])
        
        # Complexity assessment
        complexity = self._assess_complexity_heuristic(state["pr_files"], state["pr_body"])
        
        # Risk identification
        risk_notes = self._identify_heuristic_risks(state)
        
        return {
            "change_type": content_analysis["change_type"],
            "complexity": complexity,
            "modules_touched": file_analysis["modules"],
            "risk_notes": risk_notes,
            "semantic_summary": f"Heuristic analysis: {content_analysis['summary']}",
            "potential_impacts": content_analysis["impacts"],
            "security_risks": content_analysis["security_keywords"],
            "llm_confidence": 0.6,  # Lower confidence for heuristic
            "analysis_method": "heuristic",
            "file_analysis": file_analysis
        }
    
    def _analyze_file_patterns(self, files: List[str]) -> Dict[str, Any]:
        """Analyze file patterns to identify modules and types."""
        modules = set()
        file_types = {}
        
        for file_path in files:
            # Extract module from path
            if "/" in file_path:
                module = file_path.split("/")[0]
                modules.add(module)
            
            # Categorize file type
            if "." in file_path:
                ext = file_path.split(".")[-1]
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "modules": list(modules),
            "file_types": file_types,
            "total_files": len(files)
        }
    
    def _analyze_content_keywords(self, title: str, body: str) -> Dict[str, Any]:
        """Analyze PR content for semantic keywords."""
        combined_text = f"{title} {body}".lower()
        
        # Change type detection
        change_patterns = {
            "feature": ["add", "implement", "create", "new", "feature"],
            "bugfix": ["fix", "bug", "issue", "resolve", "patch"],
            "refactor": ["refactor", "cleanup", "reorganize", "restructure"],
            "security": ["security", "auth", "permission", "vulnerability"],
            "config": ["config", "setting", "environment", "deploy"],
            "performance": ["performance", "optimize", "speed", "cache"]
        }
        
        detected_type = "unknown"
        for change_type, keywords in change_patterns.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_type = change_type
                break
        
        # Security keyword detection
        security_keywords = []
        security_patterns = ["password", "token", "secret", "key", "auth", "login", "security"]
        for pattern in security_patterns:
            if pattern in combined_text:
                security_keywords.append(pattern)
        
        # Impact analysis
        impact_patterns = {
            "database": ["migration", "schema", "database", "sql", "table"],
            "api": ["api", "endpoint", "route", "interface"],
            "ui": ["ui", "frontend", "component", "view"],
            "backend": ["service", "controller", "handler", "logic"]
        }
        
        impacts = []
        for impact_type, keywords in impact_patterns.items():
            if any(keyword in combined_text for keyword in keywords):
                impacts.append(impact_type)
        
        return {
            "change_type": detected_type,
            "summary": f"{detected_type.title()} change affecting {', '.join(impacts) if impacts else 'core functionality'}",
            "security_keywords": security_keywords,
            "impacts": impacts
        }
    
    def _assess_complexity_heuristic(self, files: List[str], body: str) -> str:
        """Assess change complexity using heuristics."""
        file_count = len(files)
        
        # File count based complexity
        if file_count <= 3:
            base_complexity = "low"
        elif file_count <= 10:
            base_complexity = "medium"
        else:
            base_complexity = "high"
        
        # Content complexity indicators
        complexity_indicators = ["refactor", "migration", "breaking", "major", "architecture"]
        if any(indicator in body.lower() for indicator in complexity_indicators):
            if base_complexity == "low":
                base_complexity = "medium"
            elif base_complexity == "medium":
                base_complexity = "high"
        
        return base_complexity
    
    def _identify_heuristic_risks(self, state: RiskAnalysisState) -> List[str]:
        """Identify risks using heuristic patterns."""
        risk_notes = []
        combined_text = f"{state['pr_title']} {state['pr_body']}".lower()
        
        # Security risks
        if any(keyword in combined_text for keyword in ["auth", "security", "password", "token"]):
            risk_notes.append("security_component_modification")
        
        # Database risks
        if any(keyword in combined_text for keyword in ["migration", "schema", "database"]):
            risk_notes.append("database_schema_changes")
        
        # API risks
        if any(keyword in combined_text for keyword in ["api", "endpoint", "breaking"]):
            risk_notes.append("api_modification_detected")
        
        # Configuration risks
        config_files = [f for f in state["pr_files"] if any(cfg in f.lower() for cfg in ["config", "env", ".json", ".yaml"])]
        if config_files:
            risk_notes.append("configuration_file_changes")
        
        return risk_notes
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response that might contain extra text."""
        import re
        import json
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return minimal fallback structure
        return {
            "change_type": "unknown",
            "complexity": "medium",
            "confidence": 0.3
        }
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply analysis results to the workflow state."""
        
        # Map complexity to size category
        complexity_mapping = {
            "low": "small",
            "medium": "medium", 
            "high": "large"
        }
        
        state["change_summary"] = {
            "highlights": [state["pr_title"]],
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
        
        state["current_agent"] = self.agent_id
        state["confidence"] = result["llm_confidence"]
        
        return state
    
    def _get_required_result_fields(self) -> List[str]:
        """Required fields for validating LLM analysis result."""
        return [
            "change_type", "complexity", "modules_touched", 
            "risk_notes", "analysis_method", "llm_confidence"
        ]
```
    
    async def process(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Main processing pipeline for change log analysis."""
        
        # Step 1: Module extraction with intelligent parsing
        modules = self._extract_modules_advanced(state["pr_files"])
        
        # Step 2: Multi-dimensional change classification
        change_metrics = self._analyze_change_complexity(state)
        
        # Step 3: Semantic content analysis
        semantic_analysis = self._analyze_semantic_content(state)
        
        # Step 4: Risk pattern identification
        risk_indicators = self._identify_risk_patterns(state)
        
        # Step 5: Generate comprehensive summary
        summary = self._generate_structured_summary(
            modules, change_metrics, semantic_analysis, risk_indicators
        )
        
        state["change_summary"] = summary
        state["current_agent"] = self.agent_id
        state["confidence"] = self.get_confidence_score(state)
        
        return state
    
    def _extract_modules_advanced(self, file_list: List[str]) -> Dict[str, Any]:
        """
        Advanced module extraction with categorization.
        
        Algorithm:
        1. Parse file paths into hierarchical structure
        2. Identify module types (frontend, backend, config, tests)
        3. Calculate module coupling and complexity
        4. Map to business domain areas
        """
        modules = {
            "primary": [],      # Main application modules
            "secondary": [],    # Supporting modules
            "infrastructure": [], # Config, deployment, etc.
            "testing": []       # Test files
        }
        
        domain_mappings = {
            "auth": "authentication",
            "payment": "financial",
            "user": "user_management",
            "api": "interface",
            "db": "database",
            "config": "configuration",
            "deploy": "deployment",
            "test": "testing"
        }
        
        for file_path in file_list:
            parts = file_path.split("/")
            if len(parts) > 1:
                module_name = parts[0]
                
                # Categorize by file type and location
                if "test" in file_path.lower():
                    modules["testing"].append(module_name)
                elif any(config_indicator in file_path.lower() 
                        for config_indicator in ["config", "env", "deploy", "docker"]):
                    modules["infrastructure"].append(module_name)
                elif any(critical_indicator in module_name.lower() 
                        for critical_indicator in ["auth", "payment", "security"]):
                    modules["primary"].append(module_name)
                else:
                    modules["secondary"].append(module_name)
        
        # Remove duplicates and add metadata
        for category in modules:
            modules[category] = list(set(modules[category]))
        
        return modules
    
    def _analyze_change_complexity(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Multi-dimensional change complexity analysis.
        
        Metrics:
        - File count and distribution
        - Estimated lines changed
        - Module spread
        - File type diversity
        """
        file_count = len(state["pr_files"])
        
        # File type analysis
        file_types = {}
        for file_path in state["pr_files"]:
            ext = file_path.split(".")[-1] if "." in file_path else "unknown"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Complexity scoring
        complexity_score = 0
        if file_count > 20:
            complexity_score += 40
        elif file_count > 10:
            complexity_score += 20
        elif file_count > 5:
            complexity_score += 10
        
        # Type diversity penalty
        if len(file_types) > 5:
            complexity_score += 15
        
        # Size classification
        if file_count <= 3:
            size_category = "small"
        elif file_count <= 10:
            size_category = "medium"
        else:
            size_category = "large"
        
        return {
            "file_count": file_count,
            "file_types": file_types,
            "size_category": size_category,
            "complexity_score": complexity_score,
            "type_diversity": len(file_types)
        }
    
    def _analyze_semantic_content(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Semantic analysis of PR title and description.
        
        Categories:
        - Feature addition/modification
        - Bug fixes
        - Refactoring
        - Configuration changes
        - Security updates
        """
        title = state["pr_title"].lower()
        body = state["pr_body"].lower()
        combined_text = f"{title} {body}"
        
        semantic_categories = {
            "feature": ["add", "implement", "create", "new", "feature"],
            "bugfix": ["fix", "bug", "issue", "resolve", "patch"],
            "refactor": ["refactor", "cleanup", "reorganize", "restructure"],
            "security": ["security", "auth", "permission", "vulnerability"],
            "config": ["config", "setting", "environment", "deploy"],
            "performance": ["performance", "optimize", "speed", "cache"],
            "docs": ["doc", "readme", "comment", "documentation"]
        }
        
        detected_categories = []
        for category, keywords in semantic_categories.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_categories.append(category)
        
        # Risk indicator words
        risk_indicators = {
            "urgent": ["urgent", "critical", "hotfix", "emergency"],
            "experimental": ["experiment", "prototype", "trial", "poc"],
            "breaking": ["breaking", "major", "incompatible"],
            "database": ["migration", "schema", "database", "sql"]
        }
        
        detected_risks = []
        for risk_type, keywords in risk_indicators.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_risks.append(risk_type)
        
        return {
            "categories": detected_categories,
            "risk_indicators": detected_risks,
            "urgency_level": "high" if "urgent" in detected_risks else "normal",
            "change_type": detected_categories[0] if detected_categories else "unknown"
        }
    
    def _identify_risk_patterns(self, state: RiskAnalysisState) -> List[str]:
        """
        Pattern-based risk identification.
        
        Risk Patterns:
        - Security-related changes without security review
        - Database changes without migration tests
        - API changes without version considerations
        - Configuration changes in production files
        """
        risk_notes = []
        combined_text = f"{state['pr_title']} {state['pr_body']}".lower()
        files = state["pr_files"]
        
        # Security pattern risks
        security_keywords = ["auth", "security", "password", "token", "key"]
        if any(keyword in combined_text for keyword in security_keywords):
            risk_notes.append("security_component_modification")
        
        # API change risks
        api_keywords = ["api", "endpoint", "route", "controller"]
        if any(keyword in combined_text for keyword in api_keywords):
            risk_notes.append("api_modification_detected")
        
        # Database change risks
        db_keywords = ["database", "migration", "schema", "sql"]
        if any(keyword in combined_text for keyword in db_keywords):
            risk_notes.append("database_schema_changes")
        
        # Configuration risks
        config_files = [f for f in files if any(cfg in f.lower() for cfg in ["config", "env", ".json", ".yaml", ".yml"])]
        if config_files:
            risk_notes.append("configuration_file_changes")
        
        # Production file risks
        prod_indicators = ["prod", "production", "live", "master"]
        if any(indicator in " ".join(files).lower() for indicator in prod_indicators):
            risk_notes.append("production_file_modification")
        
        return risk_notes
    
    def get_confidence_score(self, state: RiskAnalysisState) -> float:
        """Calculate confidence based on data completeness and clarity."""
        confidence = 0.8  # Base confidence
        
        # Boost confidence for clear, well-documented changes
        if len(state["pr_body"]) > 50:
            confidence += 0.1
        
        # Reduce confidence for unclear or minimal information
        if len(state["pr_title"]) < 10:
            confidence -= 0.2
        
        if not state["pr_files"]:
            confidence -= 0.3
        
        return max(0.3, min(1.0, confidence))
```

---

## ✅ Agent 2: Policy Validator Agent with LLM Analysis

### Purpose and Scope
The Policy Validator Agent validates pull requests against organizational policies using **LLM-powered semantic analysis** combined with rule-based validation, ensuring comprehensive policy compliance with intelligent fallback mechanisms.

### LLM Integration Implementation

```python
class PolicyValidatorAgent(BaseAgent):
    """
    LLM-powered policy validation with rule-based fallback.
    
    Validation Strategy:
    1. Primary: LLM semantic analysis of policy compliance
    2. Fallback: Traditional rule-based validation
    3. Hybrid: LLM insights combined with structural checks
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_prompts = self._init_prompts()
        self.policy_rules = self._load_policy_rules()
    
    def _init_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize LLM prompts for policy validation tasks."""
        return {
            "compliance_analysis": PromptTemplate(
                input_variables=["change_summary", "file_list", "policies"],
                template="""
                Analyze this change for policy compliance:
                
                Change Summary: {change_summary}
                Files Changed: {file_list}
                Organizational Policies: {policies}
                
                Evaluate compliance and provide analysis in JSON format:
                {{
                    "compliance_status": "compliant|non_compliant|requires_review",
                    "policy_violations": [
                        {{
                            "policy": "policy_name",
                            "violation_type": "violation_description",
                            "severity": "low|medium|high|critical",
                            "evidence": "specific_evidence",
                            "recommendation": "how_to_fix"
                        }}
                    ],
                    "compliance_checks": [
                        {{
                            "check": "check_name",
                            "status": "pass|fail|warning",
                            "details": "check_details"
                        }}
                    ],
                    "risk_level": "low|medium|high|critical",
                    "approval_required": true|false,
                    "required_reviewers": ["reviewer1", "reviewer2"],
                    "confidence": 0.0-1.0,
                    "reasoning": "detailed_explanation"
                }}
                
                Focus on:
                - Security policy violations
                - Code quality standards
                - Testing requirements
                - Documentation compliance
                - Change management procedures
                - Approval workflows
                
                Consider context and intent, not just literal rule matching.
                """
            ),
            "requirement_analysis": PromptTemplate(
                input_variables=["change_data", "requirements"],
                template="""
                Analyze if this change meets organizational requirements:
                
                Change Details: {change_data}
                Requirements: {requirements}
                
                Provide requirement compliance in JSON format:
                {{
                    "requirements_met": [
                        {{
                            "requirement": "requirement_name",
                            "status": "met|partially_met|not_met",
                            "evidence": "supporting_evidence",
                            "gaps": ["gap1", "gap2"]
                        }}
                    ],
                    "missing_elements": ["element1", "element2"],
                    "recommendations": ["rec1", "rec2"],
                    "approval_status": "approve|conditional|reject",
                    "conditions": ["condition1", "condition2"]
                }}
                """
            )
        }
    
    def _load_policy_rules(self) -> Dict[str, Any]:
        """Load organizational policy rules for validation."""
        return {
            "security_policies": {
                "no_secrets_in_code": {
                    "patterns": ["password", "api_key", "secret", "token"],
                    "severity": "critical"
                },
                "secure_dependencies": {
                    "check_vulnerabilities": True,
                    "severity": "high"
                }
            },
            "quality_policies": {
                "test_coverage": {
                    "required": True,
                    "minimum_percentage": 80,
                    "severity": "medium"
                },
                "documentation": {
                    "required_for_api_changes": True,
                    "severity": "medium"
                }
            },
            "process_policies": {
                "approval_requirements": {
                    "high_risk_changes": ["security_team", "lead_developer"],
                    "database_changes": ["dba", "lead_developer"],
                    "config_changes": ["devops", "lead_developer"]
                }
            }
        }
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        LLM-powered policy compliance analysis.
        
        Process:
        1. Semantic policy interpretation
        2. Context-aware compliance checking
        3. Intelligent violation detection
        4. Recommendation generation
        """
        
        # Prepare policy context
        policies_text = self._format_policies_for_llm()
        
        # Format change summary for analysis
        change_summary = state.get("change_summary", {})
        summary_text = f"""
        Change Type: {change_summary.get('change_type', 'unknown')}
        Size: {change_summary.get('change_size', 'unknown')}
        Modules: {', '.join(change_summary.get('modules_touched', []))}
        Risk Notes: {', '.join(change_summary.get('risk_notes', []))}
        Security Risks: {', '.join(change_summary.get('security_risks', []))}
        Summary: {change_summary.get('semantic_summary', '')}
        """
        
        file_list = ", ".join(state["pr_files"][:15])
        if len(state["pr_files"]) > 15:
            file_list += f" ... and {len(state['pr_files']) - 15} more files"
        
        # Primary compliance analysis
        compliance_prompt = self.llm_prompts["compliance_analysis"].format(
            change_summary=summary_text,
            file_list=file_list,
            policies=policies_text
        )
        
        compliance_result = await self._execute_llm_with_timeout(compliance_prompt)
        if not compliance_result:
            raise ValueError("LLM compliance analysis failed")
        
        # Parse LLM response
        try:
            import json
            compliance_data = json.loads(compliance_result)
        except json.JSONDecodeError:
            compliance_data = self._extract_json_from_response(compliance_result)
        
        # Enhanced requirement analysis if needed
        if compliance_data.get("compliance_status") == "requires_review":
            requirements_prompt = self.llm_prompts["requirement_analysis"].format(
                change_data=summary_text,
                requirements=self._format_requirements_for_llm()
            )
            
            req_result = await self._execute_llm_with_timeout(requirements_prompt)
            if req_result:
                try:
                    req_data = json.loads(req_result)
                    compliance_data["requirements_analysis"] = req_data
                except json.JSONDecodeError:
                    pass
        
        # Enhance with rule-based validation
        rule_validation = self._perform_rule_based_validation(state)
        
        return {
            "compliance_status": compliance_data.get("compliance_status", "requires_review"),
            "policy_violations": compliance_data.get("policy_violations", []),
            "compliance_checks": compliance_data.get("compliance_checks", []),
            "risk_level": compliance_data.get("risk_level", "medium"),
            "approval_required": compliance_data.get("approval_required", True),
            "required_reviewers": compliance_data.get("required_reviewers", []),
            "llm_confidence": compliance_data.get("confidence", 0.7),
            "reasoning": compliance_data.get("reasoning", ""),
            "rule_validation": rule_validation,
            "analysis_method": "llm",
            "requirements_analysis": compliance_data.get("requirements_analysis", {})
        }
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Rule-based fallback validation using traditional policy checking.
        
        Fallback Strategy:
        1. Pattern-based violation detection
        2. File type validation
        3. Change size policy enforcement
        4. Required reviewer assignment
        """
        
        # Perform comprehensive rule-based validation
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
        
        # Determine required reviewers
        required_reviewers = self._determine_required_reviewers(state, rule_validation)
        
        return {
            "compliance_status": compliance_status,
            "policy_violations": rule_validation["violations"],
            "compliance_checks": rule_validation["checks"],
            "risk_level": risk_level,
            "approval_required": len(required_reviewers) > 0,
            "required_reviewers": required_reviewers,
            "llm_confidence": 0.8,  # High confidence in rule-based validation
            "reasoning": f"Rule-based validation: {len(rule_validation['violations'])} violations found",
            "rule_validation": rule_validation,
            "analysis_method": "heuristic",
            "requirements_analysis": {}
        }
    
    def _format_policies_for_llm(self) -> str:
        """Format policy rules for LLM consumption."""
        policies = []
        
        # Security policies
        policies.append("SECURITY POLICIES:")
        policies.append("- No secrets, passwords, API keys, or tokens in code")
        policies.append("- All dependencies must be scanned for vulnerabilities")
        policies.append("- Security-related changes require security team approval")
        
        # Quality policies  
        policies.append("\nQUALITY POLICIES:")
        policies.append("- Minimum 80% test coverage required")
        policies.append("- API changes must include documentation updates")
        policies.append("- Code must follow established style guidelines")
        
        # Process policies
        policies.append("\nPROCESS POLICIES:")
        policies.append("- High-risk changes require lead developer approval")
        policies.append("- Database changes require DBA approval")
        policies.append("- Configuration changes require DevOps approval")
        policies.append("- Breaking changes require extended review period")
        
        return "\n".join(policies)
    
    def _format_requirements_for_llm(self) -> str:
        """Format organizational requirements for LLM analysis."""
        return """
        ORGANIZATIONAL REQUIREMENTS:
        - All changes must have proper commit messages
        - Documentation must be updated for user-facing changes
        - Performance impact must be assessed for large changes
        - Rollback plan required for high-risk deployments
        - Testing requirements must be met before merge
        """
    
    def _perform_rule_based_validation(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Perform traditional rule-based policy validation."""
        violations = []
        checks = []
        
        # Security checks
        security_violations = self._check_security_policies(state)
        violations.extend(security_violations)
        checks.append({
            "check": "security_policy_compliance",
            "status": "pass" if not security_violations else "fail",
            "details": f"Found {len(security_violations)} security violations"
        })
        
        # Quality checks
        quality_violations = self._check_quality_policies(state)
        violations.extend(quality_violations)
        checks.append({
            "check": "quality_policy_compliance", 
            "status": "pass" if not quality_violations else "fail",
            "details": f"Found {len(quality_violations)} quality violations"
        })
        
        # File pattern checks
        file_violations = self._check_file_patterns(state)
        violations.extend(file_violations)
        checks.append({
            "check": "file_pattern_compliance",
            "status": "pass" if not file_violations else "warning",
            "details": f"Found {len(file_violations)} file pattern issues"
        })
        
        return {
            "violations": violations,
            "checks": checks,
            "total_violations": len(violations)
        }
    
    def _check_security_policies(self, state: RiskAnalysisState) -> List[Dict[str, Any]]:
        """Check for security policy violations."""
        violations = []
        
        # Check for secrets in content
        content = f"{state['pr_title']} {state['pr_body']}".lower()
        secret_patterns = self.policy_rules["security_policies"]["no_secrets_in_code"]["patterns"]
        
        for pattern in secret_patterns:
            if pattern in content:
                violations.append({
                    "policy": "no_secrets_in_code",
                    "violation_type": f"Potential {pattern} in PR content",
                    "severity": "critical",
                    "evidence": f"Pattern '{pattern}' found in PR description",
                    "recommendation": "Remove sensitive information from PR content"
                })
        
        # Check for security-related file changes
        security_files = [f for f in state["pr_files"] if any(sec in f.lower() for sec in ["auth", "security", "config", "env"])]
        if security_files:
            violations.append({
                "policy": "security_file_changes",
                "violation_type": "Security-related files modified",
                "severity": "high",
                "evidence": f"Modified files: {', '.join(security_files[:3])}",
                "recommendation": "Requires security team review"
            })
        
        return violations
    
    def _check_quality_policies(self, state: RiskAnalysisState) -> List[Dict[str, Any]]:
        """Check for code quality policy violations."""
        violations = []
        
        # Check for test files
        test_files = [f for f in state["pr_files"] if "test" in f.lower()]
        source_files = [f for f in state["pr_files"] if f.endswith(('.py', '.js', '.java', '.cpp', '.c'))]
        
        if source_files and not test_files:
            violations.append({
                "policy": "test_coverage",
                "violation_type": "No test files found for code changes",
                "severity": "medium",
                "evidence": f"{len(source_files)} source files changed, no test files",
                "recommendation": "Add appropriate test coverage"
            })
        
        # Check for API changes without documentation
        api_files = [f for f in state["pr_files"] if any(api in f.lower() for api in ["api", "endpoint", "route"])]
        doc_files = [f for f in state["pr_files"] if any(doc in f.lower() for doc in ["readme", "doc", "md"])]
        
        if api_files and not doc_files:
            violations.append({
                "policy": "documentation",
                "violation_type": "API changes without documentation updates",
                "severity": "medium", 
                "evidence": f"API files changed: {', '.join(api_files[:2])}",
                "recommendation": "Update API documentation"
            })
        
        return violations
    
    def _check_file_patterns(self, state: RiskAnalysisState) -> List[Dict[str, Any]]:
        """Check for file pattern compliance issues."""
        violations = []
        
        # Check for large number of files
        if len(state["pr_files"]) > 20:
            violations.append({
                "policy": "change_size_limit",
                "violation_type": "Large number of files changed",
                "severity": "medium",
                "evidence": f"{len(state['pr_files'])} files changed",
                "recommendation": "Consider breaking into smaller changes"
            })
        
        # Check for configuration files
        config_files = [f for f in state["pr_files"] if any(cfg in f.lower() for cfg in ["config", ".env", ".json", ".yaml"])]
        if config_files:
            violations.append({
                "policy": "configuration_changes",
                "violation_type": "Configuration files modified",
                "severity": "high",
                "evidence": f"Config files: {', '.join(config_files[:2])}",
                "recommendation": "Requires DevOps team review"
            })
        
        return violations
    
    def _determine_required_reviewers(self, state: RiskAnalysisState, rule_validation: Dict[str, Any]) -> List[str]:
        """Determine required reviewers based on change analysis."""
        reviewers = set()
        
        # Security-related changes
        security_violations = [v for v in rule_validation["violations"] if "security" in v["policy"]]
        if security_violations:
            reviewers.add("security_team")
        
        # Database-related changes
        db_files = [f for f in state["pr_files"] if any(db in f.lower() for db in ["migration", "schema", "database"])]
        if db_files:
            reviewers.add("dba")
        
        # Configuration changes
        config_files = [f for f in state["pr_files"] if any(cfg in f.lower() for cfg in ["config", "env", ".json", ".yaml"])]
        if config_files:
            reviewers.add("devops")
        
        # High-risk changes
        change_summary = state.get("change_summary", {})
        if change_summary.get("change_size") == "large" or len(rule_validation["violations"]) > 3:
            reviewers.add("lead_developer")
        
        return list(reviewers)
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply validation results to the workflow state."""
        
        state["policy_validation"] = {
            "compliance_status": result["compliance_status"],
            "violations": result["policy_violations"],
            "risk_level": result["risk_level"],
            "approval_required": result["approval_required"],
            "required_reviewers": result["required_reviewers"],
            "reasoning": result["reasoning"],
            "analysis_method": result["analysis_method"],
            "llm_confidence": result["llm_confidence"]
        }
        
        state["current_agent"] = self.agent_id
        state["confidence"] = min(state.get("confidence", 1.0), result["llm_confidence"])
        
        return state
    
    def _get_required_result_fields(self) -> List[str]:
        """Required fields for validating LLM analysis result."""
        return [
            "compliance_status", "policy_violations", "risk_level",
            "approval_required", "analysis_method", "llm_confidence"
        ]
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response that might contain extra text."""
        import re
        import json
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return minimal fallback structure
        return {
            "compliance_status": "requires_review",
            "policy_violations": [],
            "risk_level": "medium",
            "approval_required": True,
            "confidence": 0.3
        }
```
        
    def _default_weights(self) -> Dict[str, int]:
        """Default policy violation weights."""
        return {
            "missing_tests": 30,
            "secret_exposure": 100,
            "risky_modules": 20,
            "large_changes": 20,
            "missing_docs": 5,
            "unapproved_dependencies": 25,
            "security_vulnerability": 80,
            "compliance_violation": 60,
            "architecture_violation": 15
        }
    
    async def process(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Main policy validation pipeline."""
        
        # Step 1: Test coverage analysis
        test_analysis = await self._analyze_test_coverage(state)
        
        # Step 2: Security vulnerability scanning
        security_analysis = await self._scan_security_vulnerabilities(state)
        
        # Step 3: Module and architecture validation
        architecture_analysis = await self._validate_architecture(state)
        
        # Step 4: Compliance checking
        compliance_analysis = await self._check_compliance(state)
        
        # Step 5: Risk score calculation
        risk_score = self._calculate_composite_risk_score([
            test_analysis, security_analysis, 
            architecture_analysis, compliance_analysis
        ])
        
        # Step 6: Generate policy findings
        policy_findings = self._generate_policy_findings(
            test_analysis, security_analysis, 
            architecture_analysis, compliance_analysis, risk_score
        )
        
        state["policy_findings"] = policy_findings
        state["risk_score"] = risk_score
        state["current_agent"] = self.agent_id
        state["confidence"] = self.get_confidence_score(state)
        
        return state
    
    async def _analyze_test_coverage(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Comprehensive test coverage analysis.
        
        Analysis Dimensions:
        - Test file presence
        - Test-to-source ratio
        - Test type coverage (unit, integration, e2e)
        - Critical path testing
        """
        files = state["pr_files"]
        
        # Identify source and test files
        source_files = [f for f in files if self._is_source_file(f)]
        test_files = [f for f in files if self._is_test_file(f)]
        
        # Calculate coverage metrics
        has_source_changes = len(source_files) > 0
        has_test_files = len(test_files) > 0
        test_ratio = len(test_files) / len(source_files) if source_files else 0
        
        # Analyze test types
        test_types = self._identify_test_types(test_files)
        
        # Risk assessment
        missing_tests = has_source_changes and not has_test_files
        insufficient_coverage = test_ratio < 0.3 and len(source_files) > 2
        
        return {
            "has_source_changes": has_source_changes,
            "has_test_files": has_test_files,
            "test_ratio": test_ratio,
            "test_types": test_types,
            "missing_tests": missing_tests,
            "insufficient_coverage": insufficient_coverage,
            "risk_score": 30 if missing_tests else (15 if insufficient_coverage else 0)
        }
    
    async def _scan_security_vulnerabilities(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Multi-layer security vulnerability scanning.
        
        Scanning Layers:
        1. Secret pattern detection
        2. Vulnerability keyword scanning
        3. Dependency security analysis
        4. Code pattern analysis
        """
        title = state["pr_title"]
        body = state["pr_body"]
        files = state["pr_files"]
        combined_text = f"{title} {body}".lower()
        
        # Advanced secret patterns
        secret_patterns = {
            "api_keys": [
                r"api[_-]key[s]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]",
                r"sk_test_[a-zA-Z0-9]{24}",
                r"sk_live_[a-zA-Z0-9]{24}"
            ],
            "passwords": [
                r"password[s]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
                r"passwd[s]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
            ],
            "tokens": [
                r"token[s]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]",
                r"access[_-]token[s]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"
            ],
            "certificates": [
                r"-----BEGIN\s+(PRIVATE\s+KEY|RSA\s+PRIVATE\s+KEY|CERTIFICATE)",
                r"-----END\s+(PRIVATE\s+KEY|RSA\s+PRIVATE\s+KEY|CERTIFICATE)"
            ]
        }
        
        detected_secrets = {}
        for category, patterns in secret_patterns.items():
            for pattern in patterns:
                if any(keyword in combined_text for keyword in pattern.split() if len(keyword) > 3):
                    detected_secrets[category] = True
                    break
        
        # Vulnerability keywords
        vuln_keywords = [
            "injection", "xss", "csrf", "sql injection", 
            "buffer overflow", "privilege escalation",
            "authentication bypass", "authorization bypass"
        ]
        
        vulnerability_indicators = [
            keyword for keyword in vuln_keywords 
            if keyword in combined_text
        ]
        
        # Configuration security risks
        config_files = [f for f in files if self._is_config_file(f)]
        config_security_risk = len(config_files) > 0 and bool(detected_secrets)
        
        # Calculate security risk score
        security_risk = 0
        if detected_secrets:
            security_risk = 100  # Maximum risk for secrets
        elif vulnerability_indicators:
            security_risk = 80
        elif config_security_risk:
            security_risk = 40
        
        return {
            "detected_secrets": detected_secrets,
            "vulnerability_indicators": vulnerability_indicators,
            "config_security_risk": config_security_risk,
            "secret_patterns_found": len(detected_secrets),
            "vulnerability_count": len(vulnerability_indicators),
            "risk_score": security_risk
        }
    
    async def _validate_architecture(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Architecture and module boundary validation.
        
        Validation Rules:
        - Module coupling analysis
        - Layer boundary enforcement
        - Critical component isolation
        - Dependency direction validation
        """
        summary = state.get("change_summary", {})
        modules = summary.get("modules_touched", [])
        
        # Define critical modules
        critical_modules = [
            "auth", "authentication", "security",
            "payment", "billing", "financial",
            "gateway", "proxy", "router",
            "admin", "management", "core"
        ]
        
        # Identify risky modules
        risky_modules = []
        for module in modules:
            if any(critical in module.lower() for critical in critical_modules):
                risky_modules.append(module)
        
        # Module coupling analysis
        coupling_score = 0
        if len(modules) > 5:
            coupling_score = 15  # High coupling penalty
        elif len(modules) > 3:
            coupling_score = 10  # Medium coupling penalty
        
        # Critical component risk
        critical_risk = len(risky_modules) * 20
        
        total_risk = coupling_score + critical_risk
        
        return {
            "modules_analyzed": modules,
            "risky_modules": risky_modules,
            "coupling_score": coupling_score,
            "critical_components": len(risky_modules),
            "architecture_violations": [],
            "risk_score": min(total_risk, 60)  # Cap architecture risk
        }
    
    def _calculate_composite_risk_score(self, analysis_results: List[Dict[str, Any]]) -> int:
        """
        Calculate composite risk score from all policy analyses.
        
        Risk Aggregation Strategy:
        1. Security risks override other factors
        2. Weighted sum of individual risk scores
        3. Conditional risk amplification
        4. Risk ceiling enforcement
        """
        total_risk = 0
        security_override = False
        
        for analysis in analysis_results:
            risk_score = analysis.get("risk_score", 0)
            total_risk += risk_score
            
            # Check for security override conditions
            if analysis.get("detected_secrets") or risk_score >= 80:
                security_override = True
        
        # Apply security override
        if security_override:
            return 100
        
        # Apply conditional risk amplifiers
        has_missing_tests = any(a.get("missing_tests", False) for a in analysis_results)
        has_risky_modules = any(len(a.get("risky_modules", [])) > 0 for a in analysis_results)
        
        if has_missing_tests and has_risky_modules:
            total_risk += 15  # Conditional amplification
        
        # Enforce risk ceiling
        return min(total_risk, 100)
    
    def get_confidence_score(self, state: RiskAnalysisState) -> float:
        """Calculate confidence based on policy analysis completeness."""
        base_confidence = 0.9
        
        # Reduce confidence for incomplete analysis
        if not state.get("policy_findings"):
            base_confidence -= 0.3
        
        # Adjust for risk clarity
        risk_score = state.get("risk_score", 0)
        if 40 <= risk_score <= 60:  # Ambiguous risk range
            base_confidence -= 0.1
        
        return max(0.5, base_confidence)
```

---

## 🎯 Agent 3: Release Decision Agent with LLM Analysis

### Purpose and Scope
The Release Decision Agent synthesizes all analysis results into actionable Go/No-Go decisions using **LLM-powered decision reasoning** combined with quantitative risk assessment, providing comprehensive rationale and strategic recommendations.

### LLM Integration Implementation

```python
class ReleaseDecisionAgent(BaseAgent):
    """
    LLM-powered release decision engine with quantitative fallback.
    
    Decision Strategy:
    1. Primary: LLM holistic decision analysis with context reasoning
    2. Fallback: Quantitative risk scoring with threshold-based decisions
    3. Hybrid: LLM insights validated against organizational risk tolerance
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_prompts = self._init_prompts()
        self.decision_thresholds = config.get("decision_thresholds", {
            "auto_approve": 30,
            "conditional_approve": 50,
            "auto_reject": 80,
            "security_override": 100
        })
        self.risk_weights = config.get("risk_weights", self._default_risk_weights())
    
    def _init_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize LLM prompts for decision analysis tasks."""
        return {
            "decision_analysis": PromptTemplate(
                input_variables=["change_summary", "policy_validation", "organizational_context"],
                template="""
                Analyze this change and make a release decision:
                
                CHANGE SUMMARY:
                {change_summary}
                
                POLICY VALIDATION:
                {policy_validation}
                
                ORGANIZATIONAL CONTEXT:
                {organizational_context}
                
                Provide comprehensive decision analysis in JSON format:
                {{
                    "recommended_decision": "approve|conditional_approve|reject|escalate",
                    "confidence_level": 0.0-1.0,
                    "risk_assessment": {{
                        "overall_risk": "low|medium|high|critical",
                        "risk_factors": ["factor1", "factor2"],
                        "mitigation_strategies": ["strategy1", "strategy2"]
                    }},
                    "decision_rationale": {{
                        "primary_concerns": ["concern1", "concern2"],
                        "positive_indicators": ["indicator1", "indicator2"],
                        "risk_trade_offs": "analysis_of_trade_offs",
                        "business_impact": "impact_assessment"
                    }},
                    "conditions": [
                        {{
                            "condition": "condition_description",
                            "required_actions": ["action1", "action2"],
                            "responsible_party": "team_or_role",
                            "timeline": "completion_timeline"
                        }}
                    ],
                    "escalation_triggers": ["trigger1", "trigger2"],
                    "monitoring_requirements": ["requirement1", "requirement2"],
                    "rollback_plan": {{
                        "required": true|false,
                        "complexity": "low|medium|high",
                        "strategy": "rollback_approach"
                    }},
                    "stakeholder_communication": {{
                        "required_notifications": ["stakeholder1", "stakeholder2"],
                        "key_messages": ["message1", "message2"]
                    }}
                }}
                
                Consider:
                - Strategic business objectives vs. technical risks
                - Short-term delivery pressure vs. long-term stability
                - Innovation opportunities vs. compliance requirements
                - Team capacity vs. change complexity
                - Customer impact vs. internal efficiency
                
                Provide balanced, practical recommendations with clear reasoning.
                """
            ),
            "risk_quantification": PromptTemplate(
                input_variables=["analysis_data", "historical_context"],
                template="""
                Quantify the risks of this change based on analysis:
                
                Analysis Data: {analysis_data}
                Historical Context: {historical_context}
                
                Provide risk quantification in JSON format:
                {{
                    "risk_score": 0-100,
                    "risk_breakdown": {{
                        "technical_risk": 0-100,
                        "security_risk": 0-100,
                        "business_risk": 0-100,
                        "operational_risk": 0-100
                    }},
                    "probability_of_issues": 0.0-1.0,
                    "impact_severity": "low|medium|high|critical",
                    "time_to_recovery": "minutes|hours|days|weeks",
                    "affected_systems": ["system1", "system2"],
                    "risk_trends": "increasing|stable|decreasing"
                }}
                """
            )
        }
    
    def _default_risk_weights(self) -> Dict[str, float]:
        """Default risk weight configuration."""
        return {
            "security_violations": 0.4,
            "policy_compliance": 0.3,
            "change_complexity": 0.2,
            "test_coverage": 0.1
        }
    
    async def _llm_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        LLM-powered release decision analysis.
        
        Process:
        1. Holistic context analysis
        2. Strategic decision reasoning
        3. Risk-benefit assessment
        4. Stakeholder impact evaluation
        """
        
        # Prepare comprehensive context for LLM
        change_summary = self._format_change_summary(state)
        policy_validation = self._format_policy_validation(state)
        organizational_context = self._format_organizational_context()
        
        # Primary decision analysis
        decision_prompt = self.llm_prompts["decision_analysis"].format(
            change_summary=change_summary,
            policy_validation=policy_validation,
            organizational_context=organizational_context
        )
        
        decision_result = await self._execute_llm_with_timeout(decision_prompt)
        if not decision_result:
            raise ValueError("LLM decision analysis failed")
        
        # Parse LLM response
        try:
            import json
            decision_data = json.loads(decision_result)
        except json.JSONDecodeError:
            decision_data = self._extract_json_from_response(decision_result)
        
        # Enhanced risk quantification
        analysis_data = f"""
        Change Type: {state.get('change_summary', {}).get('change_type', 'unknown')}
        Complexity: {state.get('change_summary', {}).get('change_size', 'unknown')}
        Policy Status: {state.get('policy_validation', {}).get('compliance_status', 'unknown')}
        Violations: {len(state.get('policy_validation', {}).get('violations', []))}
        """
        
        risk_prompt = self.llm_prompts["risk_quantification"].format(
            analysis_data=analysis_data,
            historical_context="Similar changes in the past 6 months"
        )
        
        risk_result = await self._execute_llm_with_timeout(risk_prompt)
        if risk_result:
            try:
                risk_data = json.loads(risk_result)
                decision_data["quantitative_risk"] = risk_data
            except json.JSONDecodeError:
                pass
        
        # Validate decision against organizational thresholds
        validated_decision = self._validate_llm_decision(decision_data, state)
        
        return {
            "decision": validated_decision["recommended_decision"],
            "confidence": decision_data.get("confidence_level", 0.7),
            "risk_assessment": decision_data.get("risk_assessment", {}),
            "rationale": decision_data.get("decision_rationale", {}),
            "conditions": decision_data.get("conditions", []),
            "escalation_triggers": decision_data.get("escalation_triggers", []),
            "monitoring_requirements": decision_data.get("monitoring_requirements", []),
            "rollback_plan": decision_data.get("rollback_plan", {}),
            "stakeholder_communication": decision_data.get("stakeholder_communication", {}),
            "quantitative_risk": decision_data.get("quantitative_risk", {}),
            "analysis_method": "llm",
            "llm_confidence": decision_data.get("confidence_level", 0.7)
        }
    
    async def _heuristic_analysis(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """
        Quantitative fallback decision using risk scoring.
        
        Fallback Strategy:
        1. Calculate quantitative risk score
        2. Apply threshold-based decision rules
        3. Generate conditions based on violations
        4. Determine escalation requirements
        """
        
        # Calculate quantitative risk score
        risk_score = self._calculate_risk_score(state)
        
        # Determine decision based on thresholds
        decision = self._apply_decision_thresholds(risk_score)
        
        # Generate conditions and requirements
        conditions = self._generate_conditions(state)
        escalation_triggers = self._identify_escalation_triggers(state)
        
        # Assess rollback requirements
        rollback_plan = self._assess_rollback_requirements(state)
        
        return {
            "decision": decision,
            "confidence": 0.8,  # High confidence in quantitative methods
            "risk_assessment": {
                "overall_risk": self._score_to_risk_level(risk_score),
                "risk_factors": self._identify_risk_factors(state),
                "mitigation_strategies": self._suggest_mitigations(state)
            },
            "rationale": {
                "primary_concerns": self._identify_primary_concerns(state),
                "risk_trade_offs": f"Risk score {risk_score} against threshold {self.decision_thresholds['conditional_approve']}",
                "business_impact": "Impact determined by change scope and policy violations"
            },
            "conditions": conditions,
            "escalation_triggers": escalation_triggers,
            "monitoring_requirements": self._generate_monitoring_requirements(state),
            "rollback_plan": rollback_plan,
            "stakeholder_communication": self._determine_stakeholder_communication(state),
            "quantitative_risk": {
                "risk_score": risk_score,
                "risk_breakdown": self._calculate_risk_breakdown(state)
            },
            "analysis_method": "heuristic",
            "llm_confidence": 0.8
        }
    
    def _format_change_summary(self, state: RiskAnalysisState) -> str:
        """Format change summary for LLM analysis."""
        summary = state.get("change_summary", {})
        return f"""
        Change Type: {summary.get('change_type', 'unknown')}
        Complexity/Size: {summary.get('change_size', 'unknown')}
        Modules Affected: {', '.join(summary.get('modules_touched', []))}
        Risk Indicators: {', '.join(summary.get('risk_notes', []))}
        Security Concerns: {', '.join(summary.get('security_risks', []))}
        Description: {summary.get('semantic_summary', 'No summary available')}
        Analysis Method: {summary.get('analysis_method', 'unknown')}
        Confidence: {summary.get('llm_confidence', 0.5)}
        """
    
    def _format_policy_validation(self, state: RiskAnalysisState) -> str:
        """Format policy validation results for LLM analysis."""
        validation = state.get("policy_validation", {})
        violations = validation.get("violations", [])
        
        violation_summary = []
        for violation in violations[:5]:  # Limit to top 5 violations
            violation_summary.append(
                f"- {violation.get('policy', 'unknown')}: {violation.get('violation_type', 'unknown')} "
                f"(Severity: {violation.get('severity', 'unknown')})"
            )
        
        return f"""
        Compliance Status: {validation.get('compliance_status', 'unknown')}
        Risk Level: {validation.get('risk_level', 'unknown')}
        Approval Required: {validation.get('approval_required', True)}
        Required Reviewers: {', '.join(validation.get('required_reviewers', []))}
        Policy Violations ({len(violations)} total):
        {chr(10).join(violation_summary) if violation_summary else 'No major violations'}
        Analysis Method: {validation.get('analysis_method', 'unknown')}
        Confidence: {validation.get('llm_confidence', 0.5)}
        """
    
    def _format_organizational_context(self) -> str:
        """Format organizational context for decision making."""
        return """
        ORGANIZATIONAL CONTEXT:
        - Release Frequency: Weekly releases with hotfix capability
        - Risk Tolerance: Medium - balanced innovation with stability
        - Quality Standards: High - comprehensive testing required
        - Compliance Requirements: SOC2, GDPR compliance mandatory
        - Business Criticality: High availability system (99.9% SLA)
        - Team Structure: Cross-functional teams with security specialists
        - Change Management: Staged rollouts with feature flags preferred
        - Incident Response: 24/7 monitoring with 4-hour response SLA
        """
    
    def _validate_llm_decision(self, decision_data: Dict[str, Any], state: RiskAnalysisState) -> Dict[str, Any]:
        """Validate LLM decision against organizational constraints."""
        
        # Check for security overrides
        policy_validation = state.get("policy_validation", {})
        critical_violations = [
            v for v in policy_validation.get("violations", []) 
            if v.get("severity") == "critical"
        ]
        
        if critical_violations:
            # Override LLM decision for critical security issues
            decision_data["recommended_decision"] = "reject"
            decision_data["override_reason"] = "Critical security violations detected"
        
        # Ensure conditional approvals have conditions
        if decision_data.get("recommended_decision") == "conditional_approve":
            if not decision_data.get("conditions"):
                decision_data["conditions"] = self._generate_default_conditions(state)
        
        return decision_data
    
    def _calculate_risk_score(self, state: RiskAnalysisState) -> int:
        """Calculate quantitative risk score."""
        score = 0
        
        # Policy violations scoring
        policy_validation = state.get("policy_validation", {})
        violations = policy_validation.get("violations", [])
        
        for violation in violations:
            severity_scores = {"low": 5, "medium": 15, "high": 30, "critical": 50}
            score += severity_scores.get(violation.get("severity", "medium"), 15)
        
        # Change complexity scoring
        change_summary = state.get("change_summary", {})
        size_scores = {"small": 5, "medium": 15, "large": 30}
        score += size_scores.get(change_summary.get("change_size", "medium"), 15)
        
        # Security risk scoring
        security_risks = change_summary.get("security_risks", [])
        score += len(security_risks) * 10
        
        # File count impact
        file_count = len(state.get("pr_files", []))
        if file_count > 20:
            score += 20
        elif file_count > 10:
            score += 10
        
        return min(100, score)  # Cap at 100
    
    def _apply_decision_thresholds(self, risk_score: int) -> str:
        """Apply threshold-based decision rules."""
        if risk_score >= self.decision_thresholds["auto_reject"]:
            return "reject"
        elif risk_score >= self.decision_thresholds["conditional_approve"]:
            return "conditional_approve"
        elif risk_score >= self.decision_thresholds["auto_approve"]:
            return "conditional_approve"
        else:
            return "approve"
    
    def _score_to_risk_level(self, score: int) -> str:
        """Convert risk score to risk level."""
        if score >= 80:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"
    
    def _generate_conditions(self, state: RiskAnalysisState) -> List[Dict[str, Any]]:
        """Generate conditions based on analysis results."""
        conditions = []
        
        # Security conditions
        security_risks = state.get("change_summary", {}).get("security_risks", [])
        if security_risks:
            conditions.append({
                "condition": "Security review required",
                "required_actions": ["Security team approval", "Penetration testing"],
                "responsible_party": "security_team",
                "timeline": "48 hours"
            })
        
        # Testing conditions
        policy_validation = state.get("policy_validation", {})
        test_violations = [
            v for v in policy_validation.get("violations", [])
            if "test" in v.get("policy", "").lower()
        ]
        if test_violations:
            conditions.append({
                "condition": "Enhanced testing required",
                "required_actions": ["Increase test coverage", "Manual testing"],
                "responsible_party": "development_team",
                "timeline": "72 hours"
            })
        
        return conditions
    
    def _generate_default_conditions(self, state: RiskAnalysisState) -> List[Dict[str, Any]]:
        """Generate default conditions for conditional approvals."""
        return [{
            "condition": "Standard review process",
            "required_actions": ["Code review approval", "QA testing"],
            "responsible_party": "development_team",
            "timeline": "24 hours"
        }]
    
    async def _apply_analysis_result(self, state: RiskAnalysisState, result: Dict[str, Any]) -> RiskAnalysisState:
        """Apply decision results to the workflow state."""
        
        state["final_decision"] = {
            "decision": result["decision"],
            "confidence": result["confidence"],
            "risk_assessment": result["risk_assessment"],
            "rationale": result["rationale"],
            "conditions": result["conditions"],
            "escalation_triggers": result["escalation_triggers"],
            "monitoring_requirements": result["monitoring_requirements"],
            "rollback_plan": result["rollback_plan"],
            "stakeholder_communication": result["stakeholder_communication"],
            "quantitative_risk": result["quantitative_risk"],
            "analysis_method": result["analysis_method"],
            "timestamp": "2024-01-01T00:00:00Z"  # Would be actual timestamp
        }
        
        state["current_agent"] = self.agent_id
        state["confidence"] = min(state.get("confidence", 1.0), result["confidence"])
        
        return state
    
    def _get_required_result_fields(self) -> List[str]:
        """Required fields for validating LLM analysis result."""
        return [
            "decision", "confidence", "risk_assessment",
            "analysis_method", "llm_confidence"
        ]
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response that might contain extra text."""
        import re
        import json
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return minimal fallback structure
        return {
            "recommended_decision": "conditional_approve",
            "confidence_level": 0.3,
            "risk_assessment": {"overall_risk": "medium"},
            "decision_rationale": {"primary_concerns": ["Unable to parse LLM response"]}
        }
    
    # Additional helper methods for heuristic analysis
    def _identify_risk_factors(self, state: RiskAnalysisState) -> List[str]:
        """Identify key risk factors."""
        factors = []
        
        policy_validation = state.get("policy_validation", {})
        if policy_validation.get("violations"):
            factors.append("policy_violations")
        
        change_summary = state.get("change_summary", {})
        if change_summary.get("change_size") == "large":
            factors.append("large_change_scope")
        
        if change_summary.get("security_risks"):
            factors.append("security_implications")
        
        return factors
    
    def _suggest_mitigations(self, state: RiskAnalysisState) -> List[str]:
        """Suggest risk mitigation strategies."""
        mitigations = []
        
        # Standard mitigations
        mitigations.extend([
            "staged_rollout",
            "feature_flags",
            "enhanced_monitoring",
            "rollback_preparation"
        ])
        
        # Specific mitigations based on risks
        policy_validation = state.get("policy_validation", {})
        if any("security" in v.get("policy", "") for v in policy_validation.get("violations", [])):
            mitigations.append("security_scan")
        
        return mitigations
    
    def _identify_primary_concerns(self, state: RiskAnalysisState) -> List[str]:
        """Identify primary concerns."""
        concerns = []
        
        policy_validation = state.get("policy_validation", {})
        violations = policy_validation.get("violations", [])
        
        for violation in violations[:3]:  # Top 3 concerns
            concerns.append(f"{violation.get('policy', 'unknown')}: {violation.get('violation_type', 'unknown')}")
        
        return concerns
    
    def _calculate_risk_breakdown(self, state: RiskAnalysisState) -> Dict[str, int]:
        """Calculate detailed risk breakdown."""
        breakdown = {
            "technical_risk": 0,
            "security_risk": 0,
            "business_risk": 0,
            "operational_risk": 0
        }
        
        # Calculate based on violations and change characteristics
        policy_validation = state.get("policy_validation", {})
        violations = policy_validation.get("violations", [])
        
        for violation in violations:
            severity_score = {"low": 10, "medium": 25, "high": 50, "critical": 75}.get(
                violation.get("severity", "medium"), 25
            )
            
            if "security" in violation.get("policy", "").lower():
                breakdown["security_risk"] += severity_score
            elif "test" in violation.get("policy", "").lower():
                breakdown["technical_risk"] += severity_score
            else:
                breakdown["operational_risk"] += severity_score
        
        # Normalize to 0-100 scale
        for key in breakdown:
            breakdown[key] = min(100, breakdown[key])
        
        return breakdown
    
    def _identify_escalation_triggers(self, state: RiskAnalysisState) -> List[str]:
        """Identify escalation triggers."""
        triggers = []
        
        policy_validation = state.get("policy_validation", {})
        critical_violations = [
            v for v in policy_validation.get("violations", [])
            if v.get("severity") == "critical"
        ]
        
        if critical_violations:
            triggers.append("critical_security_violation")
        
        if len(state.get("pr_files", [])) > 50:
            triggers.append("massive_change_scope")
        
        return triggers
    
    def _generate_monitoring_requirements(self, state: RiskAnalysisState) -> List[str]:
        """Generate monitoring requirements."""
        requirements = ["standard_health_checks", "performance_monitoring"]
        
        change_summary = state.get("change_summary", {})
        if change_summary.get("security_risks"):
            requirements.append("security_monitoring")
        
        if change_summary.get("change_size") == "large":
            requirements.append("enhanced_alerting")
        
        return requirements
    
    def _assess_rollback_requirements(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Assess rollback plan requirements."""
        change_summary = state.get("change_summary", {})
        size = change_summary.get("change_size", "medium")
        
        if size == "large":
            return {
                "required": True,
                "complexity": "high",
                "strategy": "full_rollback_with_data_migration"
            }
        elif size == "medium":
            return {
                "required": True,
                "complexity": "medium", 
                "strategy": "feature_flag_rollback"
            }
        else:
            return {
                "required": False,
                "complexity": "low",
                "strategy": "quick_revert"
            }
    
    def _determine_stakeholder_communication(self, state: RiskAnalysisState) -> Dict[str, Any]:
        """Determine stakeholder communication requirements."""
        policy_validation = state.get("policy_validation", {})
        required_reviewers = policy_validation.get("required_reviewers", [])
        
        return {
            "required_notifications": required_reviewers,
            "key_messages": [
                "Change requires additional review",
                "Standard monitoring procedures apply"
            ]
        }
```
        
        # Step 1: Extract analysis results
        risk_score = state.get("risk_score", 0)
        policy_findings = state.get("policy_findings", {})
        change_summary = state.get("change_summary", {})
        
        # Step 2: Apply decision framework
        decision_result = await self._make_decision(
            risk_score, policy_findings, change_summary
        )
        
        # Step 3: Generate detailed rationale
        rationale = self._generate_rationale(
            decision_result, risk_score, policy_findings
        )
        
        # Step 4: Create recommendations
        recommendations = self._generate_recommendations(
            decision_result, policy_findings, change_summary
        )
        
        # Step 5: Determine escalation needs
        escalation = self._determine_escalation(
            decision_result, risk_score, policy_findings
        )
        
        # Step 6: Assemble final decision
        final_decision = {
            "go": decision_result["approved"],
            "risk_score": risk_score,
            "rationale": rationale,
            "confidence": decision_result["confidence"],
            "decision_factors": decision_result["factors"],
            "recommendations": recommendations,
            "escalation_required": escalation["required"],
            "escalation_reason": escalation["reason"],
            "review_required": decision_result.get("review_required", False)
        }
        
        state["decision"] = final_decision
        state["current_agent"] = self.agent_id
        state["confidence"] = decision_result["confidence"]
        
        return state
    
    async def _make_decision(
        self, 
        risk_score: int, 
        policy_findings: Dict[str, Any], 
        change_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Core decision-making algorithm with multiple decision paths.
        
        Decision Tree:
        1. Security Override Path
        2. Risk-Based Decision Path
        3. Context-Aware Adjustments
        4. Confidence Calculation
        """
        
        # Security Override Decision Path
        security_findings = policy_findings.get("security_analysis", {})
        if security_findings.get("detected_secrets") or risk_score >= 100:
            return {
                "approved": False,
                "confidence": 1.0,
                "factors": ["security_override"],
                "review_required": True,
                "decision_path": "security_override"
            }
        
        # High-Risk Decision Path
        if risk_score >= self.decision_thresholds["auto_reject"]:
            return {
                "approved": False,
                "confidence": 0.95,
                "factors": ["high_risk_score"],
                "review_required": True,
                "decision_path": "high_risk_rejection"
            }
        
        # Conditional Approval Path
        if risk_score >= self.decision_thresholds["conditional_approve"]:
            # Check for mitigating factors
            mitigating_factors = self._identify_mitigating_factors(
                policy_findings, change_summary
            )
            
            if mitigating_factors:
                return {
                    "approved": True,
                    "confidence": 0.7,
                    "factors": ["conditional_approval", "mitigating_factors"],
                    "review_required": True,
                    "decision_path": "conditional_approval",
                    "mitigating_factors": mitigating_factors
                }
            else:
                return {
                    "approved": False,
                    "confidence": 0.85,
                    "factors": ["medium_risk", "no_mitigation"],
                    "review_required": True,
                    "decision_path": "medium_risk_rejection"
                }
        
        # Low-Risk Approval Path
        if risk_score <= self.decision_thresholds["auto_approve"]:
            return {
                "approved": True,
                "confidence": 0.9,
                "factors": ["low_risk"],
                "review_required": False,
                "decision_path": "auto_approval"
            }
        
        # Default Medium-Risk Path
        return {
            "approved": True,
            "confidence": 0.75,
            "factors": ["medium_risk", "standard_review"],
            "review_required": True,
            "decision_path": "standard_approval"
        }
    
    def _identify_mitigating_factors(
        self, 
        policy_findings: Dict[str, Any], 
        change_summary: Dict[str, Any]
    ) -> List[str]:
        """
        Identify factors that mitigate identified risks.
        
        Mitigating Factors:
        - Comprehensive test coverage
        - Clear documentation
        - Gradual rollout plan
        - Rollback procedures
        - Staging validation
        """
        mitigating_factors = []
        
        # Test coverage mitigation
        test_analysis = policy_findings.get("test_analysis", {})
        if test_analysis.get("test_ratio", 0) > 0.5:
            mitigating_factors.append("comprehensive_test_coverage")
        
        # Documentation mitigation
        semantic_analysis = change_summary.get("semantic_analysis", {})
        if "docs" in semantic_analysis.get("categories", []):
            mitigating_factors.append("documented_changes")
        
        # Change size mitigation
        if change_summary.get("change_metrics", {}).get("size_category") == "small":
            mitigating_factors.append("limited_scope")
        
        # Gradual deployment indicators
        if any(keyword in change_summary.get("semantic_analysis", {}).get("categories", []) 
               for keyword in ["feature", "config"]):
            mitigating_factors.append("gradual_deployment_possible")
        
        return mitigating_factors
    
    def _generate_rationale(
        self, 
        decision_result: Dict[str, Any], 
        risk_score: int, 
        policy_findings: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable decision rationale.
        
        Rationale Components:
        1. Primary decision reason
        2. Risk factor summary
        3. Mitigating factors (if any)
        4. Confidence explanation
        """
        decision_path = decision_result["decision_path"]
        approved = decision_result["approved"]
        
        rationale_templates = {
            "security_override": (
                f"Automatic No-Go due to critical security concerns. "
                f"Potential secret exposure or security vulnerability detected "
                f"(Risk Score: {risk_score}/100). Immediate security review required."
            ),
            "high_risk_rejection": (
                f"No-Go decision due to high risk score ({risk_score}/100). "
                f"Multiple risk factors identified requiring comprehensive review "
                f"and risk mitigation before deployment."
            ),
            "conditional_approval": (
                f"Conditional Go with elevated risk ({risk_score}/100). "
                f"Approved based on identified mitigating factors: "
                f"{', '.join(decision_result.get('mitigating_factors', []))}. "
                f"Enhanced monitoring and staged deployment recommended."
            ),
            "medium_risk_rejection": (
                f"No-Go decision for medium-risk changes ({risk_score}/100). "
                f"Risk mitigation measures not sufficient. Additional review "
                f"and risk reduction measures required before approval."
            ),
            "auto_approval": (
                f"Go decision with low risk profile ({risk_score}/100). "
                f"Standard deployment procedures apply. Change falls within "
                f"acceptable risk parameters for automated approval."
            ),
            "standard_approval": (
                f"Go decision with standard review required ({risk_score}/100). "
                f"Medium-risk change requiring stakeholder approval and "
                f"standard risk mitigation procedures."
            )
        }
        
        return rationale_templates.get(decision_path, f"Decision: {'Go' if approved else 'No-Go'} with risk score {risk_score}/100")
    
    def _generate_recommendations(
        self, 
        decision_result: Dict[str, Any], 
        policy_findings: Dict[str, Any], 
        change_summary: Dict[str, Any]
    ) -> List[str]:
        """
        Generate specific, actionable recommendations.
        
        Recommendation Categories:
        1. Risk Mitigation Actions
        2. Process Improvements
        3. Technical Enhancements
        4. Monitoring and Validation
        """
        recommendations = []
        approved = decision_result["approved"]
        
        # Security-related recommendations
        security_analysis = policy_findings.get("security_analysis", {})
        if security_analysis.get("detected_secrets"):
            recommendations.extend([
                "Remove all hardcoded secrets from code and commit history",
                "Implement secure secret management (e.g., Azure Key Vault, AWS Secrets Manager)",
                "Conduct security audit of entire codebase",
                "Implement pre-commit hooks for secret detection"
            ])
        
        # Test coverage recommendations
        test_analysis = policy_findings.get("test_analysis", {})
        if test_analysis.get("missing_tests"):
            recommendations.extend([
                "Add comprehensive unit tests for all new functionality",
                "Implement integration tests for API changes",
                "Add end-to-end tests for critical user workflows",
                f"Achieve minimum {80}% test coverage before deployment"
            ])
        
        # Architecture recommendations
        arch_analysis = policy_findings.get("architecture_analysis", {})
        if arch_analysis.get("risky_modules"):
            recommendations.extend([
                "Conduct additional security review for critical component changes",
                "Implement gradual rollout strategy for sensitive modules",
                "Prepare comprehensive rollback procedures",
                "Schedule post-deployment monitoring and validation"
            ])
        
        # Process recommendations based on decision
        if approved:
            if decision_result.get("review_required"):
                recommendations.extend([
                    "Obtain stakeholder approval before deployment",
                    "Conduct peer code review with security focus",
                    "Validate changes in staging environment",
                    "Prepare deployment monitoring and alerting"
                ])
            else:
                recommendations.extend([
                    "Follow standard deployment procedures",
                    "Monitor key performance indicators post-deployment"
                ])
        else:
            recommendations.extend([
                "Address all identified risk factors before resubmission",
                "Conduct risk assessment review with stakeholders",
                "Implement recommended mitigation strategies",
                "Consider breaking changes into smaller, lower-risk deployments"
            ])
        
        return recommendations
    
    def _determine_escalation(
        self, 
        decision_result: Dict[str, Any], 
        risk_score: int, 
        policy_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if escalation to human reviewers is required.
        
        Escalation Triggers:
        - Security concerns
        - High-risk decisions
        - Policy violations
        - Low confidence scores
        - Stakeholder impact
        """
        escalation_required = False
        escalation_reasons = []
        
        # Security escalation
        if policy_findings.get("security_analysis", {}).get("detected_secrets"):
            escalation_required = True
            escalation_reasons.append("security_vulnerability")
        
        # High-risk escalation
        if risk_score >= 70:
            escalation_required = True
            escalation_reasons.append("high_risk_score")
        
        # Low confidence escalation
        if decision_result["confidence"] < 0.7:
            escalation_required = True
            escalation_reasons.append("low_confidence")
        
        # Critical module escalation
        arch_analysis = policy_findings.get("architecture_analysis", {})
        if len(arch_analysis.get("risky_modules", [])) > 2:
            escalation_required = True
            escalation_reasons.append("critical_module_impact")
        
        return {
            "required": escalation_required,
            "reason": ", ".join(escalation_reasons) if escalation_reasons else None,
            "escalation_level": "security" if "security_vulnerability" in escalation_reasons else "standard",
            "recommended_reviewers": self._get_recommended_reviewers(escalation_reasons)
        }
    
    def _get_recommended_reviewers(self, escalation_reasons: List[str]) -> List[str]:
        """Map escalation reasons to appropriate reviewer types."""
        reviewers = []
        
        if "security_vulnerability" in escalation_reasons:
            reviewers.append("security_team")
        if "high_risk_score" in escalation_reasons:
            reviewers.append("senior_engineer")
        if "critical_module_impact" in escalation_reasons:
            reviewers.append("architecture_team")
        
        return reviewers or ["standard_reviewer"]
    
    def get_confidence_score(self, state: RiskAnalysisState) -> float:
        """Calculate decision confidence based on analysis quality and clarity."""
        decision = state.get("decision", {})
        return decision.get("confidence", 0.8)
```

This comprehensive agent specification provides detailed implementation guidance for each component of the Release Risk Analyzer system, ensuring robust, scalable, and maintainable risk assessment capabilities.