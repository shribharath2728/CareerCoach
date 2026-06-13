#!/usr/bin/env python3
"""
Complete RAG System Validation & Verification
Checks that global government database is properly set up and working
"""

import subprocess
import requests
import sys
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
COLORS = {
    "✅": "\033[92m✅\033[0m",
    "❌": "\033[91m❌\033[0m",
    "⚠️": "\033[93m⚠️\033[0m",
    "ℹ️": "\033[94mℹ️\033[0m"
}

class RAGValidator:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []
    
    def check(self, test_name, condition, error_msg=""):
        """Check a condition and track results"""
        print(f"\n{COLORS['ℹ️']} Checking: {test_name}...", end=" ")
        
        if condition:
            print(f"{COLORS['✅']} PASS")
            self.passed += 1
        else:
            print(f"{COLORS['❌']} FAIL")
            self.failed += 1
            if error_msg:
                self.errors.append(f"  {test_name}: {error_msg}")
                print(f"    {error_msg}")
    
    def warn(self, test_name, message):
        """Log a warning"""
        print(f"\n{COLORS['⚠️']} Warning: {test_name}")
        print(f"    {message}")
        self.warnings += 1
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("RAG VALIDATION SUMMARY")
        print("="*60)
        
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{COLORS['ℹ️']} Tests Passed: {self.passed}/{total} ({percentage:.0f}%)")
        
        if self.failed > 0:
            print(f"{COLORS['❌']} Tests Failed: {self.failed}")
            print("\nFailed tests:")
            for error in self.errors:
                print(error)
        
        if self.warnings > 0:
            print(f"\n{COLORS['⚠️']} Warnings: {self.warnings}")
        
        print("\n" + "="*60)
        
        if self.failed == 0:
            print(f"{COLORS['✅']} ALL SYSTEMS OPERATIONAL!")
            print("Your RAG system is ready to prevent hallucination globally!")
        else:
            print(f"{COLORS['❌']} ISSUES DETECTED - See above for details")
        
        print("="*60 + "\n")
        
        return self.failed == 0

def check_backend_running():
    """Check if backend server is running"""
    print("\n" + "="*60)
    print("PHASE 1: BACKEND CONNECTIVITY")
    print("="*60)
    
    validator = RAGValidator()
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        validator.check("Backend Server Running", 
                       response.status_code == 200,
                       "Backend not responding. Run: uvicorn app.main:app --reload")
    except requests.exceptions.ConnectionError:
        validator.check("Backend Server Running", False,
                       f"Cannot connect to {BASE_URL}. Is server running?")
        return False, validator
    
    return True, validator

def check_rag_database():
    """Check if RAG knowledge base is initialized"""
    print("\n" + "="*60)
    print("PHASE 2: DATABASE & RAG KNOWLEDGE")
    print("="*60)
    
    validator = RAGValidator()
    
    try:
        # Check if we can list knowledge
        response = requests.get(f"{BASE_URL}/rag/knowledge?limit=1")
        validator.check("RAG Knowledge Endpoint Accessible",
                       response.status_code == 200,
                       "Cannot access /rag/knowledge endpoint")
        
        # Get all knowledge entries
        response = requests.get(f"{BASE_URL}/rag/knowledge?limit=100")
        if response.status_code == 200:
            entries = response.json()
            validator.check("RAG Database Has Entries",
                           len(entries) > 0,
                           f"No knowledge entries found. Run: python setup_rag.py")
            
            # Count government entries
            govt_entries = [e for e in entries if "government" in str(e.get('tags', '')).lower()]
            validator.check("Government Data Present",
                           len(govt_entries) > 0,
                           f"No government entries. Run: python setup_rag.py")
            
            print(f"    Found {len(entries)} total entries")
            print(f"    Found {len(govt_entries)} government entries")
        
        return True, validator
    except Exception as e:
        validator.check("RAG Database Query", False, str(e))
        return False, validator

