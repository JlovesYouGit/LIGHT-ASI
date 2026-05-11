#!/usr/bin/env python3
"""
Light-ASI MCP Setup Script

This script helps configure the Light-ASI MCP server for integration
with AI models like Claude Desktop, GPT, and other MCP-compatible clients.
"""

import json
import os
import sys
from pathlib import Path

def get_asi_path():
    """Get the absolute path to the ASI directory."""
    return Path(__file__).parent.absolute()

def generate_claude_config():
    """Generate Claude Desktop configuration."""
    asi_path = get_asi_path()
    server_path = asi_path / "mcp" / "server.py"
    
    config = {
        "mcpServers": {
            "light-asi": {
                "command": "python3",
                "args": [str(server_path)],
                "env": {
                    "PYTHONPATH": str(asi_path)
                }
            }
        }
    }
    
    return config

def find_claude_config_path():
    """Find Claude Desktop configuration file path."""
    home = Path.home()
    
    # Common Claude Desktop config locations
    possible_paths = [
        home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",  # macOS
        home / ".config" / "claude" / "claude_desktop_config.json",  # Linux
        home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",  # Windows
    ]
    
    for path in possible_paths:
        if path.parent.exists():
            return path
    
    return None

def setup_claude_integration():
    """Set up Claude Desktop integration."""
    print("🧠 Setting up Light-ASI MCP integration for Claude Desktop...")
    
    config_path = find_claude_config_path()
    if not config_path:
        print("❌ Could not find Claude Desktop config directory.")
        print("Please create the config manually using the generated configuration.")
        return False
    
    # Generate new config
    new_config = generate_claude_config()
    
    # Read existing config if it exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            
            # Merge configurations
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            
            existing_config["mcpServers"]["light-asi"] = new_config["mcpServers"]["light-asi"]
            final_config = existing_config
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  Error reading existing config: {e}")
            print("Creating new configuration...")
            final_config = new_config
    else:
        final_config = new_config
    
    # Write configuration
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(final_config, f, indent=2)
        
        print(f"✅ Claude Desktop configuration updated: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error writing config: {e}")
        return False

def test_mcp_server():
    """Test if the MCP server can start properly."""
    print("🧪 Testing MCP server startup...")
    
    asi_path = get_asi_path()
    server_path = asi_path / "mcp" / "server.py"
    
    if not server_path.exists():
        print(f"❌ MCP server not found: {server_path}")
        return False
    
    # Test import
    sys.path.insert(0, str(asi_path))
    try:
        import mcp.server
        print("✅ MCP server imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install requirements: pip install -r requirements.txt")
        return False

def print_manual_config():
    """Print manual configuration instructions."""
    config = generate_claude_config()
    
    print("\n" + "="*60)
    print("📋 MANUAL CONFIGURATION")
    print("="*60)
    print("\nIf automatic setup failed, add this to your Claude Desktop config:")
    print(f"\nFile location: ~/.config/claude/claude_desktop_config.json")
    print("\nConfiguration:")
    print(json.dumps(config, indent=2))
    print("\n" + "="*60)

def main():
    """Main setup function."""
    print("🚀 Light-ASI MCP Setup")
    print("=" * 40)
    
    # Test server
    if not test_mcp_server():
        print("\n❌ MCP server test failed. Please fix errors before continuing.")
        return 1
    
    # Setup Claude integration
    success = setup_claude_integration()
    
    if success:
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Look for 'Light-ASI' tools in Claude's interface")
        print("3. Try asking Claude to use 'query_asi' or 'get_system_status'")
        print("\n💡 Example: 'Use the ASI to analyze the current state of AI development'")
    else:
        print_manual_config()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())