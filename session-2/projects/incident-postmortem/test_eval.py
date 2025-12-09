"""
DeepEval Tests for Incident PostMortem System.

This module provides pytest-style evaluation tests using DeepEval:
- Report quality evaluation
- Root cause analysis accuracy
- Actionable recommendations check

Setup:
    pip install deepeval
    Uses setup_llm.py configuration (DIAL or OpenAI)

Run tests:
    pytest test_eval.py -v
    
    # Or run a specific test
    pytest test_eval.py::test_report_quality -v
    
    # Generate detailed report
    deepeval test run test_eval.py
"""

import pytest
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent paths to import setup_llm
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# DeepEval imports
try:
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
        GEval,
    )
    from deepeval.models.base_model import DeepEvalBaseLLM
    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False
    pytest.skip("DeepEval not installed", allow_module_level=True)


# ============================================================
# Custom DeepEval Model using setup_llm.py
# ============================================================

class WorkshopLLM(DeepEvalBaseLLM):
    """
    Custom DeepEval model that uses the workshop's setup_llm.py configuration.
    Works with both DIAL (EPAM) and OpenAI depending on your .env setup.
    """
    
    def __init__(self):
        from setup_llm import get_chat_model
        self._model = get_chat_model(temperature=0)
    
    def load_model(self):
        return self._model
    
    def generate(self, prompt: str) -> str:
        """Generate a response from the model."""
        response = self._model.invoke(prompt)
        return response.content
    
    async def a_generate(self, prompt: str) -> str:
        """Async generate a response from the model."""
        response = await self._model.ainvoke(prompt)
        return response.content
    
    def get_model_name(self) -> str:
        """Return model name for logging."""
        if hasattr(self._model, 'model_name'):
            return self._model.model_name
        elif hasattr(self._model, 'deployment_name'):
            return self._model.deployment_name
        return "workshop-llm"


# Create a singleton instance
def get_eval_model():
    """Get the evaluation model (cached)."""
    if not hasattr(get_eval_model, '_instance'):
        get_eval_model._instance = WorkshopLLM()
    return get_eval_model._instance


# ============================================================
# Sample Data for Testing
# ============================================================

SAMPLE_INCIDENT = {
    "incident_id": "INC-TEST001",
    "title": "Database Connection Pool Exhaustion",
    "severity": "SEV2",
    "logs": """
[2024-01-15T14:30:15Z] ERROR api-gateway: Connection pool exhausted
[2024-01-15T14:30:16Z] ERROR api-gateway: Request timeout after 30000ms
[2024-01-15T14:31:00Z] ERROR order-service: Failed to connect to database
[2024-01-15T15:00:00Z] INFO dba: Found missing index on users.email column
[2024-01-15T15:30:00Z] INFO dba: Index creation complete
[2024-01-15T16:00:00Z] INFO api-gateway: All connections healthy
    """,
    "timeline": [
        {"time": "14:30", "event": "First alerts triggered"},
        {"time": "15:00", "event": "Root cause identified"},
        {"time": "16:00", "event": "Incident resolved"},
    ],
}

SAMPLE_ROOT_CAUSE_CONTEXT = """
Based on log analysis:
- Connection pool was exhausted at 14:30
- Database queries were slow due to missing index
- The users.email column had no index, causing full table scans
- After adding the index, performance returned to normal
"""

SAMPLE_REPORT_OUTPUT = """
# Incident Postmortem: Database Connection Pool Exhaustion

## Summary
On January 15, 2024, a database connection pool exhaustion caused service degradation 
for approximately 90 minutes. The root cause was a missing index on the users.email column.

## Timeline
- 14:30 - First alerts triggered, connection pool exhausted
- 15:00 - DBA identified missing index on users.email
- 15:30 - Index creation completed
- 16:00 - All services restored to normal

## Root Cause
Missing database index on the users.email column caused full table scans during 
user lookup queries, which increased query latency significantly and exhausted 
the database connection pool.

## Action Items
1. [P1] Add database index validation to deployment checklist
2. [P1] Implement connection pool monitoring alerts
3. [P2] Review other high-traffic tables for missing indexes
4. [P3] Add query performance testing to CI/CD pipeline
"""