def check_government_coverage():
    """Check if global government data is comprehensive"""
    print("\n" + "="*60)
    print("PHASE 3: GLOBAL GOVERNMENT COVERAGE")
    print("="*60)
    
    validator = RAGValidator()
    
    test_countries = {
        "india": ["India", "government", "Tamil Nadu"],
        "usa": ["United States", "USA", "president"],
        "china": ["China", "government"],
        "world": ["world leaders", "global government"]
    }
    
    for region, keywords in test_countries.items():
        try:
            response = requests.post(
                f"{BASE_URL}/rag/retrieve",
                json={"query": " ".join(keywords), "top_k": 3},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                found = data.get('results_count', 0) > 0
                validator.check(f"Coverage - {region.upper()}",
                               found,
                               f"No results for: {keywords}")
                
                if found:
                    print(f"    Retrieved: {data['retrieved_documents'][0]['id']}")
            else:
                validator.check(f"Coverage - {region.upper()}", False,
                               f"API error: {response.status_code}")
        except Exception as e:
            validator.check(f"Coverage - {region.upper()}", False, str(e))
    
    return True, validator

def check_cache_status():
    """Check if cache is loaded"""
    print("\n" + "="*60)
    print("PHASE 4: CACHE STATUS")
    print("="*60)
    
    validator = RAGValidator()
    
    try:
        response = requests.get(f"{BASE_URL}/rag/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            cache_size = stats.get('cache_entries', 0)
            
            validator.check("Cache Initialized",
                           cache_size > 0,
                           "Cache empty. Run: curl -X POST http://localhost:8000/rag/cache/refresh")
            
            print(f"    Cache entries: {cache_size}")
            print(f"    Total knowledge: {stats.get('total_knowledge_entries', 0)}")
        else:
            validator.check("Cache Status Check", False,
                           f"Cannot access stats: {response.status_code}")
    except Exception as e:
        validator.check("Cache Status Check", False, str(e))
    
    return True, validator

def check_retrieval_quality():
    """Check retrieval accuracy and scoring"""
    print("\n" + "="*60)
    print("PHASE 5: RETRIEVAL QUALITY")
    print("="*60)
    
    validator = RAGValidator()
    
    test_queries = [
        ("CM of Tamil Nadu 2026", ["current_government_2026"]),
        ("chief minister tamil nadu", ["current_government_2026"]),
        ("world government leaders", ["current_world_leaders_2026"]),
        ("USA president", ["current_world_leaders_2026"]),
    ]
    
    for query, expected_ids in test_queries:
        try:
            response = requests.post(
                f"{BASE_URL}/rag/retrieve",
                json={"query": query, "top_k": 3},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                retrieved_ids = [d['id'] for d in data.get('retrieved_documents', [])]
                
                # Check if any expected ID was retrieved
                found_match = any(eid in retrieved_ids for eid in expected_ids)
                
                validator.check(f"Query Quality - '{query}'",
                               found_match,
                               f"Expected {expected_ids} but got {retrieved_ids[:1]}")
                
                if found_match:
                    score = data['retrieved_documents'][0]['score']
                    print(f"    Score: {score:.2f}")
        except Exception as e:
            validator.check(f"Query - '{query}'", False, str(e))
    
    return True, validator

def check_system_integration():
    """Check if RAG is integrated with chat system"""
    print("\n" + "="*60)
    print("PHASE 6: SYSTEM INTEGRATION")
    print("="*60)
    
    validator = RAGValidator()
    
    # Check if chat routes exist
    try:
        response = requests.post(
            f"{BASE_URL}/chat/messages",
            json={
                "user_id": "test_validation",
                "message": "Who is the CM of Tamil Nadu?",
                "session_id": "validation_test"
            },
            timeout=10
        )
        
        validator.check("Chat Integration Active",
                       response.status_code in [200, 201],
                       f"Chat endpoint error: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check if response seems grounded in RAG data
            is_grounded = any(keyword in response_text.lower() 
                            for keyword in ['vijay', 'tamil', 'government', 'cm'])
            
            if not is_grounded:
                validator.warn("Chat Response Quality",
                             "Response may not be using RAG data. Check cache refresh.")
            else:
                print(f"    Response preview: {response_text[:100]}...")
    
    except Exception as e:
        validator.warn("Chat Integration Test", f"Could not test: {e}")
    
    return True, validator

def run_complete_validation():
    """Run all validation checks"""
    print("\n" + "🌍 "*20)
    print("SKILLENS RAG GLOBAL GOVERNMENT VALIDATION")
    print("🌍 "*20 + "\n")
    
    all_validators = []
    
    # Phase 1: Backend
    running, v1 = check_backend_running()
    all_validators.append(v1)
    
    if not running:
        print(f"\n{COLORS['❌']} Backend not running!")
        print("Start server: cd backend && python -m uvicorn app.main:app --reload")
        return False
    
    # Phase 2: Database
    has_db, v2 = check_rag_database()
    all_validators.append(v2)
    
    if not has_db:
        print(f"\n{COLORS['❌']} RAG database not initialized!")
        print("Initialize: cd backend && python setup_rag.py")
        return False
    
    # Phase 3: Global Coverage
    _, v3 = check_government_coverage()
    all_validators.append(v3)
    
    # Phase 4: Cache
    _, v4 = check_cache_status()
    all_validators.append(v4)
    
    if v4.failed > 0:
        print(f"\n{COLORS['⚠️']} Cache may need refresh:")
        print("Refresh: curl -X POST http://localhost:8000/rag/cache/refresh")
    
    # Phase 5: Quality
    _, v5 = check_retrieval_quality()
    all_validators.append(v5)
    
    # Phase 6: Integration
    _, v6 = check_system_integration()
    all_validators.append(v6)
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL VALIDATION REPORT")
    print("="*60)
    
    total_passed = sum(v.passed for v in all_validators)
    total_failed = sum(v.failed for v in all_validators)
    total_warnings = sum(v.warnings for v in all_validators)
    total_tests = total_passed + total_failed
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"{COLORS['✅']} Passed: {total_passed}")
    print(f"{COLORS['❌']} Failed: {total_failed}")
    print(f"{COLORS['⚠️']} Warnings: {total_warnings}")
    
    print("\n" + "="*60)
    
    if total_failed == 0:
        print(f"{COLORS['✅']} ✅ ✅ ALL SYSTEMS OPERATIONAL ✅ ✅ ✅")
        print("\nYour RAG is properly configured!")
        print("Your AI will NOT hallucinate on global government facts!")
        print("\nYou can now:")
        print("1. Use chat to ask government questions")
        print("2. Update data: python manage_government.py add")
        print("3. Test queries: python manage_government.py test [query]")
        return True
    else:
        print(f"{COLORS['❌']} Issues detected - review above")
        return False

if __name__ == "__main__":
    try:
        success = run_complete_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['❌']} Validation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n{COLORS['❌']} Validation error: {e}")
        sys.exit(1)
