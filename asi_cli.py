#!/usr/bin/env python3
"""
Light-ASI CLI - Standalone persistent engine for development

Usage:
    python3 asi_cli.py query "What is AI?"
    python3 asi_cli.py search "MCP server"
    python3 asi_cli.py index "Your text here"
    python3 asi_cli.py status
"""

import json
import sys
import argparse
from pathlib import Path

# Add ASI to path
sys.path.insert(0, str(Path(__file__).parent))

# Global persistent engine
_persistent_graph = None
_engine_initialized = False

def get_engine():
    """Get or create persistent engine instance."""
    global _persistent_graph, _engine_initialized
    
    if _engine_initialized:
        return _persistent_graph
    
    try:
        from engine.core.graph import NodeGraph
        from engine.world.feeds import FeedItem
        
        print("Initializing ASI Engine...")
        _persistent_graph = NodeGraph()
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
        print("ASI Engine initialized successfully")
        
        return _persistent_graph
        
    except Exception as e:
        print(f"Failed to initialize engine: {e}")
        import traceback
        traceback.print_exc()
        return None

def query(text, top_k=3):
    """Query the ASI engine."""
    graph = get_engine()
    if not graph:
        return {"error": "Engine not initialized"}
    
    result = graph.query(text, top_k=top_k)
    search_results = graph.semantic_map.search(text, top_k=min(5, top_k + 2))
    
    # If graph query has no answer, use semantic map results
    answer = result.get('answer', '')
    if not answer or "[no stored tokens" in answer:
        if search_results:
            best_result = search_results[0]
            answer = f"[from semantic map: {best_result.title}] {best_result.text[:500]}"
    
    return {
        "query": text,
        "answer": answer,
        "resonance_score": result.get('resonance_score', 0),
        "semantic_results": len(search_results),
        "knowledge_nodes": graph.semantic_map.size
    }

def search(text, top_k=5):
    """Search the semantic map."""
    graph = get_engine()
    if not graph:
        return {"error": "Engine not initialized"}
    
    results = graph.semantic_map.search(text, top_k=top_k)
    
    return {
        "query": text,
        "results_count": len(results),
        "results": [
            {
                "title": r.title,
                "text": r.text[:500],
                "source": r.source
            } for r in results
        ],
        "knowledge_nodes": graph.semantic_map.size
    }

def index(text, source="cli"):
    """Index text into the engine."""
    graph = get_engine()
    if not graph:
        return {"error": "Engine not initialized"}
    
    from engine.world.feeds import FeedItem
    
    hashes = graph.index_text(text, metadata={"source": source, "priority": "high"})
    
    item = FeedItem(
        source=source,
        title=f"CLI injection: {source}",
        text=text,
        url="cli://injection",
        tags=["cli"]
    )
    graph.semantic_map.ingest(item)
    
    return {
        "indexed": len(text),
        "tokens": len(hashes),
        "knowledge_nodes": graph.semantic_map.size
    }

def status():
    """Get engine status."""
    graph = get_engine()
    if not graph:
        return {"error": "Engine not initialized"}
    
    stats = graph.stats()
    
    return {
        "total_nodes": stats['total_nodes'],
        "semantic_map_size": graph.semantic_map.size,
        "collective_resonance": graph.collective_resonance(),
        "engine_initialized": True
    }

def main():
    parser = argparse.ArgumentParser(description='Light-ASI CLI')
    parser.add_argument('command', choices=['query', 'search', 'index', 'status'])
    parser.add_argument('text', nargs='?', help='Text for query/search/index')
    parser.add_argument('--top_k', type=int, default=3, help='Number of results')
    
    args = parser.parse_args()
    
    if args.command == 'query':
        if not args.text:
            print("Error: query requires text argument")
            return
        result = query(args.text, args.top_k)
    elif args.command == 'search':
        if not args.text:
            print("Error: search requires text argument")
            return
        result = search(args.text, args.top_k)
    elif args.command == 'index':
        if not args.text:
            print("Error: index requires text argument")
            return
        result = index(args.text)
    elif args.command == 'status':
        result = status()
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
