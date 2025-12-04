#!/usr/bin/env python3
"""
Incident PostMortem Generation System - Main Entry Point

This is a production-ready LangGraph application that demonstrates:
- Self-reflection pattern with quality gates
- Multi-agent collaboration (Log Analyzer, Root Cause, Writer, Reviewer)
- Human-in-the-loop for critical incidents
- Streaming output
- Checkpointing for durable execution

Usage:
    python main.py --file sample_incidents/database_outage.json
    python main.py --file sample_incidents/api_timeout.json --stream
    python main.py --interactive
"""

import argparse
import json
import sys
from pathlib import Path
import uuid
import os

from langchain_openai import ChatOpenAI, AzureChatOpenAI

from config import config
from graph.workflow import create_postmortem_graph
from graph.state import IncidentState


def get_llm():
    """Get LLM instance based on configuration (DIAL or OpenAI)."""
    if config.use_dial:
        # Use Azure OpenAI with DIAL
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("DIAL_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            temperature=config.temperature,
        )
    else:
        # Use OpenAI directly
        return ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature
        )


def load_incident_from_file(filepath: str) -> dict:
    """Load incident data from JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Incident file not found: {filepath}")
    
    with open(path, 'r') as f:
        return json.load(f)


def create_synthetic_incident() -> dict:
    """Create a synthetic incident for demo purposes."""
    return {
        "incident_id": f"INC-{uuid.uuid4().hex[:6].upper()}",
        "title": "Database Connection Pool Exhaustion",
        "severity": "SEV2",
        "start_time": "2024-01-15T14:30:00Z",
        "end_time": "2024-01-15T16:45:00Z",
        "affected_services": ["api-gateway", "user-service", "order-service"],
        "logs": """
