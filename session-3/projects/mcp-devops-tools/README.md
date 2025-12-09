# MCP DevOps Tools Server

A Model Context Protocol (MCP) server that provides DevOps-related tools for LLM agents.

**Updated for LangChain v1 and LangGraph v1 (December 2024)**

## Overview

This project demonstrates how to:
1. **Create an MCP server** using FastMCP (high-level API) with **HTTP transport**
2. **Expose tools** via the MCP protocol
3. **Connect directly** using the MCP Python client over HTTP
4. **Integrate with LangChain v1** using `langchain-mcp-adapters`

## Transport Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **HTTP** (default) | `python server.py` | Production-like setup. Server runs independently. |
| **stdio** | `python server.py --stdio` | Local subprocess spawning (debugging). |

### Why HTTP Transport?

- **Clear separation**: Server runs in one terminal, clients in another
- **Production-like**: Mirrors real deployments where servers are deployed independently
- **Scalable**: Multiple clients can connect to one server
- **Observable**: Easy to monitor with standard HTTP tools

## Tools Provided

| Tool | Description |
|------|-------------|
| `get_service_status` | Get current status and version of a service |
| `get_recent_logs` | Fetch recent logs with level filtering |
| `get_metrics` | Get CPU, memory, and error rate metrics |
| `create_incident` | Create an incident ticket |
| `list_services` | List all available services |

## Project Structure

```
mcp-devops-tools/
├── README.md
├── requirements.txt       # Updated for LangChain v1 / LangGraph v1
├── Makefile              # Convenient commands
├── server.py             # MCP server (FastMCP, HTTP by default)
├── simple_client.py      # Direct MCP client (HTTP)
└── langgraph_consumer.py # LangChain v1 agent with MCP tools
```

## Quick Start

### 1. Install Dependencies

```bash
make install
# or
pip install -r requirements.txt
```

### 2. Run the Server (Terminal 1)

```bash
make server
# Server starts at http://localhost:8000/mcp
```

### 3. Run a Client (Terminal 2)

```bash
# Test basic MCP client communication
make client

# Or run the LangChain agent (requires LLM setup)
make agent
```

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | >=1.9.0 | Model Context Protocol SDK |
| `langchain` | >=1.0.0 | LangChain v1 with `create_agent` |
| `langgraph` | >=1.0.0 | Agent runtime (used by LangChain) |
| `langchain-mcp-adapters` | >=0.1.0 | Bridge MCP tools to LangChain |

## How It Works

### MCP Server (server.py)

Uses **FastMCP** with HTTP transport:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("devops-tools")

@mcp.tool()
async def get_service_status(service_name: str) -> str:
    """Get the current status of a service."""
    return f"Service: {service_name}\nStatus: healthy"

if __name__ == "__main__":
    # HTTP transport - runs server at http://localhost:8000/mcp
    mcp.run(transport="streamable-http", host="localhost", port=8000)
```

### Simple Client (simple_client.py)

Connects to the MCP server over HTTP:

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_SERVER_URL = "http://localhost:8000/mcp"

async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("list_services", {})
```

### LangChain v1 Agent (langgraph_consumer.py)

Uses the new **LangChain v1 `create_agent`** API with HTTP transport:

```python
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# Configure MCP server - HTTP transport
mcp_config = {
    "devops-tools": {
        "transport": "streamable_http",
        "url": "http://localhost:8000/mcp",
        # Optional: "headers": {"Authorization": "Bearer <token>"}
    }
}

# Connect and get tools
mcp_client = MultiServerMCPClient(mcp_config)
tools = await mcp_client.get_tools()

# LangChain v1: create_agent (replaces langgraph.prebuilt.create_react_agent)
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a DevOps assistant..."
)

# Run the agent
result = await agent.ainvoke({"messages": [("user", "Check service status")]})
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Transport                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐         HTTP/JSON          ┌──────────────┐  │
│   │             │ ─────────────────────────▶ │              │  │
│   │   Client    │                            │  MCP Server  │  │
│   │ (Python/JS) │ ◀───────────────────────── │ (FastMCP)    │  │
│   │             │    http://localhost:8000   │              │  │
│   └─────────────┘                            └──────────────┘  │
│                                                                 │
│   • Server runs independently                                   │
│   • Multiple clients can connect                                │
│   • Production-like architecture                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Make Commands

```bash
make help         # Show available commands
make install      # Install dependencies  
make server       # Run MCP server (HTTP, default)
make server-stdio # Run MCP server (stdio mode)
make client       # Run simple client demo
make agent        # Run LangChain agent demo
make test         # Auto-test: start server, run client, stop server
make clean        # Remove cache files
```

## Important Notes

1. **Two-Terminal Workflow**: With HTTP transport, you need two terminals - one for the server, one for the client

2. **Server URL**: Default is `http://localhost:8000/mcp` - change in server.py if needed

3. **Authentication**: For production, add headers in client config:
   ```python
   mcp_config = {
       "devops-tools": {
           "transport": "streamable_http",
           "url": "http://localhost:8000/mcp",
           "headers": {"Authorization": "Bearer <token>"}
       }
   }
   ```

4. **DIAL Support**: The `langgraph_consumer.py` uses the workshop's `setup_llm` module which supports both DIAL and OpenAI

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [LangChain v1 Release Notes](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [LangGraph v1 Release Notes](https://docs.langchain.com/oss/python/releases/langgraph-v1)
- [langchain-mcp-adapters](https://docs.langchain.com/oss/python/langchain/mcp)
