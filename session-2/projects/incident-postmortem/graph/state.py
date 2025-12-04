"""
State definitions for the Incident PostMortem workflow.

Uses TypedDict with Annotated reducers for proper state management.
"""

from typing import TypedDict, Annotated, List, Optional
from pydantic import BaseModel, Field
import operator


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH STATE
# ═══════════════════════════════════════════════════════════════════════════

class IncidentState(TypedDict):
    """Main state for the incident postmortem workflow."""
    
    # ─────────────────────────────────────────────────────────────────────────
    # Input: Incident data
    # ─────────────────────────────────────────────────────────────────────────
    incident_id: str
    severity: str  # SEV1, SEV2, SEV3, SEV4
    title: str
    description: str
    raw_logs: str
    metrics: dict  # Key metrics during incident
    timeline: List[dict]  # Timestamped events
    
    # ─────────────────────────────────────────────────────────────────────────
    # Log Analysis Output
    # ─────────────────────────────────────────────────────────────────────────
    log_summary: str
    error_patterns: List[str]
    affected_services: List[str]
    
    # ─────────────────────────────────────────────────────────────────────────
    # Root Cause Analysis Output
    # ─────────────────────────────────────────────────────────────────────────
    root_cause: str
    contributing_factors: List[str]
    failure_chain: List[str]  # Sequence of failures
    
    # ─────────────────────────────────────────────────────────────────────────
    # Report Generation
    # ─────────────────────────────────────────────────────────────────────────
    draft_report: str
    final_report: str
    
    # ─────────────────────────────────────────────────────────────────────────
    # Review (LLM-as-Judge)
    # ─────────────────────────────────────────────────────────────────────────
    review_feedback: dict
    quality_score: float  # 0.0 to 1.0
    
    # ─────────────────────────────────────────────────────────────────────────
    # Control Flow
    # ─────────────────────────────────────────────────────────────────────────
    iteration: int
    max_iterations: int
    quality_threshold: float
    
    # ─────────────────────────────────────────────────────────────────────────
    # History (for memory)
    # ─────────────────────────────────────────────────────────────────────────
    revision_history: Annotated[List[dict], operator.add]


# ═══════════════════════════════════════════════════════════════════════════
# STRUCTURED OUTPUT MODELS (Pydantic)
# ═══════════════════════════════════════════════════════════════════════════

class LogAnalysis(BaseModel):
    """Structured output from Log Analyzer agent."""
    
    summary: str = Field(
        description="2-3 paragraph summary of what the logs reveal"
    )
    error_patterns: List[str] = Field(
        default_factory=list,
        description="Distinct error patterns identified (max 5)"
    )
    affected_services: List[str] = Field(
        default_factory=list,
        description="Services that were impacted"
    )
    key_timestamps: List[dict] = Field(
        default_factory=list,
        description="Critical events with timestamps"
    )
    severity_indicators: List[str] = Field(
        default_factory=list,
        description="Evidence of incident severity"
    )


class RootCauseAnalysis(BaseModel):
    """Structured output from Root Cause agent."""
    
    root_cause: str = Field(
        description="Primary root cause of the incident"
    )
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="Secondary factors that contributed"
    )
    failure_chain: List[str] = Field(
        default_factory=list,
        description="Sequence of failures (first → last)"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Log evidence supporting the analysis"
    )
    five_whys: List[str] = Field(
        default_factory=list,
        description="5-whys analysis steps"
    )


class ReportReview(BaseModel):
    """Structured output from Reviewer agent (LLM-as-Judge)."""
    
    # Dimension scores (1-10)
    completeness_score: int = Field(
        default=5,
        description="Does it cover all required sections?",
        ge=1, le=10
    )
    clarity_score: int = Field(
        default=5,
        description="Is the writing clear and understandable?",
        ge=1, le=10
    )
    accuracy_score: int = Field(
        default=5,
        description="Does the root cause analysis seem accurate?",
        ge=1, le=10
    )
    actionability_score: int = Field(
        default=5,
        description="Are the action items specific and actionable?",
        ge=1, le=10
    )
    blamelessness_score: int = Field(
        default=5,
        description="Does it follow blameless postmortem principles?",
        ge=1, le=10
    )
    overall_score: int = Field(
        default=5,
        description="Overall quality score",
        ge=1, le=10
    )
    
    # Feedback
    strengths: List[str] = Field(
        default_factory=list,
        description="What the report does well"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Areas that need improvement"
    )
    revision_suggestions: List[str] = Field(
        default_factory=list,
        description="Specific suggestions for the next revision"
    )
    
    # Decision
    approved: bool = Field(
        default=False,
        description="True if report meets quality standards"
    )


# ═══════════════════════════════════════════════════════════════════════════
# INCIDENT INPUT MODEL
# ═══════════════════════════════════════════════════════════════════════════

class IncidentInput(BaseModel):
    """Input format for incident data."""
    
    incident_id: str = Field(description="Unique incident identifier")
    severity: str = Field(description="SEV1, SEV2, SEV3, or SEV4")
    title: str = Field(description="Brief incident title")
    description: str = Field(description="Incident description")
    raw_logs: str = Field(description="Raw log data from affected systems")
    metrics: dict = Field(
        default_factory=dict,
        description="Key metrics during incident"
    )
    timeline: List[dict] = Field(
        default_factory=list,
        description="Timestamped events"
    )
