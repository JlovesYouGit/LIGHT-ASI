#!/bin/bash
# Light-ASI MCP CLI Examples
# Shows how to call MCP tools via JSON-RPC like npx-styled commands

echo "🔌 Light-ASI MCP CLI Examples"
echo "================================"
echo ""

# Method 1: Using MCP Inspector (recommended)
echo "1️⃣ Using MCP Inspector (npx-style)"
echo "-----------------------------------"
echo "npx @modelcontextprotocol/inspector python3 mcp/server.py"
echo ""
echo "This opens an interactive web UI to test all MCP tools"
echo ""

# Method 2: Direct Python call (simplest)
echo "2️⃣ Direct Python Import"
echo "-------------------------"
cat << 'EOF'
python3 << 'PYTHON'
import asyncio
import sys
import json
sys.path.insert(0, '.')
from mcp.server import query_asi

async def main():
    result = await query_asi("What is AI?", 3)
    print(json.dumps(json.loads(result), indent=2))

asyncio.run(main())
PYTHON
EOF
echo ""

# Method 3: JSON-RPC via stdin (full session)
echo "3️⃣ JSON-RPC via stdin (requires full session)"
echo "----------------------------------------------"
echo "# Create a JSON-RPC session file:"
cat << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "cli", "version": "1.0"}
  }
}
EOF
echo ""
echo "# Then send tool calls after initialization"
echo ""

# Method 4: Using the demo script
echo "4️⃣ Using Demo Script"
echo "--------------------"
echo "python3 demo_mcp_usage.py"
echo ""

# Method 5: Using the usage example
echo "5️⃣ Using Usage Example (Pinecone-style)"
echo "-----------------------------------------"
echo "python3 mcp_usage_example.py"
echo ""

echo "================================"
echo "✅ Most common usage: Direct Python import"
echo "   from mcp.server import query_asi"
echo "   result = await query_asi('query', 3)"
