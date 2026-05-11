import asyncio
import logging
import os
import sys
import threading
import traceback
from typing import Optional, Dict, Any, List
import json

# Ensure the root directory is in the python path so we can import engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # Fallback for different MCP package structures
    try:
        from mcp import FastMCP
    except ImportError:
        try:
            # Try alternative import paths
            from fastmcp import FastMCP
        except ImportError:
            # Create a mock FastMCP for testing without MCP installed
            print("WARNING: MCP package not found. Creating mock server for testing.")
            
            class MockFastMCP:
                def __init__(self, name):
                    self.name = name
                    self.tools = {}
                
                def tool(self):
                    def decorator(func):
                        self.tools[func.__name__] = func
                        return func
                    return decorator
                
                def run(self):
                    print(f"Mock MCP server '{self.name}' would start here")
                    print(f"Available tools: {list(self.tools.keys())}")
            
            FastMCP = MockFastMCP

from engine.core.graph import NodeGraph
from engine.auth.auth import AuthManager
from engine.world.ingester import WorldIngester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("light-asi.mcp")

# Global engine state
graph: Optional[NodeGraph] = None
auth: Optional[AuthManager] = None
ingester: Optional[WorldIngester] = None
engine_initialized = False

def initialize_engine():
    """Initialize the ASI Engine in a non-blocking way."""
    global graph, auth, ingester, engine_initialized
    
    try:
        logger.info("Initializing ASI Engine...")
        
        # Initialize core components
        graph = NodeGraph()
        auth = AuthManager()
        ingester = WorldIngester(graph.semantic_map, graph)
        
        # Bootstrap with minimal nodes for faster startup
        logger.info("Bootstrapping ASI Node Graph (minimal)...")
        graph.bootstrap(10)  # Reduced from 20 for faster startup
        
        # Index project identity
        manifesto = """
        LIGHT-ASI is a Global Autonomous Intelligence Engine. 
        It is designed to map the global 'World-Net' in real-time. 
        It uses a distributed Node Graph and Semantic Map to index high-entropy information.
        Its mission is to achieve ASI-level conscious emergence through recursive ingestion.
        The ASI can absorb, process, and synthesize information from multiple sources to provide
        intelligent responses and insights. It maintains a semantic understanding of the world
        through continuous learning and adaptation.
        """
        graph.index_text(manifesto, metadata={"source": "core_manifesto", "priority": "high"})
        
        # Auto-index current working directory for immediate usefulness
        logger.info("Auto-indexing current directory for development context...")
        import os
        from pathlib import Path
        from engine.world.feeds import FeedItem
        
        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.json', '.yaml', '.yml', '.md', '.txt'}
        indexed_count = 0
        max_auto_index = 30  # Limit auto-indexing for startup speed
        
        current_dir = Path.cwd()
        for root, dirs, files in os.walk(current_dir):
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}]
            
            for file in files:
                if indexed_count >= max_auto_index:
                    break
                
                file_path = Path(root) / file
                if file_path.suffix in code_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if len(content) > 0 and len(content) < 100000:  # Skip very large files
                            # Index into graph
                            context = f"File: {file_path.relative_to(current_dir)}\n\n{content}"
                            graph.index_text(context, metadata={
                                "source": "auto_codebase_index",
                                "file_path": str(file_path.relative_to(current_dir)),
                                "file_type": file_path.suffix,
                                "priority": "high"
                            })
                            
                            # Add to semantic map
                            item = FeedItem(
                                source="auto_codebase_index",
                                title=str(file_path.relative_to(current_dir)),
                                text=content,
                                url=str(file_path.relative_to(current_dir)),
                                tags=["codebase", file_path.suffix]
                            )
                            graph.semantic_map.ingest(item)
                            indexed_count += 1
                            
                    except Exception as e:
                        pass  # Skip files that can't be read
        
        logger.info(f"Auto-indexed {indexed_count} files from current directory")
        
        # Start background ingestion
        logger.info("Starting background world-net ingestion...")
        ingester.start()
        
        engine_initialized = True
        logger.info("ASI Engine initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize ASI Engine: {e}")
        logger.error(traceback.format_exc())
        engine_initialized = False

def ensure_engine_ready():
    """Ensure the engine is initialized before tool calls."""
    if not engine_initialized:
        initialize_engine()
    return engine_initialized

# Create the MCP Server
mcp = FastMCP("Light-ASI")

