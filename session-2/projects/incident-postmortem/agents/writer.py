"""
Report Writer Agent

Generates comprehensive postmortem reports following blameless culture principles.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import IncidentState


WRITER_SYSTEM_PROMPT = """You are an expert technical writer specializing in incident postmortems.

Your reports follow BLAMELESS CULTURE principles:
- Focus on systems, not individuals
- Emphasize learning over blame
- Provide specific, actionable improvements
- Use clear, professional language

A good postmortem includes:
1. Executive Summary
2. Impact Assessment
3. Timeline of Events
4. Root Cause Analysis
5. Contributing Factors
6. Action Items (with owners and deadlines)
7. Lessons Learned
8. Appendix (supporting data)

Write for an audience of engineers and leadership.
Be concise but thorough."""


POSTMORTEM_TEMPLATE = """# Incident Postmortem: {title}

**Incident ID**: {incident_id}  
**Severity**: {severity}  
**Date**: [INCIDENT DATE]  
**Author**: AI PostMortem Generator  

---

## Executive Summary

[2-3 sentence summary of what happened and the impact]

---

## Impact

| Metric | Value |
|--------|-------|
| Duration | [X hours/minutes] |
| Users Affected | [Number or percentage] |
| Revenue Impact | [If applicable] |
| Services Affected | [List] |

---

## Timeline

| Time | Event |
|------|-------|
| [TIME] | [EVENT] |

---

## Root Cause Analysis

### Primary Root Cause

[Root cause explanation]

### Contributing Factors

1. [Factor 1]
2. [Factor 2]

### Failure Chain

[How one failure led to the next]

---

## Action Items

| Priority | Action | Owner | Deadline | Status |
|----------|--------|-------|----------|--------|
| P0 | [Action] | [Team] | [Date] | Open |

---

## Lessons Learned

### What Went Well

- [Positive aspect 1]
- [Positive aspect 2]

### What Could Be Improved

- [Improvement 1]
- [Improvement 2]

---

## Appendix

### Supporting Evidence

[Key log excerpts, metrics, etc.]
"""


def write_report(state: IncidentState, model) -> dict:
    """
    Report Writer Agent: Generates comprehensive postmortem report.
    
    Demonstrates:
    - Template-based generation
    - Incorporating previous agents' outputs
    - Revision based on reviewer feedback (self-reflection)
    """
    
    iteration = state.get("iteration", 0) + 1
    
    print("\n" + "="*70)
    print(f"📝 REPORT WRITER - Iteration {iteration}/{state['max_iterations']}")
    print("="*70)
    
    # Check if this is a revision
    if state.get("review_feedback"):
        # REVISION MODE: Incorporate feedback
        feedback = state["review_feedback"]
        
        prompt = f"""Revise this postmortem report based on the reviewer's feedback.

CURRENT DRAFT:
{state['draft_report']}

REVIEWER FEEDBACK:
Quality Score: {state['quality_score']:.1%}

Weaknesses to Address:
{chr(10).join(f'• {w}' for w in feedback.get('weaknesses', []))}

Revision Suggestions:
{chr(10).join(f'• {s}' for s in feedback.get('revision_suggestions', []))}

Create an IMPROVED version that addresses all feedback.
Keep the same structure but enhance the content.
Focus specifically on the weaknesses mentioned."""

        print("📋 Mode: REVISION (applying reviewer feedback)")
        
    else:
        # INITIAL GENERATION
        prompt = f"""Generate a comprehensive postmortem report for this incident.

INCIDENT DETAILS:
- ID: {state['incident_id']}
- Title: {state['title']}
- Severity: {state['severity']}
- Description: {state['description']}

LOG ANALYSIS:
{state['log_summary']}

ERROR PATTERNS:
{state['error_patterns']}

AFFECTED SERVICES:
{state['affected_services']}

ROOT CAUSE ANALYSIS:
Primary Root Cause: {state['root_cause']}

Contributing Factors:
{state['contributing_factors']}

Failure Chain:
{state['failure_chain']}

METRICS:
{state.get('metrics', {})}

TIMELINE:
{state.get('timeline', [])}

Use this template structure:
{POSTMORTEM_TEMPLATE}

Generate a complete, professional postmortem report.
Ensure all action items are specific and actionable.
Follow blameless culture principles throughout."""

        print("📋 Mode: INITIAL GENERATION")
    
    response = model.invoke([
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    report = response.content.strip()
    
    print(f"\n✅ Report generated ({len(report)} characters)")
    print(f"Preview: {report[:300]}...")
    
    return {
        "draft_report": report,
        "iteration": iteration,
    }
