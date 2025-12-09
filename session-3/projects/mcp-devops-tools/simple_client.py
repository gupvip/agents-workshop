"""
Simple MCP Client Example

This is a minimal example showing how to connect to an MCP server
over HTTP and call tools directly. Great for understanding the basics
before moving to LangGraph integration.

Prerequisites:
    1. Start the MCP server first: python server.py
    2. Then run this client:       python simple_client.py

The server runs at http://localhost:8000/mcp by default.
"""

import asyncio

# Server configuration - must match server.py
MCP_SERVER_URL = "http://localhost:8000/mcp"


async def main():
    """Demonstrate basic MCP client usage over HTTP."""
    
    print("=" * 50)
    print("Simple MCP Client Demo (HTTP Transport)")
    print("=" * 50)
    
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError:
        print("\n❌ mcp package not installed.")
        print("   Install with: pip install mcp")
        return
    
    print(f"\n📡 Connecting to MCP server at {MCP_SERVER_URL}...")
    
    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
            
                # List available tools
                print("\n✅ Connected! Listing tools...")
                tools_result = await session.list_tools()
                
                print(f"\n📦 Available tools ({len(tools_result.tools)}):")
                for tool in tools_result.tools:
                    print(f"   • {tool.name}")
                    print(f"     {tool.description[:60]}...")
                
                # Call list_services
                print("\n" + "-" * 50)
                print("Calling: list_services()")
                print("-" * 50)
                
                result = await session.call_tool("list_services", arguments={})
                content = result.content[0].text
                print(content)
                
                # Call get_service_status
                print("\n" + "-" * 50)
                print("Calling: get_service_status('api-gateway')")
                print("-" * 50)
                
                result = await session.call_tool(
                    "get_service_status",
                    arguments={"service_name": "api-gateway"}
                )
                content = result.content[0].text
                print(content)
                
                # Call get_recent_logs
                print("\n" + "-" * 50)
                print("Calling: get_recent_logs('order-service', log_level='ERROR')")
                print("-" * 50)
                
                result = await session.call_tool(
                    "get_recent_logs",
                    arguments={"service_name": "order-service", "log_level": "ERROR"}
                )
                content = result.content[0].text
                print(content)
                
                # Call get_metrics
                print("\n" + "-" * 50)
                print("Calling: get_metrics('api-gateway')")
                print("-" * 50)
                
                result = await session.call_tool(
                    "get_metrics",
                    arguments={"service_name": "api-gateway"}
                )
                content = result.content[0].text
                print(content)
                
                print("\n" + "=" * 50)
                print("✅ Demo complete!")
                print("=" * 50)
    except Exception as e:
        if "Connection refused" in str(e) or "Cannot connect" in str(e):
            print(f"\n❌ Could not connect to MCP server at {MCP_SERVER_URL}")
            print("   Make sure the server is running: python server.py")
        else:
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
