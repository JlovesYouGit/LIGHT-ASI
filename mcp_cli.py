#!/usr/bin/env python3
"""
Light-ASI MCP CLI - npx-style command line interface

Usage:
    python3 mcp_cli.py query_asi "What is AI?" --top_k 3
    python3 mcp_cli.py index_text "Your text here" --source cli --priority high
    python3 mcp_cli.py get_system_status
    python3 mcp_cli.py get_raw_graph_dump --limit 10
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path

# Add ASI to path
sys.path.insert(0, str(Path(__file__).parent))

# Global persistent engine instance
_persistent_graph = None
_persistent_auth = None
_persistent_ingester = None
_engine_initialized = False

def get_persistent_engine():
    """Get or create persistent engine instance."""
    global _persistent_graph, _persistent_auth, _persistent_ingester, _engine_initialized
    
    if _engine_initialized:
        return _persistent_graph
    
    try:
        from engine.core.graph import NodeGraph
        from engine.auth.auth import AuthManager
        from engine.world.ingester import WorldIngester
        
        print("Initializing persistent ASI Engine...")
        _persistent_graph = NodeGraph()
        _persistent_auth = AuthManager()
        _persistent_ingester = WorldIngester(_persistent_graph.semantic_map, _persistent_graph)
        
        # Bootstrap
        _persistent_graph.bootstrap(10)
        
        # Index project identity
        manifesto = """
        LIGHT-ASI is a Global Autonomous Intelligence Engine.
        It is designed to map the global 'World-Net' in real-time.
        It uses a distributed Node Graph and Semantic Map to index high-entropy information.
        """
        _persistent_graph.index_text(manifesto, metadata={"source": "core_manifesto", "priority": "high"})
        
        # Auto-index current directory
        import os
        from engine.world.feeds import FeedItem
        
        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.json', '.yaml', '.yml', '.md', '.txt'}
        indexed_count = 0
        max_auto_index = 30
        
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
                        
                        if len(content) > 0 and len(content) < 100000:
                            context = f"File: {file_path.relative_to(current_dir)}\n\n{content}"
                            _persistent_graph.index_text(context, metadata={
                                "source": "auto_codebase_index",
                                "file_path": str(file_path.relative_to(current_dir)),
                                "file_type": file_path.suffix,
                                "priority": "high"
                            })
                            
                            item = FeedItem(
                                source="auto_codebase_index",
                                title=str(file_path.relative_to(current_dir)),
                                text=content,
                                url=str(file_path.relative_to(current_dir)),
                                tags=["codebase", file_path.suffix]
                            )
                            _persistent_graph.semantic_map.ingest(item)
                            indexed_count += 1
                            
                    except Exception as e:
                        pass
        
        print(f"Auto-indexed {indexed_count} files from current directory")
        _engine_initialized = True
        print("Persistent ASI Engine initialized successfully")
        
        return _persistent_graph
        
    except Exception as e:
        print(f"Failed to initialize persistent engine: {e}")
        return None

async def call_tool(tool_name, args):
    """Call an MCP tool using persistent engine."""
    graph = get_persistent_engine()
    if not graph:
        return json.dumps({"error": "Failed to initialize persistent engine"})
    
    # Import tool functions
    from engine.world.feeds import FeedItem
    
    try:
        if tool_name == 'query_asi':
            from engine.core.hash_pipeline import query_entropy
            from engine.core.graph import run_pipeline
            
            text = args.get('text', '')
            top_k = args.get('top_k', 3)
            
            result = graph.query(text, top_k=top_k)
            search_results = graph.semantic_map.search(text, top_k=min(5, top_k + 2))
            
            # If graph query has no answer, use semantic map results
            answer = result.get('answer', '')
            if not answer or "[no stored tokens" in answer:
                if search_results:
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
                        "text": r.text[:1000],
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
            
        elif tool_name == 'search_world':
            text = args.get('text', '')
            top_k = args.get('top_k', 5)
            
            results = graph.semantic_map.search(text, top_k=top_k)
            
            raw_data = {
                "query": text,
                "top_k": top_k,
                "results_count": len(results),
                "total_knowledge_nodes": graph.semantic_map.size,
                "results": [
                    {
                        "title": r.title,
                        "text": r.text[:1000],
                        "source": r.source,
                        "url": getattr(r, 'url', None),
                        "meaning_hash": getattr(r, 'meaning_hash', None)
                    } for r in results
                ]
            }
            
            return json.dumps(raw_data, indent=2)
            
        elif tool_name == 'index_text':
            text = args.get('text', '')
            source = args.get('source', 'cli')
            priority = args.get('priority', 'normal')
            
            hashes = graph.index_text(text, metadata={"source": source, "priority": priority})
            
            item = FeedItem(
                source=source,
                title=f"CLI injection: {source}",
                text=text,
                url="cli://injection",
                tags=["cli", priority]
            )
            graph.semantic_map.ingest(item)
            
            raw_data = {
                "content_indexed": len(text),
                "word_count": len(text.split()),
                "source": source,
                "priority": priority,
                "semantic_tokens_created": len(hashes),
                "hashes": hashes,
                "knowledge_base_size": graph.semantic_map.size,
                "collective_resonance": graph.collective_resonance()
            }
            
            return json.dumps(raw_data, indent=2)
            
        elif tool_name == 'get_system_status':
            stats = graph.stats()
            emergence_status = graph.emergence_status()
            world_status = graph.world_status()
            
            raw_data = {
                "stats": stats,
                "emergence_status": emergence_status,
                "world_status": world_status,
                "engine_initialized": True,
                "knowledge_base_size": graph.semantic_map.size,
                "collective_resonance": graph.collective_resonance()
            }
            
            return json.dumps(raw_data, indent=2)
            
        elif tool_name == 'index_codebase':
            path = args.get('path', '.')
            max_files = args.get('max_files', 100)
            
            import os
            code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.json', '.yaml', '.yml', '.md', '.txt'}
            
            indexed_files = []
            total_chars = 0
            errors = []
            
            target_path = Path(path).resolve()
            
            for root, dirs, files in os.walk(target_path):
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
                                context = f"File: {file_path.relative_to(target_path)}\n\n{content}"
                                hashes = graph.index_text(context, metadata={
                                    "source": "codebase_index",
                                    "file_path": str(file_path.relative_to(target_path)),
                                    "file_type": file_path.suffix,
                                    "priority": "high"
                                })
                                
                                item = FeedItem(
                                    source="codebase_index",
                                    title=str(file_path.relative_to(target_path)),
                                    text=content,
                                    url=str(file_path.relative_to(target_path)),
                                    tags=["codebase", file_path.suffix]
                                )
                                graph.semantic_map.ingest(item)
                                
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
                "collective_resonance": graph.collective_resonance()
            }
            
            return json.dumps(raw_data, indent=2)
            
        elif tool_name == 'get_raw_graph_dump':
            limit = args.get('limit', 100)
            limit = max(1, min(limit, 1000))
            
            raw_nodes = []
            if hasattr(graph, '_nodes'):
                nodes = graph._nodes
                if isinstance(nodes, list):
                    for node_data in nodes[:limit]:
                        node_info = {
                            "node_id": getattr(node_data, 'id', None),
                            "resonance": getattr(node_data, 'resonance', 0),
                            "connections": getattr(node_data, 'connections', []),
                            "metadata": getattr(node_data, 'metadata', {}),
                            "timestamp": getattr(node_data, 'timestamp', None)
                        }
                        raw_nodes.append(node_info)
            
            raw_data = {
                "graph_nodes": raw_nodes,
                "total_graph_nodes": len(graph._nodes) if hasattr(graph, '_nodes') else 0,
                "total_semantic_entries": graph.semantic_map.size,
                "collective_resonance": graph.collective_resonance(),
                "limit_requested": limit,
                "nodes_returned": len(raw_nodes)
            }
            
            return json.dumps(raw_data, indent=2)
            
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
            
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Light-ASI MCP CLI - npx-style command line interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mcp_cli.py query_asi "What is AI?" --top_k 3
  python3 mcp_cli.py index_text "Your text here" --source cli --priority high
  python3 mcp_cli.py get_system_status
  python3 mcp_cli.py get_raw_graph_dump --limit 10
  python3 mcp_cli.py search_world "machine learning" --top_k 5
        """
    )
    
    parser.add_argument('tool', help='MCP tool name')
    parser.add_argument('text', nargs='?', help='Text argument for query_asi, index_text, search_world')
    parser.add_argument('--top_k', type=int, default=3, help='Number of results (default: 3)')
    parser.add_argument('--url', help='URL for latch_url')
    parser.add_argument('--depth', type=int, default=1, help='Crawl depth for latch_url (default: 1)')
    parser.add_argument('--source', default='cli', help='Source identifier (default: cli)')
    parser.add_argument('--priority', default='normal', help='Priority level (default: normal)')
    parser.add_argument('--limit', type=int, default=100, help='Limit for graph dump (default: 100)')
    parser.add_argument('--path', default='.', help='Directory path for index_codebase (default: current directory)')
    parser.add_argument('--max_files', type=int, default=100, help='Max files to index for index_codebase (default: 100)')
    
    args = parser.parse_args()
    
    # Build arguments dict based on tool
    tool_args = {}
    
    if args.tool == 'query_asi':
        if not args.text:
            print("Error: --text required for query_asi", file=sys.stderr)
            sys.exit(1)
        tool_args = {'text': args.text, 'top_k': args.top_k}
    
    elif args.tool == 'search_world':
        if not args.text:
            print("Error: --text required for search_world", file=sys.stderr)
            sys.exit(1)
        tool_args = {'text': args.text, 'top_k': args.top_k}
    
    elif args.tool == 'index_text':
        if not args.text:
            print("Error: --text required for index_text", file=sys.stderr)
            sys.exit(1)
        tool_args = {'text': args.text, 'source': args.source, 'priority': args.priority}
    
    elif args.tool == 'latch_url':
        if not args.url:
            print("Error: --url required for latch_url", file=sys.stderr)
            sys.exit(1)
        tool_args = {'url': args.url, 'depth': args.depth}
    
    elif args.tool == 'get_raw_graph_dump':
        tool_args = {'limit': args.limit}
    
    elif args.tool == 'index_codebase':
        tool_args = {'path': args.path, 'max_files': args.max_files}
    
    elif args.tool in ['get_system_status', 'analyze_emergence', 'get_knowledge_sources']:
        tool_args = {}
    
    else:
        print(f"Error: Unknown tool '{args.tool}'", file=sys.stderr)
        print(f"Available tools: query_asi, search_world, index_text, latch_url, get_system_status, analyze_emergence, get_knowledge_sources, get_raw_graph_dump, index_codebase", file=sys.stderr)
        sys.exit(1)
    
    # Call the tool
    result = asyncio.run(call_tool(args.tool, tool_args))
    
    # Parse and pretty-print JSON
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(result)

if __name__ == '__main__':
    main()
