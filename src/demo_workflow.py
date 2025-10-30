"""
LangGraph Demo Implementation for Release Risk Analyzer.

This is a working demonstration of how to implement the Release Risk Analyzer
using LangGraph for agent orchestration. It showcases key concepts like
state management, conditional routing, and agent coordination.
"""

from typing import Dict, Any, Literal, TypedDict, List
from datetime import datetime
import asyncio
import json

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Fallback types for demonstration
    class StateGraph:
        def __init__(self, state_type): pass
        def add_node(self, name, func): pass
        def add_edge(self, from_node, to_node): pass
        def add_conditional_edges(self, from_node, condition, mapping): pass
        def set_entry_point(self, node): pass
        def compile(self, **kwargs): return self
        async def ainvoke(self, state): return state
    
    END = "END"

from pydantic import BaseModel
from typing import Optional

# Simplified state for LangGraph demo
class RiskAnalysisState(TypedDict):
    """State object that flows through the LangGraph workflow."""
    # Input
    pr_title: str
    pr_body: str
    pr_files: List[str]
    
    # Intermediate results
    change_summary: Optional[Dict[str, Any]]
    policy_findings: Optional[Dict[str, Any]]
    risk_score: Optional[int]
    
    # Final output
    decision: Optional[Dict[str, Any]]
    
    # Workflow metadata
    current_agent: str
    confidence: float
    errors: List[str]
    processing_time: float

class SimplePRInput(BaseModel):
    """Simple PR input for demo."""
    title: str
    body: str
    files: List[str] = []

