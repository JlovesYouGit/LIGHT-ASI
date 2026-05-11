#!/usr/bin/env python3
"""
Light-ASI MCP Usage Example - Similar to Pinecone MCP

This demonstrates using the Light-ASI MCP tools in a way similar to
how you would use Pinecone MCP tools like search-records, upsert-records, etc.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add ASI to path
sys.path.insert(0, str(Path(__file__).parent))

async def demonstrate_mcp_like_pinecone():
    """Demonstrate using Light-ASI MCP tools like Pinecone MCP tools."""
    
    print("🔗 Light-ASI MCP Usage (Similar to Pinecone MCP)")
    print("=" * 60)
    
    # Import MCP tools (similar to how Pinecone MCP tools are imported)
    from mcp.server import (
        query_asi,           # Similar to mcp0_search-records
        search_world,        # Similar to mcp0_search-records
        index_text,          # Similar to mcp0_upsert-records
        get_system_status,   # Similar to mcp0_describe-index-stats
        get_raw_graph_dump,  # Similar to getting raw index data
        analyze_emergence,   # Similar to index analysis
        get_knowledge_sources # Similar to getting index info
    )
    
    # Example 1: Query the ASI (like Pinecone search-records)
    print("\n1️⃣ QUERY ASI (similar to Pinecone search-records)")
    print("-" * 50)
    query_result = await query_asi("What is artificial intelligence?", top_k=3)
    query_data = json.loads(query_result)
    print(f"Query result keys: {list(query_data.keys())}")
    print(f"Resonance score: {query_data['graph_query_result']['resonance_score']}")
    print(f"Source nodes: {query_data['graph_query_result']['source_nodes']}")
    
    # Example 2: Index text (like Pinecone upsert-records)
    print("\n2️⃣ INDEX TEXT (similar to Pinecone upsert-records)")
    print("-" * 50)
    text_to_index = "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
    index_result = await index_text(text_to_index, source="mcp_demo", priority="high")
    index_data = json.loads(index_result)
    print(f"Indexed: {index_data['content_indexed']} chars")
    print(f"Semantic tokens created: {index_data['semantic_tokens_created']}")
    print(f"Hashes: {index_data['hashes'][:2]}...")  # Show first 2 hashes
    
    # Example 3: Search world-net (like Pinecone search-records)
    print("\n3️⃣ SEARCH WORLD-NET (similar to Pinecone search-records)")
    print("-" * 50)
    search_result = await search_world("machine learning", top_k=3)
    search_data = json.loads(search_result)
    print(f"Results count: {search_data['results_count']}")
    print(f"Total knowledge nodes: {search_data['total_knowledge_nodes']}")
    
    # Example 4: Get system status (like Pinecone describe-index-stats)
    print("\n4️⃣ GET SYSTEM STATUS (similar to Pinecone describe-index-stats)")
    print("-" * 50)
    status_result = await get_system_status()
    status_data = json.loads(status_result)
    print(f"Total nodes: {status_data['stats']['total_nodes']}")
    print(f"Collective resonance: {status_data['stats']['collective_resonance']}")
    print(f"Semantic map size: {status_data['stats']['semantic_map_size']}")
    
    # Example 5: Get raw graph dump (like getting raw index data)
    print("\n5️⃣ GET RAW GRAPH DUMP (similar to getting raw index data)")
    print("-" * 50)
    dump_result = await get_raw_graph_dump(limit=5)
    dump_data = json.loads(dump_result)
    print(f"Total graph nodes: {dump_data['total_graph_nodes']}")
    print(f"Nodes returned: {dump_data['nodes_returned']}")
    print(f"Semantic entries returned: {dump_data['entries_returned']}")
    if dump_data['graph_nodes']:
        print(f"Sample node ID: {dump_data['graph_nodes'][0]['node_id']}")
        print(f"Sample node resonance: {dump_data['graph_nodes'][0]['resonance']}")
    
    # Example 6: Analyze emergence (like index analysis)
    print("\n6️⃣ ANALYZE EMERGENCE (similar to index analysis)")
    print("-" * 50)
    emergence_result = await analyze_emergence()
    emergence_data = json.loads(emergence_result)
    print(f"Emergence phase: {emergence_data['calculated_metrics']['phase']}")
    print(f"Node ratio: {emergence_data['calculated_metrics']['node_ratio']}")
    print(f"Resonance stable: {emergence_data['calculated_metrics']['resonance_stable']}")
    
    # Example 7: Get knowledge sources (like getting index info)
    print("\n7️⃣ GET KNOWLEDGE SOURCES (similar to getting index info)")
    print("-" * 50)
    sources_result = await get_knowledge_sources()
    sources_data = json.loads(sources_result)
    print(f"Active sources count: {sources_data['active_sources_count']}")
    print(f"Total entries: {sources_data['total_entries']}")
    print(f"Semantic diversity: {sources_data['data_quality_metrics']['semantic_diversity']}")
    
    print("\n" + "=" * 60)
    print("✅ All MCP tools demonstrated successfully!")
    print("\n📊 Comparison with Pinecone MCP:")
    print("- query_asi         → similar to mcp0_search-records")
    print("- index_text       → similar to mcp0_upsert-records")
    print("- search_world     → similar to mcp0_search-records")
    print("- get_system_status→ similar to mcp0_describe-index-stats")
    print("- get_raw_graph_dump→ similar to getting raw index data")
    print("- analyze_emergence→ similar to index analysis")
    print("- get_knowledge_sources→ similar to getting index info")

if __name__ == "__main__":
    asyncio.run(demonstrate_mcp_like_pinecone())
