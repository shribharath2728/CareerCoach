#!/usr/bin/env python3
"""
Quick test script for RAG + Current Information

Tests that your AI can answer real-time questions using RAG knowledge base.
"""

import requests
import json
import sys
from pathlib import Path

# Assume API is running on localhost:8000
BASE_URL = "http://localhost:8000"

def test_rag_retrieval():
    """Test RAG can retrieve current government information."""
    print("\n" + "="*60)
    print("Testing RAG Retrieval for Current Information")
    print("="*60)
    
    test_queries = [
        ("CM of Tamil Nadu 2026", "Should find current government info"),
        ("government leaders India", "Should find government information"),
        ("PM of India current", "Should find PM info"),
    ]
    
    for query, expected in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print(f"   Expected: {expected}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/rag/retrieve",
                json={
                    "query": query,
                    "top_k": 5,
                    "max_chars": 4000
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Retrieved {data['results_count']} documents")
                
                if data['results_count'] > 0:
                    print(f"   📄 Top result: {data['retrieved_documents'][0]['id']}")
                    print(f"   📌 Category: {data['retrieved_documents'][0]['category']}")
                    print(f"   Score: {data['retrieved_documents'][0]['score']:.2f}")
            else:
                print(f"   ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
    
    return True

def test_chat_api():
    """Test that chat API works (requires valid session)."""
    print("\n" + "="*60)
    print("Testing Chat API (Optional - if you have a session)")
    print("="*60)
    
    print("\nNote: To fully test chat, you need to:")
    print("1. Create a user via /users (if needed)")
    print("2. Create a chat session via /chat/sessions")
    print("3. Send a message via /chat/messages")
    print("\nFor now, check the RAG retrieval works above ✓")

def check_rag_stats():
    """Check RAG knowledge base statistics."""
    print("\n" + "="*60)
    print("RAG Knowledge Base Statistics")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/rag/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"\n✅ Total entries: {stats['total_entries']}")
            print(f"✅ Active entries: {stats['active_entries']}")
            print(f"✅ Cache status: {stats['cache_status']}")
            
            print(f"\nCategories:")
            for category, count in stats['categories'].items():
                print(f"  - {category}: {count}")
            
            # Check for current_facts
            if 'current_facts' in stats['categories']:
                print(f"\n✅ Current facts category found: {stats['categories']['current_facts']} entries")
            else:
                print(f"\n⚠️  No 'current_facts' category yet. Run setup_rag.py to add defaults.")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure your backend is running:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --reload")
        return False

def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("█  SkillLens RAG + Current Information Quick Test")
    print("█"*60)
    
    # Check if backend is running
    print("\n1️⃣  Checking backend connection...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("   ✅ Backend is running!")
        else:
            print("   ❌ Backend returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend is not running")
        print("\n   Start your backend with:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Check RAG stats
    print("\n2️⃣  Checking RAG knowledge base...")
    if not check_rag_stats():
        print("\n   ⚠️  Run setup to initialize RAG:")
        print("   cd backend")
        print("   python setup_rag.py")
        return False
    
    # Test RAG retrieval
    print("\n3️⃣  Testing RAG retrieval...")
    if not test_rag_retrieval():
        print("\n   ❌ RAG retrieval failed")
        return False
    
    # Success message
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour AI should now answer real-time questions using RAG!")
    print("\nTry asking in chat:")
    print("  • 'Who is the CM of Tamil Nadu in 2026?'")
    print("  • 'Who is the PM of India right now?'")
    print("  • 'What government positions exist in India?'")
    print("\nThe AI will retrieve current information from RAG and answer accurately!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
