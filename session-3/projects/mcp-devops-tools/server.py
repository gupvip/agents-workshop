"""
MCP DevOps Tools Server

A Model Context Protocol server that exposes DevOps-related tools
for use by LLM agents and applications.

Run with:
    python server.py              # HTTP mode (default) - production-like
    python server.py --stdio       # stdio mode - for local subprocess spawning

HTTP mode starts a server at http://localhost:8000/mcp
"""

import argparse
import random
from datetime import datetime
from typing import Literal

from mcp.server.fastmcp import FastMCP

# =============================================================================
# Server Configuration
# =============================================================================
MCP_HOST = "localhost"
MCP_PORT = 8000

# Initialize MCP server using FastMCP (high-level API)
mcp = FastMCP("devops-tools")

# =============================================================================
# Simulated Data (In production, these would call real APIs)
# =============================================================================

SERVICES = {
    "api-gateway": {"status": "healthy", "version": "2.3.1"},
    "user-service": {"status": "healthy", "version": "1.8.0"},
    "order-service": {"status": "degraded", "version": "3.1.2"},
    "payment-service": {"status": "healthy", "version": "2.0.0"},
    "database-primary": {"status": "healthy", "version": "14.2"},
}

SAMPLE_LOGS = {
    "api-gateway": [
        "2024-01-15 10:23:45 INFO Request processed successfully",
        "2024-01-15 10:23:46 INFO Health check passed",
        "2024-01-15 10:23:47 WARN High latency detected: 450ms",
    ],
    "order-service": [
        "2024-01-15 10:23:45 ERROR Connection timeout to database",
        "2024-01-15 10:23:46 WARN Retry attempt 1/3",
        "2024-01-15 10:23:47 ERROR Connection timeout to database",
        "2024-01-15 10:23:48 WARN Retry attempt 2/3",
        "2024-01-15 10:23:49 INFO Connection restored",
    ],
}

# =============================================================================
# MCP Tools
# =============================================================================


@mcp.tool()
async def get_service_status(service_name: str) -> str:
    """
    Get the current status of a service.
    
    Args:
        service_name: Name of the service to check (e.g., 'api-gateway', 'user-service')
    
    Returns:
        Service status information including health state and version.
    """
    if service_name not in SERVICES:
        available = ", ".join(SERVICES.keys())
        return f"Service '{service_name}' not found. Available services: {available}"
    
    service = SERVICES[service_name]
    return f"""Service: {service_name}
Status: {service['status']}
Version: {service['version']}
Last checked: {datetime.now().isoformat()}"""


@mcp.tool()
async def get_recent_logs(
    service_name: str,
    log_level: Literal["INFO", "WARN", "ERROR", "ALL"] = "ALL",
    limit: int = 10
) -> str:
    """
    Fetch recent logs for a service.
    
    Args:
        service_name: Name of the service to get logs from
        log_level: Filter by log level (INFO, WARN, ERROR, or ALL)
        limit: Maximum number of log entries to return (default: 10)
    
    Returns:
        Recent log entries for the specified service.
    """
    if service_name not in SAMPLE_LOGS:
        return f"No logs available for service '{service_name}'. Try: {', '.join(SAMPLE_LOGS.keys())}"
    
    logs = SAMPLE_LOGS[service_name]
    
    # Filter by log level if specified
    if log_level != "ALL":
        logs = [log for log in logs if log_level in log]
    
    # Apply limit
    logs = logs[:limit]
    
    if not logs:
        return f"No {log_level} logs found for {service_name}"
    
    return f"Recent logs for {service_name}:\n" + "\n".join(logs)


@mcp.tool()
async def get_metrics(service_name: str) -> str:
    """
    Get current metrics for a service including CPU, memory, and error rate.
    
    Args:
        service_name: Name of the service to get metrics from
    
    Returns:
        Current metrics including CPU usage, memory usage, and error rate.
    """
    if service_name not in SERVICES:
        return f"Service '{service_name}' not found."
    
    # Simulate metrics (in production, these would come from Prometheus, etc.)
    cpu = random.uniform(10, 80)
    memory = random.uniform(30, 70)
    error_rate = random.uniform(0, 5) if SERVICES[service_name]["status"] == "healthy" else random.uniform(5, 25)
    requests_per_sec = random.uniform(100, 1000)
    
    return f"""Metrics for {service_name}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPU Usage:        {cpu:.1f}%
Memory Usage:     {memory:.1f}%
Error Rate:       {error_rate:.2f}%
Requests/sec:     {requests_per_sec:.0f}
Timestamp:        {datetime.now().isoformat()}"""


@mcp.tool()
async def create_incident(
    title: str,
    severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"],
    affected_services: str,
    description: str
) -> str:
    """
    Create a new incident ticket.
    
    Args:
        title: Brief title describing the incident
        severity: Severity level (SEV1=critical, SEV2=major, SEV3=minor, SEV4=low)
        affected_services: Comma-separated list of affected services
        description: Detailed description of the incident
    
    Returns:
        Incident ticket confirmation with ID and details.
    """
    # Generate a fake incident ID
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    return f"""✅ Incident Created Successfully
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Incident ID:      {incident_id}
Title:            {title}
Severity:         {severity}
Affected Services: {affected_services}
Status:           OPEN
Created:          {datetime.now().isoformat()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Description:
{description}

Next Steps:
1. Page on-call engineer (if SEV1/SEV2)
2. Start investigation
3. Update status page"""


@mcp.tool()
async def list_services() -> str:
    """
    List all available services and their current status.
    
    Returns:
        A table of all services with their status and version.
    """
    lines = ["Available Services:", "━" * 50]
    for name, info in SERVICES.items():
        status_emoji = "✅" if info["status"] == "healthy" else "⚠️" if info["status"] == "degraded" else "❌"
        lines.append(f"{status_emoji} {name:<20} | {info['status']:<10} | v{info['version']}")
    
    return "\n".join(lines)


# =============================================================================
# Server Entry Point
# =============================================================================

# Create the Starlette app for HTTP transport (used by uvicorn)
app = mcp.streamable_http_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP DevOps Tools Server")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport instead of HTTP (for subprocess spawning)"
    )
    parser.add_argument(
        "--host",
        default=MCP_HOST,
        help=f"Host to bind to (default: {MCP_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=MCP_PORT,
        help=f"Port to bind to (default: {MCP_PORT})"
    )
    args = parser.parse_args()
    
    if args.stdio:
        # stdio transport - for local subprocess spawning
        print("🚀 Starting MCP server with stdio transport...")
        mcp.run(transport="stdio")
    else:
        # HTTP transport - production-like setup using uvicorn
        import uvicorn
        print(f"🚀 Starting MCP server at http://{args.host}:{args.port}/mcp")
        print("   Press Ctrl+C to stop")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
