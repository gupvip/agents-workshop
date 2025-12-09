#!/bin/bash
# ============================================
# Agentic AI Workshop - macOS/Linux Setup Script
# ============================================
#
# This script sets up the complete development environment.
#
# Prerequisites:
#   - Python 3.10+ installed
#   - .env file with your DIAL_API_KEY
#
# Usage: 
#   chmod +x setup.sh
#   ./setup.sh
# ============================================

set -e

echo ""
echo "===================================================="
echo "  Agentic AI Workshop - One-Click Setup"
echo "===================================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check for Python 3
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if 'python' is Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    print_error "Python 3 is not installed or not in PATH"
    echo ""
    echo "Please install Python 3.10+ from:"
    echo "  - macOS: brew install python@3.12"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  - Or download from: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

print_info "Found Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10+ is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

# Check if venv module is available
if ! $PYTHON_CMD -c "import venv" &> /dev/null; then
    print_error "Python venv module is not available"
    echo ""
    echo "Please install it:"
    echo "  - Ubuntu/Debian: sudo apt install python3-venv"
    echo "  - Fedora: sudo dnf install python3-venv"
    exit 1
fi

# Run the main setup script (includes Jupyter launch)
echo ""
print_info "Running setup script..."
echo ""

$PYTHON_CMD "$SCRIPT_DIR/setup.py"

if [ $? -ne 0 ]; then
    print_error "Setup failed. Please check the error messages above."
    exit 1
fi