# ============================================================
# Custom Metrics (using workshop LLM)
# ============================================================

def get_postmortem_quality_metric():
    """Create a custom GEval metric for postmortem report quality."""
    return GEval(
        name="Postmortem Quality",
        criteria="""
        Evaluate the quality of an incident postmortem report based on:
        1. Clear summary of what happened
        2. Accurate timeline of events
        3. Correct root cause identification
        4. Actionable remediation items
        5. Professional tone and structure
        """,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.7,
        model=get_eval_model(),
    )


def get_root_cause_accuracy_metric():
    """Create a metric for root cause analysis accuracy."""
    return GEval(
        name="Root Cause Accuracy",
        criteria="""
        Evaluate whether the root cause analysis correctly identifies:
        1. The primary cause of the incident
        2. Contributing factors
        3. The causal chain from root cause to symptoms
        """,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.7,
        model=get_eval_model(),
    )


def get_actionability_metric():
    """Create a metric for checking if recommendations are actionable."""
    return GEval(
        name="Actionability",
        criteria="""
        Evaluate whether the action items are:
        1. Specific and measurable
        2. Assigned with priority levels
        3. Realistic and implementable
        4. Address the root cause
        """,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.7,
        model=get_eval_model(),
    )


# ============================================================
# Test Cases
# ============================================================

@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
def test_report_relevancy():
    """Test that the generated report is relevant to the incident."""
    
    # Create test case
    test_case = LLMTestCase(
        input=f"Generate a postmortem for incident: {SAMPLE_INCIDENT['title']}",
        actual_output=SAMPLE_REPORT_OUTPUT,
        retrieval_context=[SAMPLE_ROOT_CAUSE_CONTEXT, json.dumps(SAMPLE_INCIDENT)],
    )
    
    # Use answer relevancy metric with workshop LLM
    metric = AnswerRelevancyMetric(threshold=0.7, model=get_eval_model())
    
    assert_test(test_case, [metric])


@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
def test_report_faithfulness():
    """Test that the report is faithful to the provided context."""
    
    test_case = LLMTestCase(
        input=f"Generate a postmortem for incident: {SAMPLE_INCIDENT['title']}",
        actual_output=SAMPLE_REPORT_OUTPUT,
        retrieval_context=[SAMPLE_ROOT_CAUSE_CONTEXT, json.dumps(SAMPLE_INCIDENT)],
    )
    
    metric = FaithfulnessMetric(threshold=0.7, model=get_eval_model())
    
    assert_test(test_case, [metric])


@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
def test_postmortem_quality():
    """Test overall postmortem report quality using custom GEval."""
    
    test_case = LLMTestCase(
        input=f"Generate a postmortem report for: {SAMPLE_INCIDENT['title']}\n\nContext: {SAMPLE_ROOT_CAUSE_CONTEXT}",
        actual_output=SAMPLE_REPORT_OUTPUT,
    )
    
    metric = get_postmortem_quality_metric()
    
    assert_test(test_case, [metric])


@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
def test_root_cause_accuracy():
    """Test that root cause analysis is accurate."""
    
    root_cause_output = """
    Root Cause: Missing database index on users.email column
    
    The users.email column had no index, causing full table scans whenever 
    a user lookup query was executed. During peak traffic, these slow queries 
    accumulated and exhausted the database connection pool, leading to timeouts 
    across multiple services.
    
    Contributing Factors:
    1. High traffic during peak hours
    2. Lack of query performance monitoring
    3. Missing index validation in deployment process
    """
    
    test_case = LLMTestCase(
        input=f"Analyze root cause for:\n{SAMPLE_INCIDENT['logs']}",
        actual_output=root_cause_output,
        expected_output="Missing index on users.email column causing connection pool exhaustion",
    )
    
    metric = get_root_cause_accuracy_metric()
    
    assert_test(test_case, [metric])


