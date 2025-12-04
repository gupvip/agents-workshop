"""
Report Reviewer Agent (LLM-as-Judge)

Evaluates postmortem report quality using structured rubric.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import IncidentState, ReportReview


REVIEWER_SYSTEM_PROMPT = """You are a senior SRE manager reviewing incident postmortems.

Your evaluation criteria:

1. COMPLETENESS (1-10): Does the report cover all required sections?
   - Executive summary, impact, timeline, root cause, action items, lessons

2. CLARITY (1-10): Is the writing clear and understandable?
   - Can a new team member understand what happened?
   - Are technical terms explained?

3. ACCURACY (1-10): Does the root cause analysis seem accurate?
   - Is there evidence supporting the conclusions?
   - Does the failure chain make logical sense?

4. ACTIONABILITY (1-10): Are action items specific?
   - Do they have clear owners?
   - Are deadlines realistic?
   - Would they prevent recurrence?

5. BLAMELESSNESS (1-10): Does it follow blameless culture?
   - Focus on systems, not people?
   - Learning-oriented language?
   - No finger-pointing?

Set approved=True ONLY if overall quality is >= 7/10 and no critical gaps exist."""


def review_report(state: IncidentState, model) -> dict:
    """
    Report Reviewer Agent: LLM-as-Judge evaluation.
    
    Demonstrates:
    - LLM-as-Judge pattern with structured rubric
    - Multi-dimension scoring
    - Quality gate decision making
    """
    
    print("\n" + "="*70)
    print("🔍 REVIEWER (LLM-as-Judge) - Evaluating Report")
    print("="*70)
    
    # Create structured output model (use function_calling for Azure/DIAL compatibility)
    reviewer = model.with_structured_output(ReportReview, method="function_calling")
    
    prompt = f"""Evaluate this incident postmortem report.

INCIDENT CONTEXT:
- Title: {state['title']}
- Severity: {state['severity']}
- Root Cause (expected): {state['root_cause']}

REPORT TO REVIEW:
{state['draft_report']}

Evaluate against these criteria:
1. Completeness (1-10): All required sections covered?
2. Clarity (1-10): Clear and understandable writing?
3. Accuracy (1-10): Root cause analysis seems accurate?
4. Actionability (1-10): Specific, actionable items with owners?
5. Blamelessness (1-10): Follows blameless culture?
6. Overall (1-10): Overall quality

Provide:
- 2-3 strengths
- 2-3 weaknesses
- 2-3 specific revision suggestions
- approved: True if overall >= 7 and no critical gaps"""

    result = reviewer.invoke([
        SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    # Calculate normalized quality score
    scores = [
        result.completeness_score,
        result.clarity_score,
        result.accuracy_score,
        result.actionability_score,
        result.blamelessness_score,
        result.overall_score,
    ]
    quality_score = sum(scores) / (len(scores) * 10)
    
    # Build feedback dict
    feedback = {
        "completeness_score": result.completeness_score,
        "clarity_score": result.clarity_score,
        "accuracy_score": result.accuracy_score,
        "actionability_score": result.actionability_score,
        "blamelessness_score": result.blamelessness_score,
        "overall_score": result.overall_score,
        "strengths": result.strengths,
        "weaknesses": result.weaknesses,
        "revision_suggestions": result.revision_suggestions,
        "approved": result.approved,
    }
    
    # Print evaluation
    print(f"\n📊 QUALITY SCORES:")
    print(f"   Completeness:   {result.completeness_score}/10")
    print(f"   Clarity:        {result.clarity_score}/10")
    print(f"   Accuracy:       {result.accuracy_score}/10")
    print(f"   Actionability:  {result.actionability_score}/10")
    print(f"   Blamelessness:  {result.blamelessness_score}/10")
    print(f"   Overall:        {result.overall_score}/10")
    
    print(f"\n🎯 QUALITY SCORE: {quality_score:.1%}")
    print(f"   Threshold: {state['quality_threshold']:.1%}")
    print(f"   Approved: {'✅ YES' if result.approved else '❌ NO'}")
    
    print(f"\n✨ STRENGTHS:")
    for s in result.strengths:
        print(f"   • {s}")
    
    print(f"\n⚠️  WEAKNESSES:")
    for w in result.weaknesses:
        print(f"   • {w}")
    
    # Track revision history
    history_entry = {
        "iteration": state["iteration"],
        "quality_score": quality_score,
        "approved": result.approved,
        "overall_score": result.overall_score,
    }
    
    return {
        "review_feedback": feedback,
        "quality_score": quality_score,
        "revision_history": [history_entry],
    }
