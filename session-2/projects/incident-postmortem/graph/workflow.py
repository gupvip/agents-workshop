"""
LangGraph Workflow for Incident PostMortem Generation.

Demonstrates:
- Multi-agent collaboration
- Self-reflection (Writer → Reviewer loop)
- Quality gates
- HITL for high-severity incidents
- Latest LangGraph v1 features (Command API, modern interrupts)
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from graph.state import IncidentState
from agents import analyze_logs, analyze_root_cause, write_report, review_report
from config import config


def create_postmortem_graph(model, enable_hitl: bool = True):
    """
    Create the incident postmortem workflow graph.
    
    Architecture:
    START → log_analyzer → root_cause → writer ⟷ reviewer → finalize → END
                                           ↑_________|
                                        (self-reflection loop)
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # NODE WRAPPERS (inject model dependency)
    # ═══════════════════════════════════════════════════════════════════════
    
    def log_analyzer_node(state: IncidentState) -> dict:
        """Log Analyzer Agent node."""
        return analyze_logs(state, model)
    
    def root_cause_node(state: IncidentState) -> dict:
        """Root Cause Analyzer Agent node."""
        return analyze_root_cause(state, model)
    
    def writer_node(state: IncidentState) -> dict:
        """Report Writer Agent node."""
        return write_report(state, model)
    
    def reviewer_node(state: IncidentState) -> dict:
        """Report Reviewer Agent (LLM-as-Judge) node."""
        return review_report(state, model)
    
    def human_review_node(state: IncidentState) -> dict:
        """
        Human-in-the-loop review for high-severity incidents.
        
        Uses interrupt() for HITL - the workflow pauses here
        until a human provides approval via Command(resume=...).
        """
        print("\n" + "="*70)
        print("⚠️  HUMAN REVIEW REQUIRED (SEV1 Incident)")
        print("="*70)
        print(f"\nIncident: {state['title']}")
        print(f"Severity: {state['severity']}")
        print(f"Quality Score: {state.get('quality_score', 0):.1%}")
        print("\nDraft report ready for review.")
        print("To resume: provide {'approved': True/False, 'feedback': '...'}")
        
        # Interrupt with report for human review
        # When resumed with Command(resume=...), the value becomes the return value
        human_decision = interrupt({
            "incident_id": state["incident_id"],
            "severity": state["severity"],
            "title": state["title"],
            "draft_report": state["draft_report"],
            "quality_score": state.get("quality_score", 0),
            "action": "Please review and approve/reject this postmortem report",
            "instructions": "Resume with: {'approved': True/False, 'feedback': 'your feedback'}",
        })
        
        print(f"\n👤 Human Decision: {human_decision}")
        
        if human_decision.get("approved", False):
            return {"final_report": state["draft_report"]}
        else:
            # Human rejected - needs revision
            return {
                "review_feedback": {
                    **state.get("review_feedback", {}),
                    "human_feedback": human_decision.get("feedback", ""),
                    "revision_suggestions": [human_decision.get("feedback", "Address human feedback")],
                },
            }
    
    def finalize_node(state: IncidentState) -> dict:
        """Finalize the postmortem report."""
        print("\n" + "="*70)
        print("✅ POSTMORTEM COMPLETE")
        print("="*70)
        
        history = state.get("revision_history", [])
        
        # Calculate improvement metrics
        if len(history) >= 2:
            initial_score = history[0]["quality_score"]
            final_score = history[-1]["quality_score"]
            improvement = final_score - initial_score
        else:
            initial_score = history[0]["quality_score"] if history else 0
            final_score = initial_score
            improvement = 0
        
        print(f"\n📊 QUALITY METRICS:")
        print(f"   Initial Score: {initial_score:.1%}")
        print(f"   Final Score:   {final_score:.1%}")
        print(f"   Improvement:   {improvement:+.1%}")
        print(f"   Iterations:    {state['iteration']}/{state['max_iterations']}")
        
        return {"final_report": state["draft_report"]}
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUTING LOGIC
    # ═══════════════════════════════════════════════════════════════════════
    
    def should_continue_revision(state: IncidentState) -> Literal["revise", "human_review", "finalize"]:
        """
        Quality gate: Decide whether to continue reflection or finalize.
        """
        quality_score = state["quality_score"]
        threshold = state["quality_threshold"]
        iteration = state["iteration"]
        max_iter = state["max_iterations"]
        feedback = state.get("review_feedback", {})
        
        print(f"\n🚦 QUALITY GATE")
        print(f"   Quality: {quality_score:.1%} | Threshold: {threshold:.1%}")
        print(f"   Iteration: {iteration}/{max_iter}")
        print(f"   Approved by Reviewer: {feedback.get('approved', False)}")
        
        # Check if approved by reviewer
        if feedback.get("approved", False):
            # For SEV1, require human review
            if enable_hitl and state["severity"] == config.high_severity_threshold:
                print("   → Human review required (SEV1)")
                return "human_review"
            print("   → Finalizing (reviewer approved)")
            return "finalize"
        
        # Check max iterations (cost control)
        if iteration >= max_iter:
            print("   → Finalizing (max iterations)")
            return "finalize"
        
        # Check quality threshold
        if quality_score >= threshold:
            # For SEV1, require human review
            if enable_hitl and state["severity"] == config.high_severity_threshold:
                print("   → Human review required (SEV1)")
                return "human_review"
            print("   → Finalizing (quality threshold met)")
            return "finalize"
        
        print("   → Continuing revision loop")
        return "revise"
    
    def after_human_review(state: IncidentState) -> Literal["revise", "finalize"]:
        """Route after human review."""
        if state.get("final_report"):
            return "finalize"
        return "revise"
    
    # ═══════════════════════════════════════════════════════════════════════
    # BUILD GRAPH
    # ═══════════════════════════════════════════════════════════════════════
    
    builder = StateGraph(IncidentState)
    
    # Add nodes
    builder.add_node("log_analyzer", log_analyzer_node)
    builder.add_node("root_cause", root_cause_node)
    builder.add_node("writer", writer_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("finalize", finalize_node)
    
    # Add edges
    builder.add_edge(START, "log_analyzer")
    builder.add_edge("log_analyzer", "root_cause")
    builder.add_edge("root_cause", "writer")
    builder.add_edge("writer", "reviewer")
    
    # Quality gate after reviewer
    builder.add_conditional_edges(
        "reviewer",
        should_continue_revision,
        {
            "revise": "writer",           # Loop back for revision
            "human_review": "human_review",  # HITL for SEV1
            "finalize": "finalize",       # Done
        }
    )
    
    # After human review
    builder.add_conditional_edges(
        "human_review",
        after_human_review,
        {
            "revise": "writer",
            "finalize": "finalize",
        }
    )
    
    builder.add_edge("finalize", END)
    
    # Compile with checkpointer for HITL support
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


def print_graph_structure():
    """Print the graph structure for documentation."""
    print("""
Incident PostMortem Workflow:

    START
      │
      ▼
  ┌───────────────┐
  │ log_analyzer  │ ← Parses logs, identifies patterns
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │  root_cause   │ ← 5-whys analysis, failure chain
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │    writer     │ ◄─────────────────┐
  └───────┬───────┘                   │
          │                           │
          ▼                           │
  ┌───────────────┐                   │
  │   reviewer    │ (LLM-as-Judge)    │
  └───────┬───────┘                   │
          │                           │
          ▼                           │
  ┌───────────────┐                   │
  │ quality_gate  │                   │
  └───────┬───────┘                   │
          │                           │
    ┌─────┼─────┬─────────────────────┘
    ▼     ▼     ▼                 (revise)
 [pass] [sev1] [fail]
    │     │
    │     ▼
    │  ┌───────────────┐
    │  │ human_review  │ (HITL)
    │  └───────┬───────┘
    │          │
    └────┬─────┘
         ▼
  ┌───────────────┐
  │   finalize    │
  └───────┬───────┘
          │
          ▼
         END
""")
