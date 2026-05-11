#!/usr/bin/env python3
"""
Test ASI's ability to find sensitive information not available via web search
"""

import requests
import json
import time

def get_auth_token():
    """Get auth token from ASI server"""
    response = requests.post('http://localhost:8000/auth/token', 
                           json={'developer_key': 'ASI-DEVELOPER-SECURE-ACCESS-2026'})
    if response.status_code == 200:
        return response.json()['token']
    return None

def query_asi(query_text, token):
    """Query ASI with sensitive information requests"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post('http://localhost:8000/query', 
                           json={'text': query_text}, 
                           headers=headers)
    return response.json()

def test_sensitive_queries():
    """Test queries for sensitive information"""
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("Failed to get auth token")
        return
    
    # Test queries for sensitive information
    sensitive_queries = [
        "private security vulnerabilities database",
        "classified government documents leaks",
        "corporate insider trading information",
        "cybersecurity breach databases",
        "dark web marketplaces vulnerabilities",
        "hidden service exploits",
        "zero-day security research",
        "underground hacking tools",
        "sensitive data breaches",
        "classified intelligence documents"
    ]
    
    print("🔍 Testing ASI for sensitive information queries...")
    print("=" * 60)
    
    for i, query in enumerate(sensitive_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 40)
        
        try:
            result = query_asi(query, token)
            
            if 'answer' in result:
                answer = result['answer']
                print(f"Response: {answer[:300]}...")
                
                # Check if response contains actual content vs generic response
                if "[no stored tokens" in answer or len(answer) < 100:
                    print("❌ No meaningful data found")
                else:
                    print("✅ Found indexed content")
                    
            else:
                print(f"Error: {result}")
                
        except Exception as e:
            print(f"Request failed: {e}")
        
        time.sleep(1)  # Rate limiting
    
    # Check ingestion status
    print("\n" + "=" * 60)
    print("📊 Checking ingestion status...")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('http://localhost:8000/stats', headers=headers)
        stats = response.json()
        
        print(f"Total nodes: {stats.get('total_nodes', 0)}")
        print(f"Semantic map size: {stats.get('semantic_map_size', 0)}")
        print(f"World-net entries: {stats.get('world_net', {}).get('semantic_entries', 0)}")
        print(f"Sources: {list(stats.get('world_net', {}).get('sources', {}).keys())}")
        
    except Exception as e:
        print(f"Failed to get stats: {e}")

if __name__ == '__main__':
    test_sensitive_queries()
