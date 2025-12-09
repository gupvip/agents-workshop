.PHONY: help install server server-stdio client agent test clean

# Default Python from venv
PYTHON = ../../../.venv/bin/python

help:
	@echo "MCP DevOps Tools - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make server        - Run the MCP server (HTTP mode) at http://localhost:8000/mcp"
	@echo "  make server-stdio  - Run the MCP server (stdio mode, for subprocess spawning)"
	@echo "  make client        - Run the simple MCP client demo (requires server running)"
	@echo "  make agent         - Run the LangGraph agent demo (requires server running)"
	@echo "  make test          - Quick test: start server, run client, stop server"
	@echo "  make clean         - Remove cache files"
	@echo ""
	@echo "📖 Typical workflow:"
	@echo "   Terminal 1: make server"
	@echo "   Terminal 2: make client (or make agent)"
	@echo ""

install:
	@echo "📦 Installing dependencies..."
	$(PYTHON) -m pip install -q -r requirements.txt
	@echo "✅ Dependencies installed"

server:
	@echo "🚀 Starting MCP server (HTTP transport)..."
	@echo "   Server URL: http://localhost:8000/mcp"
	@echo "   Press Ctrl+C to stop"
	@echo ""
	$(PYTHON) server.py

server-stdio:
	@echo "🚀 Starting MCP server (stdio transport)..."
	@echo "   Press Ctrl+C to stop"
	$(PYTHON) server.py --stdio

client:
	@echo "🔌 Running simple MCP client..."
	@echo "   Make sure server is running: make server"
	@echo ""
	$(PYTHON) simple_client.py

agent:
	@echo "🤖 Running LangGraph agent with MCP tools..."
	@echo "   Make sure server is running: make server"
	@echo ""
	$(PYTHON) langgraph_consumer.py

test:
	@echo "🧪 Running test (starting server in background)..."
	@$(PYTHON) server.py &
	@sleep 2
	@$(PYTHON) simple_client.py || true
	@pkill -f "server.py" || true
	@echo ""
	@echo "✅ Test complete!"

clean:
	@echo "🧹 Cleaning cache files..."
	rm -rf __pycache__ .ipynb_checkpoints
	@echo "✅ Clean complete"