class LangGraphRiskAnalyzer:
    """Demo implementation using LangGraph for agent orchestration."""
    
    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            print("⚠️  LangGraph not available. Install with: pip install langgraph")
            return
        
        self.graph = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(RiskAnalysisState)
        
        # Add agent nodes
        workflow.add_node("summarizer", self._summarizer_agent)
        workflow.add_node("validator", self._validator_agent)
        workflow.add_node("decision_maker", self._decision_agent)
        workflow.add_node("quality_check", self._quality_agent)
        
        # Set entry point
        workflow.set_entry_point("summarizer")
        
        # Define workflow edges
        workflow.add_edge("summarizer", "validator")
        workflow.add_edge("validator", "decision_maker")
        
        # Conditional routing based on confidence
        workflow.add_conditional_edges(
            "decision_maker",
            self._confidence_router,
            {
                "high_confidence": END,
                "low_confidence": "quality_check",
                "retry": "summarizer"
            }
        )
        
        workflow.add_edge("quality_check", END)
        
        # Compile without checkpointer for simplicity
        return workflow.compile()
    
    async def _summarizer_agent(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Agent that summarizes PR changes."""
        print(f"🔍 Summarizer Agent processing: {state['pr_title']}")
        
        # Extract modules from file paths
        modules = []
        for file_path in state["pr_files"]:
            if "/" in file_path:
                module = file_path.split("/")[0] + "/"
                if module not in modules:
                    modules.append(module)
        
        # Determine change size
        file_count = len(state["pr_files"])
        if file_count < 3:
            change_size = "small"
        elif file_count < 10:
            change_size = "medium"
        else:
            change_size = "large"
        
        # Generate risk notes
        risk_notes = []
        body_lower = state["pr_body"].lower()
        
        if any(keyword in body_lower for keyword in ["auth", "security", "payment"]):
            risk_notes.append("touches sensitive modules")
        
        if any(keyword in body_lower for keyword in ["api", "protocol", "breaking"]):
            risk_notes.append("potential API changes")
        
        # Update state
        state["change_summary"] = {
            "highlights": [state["pr_title"]],
            "modules_touched": modules,
            "risk_notes": risk_notes,
            "change_size": change_size
        }
        state["current_agent"] = "summarizer"
        state["confidence"] = 0.8
        
        await asyncio.sleep(0.1)  # Simulate processing time
        return state
    
    async def _validator_agent(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Agent that validates policies and calculates risk."""
        print("⚙️ Validator Agent checking policies...")
        
        # Check for missing tests
        has_tests = any("test" in file.lower() for file in state["pr_files"])
        has_source = any(
            file.endswith(('.py', '.js', '.ts', '.java')) 
            for file in state["pr_files"]
        )
        missing_tests = has_source and not has_tests
        
        # Check for secrets
        combined_text = f"{state['pr_title']} {state['pr_body']}".lower()
        secret_patterns = ["api_key", "secret", "password", "-----begin", "sk_test", "sk_live"]
        secret_detected = any(pattern in combined_text for pattern in secret_patterns)
        
        # Check risky modules
        summary = state["change_summary"]
        risky_modules = []
        if summary:
            for module in summary.get("modules_touched", []):
                if any(risky in module.lower() for risky in ["auth", "payment", "gateway"]):
                    risky_modules.append(module)
        
        # Calculate risk score
        risk_score = 0
        if missing_tests:
            risk_score += 30
        if secret_detected:
            risk_score = 100  # Auto max risk
        if risky_modules:
            risk_score += 20
        if summary and summary.get("change_size") == "large":
            risk_score += 20
        
        # Conditional bumps
        if missing_tests and risky_modules:
            risk_score += 15
        
        risk_score = min(risk_score, 100)
        
        # Update state
        state["policy_findings"] = {
            "missing_tests": missing_tests,
            "secret_detected": secret_detected,
            "risky_modules": risky_modules,
            "policy_violations": []
        }
        
        if missing_tests:
            state["policy_findings"]["policy_violations"].append("missing_tests")
        if secret_detected:
            state["policy_findings"]["policy_violations"].append("secret_exposure")
        
        state["risk_score"] = risk_score
        state["current_agent"] = "validator"
        state["confidence"] = 0.9 if not secret_detected else 1.0
        
        await asyncio.sleep(0.1)  # Simulate processing time
        return state
    
    async def _decision_agent(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Agent that makes final Go/No-Go decision."""
        print("🧑‍💼 Decision Agent making final decision...")
        
        risk_score = state["risk_score"] or 0
        findings = state["policy_findings"] or {}
        
        # Decision logic
        if findings.get("secret_detected"):
            go_decision = False
            rationale = "Automatic No-Go due to potential secret exposure"
            confidence = 1.0
        elif risk_score >= 50:  # Using strict threshold
            go_decision = False
            rationale = f"No-Go decision due to high risk score ({risk_score}/100)"
            confidence = 0.9
        else:
            go_decision = True
            rationale = f"Go decision with acceptable risk level ({risk_score}/100)"
            confidence = 0.8
        
        # Update state
        state["decision"] = {
            "go": go_decision,
            "risk_score": risk_score,
            "rationale": rationale,
            "confidence": confidence
        }
        state["current_agent"] = "decision_maker"
        state["confidence"] = confidence
        
        await asyncio.sleep(0.1)  # Simulate processing time
        return state
    
    async def _quality_agent(self, state: RiskAnalysisState) -> RiskAnalysisState:
        """Agent that performs quality assurance."""
        print("🔧 Quality Agent performing final checks...")
        
        # Basic quality checks
        quality_issues = []
        
        if not state.get("change_summary"):
            quality_issues.append("Missing change summary")
        if not state.get("policy_findings"):
            quality_issues.append("Missing policy findings")
        if not state.get("decision"):
            quality_issues.append("Missing decision")
        
        # Update confidence based on quality
        if quality_issues:
            state["confidence"] = max(0.3, state["confidence"] - len(quality_issues) * 0.1)
            state["errors"].extend(quality_issues)
        
        state["current_agent"] = "quality_check"
        await asyncio.sleep(0.1)  # Simulate processing time
        return state
    
    def _confidence_router(self, state: RiskAnalysisState) -> str:
        """Route based on confidence level."""
        confidence = state.get("confidence", 0.0)
        retry_count = len([e for e in state.get("errors", []) if "retry" in e])
        
        if confidence >= 0.8:
            return "high_confidence"
        elif confidence >= 0.5 and retry_count < 2:
            return "low_confidence"
        elif retry_count < 3:
            state["errors"].append("retry_attempt")
            return "retry"
        else:
            return "high_confidence"  # Give up and proceed
    
    async def analyze_pr(self, pr_input: SimplePRInput) -> Dict[str, Any]:
        """Analyze a PR using the LangGraph workflow."""
        if not LANGGRAPH_AVAILABLE:
            return {"error": "LangGraph not available"}
        
        start_time = datetime.now()
        
        # Create initial state
        initial_state: RiskAnalysisState = {
            "pr_title": pr_input.title,
            "pr_body": pr_input.body,
            "pr_files": pr_input.files,
            "change_summary": None,
            "policy_findings": None,
            "risk_score": None,
            "decision": None,
            "current_agent": "starting",
            "confidence": 0.0,
            "errors": [],
            "processing_time": 0.0
        }
        
        try:
            # Execute the workflow
            print(f"🚀 Starting LangGraph workflow for: {pr_input.title}")
            final_state = await self.graph.ainvoke(initial_state)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            final_state["processing_time"] = processing_time
            
            print(f"✅ Workflow completed in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "processing_time": processing_time,
                "summary": final_state.get("change_summary"),
                "policy_findings": final_state.get("policy_findings"),
                "decision": final_state.get("decision"),
                "confidence": final_state.get("confidence"),
                "errors": final_state.get("errors", [])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }

# Demo function
async def demo_langgraph_analyzer():
    """Demonstrate the LangGraph-based analyzer."""
    print("🎯 LangGraph Release Risk Analyzer Demo")
    print("=" * 50)
    
    analyzer = LangGraphRiskAnalyzer()
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph not available. Please install:")
        print("   pip install langgraph langchain")
        return
    
    # Sample PRs from the specification
    sample_prs = [
        SimplePRInput(
            title="Improve product search ranking for typos",
            body="Adjust tokenization and add synonyms. Docs updated.",
            files=["search/ranker.py", "tests/test_ranker.py", "docs/search.md"]
        ),
        SimplePRInput(
            title="Add payment retries in gateway", 
            body="Introduce idempotency keys for retries. Will add tests later.",
            files=["gateway/router.ts", "payments/processor.ts"]
        ),
        SimplePRInput(
            title="Update API keys for staging",
            body="New API key: sk_test_123456789. Temporary for testing.",
            files=["config/staging.env"]
        )
    ]
    
    for i, pr in enumerate(sample_prs, 1):
        print(f"\n📋 Analyzing PR {i}: {pr.title}")
        print("-" * 40)
        
        result = await analyzer.analyze_pr(pr)
        
        if result["status"] == "success":
            decision = result.get("decision", {})
            status = "✅ GO" if decision.get("go") else "❌ NO-GO"
            risk_score = decision.get("risk_score", 0)
            
            print(f"Result: {status} (Risk: {risk_score}/100)")
            print(f"Rationale: {decision.get('rationale', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 0):.2f}")
            print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
            
            if result.get("errors"):
                print(f"Warnings: {', '.join(result['errors'])}")
        else:
            print(f"❌ Error: {result.get('error')}")
    
    print(f"\n🎉 Demo completed!")
    print(f"💡 This demonstrates key LangGraph concepts:")
    print(f"   • State management across agents")
    print(f"   • Conditional routing based on confidence") 
    print(f"   • Sequential agent execution")
    print(f"   • Error handling and retry logic")

if __name__ == "__main__":
    asyncio.run(demo_langgraph_analyzer())