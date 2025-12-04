.PHONY: help install demo demo-stream database api memory interactive test clean setup venv

# Python interpreter
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python

# Default target
help:
	@echo "════════════════════════════════════════════════════════════════════════"
	@echo "  Incident Postmortem Generator - Makefile Commands"
	@echo "════════════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "  Setup & Installation:"
	@echo "    make setup          - Complete setup (venv + deps + .env)"
	@echo "    make venv           - Create virtual environment only"
	@echo "    make install        - Install Python dependencies"
	@echo ""
	@echo "  Run Demos:"
	@echo "    make demo           - Run synthetic demo (batch mode)"
	@echo "    make demo-stream    - Run demo with streaming output"
	@echo "    make database       - Run database outage sample"
	@echo "    make api            - Run API timeout sample"
	@echo "    make memory         - Run memory leak sample"
	@echo "    make interactive    - Run in interactive mode"
	@echo ""
	@echo "  Testing & Maintenance:"
	@echo "    make test           - Run tests"
	@echo "    make clean          - Clean cache and remove venv"
	@echo ""
	@echo "════════════════════════════════════════════════════════════════════════"
	@echo ""

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "🔧 Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		echo "✅ Virtual environment created!"; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi

# Complete setup
setup: venv
	@echo "🚀 Setting up Incident Postmortem Generator..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env and add your API keys!"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@echo "📦 Installing dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Setup complete! Run 'make demo' to test."

# Install dependencies
install: venv
	@echo "📦 Installing dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Installation complete!"

# Run synthetic demo
demo: venv
	@echo "🚀 Running synthetic demo..."
	@$(PYTHON_VENV) main.py --demo

# Run demo with streaming
demo-stream: venv
	@echo "🚀 Running demo with streaming..."
	@$(PYTHON_VENV) main.py --demo --stream

# Run database outage sample
database: venv
	@echo "📊 Running database outage incident..."
	@$(PYTHON_VENV) main.py --file sample_incidents/database_outage.json --stream

# Run API timeout sample
api: venv
	@echo "⚡ Running API timeout incident..."
	@$(PYTHON_VENV) main.py --file sample_incidents/api_timeout.json --stream

# Run memory leak sample
memory: venv
	@echo "💾 Running memory leak incident..."
	@$(PYTHON_VENV) main.py --file sample_incidents/memory_leak.json --stream

# Run interactive mode
interactive: venv
	@echo "🎯 Starting interactive mode..."
	@$(PYTHON_VENV) main.py --interactive

# Run tests
test: venv
	@echo "🧪 Running tests..."
	@$(VENV_BIN)/pytest test_postmortem.py -v

# Clean cache files and remove venv
clean:
	@echo "🧹 Cleaning cache files and virtual environment..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(VENV)
	@echo "✅ Cleanup complete!"
