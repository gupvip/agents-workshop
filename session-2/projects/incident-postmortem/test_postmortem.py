"""
Tests for the Incident PostMortem system.

Run with: pytest test_postmortem.py -v
"""

import pytest
import json
import os
from pathlib import Path

# Test imports work
def test_imports():
    """Verify all modules can be imported."""
    from config import config, Config
    from graph.state import IncidentState, LogAnalysis, RootCauseAnalysis
    from agents import analyze_logs, analyze_root_cause, write_report, review_report
    from memory import IncidentStore
    
    assert config is not None
    assert IncidentState is not None


def test_config():
    """Test configuration."""
    from config import Config
    
    # Test default settings
    c = Config()
    assert c.model_name is not None
    assert c.max_revision_iterations == 3
    assert c.quality_threshold == 0.75


def test_incident_store():
    """Test incident store operations."""
    from memory import IncidentStore
    
    store = IncidentStore()
    
    # Test save and retrieve
    store.save_incident(
        incident_id="TEST-001",
        title="Test Incident",
        severity="SEV3",
        root_cause="Test cause",
        report="Test report content"
    )
    
    incident = store.get_incident("TEST-001")
    assert incident is not None
    assert incident["title"] == "Test Incident"
    assert incident["severity"] == "SEV3"


def test_sample_incidents_valid_json():
    """Test that sample incidents are valid JSON."""
    sample_dir = Path(__file__).parent / "sample_incidents"
    
    if not sample_dir.exists():
        pytest.skip("Sample incidents directory not found")
    
    for json_file in sample_dir.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            assert "incident_id" in data
            assert "title" in data
            assert "severity" in data
            assert "logs" in data


def test_log_analysis_model():
    """Test LogAnalysis Pydantic model."""
    from graph.state import LogAnalysis
    
    analysis = LogAnalysis(
        summary="Test summary of logs",
        error_patterns=["Error 1", "Error 2"],
        affected_services=["service-a", "service-b"],
        key_timestamps=[{"time": "09:00", "event": "Incident started"}],
        severity_indicators=["High CPU usage"]
    )
    
    assert len(analysis.error_patterns) == 2
    assert len(analysis.affected_services) == 2
    assert analysis.summary == "Test summary of logs"


def test_root_cause_model():
    """Test RootCauseAnalysis Pydantic model."""
    from graph.state import RootCauseAnalysis
    
    rca = RootCauseAnalysis(
        root_cause="Database connection pool exhausted",
        contributing_factors=["Missing index", "High traffic"],
        failure_chain=["Traffic spike", "Slow queries", "Pool exhaustion"],
        five_whys=[
            "Why did requests fail? Connection pool exhausted",
            "Why was pool exhausted? Slow queries",
        ],
        evidence=["Log line 1", "Log line 2"]
    )
    
    assert "Database" in rca.root_cause
    assert len(rca.contributing_factors) == 2
    assert len(rca.failure_chain) == 3


def test_report_review_model():
    """Test ReportReview Pydantic model."""
    from graph.state import ReportReview
    
    review = ReportReview(
        completeness_score=8,
        clarity_score=9,
        accuracy_score=7,
        actionability_score=8,
        blamelessness_score=9,
        overall_score=8,
        strengths=["Clear timeline", "Good root cause analysis"],
        weaknesses=["Missing metrics"],
        revision_suggestions=["Add more metrics"],
        approved=True
    )
    
    assert review.approved is True
    assert review.overall_score == 8
    assert len(review.strengths) == 2


# Integration test (requires API key)
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("DIAL_API_KEY"),
    reason="Requires API key"
)
def test_graph_creation():
    """Test that the graph can be created."""
    from graph.workflow import create_postmortem_graph
    from main import get_llm
    
    model = get_llm()
    graph = create_postmortem_graph(model)
    assert graph is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
