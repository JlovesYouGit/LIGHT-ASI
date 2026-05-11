#!/bin/bash
# Light-ASI MCP Server Launcher

echo "🧠 Starting Light-ASI MCP Server..."
echo "=================================="

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Set PYTHONPATH to include the ASI directory
export PYTHONPATH="$DIR:$PYTHONPATH"

# Change to ASI directory
cd "$DIR"

# Check if requirements are installed
echo "Checking dependencies..."
python3 -c "import mcp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ MCP package not found. Installing requirements..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements. Please install manually:"
        echo "   pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo "✅ Dependencies OK"
echo "🚀 Starting MCP server..."
echo ""

# Start the MCP server
python3 mcp/server.py

echo ""
echo "🛑 MCP Server stopped"