"""
Tests for the Incident PostMortem system.

Run with: pytest test_postmortem.py -v
"""

import pytest
import json
from pathlib import Path

# Test imports work
def test_imports():
    """Verify all modules can be imported."""
    from config import settings, Settings
    from graph.state import IncidentState, LogAnalysis, RootCauseAnalysis
    from agents import log_analyzer_agent, root_cause_agent, writer_agent, reviewer_agent
    from memory import IncidentStore, incident_store
    
    assert settings is not None
    assert IncidentState is not None


def test_settings():
    """Test settings configuration."""
    from config import Settings
    
    # Test default settings
    s = Settings()
    assert s.model is not None
    assert s.max_iterations == 3
    assert s.quality_threshold == 0.8


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
        timeline=[{"time": "09:00", "event": "Incident started"}],
        errors=["Error 1", "Error 2"],
        warnings=["Warning 1"],
        patterns=["Pattern 1"],
        key_events=["Event 1"]
    )
    
    assert len(analysis.errors) == 2
    assert len(analysis.timeline) == 1


def test_root_cause_model():
    """Test RootCauseAnalysis Pydantic model."""
    from graph.state import RootCauseAnalysis
    
    rca = RootCauseAnalysis(
        primary_cause="Database connection pool exhausted",
        contributing_factors=["Missing index", "High traffic"],
        five_whys=[
            "Why did requests fail? Connection pool exhausted",
            "Why was pool exhausted? Slow queries",
        ],
        evidence=["Log line 1", "Log line 2"]
    )
    
    assert "Database" in rca.primary_cause
    assert len(rca.contributing_factors) == 2


def test_review_result_model():
    """Test ReviewResult Pydantic model."""
    from graph.state import ReviewResult
    
    review = ReviewResult(
        quality_score=0.85,
        passed=True,
        feedback="Good report",
        strengths=["Clear timeline"],
        improvements=[]
    )
    
    assert review.passed is True
    assert review.quality_score > 0.8


# Integration test (requires API key)
@pytest.mark.skipif(
    True,  # Skip by default, enable when API key is available
    reason="Requires API key"
)
def test_graph_creation():
    """Test that the graph can be created."""
    from graph.workflow import create_postmortem_graph
    
    graph = create_postmortem_graph()
    assert graph is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
