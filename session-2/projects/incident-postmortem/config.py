"""
Configuration for Incident PostMortem Generator.

Supports both DIAL and OpenAI configuration with latest LangGraph v1 features.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Configuration settings for the postmortem system."""
    
    # LLM Settings
    model_name: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4096
    
    # Provider detection
    use_dial: bool = False
    
    # Quality Gates
    quality_threshold: float = 0.75  # Minimum quality score (0-1)
    max_revision_iterations: int = 3  # Max Writer → Reviewer loops
    
    # Severity Thresholds
    high_severity_threshold: str = "SEV1"  # Requires human approval
    
    # Memory Settings
    store_incidents: bool = True
    incident_retention_days: int = 90
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Detect provider (DIAL takes priority)
        use_dial = bool(os.getenv("DIAL_API_KEY"))
        
        return cls(
            model_name=os.getenv("MODEL_NAME", "gpt-4o"),
            temperature=float(os.getenv("TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            quality_threshold=float(os.getenv("QUALITY_THRESHOLD", "0.75")),
            max_revision_iterations=int(os.getenv("MAX_REVISIONS", "3")),
            high_severity_threshold=os.getenv("HIGH_SEV_THRESHOLD", "SEV1"),
            use_dial=use_dial,
        )


# Global config instance
config = Config.from_env()


# Default configuration
config = Config.from_env()
