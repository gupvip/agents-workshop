"""
Langfuse Integration for Incident PostMortem System.

This module provides observability for the postmortem generation workflow:
- Tracing all LLM calls and agent interactions
- Scoring outputs for quality metrics
- Session tracking across incident investigations

Setup:
    1. Get API keys from https://cloud.langfuse.com or self-host
    2. Set environment variables:
       export LANGFUSE_PUBLIC_KEY="pk-lf-..."
       export LANGFUSE_SECRET_KEY="sk-lf-..."
       export LANGFUSE_HOST="https://cloud.langfuse.com"  # or self-hosted URL

Usage:
    from observability import get_traced_llm, trace_workflow_run, score_output
    
    # Get LLM with tracing
    llm = get_traced_llm()
    
    # Or use the callback handler directly
    from observability import langfuse_handler
    llm.invoke(prompt, config={"callbacks": [langfuse_handler]})
"""

import os
from pathlib import Path
from typing import Optional, Any
from functools import wraps

# Load environment variables from root .env file
try:
    from dotenv import load_dotenv
    # Try project .env first, then root workshop .env
    project_env = Path(__file__).parent / ".env"
    root_env = Path(__file__).parent.parent.parent.parent / ".env"
    
    if project_env.exists():
        load_dotenv(project_env)
    if root_env.exists():
        load_dotenv(root_env, override=False)  # Don't override project-level settings
except ImportError:
    pass

# Check if Langfuse is available
try:
    # Langfuse v3.x uses langfuse.langchain for LangChain integration
    from langfuse.langchain import CallbackHandler
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    try:
        # Fallback for older versions
        from langfuse.callback import CallbackHandler
        from langfuse import Langfuse
        LANGFUSE_AVAILABLE = True
    except ImportError:
        LANGFUSE_AVAILABLE = False
        CallbackHandler = None
        Langfuse = None


def is_langfuse_configured() -> bool:
    """Check if Langfuse credentials are configured."""
    return all([
        os.getenv("LANGFUSE_PUBLIC_KEY"),
        os.getenv("LANGFUSE_SECRET_KEY"),
    ])


def get_langfuse_handler() -> Optional[CallbackHandler]:
    """
    Get a Langfuse callback handler for LangChain/LangGraph.
    
    Note: In Langfuse v3, session_id, user_id, and tags are passed via
    metadata in the chain invocation config, not in the handler constructor.
    
    Returns:
        CallbackHandler if Langfuse is configured, None otherwise
    """
    if not LANGFUSE_AVAILABLE:
        print("⚠️  Langfuse not installed. Run: pip install langfuse")
        return None
    
    if not is_langfuse_configured():
        print("⚠️  Langfuse not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return None
    
    # Langfuse v3: CallbackHandler takes no arguments for session/user/tags
    # These are now passed via metadata in chain.invoke() config
    return CallbackHandler()


def get_langfuse_client() -> Optional[Any]:
    """Get a direct Langfuse client for scoring and custom events."""
    if not LANGFUSE_AVAILABLE or not is_langfuse_configured():
        return None
    
    try:
        from langfuse import get_client
        return get_client()
    except Exception:
        return None


def score_trace(
    trace_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None,
) -> None:
    """
    Add a score to a trace.
    
    Args:
        trace_id: The trace ID to score
        name: Score name (e.g., "quality_score", "accuracy")
        value: Score value (0-1 for normalized scores)
        comment: Optional comment explaining the score
    """
    client = get_langfuse_client()
    if client:
        try:
            client.create_score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
        except Exception as e:
            print(f"⚠️  Failed to score trace: {e}")


def create_incident_handler(incident_id: str, severity: str) -> Optional[CallbackHandler]:
    """
    Create a handler configured for a specific incident.
    
    Note: In Langfuse v3, this just returns a basic handler.
    Session/user/tags are passed via metadata in get_traced_config().
    
    Args:
        incident_id: The incident being processed
        severity: Incident severity (SEV1, SEV2, etc.)
    
    Returns:
        Configured CallbackHandler
    """
    return get_langfuse_handler()


# ============================================================
# Integration with main.py
# ============================================================

def get_traced_config(
    incident_id: str,
    severity: str = "SEV2",
    run_name: Optional[str] = None,
) -> dict:
    """
    Get a LangGraph config dict with Langfuse tracing.
    
    Usage in main.py:
        from observability import get_traced_config
        
        run_config = get_traced_config(
            incident_id=incident["incident_id"],
            severity=incident["severity"],
        )
        result = graph.invoke(initial_state, config=run_config)
    
    Args:
        incident_id: Incident identifier
        severity: Incident severity level
        run_name: Optional name for this run
    
    Returns:
        Config dict for LangGraph with callbacks and metadata
    """
    handler = get_langfuse_handler()
    
    # Base config
    config = {
        "configurable": {"thread_id": incident_id},
    }
    
    if handler:
        config["callbacks"] = [handler]
        # Langfuse v3: Pass session_id, user_id, tags via metadata
        config["metadata"] = {
            "langfuse_session_id": incident_id,
            "langfuse_tags": ["incident-postmortem", f"severity:{severity}"],
        }
        if run_name:
            config["run_name"] = run_name
    
    return config


# ============================================================
# Decorator for function-level tracing
# ============================================================

def observe(name: Optional[str] = None):
    """
    Decorator for tracing individual functions.
    
    Usage:
        @observe("analyze_logs")
        def analyze_logs(state, model):
            ...
    """
    def decorator(func):
        if not LANGFUSE_AVAILABLE:
            return func
        
        try:
            from langfuse.decorators import observe as lf_observe
            return lf_observe(name=name or func.__name__)(func)
        except ImportError:
            return func
    
    return decorator


# ============================================================
# Quick setup check
# ============================================================

def check_langfuse_setup():
    """Print Langfuse configuration status."""
    print("\n" + "=" * 50)
    print("Langfuse Configuration Check")
    print("=" * 50)
    
    if not LANGFUSE_AVAILABLE:
        print("❌ Langfuse package not installed")
        print("   Run: pip install langfuse")
        return False
    
    print("✅ Langfuse package installed")
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if public_key:
        print(f"✅ LANGFUSE_PUBLIC_KEY: {public_key[:10]}...")
    else:
        print("❌ LANGFUSE_PUBLIC_KEY not set")
    
    if secret_key:
        print(f"✅ LANGFUSE_SECRET_KEY: {secret_key[:10]}...")
    else:
        print("❌ LANGFUSE_SECRET_KEY not set")
    
    print(f"ℹ️  LANGFUSE_HOST: {host}")
    
    if public_key and secret_key:
        print("\n✅ Langfuse is configured!")
        print(f"   View traces at: {host}")
        return True
    else:
        print("\n❌ Langfuse not fully configured")
        print("   Get keys at: https://cloud.langfuse.com")
        return False


if __name__ == "__main__":
    check_langfuse_setup()