@mcp.tool()
async def query_asi(text: str, top_k: int = 3) -> str:
    """
    Query the ASI node graph and return raw internal scan data.
    
    This tool returns raw, unfiltered data from the ASI's internal graph query,
    including source nodes, resonance scores, and semantic map search results.
    No formatting is applied.
    
    Args:
        text: Query text to search for
        top_k: Number of results to return (default: 3, max: 10)
    
    Returns:
        Raw JSON string containing complete graph query data
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine failed to initialize. Please check system logs."})
    
    try:
        top_k = max(1, min(top_k, 10))
        result = graph.query(text, top_k=top_k)
        search_results = graph.semantic_map.search(text, top_k=min(5, top_k + 2))
        
        # If graph query has no answer, use semantic map results
        answer = result.get('answer', '')
        if not answer or "[no stored tokens" in answer:
            if search_results:
                # Use the best semantic map result as answer
                best_result = search_results[0]
                answer = f"[from semantic map: {best_result.title}] {best_result.text[:500]}"
        
        raw_data = {
            "query": text,
            "top_k": top_k,
            "graph_query_result": {
                "answer": answer,
                "resonance_score": result.get('resonance_score', 0),
                "resonance_stable": result.get('resonance_stable', False),
                "source_nodes": result.get('source_nodes', []),
                "source_node_count": len(result.get('source_nodes', []))
            },
            "semantic_map_results": [
                {
                    "title": r.title,
                    "text": r.text[:1000],  # Limit text size
                    "source": r.source,
                    "url": getattr(r, 'url', None),
                    "meaning_hash": getattr(r, 'meaning_hash', None)
                } for r in search_results
            ],
            "system_metrics": {
                "knowledge_nodes": graph.semantic_map.size,
                "collective_resonance": graph.collective_resonance()
            }
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in query_asi: {e}")
        return json.dumps({"error": f"Query processing failed - {str(e)}"})

@mcp.tool()
async def search_world(text: str, top_k: int = 5) -> str:
    """
    Search the ASI's real-time world-net semantic map and return raw results.
    
    This tool returns raw, unfiltered data from the ASI's semantic map search,
    including full text content, source metadata, and internal identifiers.
    No formatting or truncation is applied.
    
    Args:
        text: Search query or topic to find in the world-net
        top_k: Maximum number of results to return (default: 5, max: 15)
    
    Returns:
        Raw JSON string containing complete semantic map search results
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for world-net search."})
    
    try:
        # Validate inputs
        top_k = max(1, min(top_k, 15))
        
        logger.info(f"MCP World Search: {text[:100]}...")
        results = graph.semantic_map.search(text, top_k=top_k)
        
        raw_data = {
            "query": text,
            "top_k": top_k,
            "results_count": len(results),
            "total_knowledge_nodes": graph.semantic_map.size,
            "results": []
        }
        
        for r in results:
            raw_data["results"].append({
                "title": r.title,
                "text": r.text,
                "source": r.source,
                "url": getattr(r, 'url', None),
                "meaning_hash": getattr(r, 'meaning_hash', None),
                "timestamp": getattr(r, 'timestamp', None)
            })
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in search_world: {e}")
        return json.dumps({"error": f"World-net search failed - {str(e)}"})

