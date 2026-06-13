#!/usr/bin/env python3
"""
Global Government Information Manager for RAG

Helps you update government information across the world to prevent AI hallucination.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

# Government data template
GOVERNMENT_TEMPLATES = {
    "country": {
        "category": "current_facts",
        "tags": ["government", "COUNTRY_NAME", "2026", "current"],
        "content": """[COUNTRY] Government (June 2026)

Head of State: [Name] ([Title - President/King/Queen])
Head of Government: [Name] ([Title - PM/Chancellor])

Key Ministers:
- Finance Minister: [Name]
- Foreign Minister: [Name]
- Defense Minister: [Name]
- Interior Minister: [Name]

Election Information:
- Last election: [Date]
- Next election: [Date]
- Governing party/coalition: [Name]

Government Structure:
- [Chamber 1]: [Details]
- [Chamber 2]: [Details]

Current Status: [Stable/Coalition/Transitional/etc]

Source: [Official government website/verified news source]
Updated: June 2026""",
        "source": "admin_2026_verified"
    },
    "region": {
        "category": "current_facts",
        "tags": ["government", "region", "2026", "current"],
        "content": """Government Leaders - [REGION] (June 2026)

[List leaders by country]
- Country 1 Leader: [Name] ([Party/Title])
- Country 2 Leader: [Name] ([Party/Title])
...

Recent Changes:
[Any recent transitions, elections, or changes]

Source: Verified June 2026""",
        "source": "admin_2026_verified"
    }
}

def refresh_cache():
    """Refresh RAG cache after updates."""
    print("🔄 Refreshing RAG cache...")
    try:
        response = requests.post(f"{BASE_URL}/rag/cache/refresh")
        if response.status_code == 200:
            print("✅ Cache refreshed successfully!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def add_government_data(country: str, leader: str, title: str, party: str = ""):
    """Add/update government data for a country."""
    print(f"📝 Adding government data for {country}...")
    
    content = f"""{country} Government (June 2026)

Head of Government: {leader} ({title})"""
    
    if party:
        content += f"\nParty: {party}"
    
    content += "\n\nFor complete information, check official government sources."
    
    payload = {
        "category": "current_facts",
        "content": content,
        "tags": ["government", country.lower(), "2026", "current"],
        "source": "admin_2026_verified"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/rag/knowledge",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Added: {data['entry']['id']}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def list_government_entries():
    """List all government-related knowledge entries."""
    print("📚 Government Knowledge Entries in RAG:\n")
    
    try:
        response = requests.get(f"{BASE_URL}/rag/knowledge?limit=100")
        
        if response.status_code == 200:
            entries = response.json()
            govt_entries = [e for e in entries if e.get("category") == "current_facts"]
            
            for entry in govt_entries:
                print(f"ID: {entry['id']}")
                print(f"   Tags: {', '.join(entry['tags'][:3])}")
                print(f"   Source: {entry['source']}")
                print(f"   Content preview: {entry['content'][:100]}...")
                print()
            
            print(f"Total government entries: {len(govt_entries)}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_government_query(query: str):
    """Test retrieval of government information."""
    print(f"🔍 Testing query: '{query}'\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/rag/retrieve",
            json={"query": query, "top_k": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['results_count']} results:\n")
            
            for i, doc in enumerate(data['retrieved_documents'], 1):
                print(f"{i}. {doc['id']} (score: {doc['score']:.2f})")
                print(f"   Category: {doc['category']}")
                print(f"   Tags: {', '.join(doc['tags'][:3])}")
                print()
            
            if data['results_count'] > 0:
                print("Retrieved Context:")
                print(data['context'][:500] + "..." if len(data['context']) > 500 else data['context'])
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def main():
    """Main menu."""
    print("\n" + "="*60)
    print("Global Government Information Manager for RAG")
    print("="*60)
    print("\nUsage:")
    print("  python manage_government.py list      - List all government entries")
    print("  python manage_government.py test      - Test a query")
    print("  python manage_government.py add       - Add new country data")
    print("  python manage_government.py refresh   - Refresh cache")
    print("  python manage_government.py guide     - Show update guide")
    
    if len(sys.argv) < 2:
        print("\n💡 Quick example:")
        print("  python manage_government.py test 'PM of India'")
        print("  python manage_government.py list")
        print("  python manage_government.py refresh")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_government_entries()
    elif command == "refresh":
        refresh_cache()
    elif command == "test":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "government leaders"
        test_government_query(query)
    elif command == "add":
        print("\n📝 Interactive Government Data Entry\n")
        country = input("Country name: ").strip()
        leader = input("Leader/PM/President name: ").strip()
        title = input("Title (PM/President/Chancellor/etc): ").strip()
        party = input("Party (optional): ").strip()
        
        if country and leader and title:
            if add_government_data(country, leader, title, party):
                print("\n🔄 Refreshing cache...")
                refresh_cache()
        else:
            print("❌ Missing required information")
    elif command == "guide":
        print("""
╔════════════════════════════════════════════════════════════╗
║  How to Update Government Information Globally            ║
╚════════════════════════════════════════════════════════════╝

1. VERIFY INFORMATION
   - Use official government websites
   - Cross-check with reputable news sources
   - Note the date information is from

2. ADD TO RAG (Choose one method)

   METHOD A: Use this script
   $ python manage_government.py add
   Then follow prompts

   METHOD B: Use API directly
   $ curl -X POST http://localhost:8000/rag/knowledge \\
     -H "Content-Type: application/json" \\
     -d '{
       "category": "current_facts",
       "content": "...",
       "tags": ["government", "country", "2026"],
       "source": "admin_2026_verified"
     }'

   METHOD C: Use browser (Swagger UI)
   Visit http://localhost:8000/docs
   Find POST /rag/knowledge
   Fill in the form and execute

3. REFRESH CACHE (IMPORTANT!)
   $ python manage_government.py refresh
   OR
   $ curl -X POST http://localhost:8000/rag/cache/refresh

4. TEST THE CHANGE
   $ python manage_government.py test "who is PM of [country]"
   
   The AI should now answer using your updated data!

5. MONITOR
   $ python manage_government.py list
   $ python manage_government.py test "global government"

╔════════════════════════════════════════════════════════════╗
║  Important Notes                                           ║
╚════════════════════════════════════════════════════════════╝

✅ DO:
- Verify all information before adding
- Update regularly (quarterly recommended)
- Use consistent format
- Include source/date
- Refresh cache after every change

❌ DON'T:
- Add unverified information
- Mix old and new data
- Forget to refresh cache
- Add speculation as fact
- Leave incorrect data in RAG

Your AI's accuracy depends on RAG data quality!
""")
    else:
        print(f"❌ Unknown command: {command}")
        print("Use: list, test, add, refresh, or guide")

if __name__ == "__main__":
    main()
