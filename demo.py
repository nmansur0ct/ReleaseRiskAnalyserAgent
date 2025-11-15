"""
Release Risk Analyzer - Main Demo

This script demonstrates the LangGraph-based Release Risk Analyzer
with advanced workflow orchestration using Pydantic and LangGraph.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from demo_workflow import demo_langgraph_analyzer

async def main():
    """Main demo function."""
    print("🎯 Release Risk Analyzer - LangGraph Implementation")
    print("=" * 60)
    print("Demonstrating advanced agentic workflow with:")
    print("• State management across agents")
    print("• Conditional routing based on confidence")
    print("• Pydantic models for type safety")
    print("• LangGraph orchestration")
    print()
    
    await demo_langgraph_analyzer()

if __name__ == "__main__":
    asyncio.run(main())