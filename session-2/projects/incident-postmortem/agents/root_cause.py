"""
Root Cause Analyzer Agent

Identifies the root cause and contributing factors using 5-whys analysis.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import IncidentState, RootCauseAnalysis


ROOT_CAUSE_SYSTEM_PROMPT = """You are an expert incident analyst specializing in root cause analysis.

Your role is to identify:
1. The PRIMARY root cause (the thing that, if fixed, would prevent recurrence)
2. Contributing factors (secondary issues that made things worse)
3. The failure chain (how one failure led to the next)
4. Supporting evidence from logs

Use the 5-WHYS technique:
- Start with the symptom
- Ask "Why did this happen?" repeatedly
- Stop when you reach a systemic or process issue

IMPORTANT: 
- Focus on systems and processes, not people
- Look for actionable root causes
- Distinguish between immediate triggers and underlying causes"""


def analyze_root_cause(state: IncidentState, model) -> dict:
    """
    Root Cause Analyzer Agent: Identifies failure chain and root cause.
    
    Demonstrates:
    - Chain-of-thought reasoning (5-whys)
    - Structured output with Pydantic (RootCauseAnalysis)
    - Building on previous agent's output (log_summary)
    """
    
    print("\n" + "="*70)
    print("🔍 ROOT CAUSE ANALYZER - Identifying Failure Chain")
    print("="*70)
    
    # Create structured output model (use function_calling for Azure/DIAL compatibility)
    analyzer = model.with_structured_output(RootCauseAnalysis, method="function_calling")
    
    prompt = f"""Perform root cause analysis for this incident.

INCIDENT: {state['title']}
SEVERITY: {state['severity']}

LOG ANALYSIS SUMMARY:
{state['log_summary']}

ERROR PATTERNS IDENTIFIED:
{state['error_patterns']}

AFFECTED SERVICES:
{state['affected_services']}

ORIGINAL DESCRIPTION:
{state['description']}

Using the 5-WHYS technique, identify:
1. The primary root cause
2. Contributing factors
3. The failure chain (sequence of failures)
4. Evidence from logs
5. Your 5-whys reasoning steps

Remember: Focus on systems and processes, not individuals. 
The root cause should be actionable and preventable."""

    result = analyzer.invoke([
        SystemMessage(content=ROOT_CAUSE_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    # Print analysis
    print(f"\n🎯 ROOT CAUSE:")
    print(f"   {result.root_cause}")
    
    print(f"\n📋 CONTRIBUTING FACTORS ({len(result.contributing_factors)}):")
    for factor in result.contributing_factors:
        print(f"   • {factor}")
    
    print(f"\n🔗 FAILURE CHAIN:")
    for i, step in enumerate(result.failure_chain, 1):
        print(f"   {i}. {step}")
    
    print(f"\n❓ 5-WHYS ANALYSIS:")
    for i, why in enumerate(result.five_whys, 1):
        print(f"   Why {i}: {why}")
    
    return {
        "root_cause": result.root_cause,
        "contributing_factors": result.contributing_factors,
        "failure_chain": result.failure_chain,
    }
