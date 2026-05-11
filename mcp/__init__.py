"""
Light-ASI MCP (Model Context Protocol) Integration

This module provides MCP server functionality for the Light-ASI system,
allowing AI models like Claude Sonnet and GPT to interact with the ASI
through standardized tool interfaces.

The MCP server exposes the following capabilities:
- Query the ASI's knowledge graph
- Search real-time world-net data
- Index new information
- Monitor system status and emergence
- Direct URL latching for targeted learning

Usage:
    python -m mcp.server  # Start MCP server
    
For integration with Claude Desktop, add to claude_desktop_config.json:
{
  "mcpServers": {
    "light-asi": {
      "command": "python3",
      "args": ["/path/to/ASI-/mcp/server.py"]
    }
  }
}
"""

__version__ = "0.2.0"
__author__ = "Light-ASI Project"