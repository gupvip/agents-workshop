"""
LangGraph Consumer for MCP DevOps Tools

This example shows how to:
1. Connect to the MCP server over HTTP
2. Load MCP tools as LangChain tools  
3. Use them with LangChain's create_agent (LangChain v1 API)

Updated for LangChain v1 and LangGraph v1 (December 2024)

Prerequisites:
    1. Start the MCP server first: python server.py
    2. Then run this agent:        python langgraph_consumer.py

The server runs at http://localhost:8000/mcp by default.
"""

import asyncio
import sys
sys.path.append("../../..")

# LangChain v1: create_agent replaces langgraph.prebuilt.create_react_agent
from langchain.agents import create_agent

# Import workshop's LLM setup
try:
    from setup_llm import get_chat_model, verify_setup
except ImportError:
    print("❌ Could not import setup_llm. Run from mcp-devops-tools directory.")
    exit(1)

# Server configuration - must match server.py
MCP_SERVER_URL = "http://localhost:8000/mcp"


async def main():
    """Main function demonstrating MCP + LangGraph integration."""
    
    print("=" * 60)
    print("MCP + LangGraph Integration Demo (HTTP Transport)")
    print("=" * 60)
    
    # Verify LLM setup
    if not verify_setup():
        print("❌ LLM setup verification failed")
        exit(1)
    
    # Import MCP adapters (requires langchain-mcp-adapters)
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        print("\n❌ langchain-mcp-adapters not installed.")
        print("   Install with: pip install langchain-mcp-adapters")
        exit(1)
    
    # Configure MCP server connection using HTTP transport
    # This is the production-like approach: client connects to a running server
    # The server must be started separately: python server.py
    mcp_config = {
        "devops-tools": {
            "transport": "streamable_http",
            "url": MCP_SERVER_URL,
            # Optional: Add headers for authentication
            # "headers": {"Authorization": "Bearer <token>"}
        }
    }
    
    print(f"\n📡 Connecting to MCP server at {MCP_SERVER_URL}...")
    
    try:
        # langchain-mcp-adapters 0.1.0+ new API
        mcp_client = MultiServerMCPClient(mcp_config)
        
        # Get tools from MCP server (async)
        tools = await mcp_client.get_tools()
    except Exception as e:
        if "Connection refused" in str(e) or "Cannot connect" in str(e):
            print(f"\n❌ Could not connect to MCP server at {MCP_SERVER_URL}")
            print("   Make sure the server is running: python server.py")
            exit(1)
        raise
    
    print(f"✅ Connected! Loaded {len(tools)} tools:")
    for tool in tools:
        print(f"   • {tool.name}: {tool.description[:50]}...")
    
    # Create LLM using workshop setup
    llm = get_chat_model(temperature=0)
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are a DevOps assistant with access to tools for:
        - Checking service status
        - Fetching logs
        - Getting metrics
        - Creating incident tickets
        
        When investigating issues:
        1. First list services to understand the environment
        2. Check status of relevant services
        3. Fetch logs if there are issues
        4. Get metrics for more details
        5. Create an incident if needed
        
        Be thorough but concise in your analysis."""
    )
    
    print("\n" + "=" * 60)
    print("Running DevOps Investigation")
    print("=" * 60)
    
    # Example task: Investigate a reported issue
    task = """
    Users are reporting slow response times. 
    Please investigate the services, check their status, 
    and determine if there are any issues that need attention.
    If you find problems, create an incident ticket.
    """
    
    print(f"\n📋 Task: {task.strip()}")
    print("\n🔍 Starting investigation...\n")
    
    # Run the agent
    result = await agent.ainvoke({
        "messages": [("user", task)]
    })
    
    # Print final response
    print("\n" + "=" * 60)
    print("Investigation Complete")
    print("=" * 60)
    
    # Get the last AI message
    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and msg.content:
            print(f"\n{msg.content}")
            break


if __name__ == "__main__":
    asyncio.run(main())