@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
def test_action_items_actionability():
    """Test that action items are specific and actionable."""
    
    action_items = """
    Action Items:
    1. [P1] Add database index validation to deployment checklist - Owner: Platform Team
    2. [P1] Configure CloudWatch alarm for connection pool usage > 80% - Owner: SRE
    3. [P2] Run EXPLAIN ANALYZE on top 10 queries and add missing indexes - Owner: DBA
    4. [P3] Add query performance benchmarks to CI pipeline - Owner: Dev Team
    """
    
    test_case = LLMTestCase(
        input="Generate action items to prevent database connection pool exhaustion",
        actual_output=action_items,
    )
    
    metric = get_actionability_metric()
    
    assert_test(test_case, [metric])


# ============================================================
# Integration Test with Real System
# ============================================================

@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
@pytest.mark.integration
def test_full_postmortem_generation():
    """
    Integration test: Run the full postmortem system and evaluate output.
    
    This test requires:
    - OPENAI_API_KEY environment variable
    - The full incident-postmortem system to be available
    
    Run with: pytest test_eval.py -v -m integration
    """
    import os
    
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("DIAL_API_KEY"):
        pytest.skip("OPENAI_API_KEY or DIAL_API_KEY not set")
    
    # Import the system
    try:
        from main import get_llm, create_synthetic_incident
        from graph.workflow import create_postmortem_graph
    except ImportError:
        pytest.skip("Postmortem system not available")
    
    # Generate a postmortem
    model = get_llm()
    graph = create_postmortem_graph(model, enable_hitl=False)
    incident = create_synthetic_incident()
    
    initial_state = {
        "incident_id": incident["incident_id"],
        "severity": incident["severity"],
        "title": incident["title"],
        "description": incident.get("description", ""),
        "raw_logs": incident["logs"],
        "metrics": incident.get("metrics", {}),
        "timeline": incident.get("timeline", []),
        "log_summary": "",
        "error_patterns": [],
        "affected_services": incident.get("affected_services", []),
        "root_cause": "",
        "contributing_factors": [],
        "failure_chain": [],
        "draft_report": "",
        "final_report": "",
        "review_feedback": {},
        "quality_score": 0.0,
        "iteration": 0,
        "max_iterations": 2,
        "quality_threshold": 0.7,
        "revision_history": [],
    }
    
    result = graph.invoke(initial_state, {"configurable": {"thread_id": "test"}})
    
    # Evaluate the result
    report = result.get("final_report") or result.get("draft_report", "")
    
    test_case = LLMTestCase(
        input=f"Generate postmortem for: {incident['title']}",
        actual_output=report,
        retrieval_context=[incident["logs"]],
    )
    
    metrics = [
        AnswerRelevancyMetric(threshold=0.6, model=get_eval_model()),
        get_postmortem_quality_metric(),
    ]
    
    assert_test(test_case, metrics)


# ============================================================
# Batch Evaluation
# ============================================================

def run_batch_evaluation(test_cases: list[dict]) -> dict:
    """
    Run evaluation on multiple test cases and return aggregate metrics.
    
    Args:
        test_cases: List of dicts with 'input', 'output', 'context' keys
    
    Returns:
        Aggregate metrics across all test cases
    """
    if not DEEPEVAL_AVAILABLE:
        return {"error": "DeepEval not available"}
    
    from deepeval import evaluate
    
    llm_test_cases = []
    for tc in test_cases:
        llm_test_cases.append(LLMTestCase(
            input=tc["input"],
            actual_output=tc["output"],
            retrieval_context=tc.get("context", []),
        ))
    
    # Use workshop LLM for evaluation
    eval_model = get_eval_model()
    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model=eval_model),
        FaithfulnessMetric(threshold=0.7, model=eval_model),
    ]
    
    results = evaluate(llm_test_cases, metrics)
    
    return {
        "total_tests": len(test_cases),
        "passed": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "details": results,
    }


if __name__ == "__main__":
    # Quick check
    if not DEEPEVAL_AVAILABLE:
        print("❌ DeepEval not installed. Run: pip install deepeval")
    else:
        print("✅ DeepEval available")
        print("✅ Using workshop LLM (DIAL or OpenAI based on .env)")
        print("\nRun tests with: pytest test_eval.py -v")
        print("Run integration tests: pytest test_eval.py -v -m integration")