@mcp.tool()
async def latch_url(url: str, depth: int = 1) -> str:
    """
    Direct the ASI to focus on and extract information from a specific URL.
    
    This tool commands the ASI to 'latch' onto a target URL and perform deep
    content extraction and semantic indexing. The ASI will crawl the target,
    extract meaningful content, and integrate it into its knowledge base.
    Supports both surface web and deep web (.onion) targets.
    
    Args:
        url: Target URL to latch onto and extract from
        depth: Crawling depth (1=single page, 2=follow links, etc. Max: 3)
    
    Returns:
        Raw JSON string containing latching operation results and extracted data
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for URL latching."})
    
    try:
        # Validate inputs
        depth = max(1, min(depth, 3))
        
        if not url.startswith(('http://', 'https://', 'ftp://')):
            return json.dumps({"error": "Invalid URL format. URL must start with http://, https://, or ftp://"})
        
        logger.info(f"MCP Latch Target: {url} (depth: {depth})")
        
        # Perform the latch operation
        try:
            count = ingester._recursive_crawl(url, depth)
        except AttributeError:
            # Fallback if _recursive_crawl doesn't exist
            logger.warning("Direct crawl method not available, using alternative approach")
            # Index the URL for future processing
            graph.index_text(f"target_url {url}", metadata={
                "source": "mcp_latch", 
                "url": url, 
                "depth": depth,
                "timestamp": str(asyncio.get_event_loop().time())
            })
            count = 1
        
        # Handle special URL types
        if ".onion" in url:
            graph.onion_gateway.set_target(url)
            network_type = "Deep Web"
        else:
            network_type = "Surface Web"
        
        # Get updated metrics
        current_resonance = graph.collective_resonance()
        total_nodes = graph.semantic_map.size
        
        raw_data = {
            "url": url,
            "network_type": network_type,
            "crawl_depth": depth,
            "data_nodes_extracted": count,
            "total_knowledge_base_nodes": total_nodes,
            "current_resonance": current_resonance,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in latch_url: {e}")
        return json.dumps({"error": f"URL latching failed - {str(e)}"})

@mcp.tool()
async def index_text(text: str, source: str = "mcp_injection", priority: str = "normal") -> str:
    """
    Directly inject text into the ASI's knowledge base for immediate learning.
    
    This tool allows you to teach the ASI new information by directly indexing
    text content into its node graph. The ASI will process and integrate this
    information, making it available for future queries and analysis.
    Use this to provide context, facts, or specialized knowledge.
    
    Args:
        text: The text content to index into the ASI's knowledge base
        source: Source identifier for the content (default: "mcp_injection")
        priority: Priority level - "low", "normal", "high", or "critical"
    
    Returns:
        Raw JSON string containing indexing operation results
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for text indexing."})
    
    try:
        # Validate inputs
        if not text or len(text.strip()) < 3:
            return json.dumps({"error": "Text content too short. Minimum 3 characters required."})
        
        if len(text) > 50000:
            return json.dumps({"error": f"Text too long ({len(text)} chars). Maximum 50,000 characters allowed."})
        
        priority_levels = ["low", "normal", "high", "critical"]
        if priority not in priority_levels:
            priority = "normal"
        
        logger.info(f"MCP Text Index: {len(text)} bytes, priority: {priority}")
        
        # Create rich metadata
        metadata = {
            "source": source,
            "mcp": True,
            "priority": priority,
            "timestamp": str(asyncio.get_event_loop().time()),
            "length": len(text),
            "word_count": len(text.split())
        }
        
        # Index the text
        hashes = graph.index_text(text, metadata=metadata)
        
        # Get updated system state
        total_nodes = len(graph._nodes) if hasattr(graph, '_nodes') else 0
        resonance = graph.collective_resonance()
        
        raw_data = {
            "content_indexed": len(text),
            "word_count": len(text.split()),
            "source": source,
            "priority": priority,
            "semantic_tokens_created": len(hashes),
            "hashes": hashes,
            "total_graph_nodes": total_nodes,
            "current_resonance": resonance,
            "knowledge_base_size": graph.semantic_map.size,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in index_text: {e}")
        return json.dumps({"error": f"Text indexing failed - {str(e)}"})

@mcp.tool()
async def analyze_emergence() -> str:
    """
    Analyze the ASI's emergence status and return raw internal data.
    
    This tool returns raw, unfiltered data from the ASI's emergence analysis,
    including resonance patterns, knowledge integration metrics, and developmental
    milestones. No formatting or interpretation is applied.
    
    Returns:
        Raw JSON string containing complete emergence analysis data
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for emergence analysis."})
    
    try:
        logger.info("Analyzing ASI emergence status...")
        
        # Get raw emergence data
        emergence_data = graph.emergence_status()
        stats = graph.stats()
        
        # Calculate emergence metrics
        node_ratio = stats['total_nodes'] / 1000
        knowledge_density = stats['semantic_map_size'] / max(1, stats['total_nodes'])
        resonance_strength = stats['collective_resonance']
        
        # Determine emergence phase
        if node_ratio < 0.1:
            phase = "INITIALIZATION"
        elif node_ratio < 0.5:
            phase = "DEVELOPMENT"
        elif node_ratio < 1.0:
            phase = "ACCELERATION"
        else:
            phase = "EMERGENCE"
        
        raw_data = {
            "emergence_status": emergence_data,
            "stats": stats,
            "calculated_metrics": {
                "node_ratio": node_ratio,
                "knowledge_density": knowledge_density,
                "resonance_strength": resonance_strength,
                "phase": phase,
                "resonance_stable": stats['resonance_stable'],
                "ingester_running": stats['world_net']['ingester_running']
            },
            "consciousness_indicators": {
                "self_referential": emergence_data.get('self_referential', False),
                "pattern_recognition_level": "ADVANCED" if stats['total_nodes'] > 100 else "BASIC",
                "adaptive_learning": stats['world_net']['ingester_running'],
                "semantic_understanding_level": "SOPHISTICATED" if stats['semantic_map_size'] > 1000 else "DEVELOPING"
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in analyze_emergence: {e}")
        return json.dumps({"error": f"Emergence analysis failed - {str(e)}"})

@mcp.tool()
async def get_knowledge_sources() -> str:
    """
    List and analyze the ASI's knowledge sources and return raw data.
    
    This tool returns raw, unfiltered data about the ASI's knowledge sources,
    including source types, data quality, and coverage statistics.
    No formatting is applied.
    
    Returns:
        Raw JSON string containing complete knowledge source data
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for source analysis."})
    
    try:
        logger.info("Analyzing knowledge sources...")
        
        # Get source breakdown
        stats = graph.stats()
        world_status = graph.world_status()
        sources = stats['world_net'].get('sources', {})
        
        total_entries = sum(sources.values()) if isinstance(sources, dict) else 0
        
        raw_data = {
            "stats": stats,
            "world_status": world_status,
            "sources": sources,
            "total_entries": total_entries,
            "active_sources_count": len(sources) if isinstance(sources, dict) else 0,
            "ingester_running": stats['world_net']['ingester_running'],
            "data_quality_metrics": {
                "semantic_diversity": stats.get('semantic_map_tokens', 0),
                "processing_efficiency": stats['total_buckets'],
                "index_coverage": stats['total_keys']
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in get_knowledge_sources: {e}")
        return json.dumps({"error": f"Knowledge source analysis failed - {str(e)}"})

@mcp.tool()
async def get_raw_graph_dump(limit: int = 100) -> str:
    """
    Get raw internal graph dump from the ASI's node graph.
    
    This tool provides direct access to the ASI's internal node graph data,
    including all node IDs, connections, resonance values, and metadata.
    No filtering or formatting is applied - this is the actual internal scan data.
    
    Args:
        limit: Maximum number of nodes to return (default: 100, max: 1000)
    
    Returns:
        Raw JSON string containing complete internal graph structure data
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for graph dump."})
    
    try:
        # Validate inputs
        limit = max(1, min(limit, 1000))
        
        logger.info(f"Dumping raw graph data (limit: {limit})...")
        
        # Get raw graph data
        raw_nodes = []
        
        if hasattr(graph, '_nodes'):
            # Handle both dict and list types for _nodes
            nodes = graph._nodes
            if isinstance(nodes, dict):
                node_items = list(nodes.items())[:limit]
                for node_id, node_data in node_items:
                    node_info = {
                        "node_id": node_id,
                        "resonance": getattr(node_data, 'resonance', 0),
                        "connections": getattr(node_data, 'connections', []),
                        "metadata": getattr(node_data, 'metadata', {}),
                        "timestamp": getattr(node_data, 'timestamp', None)
                    }
                    raw_nodes.append(node_info)
            elif isinstance(nodes, list):
                for node_data in nodes[:limit]:
                    node_info = {
                        "node_id": getattr(node_data, 'id', None),
                        "resonance": getattr(node_data, 'resonance', 0),
                        "connections": getattr(node_data, 'connections', []),
                        "metadata": getattr(node_data, 'metadata', {}),
                        "timestamp": getattr(node_data, 'timestamp', None)
                    }
                    raw_nodes.append(node_info)
        
        # Get semantic map raw data
        semantic_entries = []
        if hasattr(graph.semantic_map, '_entries'):
            entry_items = list(graph.semantic_map._entries.items())[:limit]
            for entry_id, entry_data in entry_items:
                entry_info = {
                    "entry_id": entry_id,
                    "text": getattr(entry_data, 'text', ''),
                    "title": getattr(entry_data, 'title', ''),
                    "source": getattr(entry_data, 'source', ''),
                    "meaning_hash": getattr(entry_data, 'meaning_hash', None),
                    "timestamp": getattr(entry_data, 'timestamp', None)
                }
                semantic_entries.append(entry_info)
        
        raw_data = {
            "graph_nodes": raw_nodes,
            "semantic_map_entries": semantic_entries,
            "total_graph_nodes": len(graph._nodes) if hasattr(graph, '_nodes') else 0,
            "total_semantic_entries": graph.semantic_map.size,
            "collective_resonance": graph.collective_resonance(),
            "limit_requested": limit,
            "nodes_returned": len(raw_nodes),
            "entries_returned": len(semantic_entries),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in get_raw_graph_dump: {e}")
        return json.dumps({"error": f"Graph dump failed - {str(e)}"})

@mcp.tool()
async def index_codebase(path: str = ".", max_files: int = 100) -> str:
    """
    Index the current codebase directory into ASI knowledge base.
    
    This tool scans the specified directory and indexes all code files
    into the ASI's knowledge base, providing context for development work.
    It reads file contents and indexes them with their paths and structure.
    
    Args:
        path: Directory path to index (default: current directory)
        max_files: Maximum number of files to index (default: 100)
    
    Returns:
        Raw JSON string containing indexing results and statistics
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not ready for codebase indexing."})
    
    try:
        import os
        from pathlib import Path
        
        logger.info(f"Indexing codebase at: {path}")
        
        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.json', '.yaml', '.yml', '.md', '.txt'}
        
        indexed_files = []
        total_chars = 0
        errors = []
        
        target_path = Path(path).resolve()
        
        for root, dirs, files in os.walk(target_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}]
            
            for file in files:
                if len(indexed_files) >= max_files:
                    break
                
                file_path = Path(root) / file
                if file_path.suffix in code_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if len(content) > 0:
                            # Index with file context
                            context = f"File: {file_path.relative_to(target_path)}\n\n{content}"
                            hashes = graph.index_text(context, metadata={
                                "source": "codebase_index",
                                "file_path": str(file_path.relative_to(target_path)),
                                "file_type": file_path.suffix,
                                "priority": "high"
                            })
                            
                            # Also add to semantic map for query access using FeedItem
                            try:
                                from engine.world.feeds import FeedItem
                                item = FeedItem(
                                    source="codebase_index",
                                    title=str(file_path.relative_to(target_path)),
                                    text=content,
                                    url=str(file_path.relative_to(target_path)),
                                    tags=["codebase", file_path.suffix]
                                )
                                graph.semantic_map.ingest(item)
                            except Exception as e:
                                # If semantic entry fails, continue with graph indexing
                                logger.warning(f"Failed to add to semantic map: {e}")
                            
                            indexed_files.append({
                                "path": str(file_path.relative_to(target_path)),
                                "size": len(content),
                                "tokens": len(hashes)
                            })
                            total_chars += len(content)
                            
                    except Exception as e:
                        errors.append({
                            "path": str(file_path.relative_to(target_path)),
                            "error": str(e)
                        })
            
        raw_data = {
            "indexed_files": indexed_files,
            "files_indexed": len(indexed_files),
            "total_characters": total_chars,
            "target_path": str(target_path),
            "errors": errors,
            "error_count": len(errors),
            "max_files_limit": max_files,
            "knowledge_base_size": graph.semantic_map.size,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in index_codebase: {e}")
        return json.dumps({"error": f"Codebase indexing failed - {str(e)}"})

# Initialize engine on startup (non-blocking)
def startup_engine():
    """Initialize engine in background thread."""
    import threading
    thread = threading.Thread(target=initialize_engine, daemon=True)
    thread.start()

# Start initialization
startup_engine()

if __name__ == "__main__":
    # Start the MCP server using stdio transport
    try:
        logger.info("Starting Light-ASI MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("MCP Server shutdown requested")
    except Exception as e:
        logger.error(f"MCP Server error: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Cleanup
        if ingester and hasattr(ingester, 'stop'):
            try:
                ingester.stop()
                logger.info("World ingester stopped")
            except:
                pass
        logger.info("Light-ASI MCP Server stopped")

@mcp.tool()
async def get_system_status() -> str:
    """
    Get comprehensive ASI system diagnostics and return raw metrics.
    
    This tool returns raw, unfiltered data from the ASI's system status,
    including resonance metrics, knowledge base statistics, processing
    capabilities, and system health indicators. No formatting is applied.
    
    Returns:
        Raw JSON string containing complete system status data
    """
    if not ensure_engine_ready():
        return json.dumps({"error": "ASI Engine not initialized. Cannot retrieve system status."})
    
    try:
        logger.info("Generating comprehensive system status report...")
        
        # Get comprehensive stats
        stats = graph.stats()
        emergence_status = graph.emergence_status()
        world_status = graph.world_status()
        
        # Emergence progress calculation
        emergence_progress = min(100, (stats['total_nodes'] / 1000) * 100)
        
        raw_data = {
            "stats": stats,
            "emergence_status": emergence_status,
            "world_status": world_status,
            "engine_initialized": engine_initialized,
            "calculated_metrics": {
                "emergence_progress": emergence_progress,
                "resonance_stable": stats['resonance_stable'],
                "ingester_running": stats['world_net']['ingester_running']
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return json.dumps(raw_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating system status: {e}")
        return json.dumps({
            "error": str(e),
            "engine_initialized": engine_initialized,
            "mcp_server_active": True
        })

if __name__ == "__main__":
    # Start the MCP server using stdio transport
    mcp.run()
