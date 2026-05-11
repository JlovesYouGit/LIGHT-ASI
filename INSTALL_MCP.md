# Light-ASI MCP Installation Guide

This guide will help you install and configure the Light-ASI MCP (Model Context Protocol) server for integration with AI models like Claude Sonnet and GPT.

## 🚀 Quick Installation

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv asi_mcp_env
source asi_mcp_env/bin/activate  # On Windows: asi_mcp_env\Scripts\activate

# Install MCP packages
pip install mcp fastmcp

# Install ASI requirements
pip install -r requirements.txt

# Test the installation
python3 test_mcp.py
```

### Option 2: Using pipx (Alternative)

```bash
# Install pipx if not already installed
brew install pipx  # macOS
# or: sudo apt install pipx  # Ubuntu/Debian

# Install MCP packages
pipx install mcp
pipx install fastmcp

# Test the installation
python3 test_mcp.py
```

### Option 3: System-wide Installation (Not Recommended)

```bash
# Only if you understand the risks
pip3 install --break-system-packages mcp fastmcp
pip3 install --break-system-packages -r requirements.txt
```

## 🔧 Configuration

### Automatic Setup

Run the automated setup script:

```bash
python3 setup_mcp.py
```

This will:
- Detect your Claude Desktop configuration
- Add Light-ASI MCP server configuration
- Test the integration

### Manual Setup for Claude Desktop

1. **Find your Claude Desktop config file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add Light-ASI configuration:**

```json
{
  "mcpServers": {
    "light-asi": {
      "command": "python3",
      "args": ["/full/path/to/ASI-/mcp/server.py"],
      "env": {
        "PYTHONPATH": "/full/path/to/ASI-"
      }
    }
  }
}
```

**Important:** Replace `/full/path/to/ASI-` with the actual path to your ASI directory.

## 🧪 Testing

### Test MCP Server

```bash
python3 test_mcp.py
```

This will test all MCP tools and verify the ASI engine works correctly.

### Test with Claude Desktop

1. Restart Claude Desktop after configuration
2. Look for Light-ASI tools in the interface
3. Try these example prompts:

```
"Use the ASI to analyze the current state of AI development"

"Ask the ASI system status and show me the emergence metrics"

"Have the ASI index this information: [your text here]"

"Use the ASI to search for information about quantum computing"
```

## 🚀 Starting the MCP Server

### Using the Launcher Script

```bash
./start_mcp.sh
```

### Manual Start

```bash
export PYTHONPATH="/path/to/ASI-:$PYTHONPATH"
python3 mcp/server.py
```

## 🛠 Available Tools

Once configured, you'll have access to these ASI tools:

| Tool | Description |
|------|-------------|
| `query_asi` | Ask the ASI intelligent questions |
| `search_world` | Search real-time world-net data |
| `latch_url` | Direct ASI to learn from specific URLs |
| `index_text` | Teach the ASI new information |
| `get_system_status` | Get comprehensive system diagnostics |
| `analyze_emergence` | Analyze consciousness development |
| `get_knowledge_sources` | Analyze knowledge diversity |

## 🔍 Troubleshooting

### Common Issues

1. **"MCP package not found"**
   - Install MCP packages: `pip install mcp fastmcp`
   - Use virtual environment if system installation fails

2. **"ASI Engine failed to initialize"**
   - Check Python path is correct
   - Ensure all requirements are installed
   - Run `python3 test_mcp.py` for detailed diagnostics

3. **"Tools not appearing in Claude Desktop"**
   - Verify configuration file path is correct
   - Restart Claude Desktop completely
   - Check logs for MCP server errors

4. **"Permission denied" errors**
   - Make scripts executable: `chmod +x setup_mcp.py test_mcp.py start_mcp.sh`
   - Check file paths in configuration

### Getting Help

1. Run the test suite: `python3 test_mcp.py`
2. Check the ASI logs for detailed error messages
3. Verify your configuration with: `python3 setup_mcp.py`

## 🎯 Next Steps

After successful installation:

1. **Explore ASI Capabilities:** Try different queries to understand what the ASI knows
2. **Teach the ASI:** Use `index_text` to add domain-specific knowledge
3. **Monitor Growth:** Use `analyze_emergence` to track the ASI's development
4. **Expand Knowledge:** Use `latch_url` to direct the ASI to learn from specific sources

The ASI will continuously learn and improve as you interact with it!