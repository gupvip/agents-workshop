"""
Log Analyzer Agent

Parses and summarizes incident logs to extract key patterns and affected services.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import IncidentState, LogAnalysis


LOG_ANALYZER_SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) specializing in log analysis.

Your role is to analyze incident logs and extract:
1. A clear summary of what the logs reveal
2. Distinct error patterns (not just individual errors)
3. Services that were affected
4. Critical timestamps and events
5. Evidence of incident severity

Be thorough but concise. Focus on patterns, not individual log lines.
Use technical language appropriate for engineering postmortems.

IMPORTANT: Look for the chain of events, not just symptoms."""


def analyze_logs(state: IncidentState, model) -> dict:
    """
    Log Analyzer Agent: Parses and summarizes incident logs.
    
    Demonstrates:
    - Structured output with Pydantic (LogAnalysis)
    - COMPRESS pillar: Summarizing verbose logs
    """
    
    print("\n" + "="*70)
    print("📊 LOG ANALYZER - Parsing Incident Logs")
    print("="*70)
    
    # Create structured output model (use function_calling for Azure/DIAL compatibility)
    analyzer = model.with_structured_output(LogAnalysis, method="function_calling")
    
    prompt = f"""Analyze the following incident logs and extract key information.

INCIDENT: {state['title']}
SEVERITY: {state['severity']}
DESCRIPTION: {state['description']}

RAW LOGS:
{state['raw_logs']}

TIMELINE EVENTS:
{state.get('timeline', [])}

METRICS:
{state.get('metrics', {})}

Provide a comprehensive analysis focusing on:
1. What happened based on the logs
2. Error patterns (group similar errors)
3. Which services were affected
4. Key timestamps of important events
5. Evidence that supports the severity level"""

    result = analyzer.invoke([
        SystemMessage(content=LOG_ANALYZER_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    # Print summary
    print(f"\n📋 Log Summary:")
    print(f"   {result.summary[:200]}...")
    print(f"\n🔴 Error Patterns ({len(result.error_patterns)}):")
    for pattern in result.error_patterns:
        print(f"   • {pattern}")
    print(f"\n🖥️  Affected Services ({len(result.affected_services)}):")
    for service in result.affected_services:
        print(f"   • {service}")
    
    return {
        "log_summary": result.summary,
        "error_patterns": result.error_patterns,
        "affected_services": result.affected_services,
    }
