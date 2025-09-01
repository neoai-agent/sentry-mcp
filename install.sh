#!/bin/bash

# Sentry MCP Server Installation Script

set -e

echo "Installing Sentry MCP Server..."

# Check if Python 3.8+ is installed
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8 or higher is required. Found Python $python_version"
    exit 1
fi

echo "Python version $python_version detected"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "sentry-venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv sentry-venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source sentry-venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
echo "Installing Sentry MCP Server..."
pip install -e .

# Install development dependencies if requested
if [ "$1" = "--dev" ]; then
    echo "Installing development dependencies..."
    pip install -e ".[dev]"
fi

echo ""
echo "Sentry MCP Server installed successfully!"
echo ""
echo "Next steps:"
echo "1. Set up your environment variables:"
echo "   export SENTRY_API_TOKEN='your-sentry-api-token'"
echo "   export SENTRY_ORG='your-organization'"
echo "   export OPENAI_API_KEY='your-openai-api-key'"
echo ""
echo "2. Run the server:"
echo "   source sentry-venv/bin/activate"
echo "   sentry-mcp"
echo ""
echo "3. Or run with explicit arguments:"
echo "   sentry-mcp --sentry-api-token 'your-token' --sentry-org 'your-org' --openai-api-key 'your-key'"
echo ""
echo "For more information, see the README.md file"
