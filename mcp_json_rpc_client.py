#!/usr/bin/env python3
"""
Light-ASI MCP JSON-RPC Client

This demonstrates how to call MCP tools via JSON-RPC protocol,
similar to how you would use npx-style commands.
"""

import json
import subprocess
import sys

def call_mcp_tool(tool_name, args=None):
    """
    Call an MCP tool via JSON-RPC protocol.
    
    This is similar to how npx @modelcontextprotocol/cli would work,
    but adapted for the local Python MCP server.
    
    Args:
        tool_name: Name of the MCP tool to call
        args: Dictionary of arguments for the tool
    
    Returns:
        JSON-RPC response from the MCP server
    """
    if args is None:
        args = {}
    
    # Construct JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args
        }
    }
    
    # For stdio-based MCP, we would pipe this to the server process
    # Since this is a local Python server, we can also call it directly
    print(f"📡 JSON-RPC Request:")
    print(json.dumps(request, indent=2))
    print()
    
    return request

def main():
    """Demonstrate JSON-RPC calls to MCP tools."""
    
    print("🔌 Light-ASI MCP JSON-RPC Client")
    print("=" * 60)
    print("This shows how to call MCP tools via JSON-RPC protocol\n")
    
    # Example 1: Call query_asi via JSON-RPC
    print("1️⃣ Call query_asi via JSON-RPC")
    print("-" * 50)
    query_request = call_mcp_tool("query_asi", {
        "text": "What is artificial intelligence?",
        "top_k": 3
    })
    
    # Example 2: Call index_text via JSON-RPC
    print("\n2️⃣ Call index_text via JSON-RPC")
    print("-" * 50)
    index_request = call_mcp_tool("index_text", {
        "text": "Machine learning enables systems to learn from data.",
        "source": "json_rpc_demo",
        "priority": "high"
    })
    
    # Example 3: Call get_system_status via JSON-RPC
    print("\n3️⃣ Call get_system_status via JSON-RPC")
    print("-" * 50)
    status_request = call_mcp_tool("get_system_status", {})
    
    # Example 4: Call get_raw_graph_dump via JSON-RPC
    print("\n4️⃣ Call get_raw_graph_dump via JSON-RPC")
    print("-" * 50)
    dump_request = call_mcp_tool("get_raw_graph_dump", {
        "limit": 10
    })
    
    print("\n" + "=" * 60)
    print("📝 To actually execute these JSON-RPC requests:")
    print()
    print("Option 1: Direct Python import (easiest)")
    print("  ```python")
    print("  from mcp.server import query_asi")
    print("  result = await query_asi('What is AI?', 3)")
    print("  ```")
    print()
    print("Option 2: Via MCP client (stdio)")
    print("  ```bash")
    print("  echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"query_asi\",\"arguments\":{\"text\":\"What is AI?\"}}}' | python3 mcp/server.py")
    print("  ```")
    print()
    print("Option 3: Via MCP Inspector")
    print("  ```bash")
    print("  npx @modelcontextprotocol/inspector python3 mcp/server.py")
    print("  ```")

if __name__ == "__main__":
    main()