[2024-01-15T14:30:15Z] ERROR api-gateway: Connection pool exhausted, waiting for available connection
[2024-01-15T14:30:16Z] ERROR api-gateway: Request timeout after 30000ms
[2024-01-15T14:30:17Z] WARN user-service: Slow query detected: SELECT * FROM users WHERE id=? (took 15234ms)
[2024-01-15T14:30:18Z] ERROR api-gateway: Connection pool exhausted, 50 connections in use
[2024-01-15T14:31:00Z] ERROR order-service: Failed to connect to database: connection timed out
[2024-01-15T14:32:00Z] WARN monitoring: Alert triggered - Database connection latency > 10s
[2024-01-15T14:35:00Z] INFO oncall: Page sent to database team
[2024-01-15T14:45:00Z] INFO dba: Investigating connection pool settings
[2024-01-15T15:00:00Z] INFO dba: Found missing index on users.email column
[2024-01-15T15:15:00Z] INFO dba: Adding index to users.email
[2024-01-15T15:30:00Z] INFO dba: Index creation complete
[2024-01-15T15:45:00Z] INFO monitoring: Connection latency returning to normal
[2024-01-15T16:00:00Z] INFO api-gateway: All connections healthy
[2024-01-15T16:30:00Z] INFO oncall: Incident marked as resolved
[2024-01-15T16:45:00Z] INFO monitoring: All metrics within normal range for 15 minutes
        """,
        "timeline": [
            {"time": "14:30", "event": "First alerts triggered"},
            {"time": "14:35", "event": "On-call paged"},
            {"time": "14:45", "event": "DBA team engaged"},
            {"time": "15:00", "event": "Root cause identified - missing index"},
            {"time": "15:30", "event": "Fix deployed"},
            {"time": "16:45", "event": "Incident resolved"},
        ],
        "responders": ["Alice Chen (On-call)", "Bob Smith (DBA)", "Carol Davis (SRE)"],
    }


def run_streaming(graph, initial_state: IncidentState, run_config: dict):
    """Run the graph with streaming output."""
    print("\n" + "="*60)
    print("🚀 Starting Incident PostMortem Generation (Streaming)")
    print("="*60)
    
    for event in graph.stream(initial_state, run_config, stream_mode="updates"):
        for node_name, output in event.items():
            print(f"\n{'─'*40}")
            print(f"📍 Node: {node_name}")
            print(f"{'─'*40}")
            
            if node_name == "analyze_logs":
                analysis = output.get("log_analysis")
                if analysis:
                    print(f"  ⏰ Timeline entries: {len(analysis.get('timeline', []))}")
                    print(f"  ⚠️  Errors found: {len(analysis.get('errors', []))}")
                    print(f"  📊 Patterns: {len(analysis.get('patterns', []))}")
            
            elif node_name == "analyze_root_cause":
                rca = output.get("root_cause_analysis")
                if rca:
                    print(f"  🔍 Primary cause: {rca.get('primary_cause', 'Unknown')[:100]}")
                    print(f"  📋 Contributing factors: {len(rca.get('contributing_factors', []))}")
            
            elif node_name == "write_report":
                report = output.get("draft_report")
                if report:
                    lines = report.split('\n')[:5]
                    print(f"  📝 Draft preview:")
                    for line in lines:
                        if line.strip():
                            print(f"     {line[:80]}")
                iteration = output.get("iteration_count", 0)
                print(f"  🔄 Iteration: {iteration}")
            
            elif node_name == "review_report":
                review = output.get("review_result")
                if review:
                    print(f"  ⭐ Quality score: {review.get('quality_score', 0):.2f}")
                    print(f"  ✅ Passed: {review.get('passed', False)}")
                    if review.get('feedback'):
                        print(f"  💬 Feedback: {review.get('feedback', '')[:100]}")
            
            elif node_name == "approve_report":
                print(f"  ✨ Final report approved!")
                final = output.get("final_report")
                if final:
                    print(f"  📄 Report length: {len(final)} characters")


def run_batch(graph, initial_state: IncidentState, run_config: dict):
    """Run the graph in batch mode (non-streaming)."""
    print("\n" + "="*60)
    print("🚀 Starting Incident PostMortem Generation (Batch)")
    print("="*60)
    
    result = graph.invoke(initial_state, run_config)
    
    # Check for interrupts (HITL for SEV1)
    if result.get("__interrupt__"):
        print("\n" + "="*60)
        print("🛑 HUMAN APPROVAL REQUIRED")
        print("="*60)
        interrupt_info = result["__interrupt__"][0]
        print(f"\nIncident requires human review:")
        print(f"  Title: {interrupt_info['value']['title']}")
        print(f"  Severity: {interrupt_info['value']['severity']}")
        print(f"  Quality Score: {interrupt_info['value']['quality_score']:.1%}")
        print(f"\nReview the draft report and provide decision.")
        print(f"\nTo resume execution, use:")
        print(f"  graph.invoke(Command(resume={{'approved': True}}), run_config)")
        print(f"\nOr to reject:")
        print(f"  graph.invoke(Command(resume={{'approved': False, 'feedback': '...'}}), run_config)")
        return result
    
    # Final report ready
    print("\n" + "="*60)
    print("📋 FINAL POSTMORTEM REPORT")
    print("="*60)
    
    if result.get("final_report"):
        print(result["final_report"])
    elif result.get("draft_report"):
        print("⚠️  Draft report (not finalized):")
        print(result["draft_report"])
    
    print("\n" + "="*60)
    print("📊 EXECUTION SUMMARY")
    print("="*60)
    print(f"  Incident ID: {result.get('incident_id', 'Unknown')}")
    print(f"  Iterations: {result.get('iteration', 0)}")
    print(f"  Final score: {result.get('quality_score', 'N/A')}")
    
    return result


def interactive_mode():
    """Run in interactive mode for demo purposes."""
    print("\n" + "="*60)
    print("🎯 Incident PostMortem Generator - Interactive Mode")
    print("="*60)
    
    print("\nOptions:")
    print("  1. Use synthetic database outage incident")
    print("  2. Load from file")
    print("  3. Enter incident details manually")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        incident_data = create_synthetic_incident()
    elif choice == "2":
        filepath = input("Enter file path: ").strip()
        incident_data = load_incident_from_file(filepath)
    else:
        print("\n📝 Enter incident details:")
        incident_data = {
            "incident_id": input("  Incident ID: ").strip() or f"INC-{uuid.uuid4().hex[:6].upper()}",
            "title": input("  Title: ").strip() or "Unknown Incident",
            "severity": input("  Severity (SEV1-SEV4): ").strip().upper() or "SEV3",
            "logs": input("  Paste logs (or press Enter for demo): ").strip() or "No logs provided",
        }
    
    stream_choice = input("\nEnable streaming output? (y/n): ").strip().lower()
    use_streaming = stream_choice == 'y'
    
    # Initialize LLM
    model = get_llm()
    
    # Create graph
    graph = create_postmortem_graph(model, enable_hitl=True)
    
    initial_state = {
        "incident_id": incident_data.get("incident_id", f"INC-{uuid.uuid4().hex[:6].upper()}"),
        "severity": incident_data.get("severity", "SEV3"),
        "title": incident_data.get("title", "Unknown Incident"),
        "description": incident_data.get("description", ""),
        "raw_logs": incident_data.get("logs", ""),
        "metrics": incident_data.get("metrics", {}),
        "timeline": incident_data.get("timeline", []),
        "log_summary": "",
        "error_patterns": [],
        "affected_services": [],
        "root_cause": "",
        "contributing_factors": [],
        "failure_chain": [],
        "draft_report": "",
        "final_report": "",
        "review_feedback": {},
        "quality_score": 0.0,
        "iteration": 0,
        "max_iterations": config.max_revision_iterations,
        "quality_threshold": config.quality_threshold,
        "revision_history": [],
    }
    
    run_config = {"configurable": {"thread_id": incident_data.get("incident_id", "default")}}
    
    if use_streaming:
        run_streaming(graph, initial_state, run_config)
    else:
        run_batch(graph, initial_state, run_config)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate incident postmortem reports using AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo
  python main.py --file sample_incidents/database_outage.json
  python main.py --file incident.json --stream
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to incident JSON file"
    )
    parser.add_argument(
        "--stream", "-s",
        action="store_true",
        help="Enable streaming output"
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run with synthetic demo incident"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum refinement iterations (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if config.use_dial:
        if not os.getenv("DIAL_API_KEY"):
            print("❌ Error: DIAL_API_KEY not set!")
            print("   Set DIAL_API_KEY in .env file")
            sys.exit(1)
        print(f"✅ Using DIAL (Azure OpenAI)")
        print(f"   Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')}")
    else:
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Error: OPENAI_API_KEY not set!")
            print("   Set OPENAI_API_KEY in .env file")
            sys.exit(1)
        print(f"✅ Using OpenAI")
        print(f"   Model: {config.model_name}")
    
    print(f"   Temperature: {config.temperature}")
    print(f"   Max iterations: {config.max_revision_iterations}")
    
    if args.interactive:
        interactive_mode()
        return
    
    # Load incident data
    if args.demo:
        incident_data = create_synthetic_incident()
    elif args.file:
        incident_data = load_incident_from_file(args.file)
    else:
        print("No input specified. Use --demo, --file, or --interactive")
        parser.print_help()
        sys.exit(1)
    
    # Initialize LLM
    model = get_llm()
    
    # Create graph
    graph = create_postmortem_graph(model, enable_hitl=True)
    
    # Create initial state
    initial_state = {
        "incident_id": incident_data.get("incident_id", f"INC-{uuid.uuid4().hex[:6].upper()}"),
        "severity": incident_data.get("severity", "SEV3"),
        "title": incident_data.get("title", "Unknown Incident"),
        "description": incident_data.get("description", ""),
        "raw_logs": incident_data.get("logs", ""),
        "metrics": incident_data.get("metrics", {}),
        "timeline": incident_data.get("timeline", []),
        "log_summary": "",
        "error_patterns": [],
        "affected_services": [],
        "root_cause": "",
        "contributing_factors": [],
        "failure_chain": [],
        "draft_report": "",
        "final_report": "",
        "review_feedback": {},
        "quality_score": 0.0,
        "iteration": 0,
        "max_iterations": args.max_iterations,
        "quality_threshold": config.quality_threshold,
        "revision_history": [],
    }
    
    run_config = {"configurable": {"thread_id": incident_data.get("incident_id", "default")}}
    
    # Run
    if args.stream:
        run_streaming(graph, initial_state, run_config)
    else:
        run_batch(graph, initial_state, run_config)


if __name__ == "__main__":
    main()
