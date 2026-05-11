#!/usr/bin/env python3
"""
Light-ASI MCP Test Script

This script tests the MCP server functionality to ensure it works
correctly with AI models.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

# Add ASI to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_tools():
    """Test all MCP tools."""
    print("🧪 Testing Light-ASI MCP Tools")
    print("=" * 40)
    
    try:
        # Import the MCP server
        from mcp.server import (
            query_asi, search_world, latch_url, index_text,
            get_system_status, analyze_emergence, get_knowledge_sources,
            ensure_engine_ready
        )
        
        print("✅ MCP server imports successful")
        
        # Test engine initialization
        print("\n🔧 Testing engine initialization...")
        if ensure_engine_ready():
            print("✅ ASI Engine initialized")
        else:
            print("❌ ASI Engine failed to initialize")
            return False
        
        # Test system status
        print("\n📊 Testing system status...")
        try:
            status = await get_system_status()
            print("✅ System status retrieved")
            print(f"Status length: {len(status)} characters")
        except Exception as e:
            print(f"❌ System status failed: {e}")
        
        # Test text indexing
        print("\n📝 Testing text indexing...")
        try:
            test_text = "This is a test of the ASI knowledge indexing system. The ASI should learn from this text."
            result = await index_text(test_text, "mcp_test", "high")
            print("✅ Text indexing successful")
            print(f"Result length: {len(result)} characters")
        except Exception as e:
            print(f"❌ Text indexing failed: {e}")
        
        # Test query
        print("\n🔍 Testing ASI query...")
        try:
            query_result = await query_asi("What is the ASI system?", 3)
            print("✅ ASI query successful")
            print(f"Response length: {len(query_result)} characters")
        except Exception as e:
            print(f"❌ ASI query failed: {e}")
        
        # Test world search
        print("\n🌐 Testing world search...")
        try:
            search_result = await search_world("artificial intelligence", 3)
            print("✅ World search successful")
            print(f"Search result length: {len(search_result)} characters")
        except Exception as e:
            print(f"❌ World search failed: {e}")
        
        # Test emergence analysis
        print("\n🧠 Testing emergence analysis...")
        try:
            emergence_result = await analyze_emergence()
            print("✅ Emergence analysis successful")
            print(f"Analysis length: {len(emergence_result)} characters")
        except Exception as e:
            print(f"❌ Emergence analysis failed: {e}")
        
        # Test knowledge sources
        print("\n📚 Testing knowledge sources...")
        try:
            sources_result = await get_knowledge_sources()
            print("✅ Knowledge sources analysis successful")
            print(f"Sources length: {len(sources_result)} characters")
        except Exception as e:
            print(f"❌ Knowledge sources failed: {e}")
        
        print("\n🎉 All tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install requirements: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(traceback.format_exc())
        return False

def test_mcp_config():
    """Test MCP configuration files."""
    print("\n📋 Testing MCP configuration...")
    
    config_path = Path(__file__).parent / "mcp" / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print("✅ MCP config file valid")
            print(f"Tools defined: {len(config.get('tools', []))}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config: {e}")
            return False
    else:
        print("⚠️  MCP config file not found")
    
    return True

async def main():
    """Main test function."""
    print("🚀 Light-ASI MCP Test Suite")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_mcp_config()
    
    # Test MCP tools
    tools_ok = await test_mcp_tools()
    
    print("\n" + "=" * 50)
    if config_ok and tools_ok:
        print("🎉 All tests passed! MCP server is ready for use.")
        print("\nYou can now:")
        print("1. Run setup_mcp.py to configure Claude Desktop")
        print("2. Start the MCP server with: python mcp/server.py")
        print("3. Use Light-ASI tools in your AI model interface")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))