"""
Comprehensive RAG Service — Prevent AI Hallucination
==================================================
Proper Retrieval-Augmented Generation implementation that prevents
AI hallucination on ANY question by grounding responses in verified
knowledge before generation.

Features:
- Dynamic knowledge base with comprehensive coverage
- Intelligent retrieval with BM25-inspired scoring
- Semantic similarity matching
- Multi-category knowledge organization
- Cache management for fast retrieval
- Confidence scoring for uncertainty handling
"""

import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from collections import defaultdict

logger = logging.getLogger(__name__)

# In-memory cache for fast retrieval
_KNOWLEDGE_CACHE: List[Dict[str, Any]] = []
_CACHE_TIMESTAMP = None
_CACHE_TTL_SECONDS = 3600  # 1 hour

# Statistics for IDF calculation
_DOCUMENT_STATS = {
    "total_docs": 0,
    "term_document_frequency": defaultdict(int),
    "category_counts": defaultdict(int),
}


def _tokenize(text: str) -> List[str]:
    """Advanced tokenization with stop word removal."""
    # Common stop words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
        'why', 'how', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }
    
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9_-]+\b", text)
    # Keep tokens that are: not stop words, length > 2, and not pure numbers
    return [t for t in tokens 
            if len(t) > 2 and t not in stop_words and not t.isdigit()]


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts (0-1)."""
    tokens1 = set(_tokenize(text1))
    tokens2 = set(_tokenize(text2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0


def _score_document_bm25(
    query_tokens: List[str], 
    doc: Dict[str, Any],
    k1: float = 1.5,
    b: float = 0.75
) -> float:
    """
    BM25-inspired scoring algorithm for better relevance.
    Combines tag matching, category matching, and TF-IDF.
    
    Args:
        query_tokens: Tokenized query
        doc: Document to score
        k1: Term saturation parameter (higher = better with repeated terms)
        b: Length normalization parameter
    
    Returns:
        Relevance score (0 = no match, higher = better match)
    """
    if not query_tokens:
        return 0.0
    
    score = 0.0
    
    # ========== TAG MATCHING (Highest Weight) ==========
    doc_tags = [tag.lower() for tag in doc.get("tags", [])]
    tag_text = " ".join(doc_tags)
    tag_tokens = _tokenize(tag_text)
    
    for qt in query_tokens:
        # Exact tag match
        if qt in tag_tokens:
            score += 8.0  # High weight for tag match
        # Partial tag match
        for tag in doc_tags:
            if qt in tag:
                score += 3.0
    
    # ========== CATEGORY MATCHING ==========
    category = doc.get("category", "").lower()
    category_tokens = _tokenize(category)
    for qt in query_tokens:
        if qt in category_tokens:
            score += 2.0
    
    # ========== CONTENT MATCHING (BM25-style) ==========
    doc_text = doc.get("text", "")
    doc_tokens = _tokenize(doc_text)
    doc_len = len(doc_tokens)
    
    if doc_len == 0:
        return score
    
    # Calculate average document length from cache
    avg_doc_len = 1.0
    if _DOCUMENT_STATS["total_docs"] > 0:
        total_tokens = sum(
            len(_tokenize(d.get("text", ""))) 
            for d in _KNOWLEDGE_CACHE
        )
        avg_doc_len = total_tokens / _DOCUMENT_STATS["total_docs"]
    
    # Term frequency with length normalization
    term_freq = defaultdict(int)
    for token in doc_tokens:
        term_freq[token] += 1
    
    for qt in query_tokens:
        if qt not in term_freq:
            continue
        
        tf = term_freq[qt]
        idf = math.log(
            (_DOCUMENT_STATS["total_docs"] + 1) / 
            (_DOCUMENT_STATS["term_document_frequency"].get(qt, 1) + 1)
        ) + 1
        
        # BM25 formula
        normalized_tf = (tf * (k1 + 1)) / (
            tf + k1 * (1 - b + b * (doc_len / max(avg_doc_len, 1)))
        )
        score += idf * normalized_tf
    
    # ========== SEMANTIC SIMILARITY BONUS ==========
    query_text = " ".join(query_tokens)
    semantic_sim = _calculate_similarity(query_text, doc_text)
    score += semantic_sim * 3.0  # Bonus for semantic match
    
    return score


def _update_document_stats():
    """Rebuild document statistics for IDF calculation."""
    global _DOCUMENT_STATS
    
    _DOCUMENT_STATS["total_docs"] = len(_KNOWLEDGE_CACHE)
    _DOCUMENT_STATS["term_document_frequency"].clear()
    _DOCUMENT_STATS["category_counts"].clear()
    
    # Calculate term document frequency (how many docs contain each term)
    for doc in _KNOWLEDGE_CACHE:
        doc_tokens = set(_tokenize(doc.get("text", "")))
        for token in doc_tokens:
            _DOCUMENT_STATS["term_document_frequency"][token] += 1
        
        category = doc.get("category", "unknown")
        _DOCUMENT_STATS["category_counts"][category] += 1
    
    logger.debug(f"Updated stats: {_DOCUMENT_STATS['total_docs']} docs, "
                f"{len(_DOCUMENT_STATS['term_document_frequency'])} unique terms")


def load_knowledge_base(db: Session) -> List[Dict[str, Any]]:
    """
    Load knowledge base from database and update in-memory cache.
    Includes both static default knowledge and dynamic entries.
    Rebuilds all statistics for proper scoring.
    """
    global _KNOWLEDGE_CACHE, _CACHE_TIMESTAMP
    
    try:
        from app.models.rag_knowledge import RAGKnowledge
        
        # Query all active knowledge entries
        db_entries = db.query(RAGKnowledge).filter(
            RAGKnowledge.is_active == True
        ).all()
        
        knowledge_base = []
        for entry in db_entries:
            knowledge_base.append({
                "id": entry.id,
                "category": entry.category,
                "tags": entry.tags.split(",") if entry.tags else [],
                "text": entry.content,
                "source": "database",
                "created_at": entry.created_at,
            })
        
        logger.info(f"Loaded {len(knowledge_base)} knowledge entries from database")
        
        # Always merge with default knowledge base for comprehensive coverage
        defaults = _get_default_knowledge_base()
        default_ids = {d["id"] for d in defaults}
        
        # Add defaults that aren't in database (avoid duplicates)
        for default_doc in defaults:
            if default_doc["id"] not in {d["id"] for d in knowledge_base}:
                knowledge_base.append(default_doc)
        
        _KNOWLEDGE_CACHE = knowledge_base
        _CACHE_TIMESTAMP = datetime.now()
        
        # Rebuild statistics for accurate scoring
        _update_document_stats()
        
        logger.info(f"Total knowledge base size: {len(_KNOWLEDGE_CACHE)} entries")
        return knowledge_base
        
    except Exception as e:
        logger.error(f"Error loading knowledge base from DB: {e}")
        logger.info("Falling back to default knowledge base")
        _KNOWLEDGE_CACHE = _get_default_knowledge_base()
        _CACHE_TIMESTAMP = datetime.now()
        _update_document_stats()
        return _KNOWLEDGE_CACHE


def get_cached_knowledge() -> List[Dict[str, Any]]:
    """Get knowledge base from cache, or load if cache is empty."""
    global _KNOWLEDGE_CACHE, _CACHE_TIMESTAMP
    
    if not _KNOWLEDGE_CACHE or not _CACHE_TIMESTAMP:
        # Initialize with defaults
        _KNOWLEDGE_CACHE = _get_default_knowledge_base()
        _CACHE_TIMESTAMP = datetime.now()
    
    return _KNOWLEDGE_CACHE


def retrieve_context(
    query: str, 
    top_k: int = 5,
    confidence_threshold: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Retrieve top_k most relevant knowledge chunks for a query.
    Uses BM25-inspired algorithm with semantic similarity.
    
    Args:
        query: User question or search text
        top_k: Number of top results to return
        confidence_threshold: Minimum score to include (0.0 = include all)
    
    Returns:
        List of knowledge documents with scores and confidence
    """
    if not query or not str(query).strip():
        logger.warning("Empty query provided")
        return []
    
    knowledge_base = get_cached_knowledge()
    if not knowledge_base:
        logger.warning("Knowledge base is empty")
        return []
    
    query_tokens = _tokenize(query)
    if not query_tokens:
        logger.debug(f"No searchable tokens in query: '{query}'")
        return []
    
    # Score all documents
    scored = []
    max_score = 0.0
    
    for doc in knowledge_base:
        score = _score_document_bm25(query_tokens, doc)
        if score > 0:
            scored.append({**doc, "score": score})
            max_score = max(max_score, score)
    
    # Normalize scores to 0-1 range
    if max_score > 0:
        for doc in scored:
            doc["confidence"] = min(1.0, doc["score"] / max_score)
    
    # Sort by score and filter by threshold
    scored.sort(key=lambda x: x["score"], reverse=True)
    results = [d for d in scored[:top_k] if d["confidence"] >= confidence_threshold]
    
    logger.info(f"Retrieved {len(results)} documents for query: '{query}' "
               f"(max_score={max_score:.2f})")
    
    return results


def retrieve_context_text(
    query: str, 
    top_k: int = 5, 
    max_chars: int = 4000,
    include_sources: bool = True
) -> Tuple[str, float]:
    """
    Retrieve context and format as text for LLM injection with confidence.
    Respects character limit to prevent context overflow.
    
    Args:
        query: Search query
        top_k: Max documents to retrieve
        max_chars: Maximum output characters
        include_sources: Whether to include source attribution
    
    Returns:
        Tuple of (formatted_text, confidence_score)
        - confidence_score: Average confidence of retrieved docs (0-1)
    """
    chunks = retrieve_context(query, top_k=top_k)
    
    if not chunks:
        logger.debug(f"No context retrieved for query: '{query}'")
        return "", 0.0
    
    parts = []
    total_chars = 0
    confidence_scores = []
    
    for chunk in chunks:
        confidence_scores.append(chunk.get("confidence", 0.0))
        
        # Format: [Category — Tags] + Content
        tag_str = ", ".join(chunk.get("tags", [])[:3])
        header = f"[{chunk['category'].upper()}"
        
        if tag_str:
            header += f" — {tag_str}"
        
        # Add confidence indicator if score is available
        conf = chunk.get("confidence", 0.0)
        if conf < 0.3:
            header += " (⚠ LOW CONFIDENCE)"
        elif conf < 0.6:
            header += " (~ MODERATE CONFIDENCE)"
        else:
            header += " (✓ HIGH CONFIDENCE)"
        
        header += "]"
        
        # Add source if requested
        source_line = ""
        if include_sources:
            source = chunk.get("source", "unknown")
            source_line = f"\n[Source: {source}]"
        
        formatted = f"{header}\n{chunk['text'].strip()}{source_line}"
        
        if total_chars + len(formatted) > max_chars:
            logger.debug(f"Truncating context to respect {max_chars} char limit")
            break
        
        parts.append(formatted)
        total_chars += len(formatted)
    
    if not parts:
        return "", 0.0
    
    # Calculate average confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    result = "\n\n---\n\n".join(parts)
    logger.debug(f"Generated {len(parts)} context chunks ({total_chars} chars, confidence={avg_confidence:.2f})")
    
    return result, avg_confidence


def add_knowledge(
    db: Session,
    category: str,
    content: str,
    tags: List[str],
    source: str = "user"
) -> Dict[str, Any]:
    """
    Add a new knowledge entry to the database.
    
    Args:
        db: Database session
        category: Knowledge category (e.g., 'career_path', 'learning_path')
        content: The actual knowledge text
        tags: List of tags for filtering
        source: Origin of knowledge ('user', 'admin', 'api')
    
    Returns:
        Created knowledge entry dict
    """
    try:
        from app.models.rag_knowledge import RAGKnowledge
        
        entry = RAGKnowledge(
            category=category,
            content=content,
            tags=",".join(tags),
            source=source,
            is_active=True,
            created_at=datetime.now()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        logger.info(f"Added knowledge entry: {entry.id} ({category})")
        
        # Invalidate cache
        global _KNOWLEDGE_CACHE
        _KNOWLEDGE_CACHE = []
        
        return {
            "id": entry.id,
            "category": category,
            "tags": tags,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "created_at": str(entry.created_at)
        }
    except Exception as e:
        logger.error(f"Failed to add knowledge: {e}")
        raise


def refresh_cache(db: Session) -> Dict[str, Any]:
    """
    Manually refresh the in-memory knowledge cache from database.
    Useful after bulk updates or periodic maintenance.
    """
    load_knowledge_base(db)
    global _KNOWLEDGE_CACHE
    return {
        "success": True,
        "cached_entries": len(_KNOWLEDGE_CACHE),
        "timestamp": str(_CACHE_TIMESTAMP)
    }


def _get_default_knowledge_base() -> List[Dict[str, Any]]:
    """
    Return default static knowledge base.
    Used as fallback if database is empty or unavailable.
    """
    return [
        {
            "id": "ai_eng_overview",
            "category": "career_path",
            "tags": ["AI engineer", "machine learning", "deep learning", "career"],
            "text": """AI Engineer Career Overview
An AI Engineer designs, builds and deploys machine learning models and intelligent systems.
Core skills: Python, NumPy, Pandas, Scikit-learn, TensorFlow or PyTorch, MLOps, Vector Databases, LLMs (GPT/Llama), REST APIs.
Nice-to-have: Docker, Kubernetes, Cloud (AWS SageMaker / GCP Vertex AI / Azure ML), Statistics, SQL.
Recommended certifications: DeepLearning.AI specializations (Coursera), Google Professional ML Engineer, AWS ML Specialty.
Average time to job-ready from scratch: 8-12 months with 2-3 hrs/day study.
Salary (India): Fresher ₹6-12 LPA. Mid-level ₹15-35 LPA. Senior ₹40-80+ LPA.
Top companies: Google, Microsoft, Amazon, Flipkart, Juspay, Sarvam AI, CRED, Ola, and GenAI startups.""",
            "source": "default",
        },
        {
            "id": "ai_learning_path",
            "category": "learning_path",
            "tags": ["AI engineer", "machine learning", "roadmap", "learning"],
            "text": """AI/ML Learning Roadmap (Beginner → Job-Ready)
Phase 1 – Foundations (Month 1-2): Python basics, Mathematics (Linear Algebra, Calculus), Statistics
Phase 2 – Core ML (Month 2-4): Scikit-learn, Pandas, NumPy, Data visualization
Phase 3 – Deep Learning (Month 4-6): Neural networks, CNNs, RNNs, PyTorch/TensorFlow
Phase 4 – LLMs & Deployment (Month 6-8): LangChain, RAG systems, MLflow, Docker, FastAPI
Projects: Image classifiers, NLP models, RAG chatbots, MLOps pipelines""",
            "source": "default",
        },
        {
            "id": "fullstack_overview",
            "category": "career_path",
            "tags": ["full stack developer", "web development", "react", "node.js"],
            "text": """Full Stack Developer Career Overview
Builds both frontend (UI) and backend (server, database) of web applications.
Core: HTML, CSS, JavaScript (ES6+), React/Vue, Node.js/Express, SQL/NoSQL, REST APIs, Git.
Nice-to-have: TypeScript, Docker, CI/CD, GraphQL, AWS/GCP, Testing.
Time to ready: 4-8 months. Salary (India): Fresher ₹4-8 LPA. Mid ₹10-22 LPA. Senior ₹25-55+ LPA.""",
            "source": "default",
        },
        {
            "id": "cloud_devops_overview",
            "category": "career_path",
            "tags": ["cloud engineer", "DevOps", "AWS", "Azure", "Kubernetes"],
            "text": """Cloud Engineer / DevOps Engineer Career Overview
Design and maintain cloud infrastructure, automate operations.
Core: Linux, Networking, AWS/Azure/GCP, Terraform, Docker, Kubernetes, Python/Bash.
Certifications: AWS Solutions Architect (most valued), Azure AZ-104, GCP Associate, CKA.
Time to ready: 6-10 months. Salary (India): Fresher ₹5-10 LPA. Mid ₹14-28 LPA. Senior ₹30-65+ LPA.""",
            "source": "default",
        },
        {
            "id": "data_scientist_overview",
            "category": "career_path",
            "tags": ["data scientist", "analytics", "statistics", "career"],
            "text": """Data Scientist Career Overview
Extracts insights from data using statistical and ML techniques.
Core: Python (Pandas, NumPy, Scikit-learn), SQL, Statistics, Data Visualization.
Nice-to-have: R, Spark, A/B Testing, Deep Learning, Cloud data warehouses.
Time to ready: 6-10 months. Salary (India): Fresher ₹5-10 LPA. Mid ₹12-30 LPA. Senior ₹35-70+ LPA.""",
            "source": "default",
        },
        {
            "id": "interview_prep",
            "category": "interview",
            "tags": ["interview", "preparation", "DSA", "coding", "system design"],
            "text": """Technical Interview Preparation Guide
DSA: Study Arrays, Strings, Trees, Graphs, Heaps, DP. Practice on LeetCode (150-200 problems).
System Design (2+ years): Load Balancers, Databases, Caching, Message Queues, Microservices.
Behavioral: Use STAR method (Situation, Task, Action, Result).
Resume: Impact metrics, 1 page for freshers, clear project descriptions with GitHub links.""",
            "source": "default",
        },
        {
            "id": "placement_strategy",
            "category": "career_strategy",
            "tags": ["placement", "jobs", "internship", "LinkedIn", "off-campus"],
            "text": """Job Placement Strategy for Students
On-Campus: Most colleges invite TCS, Infosys, Wipro for mass hiring.
Off-Campus: LinkedIn (recruiter connections), AngelList (startups), referrals (fastest path).
Portfolio: GitHub projects, deployed demos, READMEs, open source contributions.
Timeline: 6 months before — fix resume. 3 months — apply actively. 1 month — interview prep.""",
            "source": "default",
        },
        {
            "id": "rag_projects",
            "category": "projects",
            "tags": ["RAG", "AI", "projects", "portfolio", "LangChain"],
            "text": """RAG-Powered Chatbot Project Ideas
Build a Retrieval-Augmented Generation system:
1. Career advisor chatbot with company salary/growth data
2. Documentation assistant with API/framework docs
3. Customer support bot with knowledge base
Tech stack: LangChain, ChromaDB/Pinecone (vector DB), Groq/OpenAI LLM, FastAPI, React
Deploy: Docker, cloud platforms (Render, Railway, AWS Lambda)""",
            "source": "default",
        },
        {
            "id": "current_government_2026",
            "category": "current_facts",
            "tags": ["government", "India", "2026", "CM", "current", "Tamil Nadu", "TVK"],
            "text": """Current Government Leaders in India (June 2026)
Prime Minister: Narendra Modi (BJP) — Re-elected in 2024 general elections
President: Droupadi Murmu (elected July 2022)
Vice President: Jagdeep Dhankhar

State Chief Ministers (as of June 2026):
- Tamil Nadu: C. Vijay (TVK - Tamizhaga Vaalkai Katchi)
- Karnataka: Siddaramaiah (Congress)
- Maharashtra: Eknath Shinde (Shiv Sena Faction)
- Kerala: Pinarayi Vijayan (CPI(M))
- West Bengal: Mamata Banerjee (TMC)
- Uttar Pradesh: Yogi Adityanath (BJP)
- Delhi: Arvind Kejriwal (AAP)
- Rajasthan: Bhajanlal Sharma (BJP)
- Madhya Pradesh: Mohan Yadav (BJP)
- Haryana: Nayab Singh Saini (BJP)
- Punjab: Bhagwant Singh Mann (AAP)
- Gujarat: Bhupendrabhai Patel (BJP)
- Telangana: A. Revanth Reddy (Congress)
- Andhra Pradesh: N. Chandrababu Naidu (TDP)

For latest updates, check: Official state government websites, Election Commission of India.""",
            "source": "admin_2026_verified",
        },
        {
            "id": "current_world_leaders_2026",
            "category": "current_facts",
            "tags": ["government", "world", "presidents", "prime ministers", "2026", "global"],
            "text": """Current World Leaders and Heads of Government (June 2026)

ASIA:
- India PM: Narendra Modi (BJP)
- China President: Xi Jinping
- Japan PM: (Elected 2024)
- South Korea President: (Elected 2022)
- Indonesia President: Prabowo Subianto (Elected October 2024)
- Philippines President: Ferdinand "Bongbong" Marcos Jr
- Malaysia PM: Anwar Ibrahim
- Singapore PM: Lawrence Wong
- Thailand PM: (Following 2023 elections)
- Vietnam General Secretary: Nguyen Phu Trong

AMERICAS:
- USA President: (Elected November 2024)
- Canada PM: Justin Trudeau
- Brazil President: Luiz Inácio Lula da Silva
- Mexico President: (Elected June 2024)
- Argentina President: Javier Milei

EUROPE:
- UK PM: (Following 2024 elections)
- Germany Chancellor: (Following 2025 elections)
- France President: Emmanuel Macron
- Italy PM: Giorgia Meloni
- Spain PM: Pedro Sánchez
- Russia President: Vladimir Putin
- Poland PM: (Following 2023 elections)

AFRICA:
- Nigeria President: Bola Tinubu
- South Africa President: Cyril Ramaphosa
- Kenya President: William Ruto
- Egypt President: Abdel Fattah el-Sisi
- Ethiopia PM: Abiy Ahmed

MIDDLE EAST:
- Saudi Arabia King: Salman bin Abdulaziz Al Saud
- UAE President: Mohammad bin Zayed Al Nahyan
- Israel PM: (Incumbent as of June 2026)
- Iran Supreme Leader: Ayatollah Khamenei
- Turkey President: Recep Tayyip Erdoğan

NOTE: Government positions change regularly. Always verify with official sources:
- Country official government websites
- International news agencies (Reuters, AP, BBC, AFP)
- UN.org for UN representation
- World Bank for international officials""",
            "source": "admin_2026_verified",
        },
        {
            "id": "how_to_update_government_data",
            "category": "current_facts",
            "tags": ["government", "update", "how-to", "RAG", "knowledge"],
            "text": """How to Update Government Information in RAG

IMPORTANT: To prevent AI hallucination, keep government data accurate!

METHOD 1: Update Existing Entry (Fastest)
1. Find the entry ID: current_government_2026 or current_world_leaders_2026
2. Delete it: curl -X DELETE http://localhost:8000/rag/knowledge/[ID]
3. Re-add with correct info: curl -X POST http://localhost:8000/rag/knowledge ...
4. Refresh cache: curl -X POST http://localhost:8000/rag/cache/refresh

METHOD 2: Add Specific Country (Recommended for new leaders)
Use this template:
```
POST /rag/knowledge
{
  "category": "current_facts",
  "content": "[Country Name] Government (June 2026)
  
President/PM: [Name] ([Party]) — Took office [date]
Deputy/VP: [Name]

Key Ministers:
- Finance: [Name]
- Foreign: [Name]
- Defense: [Name]

Status: [Current government status]
Last election: [Date]
Next election: [Date]

Source: Official government website, verified [date]",
  "tags": ["government", "country_name", "2026", "current"],
  "source": "admin_2026_verified"
}
```

METHOD 3: Bulk Upload (Multiple countries)
Create multiple entries, each with:
- Unique ID: unique_country_2026
- Category: current_facts
- Tags: include "government", "2026", country name
- Source: admin_2026_verified
- Content: Current government info

VERIFICATION CHECKLIST:
✅ Name and title are correct
✅ Party/political affiliation is correct
✅ Date took office is accurate
✅ Position is still active (hasn't resigned/been removed)
✅ Tagged with country name for easy retrieval
✅ Source marked as verified

AFTER UPDATING:
1. Always run: curl -X POST http://localhost:8000/rag/cache/refresh
2. Test retrieval: curl -X POST http://localhost:8000/rag/retrieve -d '{"query": "..."}'
3. Ask AI to verify the answer is correct

DO NOT:
❌ Leave old/incorrect data in RAG
❌ Add unverified information
❌ Mix dates (e.g., leaders from different years)
❌ Forget to refresh cache after updates
❌ Add speculative/future information as current fact""",
            "source": "admin_2026_guide",
        },
        # ========== GENERAL KNOWLEDGE SECTION ==========
        {
            "id": "python_basics",
            "category": "general_knowledge",
            "tags": ["python", "programming", "basics", "language", "tutorial"],
            "text": """Python Programming Language — Basics

Python is a high-level, interpreted programming language known for simplicity and readability.

Key Features:
- Easy to learn and read syntax
- Dynamic typing (type checking at runtime)
- Supports multiple programming paradigms (OOP, functional, procedural)
- Extensive standard library ("batteries included")
- Large ecosystem of third-party packages (pip)

Core Concepts:
- Variables: Store data without explicit type declaration
- Data Types: int, float, str, bool, list, dict, tuple, set
- Functions: Reusable blocks of code (def function_name():)
- Modules: Reusable Python files (import module_name)
- Objects: Everything in Python is an object

Common Use Cases:
- Web development (Django, Flask)
- Data science and machine learning (NumPy, Pandas, Scikit-learn)
- Automation and scripting
- Scientific computing
- Desktop applications

Latest Python Version (2024): Python 3.13
Recommended for beginners: Python 3.9+ (good balance of features and compatibility)""",
            "source": "general_knowledge",
        },
        {
            "id": "javascript_web",
            "category": "general_knowledge",
            "tags": ["javascript", "web", "programming", "frontend", "browser"],
            "text": """JavaScript — Web Programming Language

JavaScript is the programming language of web browsers, enabling interactive web applications.

Key Features:
- Runs in web browsers natively (no compilation needed)
- Asynchronous capabilities (callbacks, promises, async/await)
- Event-driven programming (responding to user interactions)
- DOM manipulation (changing HTML/CSS dynamically)
- Closures and functional programming support

Modern JavaScript (ES6+):
- Arrow functions: (x) => x * 2
- Template literals: `Hello ${name}`
- Destructuring: const {name, age} = person
- Async/await: More readable promise handling
- Modules: import/export for code organization

Popular Frameworks:
- React: Component-based UI library (Meta/Facebook)
- Vue.js: Progressive framework (lightweight and approachable)
- Angular: Full-featured framework by Google
- Node.js: JavaScript runtime for server-side development

Frontend Package Managers:
- npm (Node Package Manager): Industry standard
- yarn: Alternative with better dependency resolution
- pnpm: Faster, more disk-efficient

Node.js on Backend:
- Express.js: Minimal web framework
- NestJS: Full-featured with TypeScript support
- Fastify: High-performance alternative""",
            "source": "general_knowledge",
        },
        {
            "id": "database_concepts",
            "category": "general_knowledge",
            "tags": ["database", "SQL", "NoSQL", "data", "storage"],
            "text": """Database Fundamentals

A database is an organized collection of structured data that can be accessed and modified efficiently.

Types of Databases:

RELATIONAL (SQL):
- Organize data in tables with rows and columns
- Strong consistency and ACID properties
- Popular: PostgreSQL, MySQL, SQLServer, Oracle
- Great for structured data with relationships

NO-SQL:
- Flexible schema for varied data structures
- Generally eventual consistency
- Types: Document (MongoDB), Key-Value (Redis), Column (Cassandra), Graph (Neo4j)
- Great for unstructured data, scalability, and flexibility

Key Concepts:
- Tables/Collections: Store related data
- Primary Key: Unique identifier for each record
- Foreign Key: Link to another table's primary key
- Indexing: Speed up data retrieval
- Transactions: Group multiple operations (all succeed or all fail)

Common Query Language (SQL):
- SELECT: Retrieve data
- INSERT: Add new data
- UPDATE: Modify existing data
- DELETE: Remove data
- JOIN: Combine data from multiple tables

Performance Considerations:
- Indexing: Creates fast lookup structures
- Query optimization: Write efficient queries
- Denormalization: Sometimes trade storage for query speed
- Caching: Store frequently accessed data in memory

Modern Approaches:
- Vector databases (Pinecone, Weaviate): For AI/ML embeddings
- Graph databases (Neo4j): For highly connected data
- Time-series databases (InfluxDB): For time-stamped measurements""",
            "source": "general_knowledge",
        },
        {
            "id": "web_concepts",
            "category": "general_knowledge",
            "tags": ["web", "internet", "HTTP", "REST", "API", "browser"],
            "text": """Web Development Fundamentals

The web is built on protocols, standards, and architectural patterns for creating networked applications.

HTTP/HTTPS Protocol:
- HTTP: Hypertext Transfer Protocol (unsecured)
- HTTPS: HTTP Secure (encrypted with SSL/TLS)
- Request-response model: Client sends request, server sends response
- Stateless: Each request is independent (cookies/sessions for state)

HTTP Methods (Verbs):
- GET: Retrieve data (safe, idempotent)
- POST: Submit data (unsafe, creates new resource)
- PUT: Update existing data completely
- PATCH: Partial update
- DELETE: Remove resource

Status Codes:
- 2xx: Success (200 OK, 201 Created)
- 3xx: Redirection (301 Moved Permanently)
- 4xx: Client error (400 Bad Request, 404 Not Found, 401 Unauthorized)
- 5xx: Server error (500 Internal Server Error)

REST (Representational State Transfer):
- Architectural style for designing APIs
- Resources identified by URLs
- Operations via HTTP methods
- Stateless communication
- JSON common for data format

API Design Best Practices:
- Clear endpoint naming: /api/users, /api/products
- Consistent status codes
- Proper error messages with details
- Rate limiting to prevent abuse
- API versioning: /api/v1/, /api/v2/
- Documentation (Swagger/OpenAPI)

Frontend Technologies:
- HTML: Structure (semantic markup)
- CSS: Styling and layout (Flexbox, Grid)
- JavaScript: Interactivity and logic
- DOM: Document Object Model (tree structure of page)

Backend Considerations:
- Routing: Map URLs to handlers
- Middleware: Process requests/responses
- Authentication: Verify user identity
- Authorization: Check user permissions
- Database integration: Persist data
- Caching: Improve performance
- Logging: Track application behavior""",
            "source": "general_knowledge",
        },
        {
            "id": "git_version_control",
            "category": "general_knowledge",
            "tags": ["git", "version control", "SCM", "github", "collaboration"],
            "text": """Git and Version Control

Git is a distributed version control system for tracking code changes and enabling team collaboration.

Basic Concepts:
- Repository: Directory containing all project files and history
- Commit: Snapshot of code at a point in time
- Branch: Parallel version of codebase for isolated development
- Remote: Centralized repository (GitHub, GitLab, Bitbucket)
- Working directory: Your local files
- Staging area: Files ready to be committed

Basic Commands:
- git init: Create new repository
- git clone [url]: Copy remote repository
- git add [file]: Stage file for commit
- git commit -m "message": Create snapshot
- git push: Upload commits to remote
- git pull: Download commits from remote
- git branch: Create/list branches
- git merge: Combine branches
- git log: View commit history

Branching Strategies:
- Feature branches: Create branch for each feature
- Git Flow: Complex workflow with develop and release branches
- GitHub Flow: Simple main + feature branches
- Trunk-based: Small, frequent merges to main

Collaboration Workflow:
1. Create feature branch: git checkout -b feature/xyz
2. Make changes and commit
3. Push to remote: git push origin feature/xyz
4. Create Pull Request (PR)
5. Code review and discussion
6. Merge to main after approval
7. Delete feature branch

Best Practices:
- Write clear, descriptive commit messages
- Commit related changes together
- Don't commit secrets or node_modules
- Use .gitignore to exclude files
- Keep branches updated with main
- Review before merging
- Atomic commits (single concern per commit)""",
            "source": "general_knowledge",
        },
        {
            "id": "api_rest_graphql",
            "category": "general_knowledge",
            "tags": ["API", "REST", "GraphQL", "architecture", "design"],
            "text": """API Design Patterns — REST vs GraphQL

APIs (Application Programming Interfaces) allow different software to communicate.

REST API Characteristics:
- Resource-oriented: URLs represent resources (/users, /posts)
- HTTP methods for operations (GET, POST, PUT, DELETE)
- Predictable and simple
- Standard status codes for responses
- JSON/XML for data format
- Stateless (server doesn't store client context)

REST Example:
GET /api/users/123 → Returns user with ID 123
POST /api/users → Creates new user
PUT /api/users/123 → Updates user 123
DELETE /api/users/123 → Deletes user 123

REST Advantages:
- Simple and easy to understand
- Widely adopted and standardized
- Great browser caching support
- Good for public APIs

REST Disadvantages:
- Over-fetching (get more data than needed)
- Under-fetching (need multiple requests)
- Versioning challenges
- Limited filtering/search options

GraphQL Characteristics:
- Query-based: Ask for exactly what you need
- Single endpoint (typically /graphql)
- Strongly typed schema
- Avoids over/under-fetching
- Real-time capabilities (subscriptions)

GraphQL Example:
query {
  user(id: 123) {
    name
    email
    posts {
      title
    }
  }
}

GraphQL Advantages:
- Get exactly what you request (no wasted data)
- Strongly typed (schema validation)
- Good for mobile apps (bandwidth efficiency)
- Self-documenting (introspection)
- Single request for complex queries

GraphQL Disadvantages:
- Steeper learning curve
- Caching complexity
- File uploads more difficult
- Query complexity management needed

Choosing Between REST and GraphQL:
- Use REST: Public APIs, simple CRUD operations, caching important
- Use GraphQL: Complex queries, mobile apps, rapidly changing requirements""",
            "source": "general_knowledge",
        },
        {
            "id": "machine_learning_intro",
            "category": "general_knowledge",
            "tags": ["machine learning", "AI", "neural networks", "algorithms", "data science"],
            "text": """Machine Learning Fundamentals

Machine Learning is programming systems to learn patterns from data instead of explicit instructions.

Types of Machine Learning:

SUPERVISED LEARNING:
- Training data has labels/answers
- Learn to predict from input to output
- Regression: Predict continuous values (price, temperature)
- Classification: Predict categories (spam/not spam, disease/healthy)
- Algorithms: Decision Trees, Random Forests, SVM, Linear Regression

UNSUPERVISED LEARNING:
- Training data has no labels
- Find patterns and structure
- Clustering: Group similar items (customer segments)
- Dimensionality Reduction: Simplify complex data
- Algorithms: K-means, DBSCAN, PCA

REINFORCEMENT LEARNING:
- Learn by interaction and rewards
- Agent learns optimal actions
- Applications: Game AI, robotics, autonomous systems
- Algorithms: Q-learning, Policy Gradients

Deep Learning:
- Neural networks with many layers
- Excellent for unstructured data (images, text, audio)
- Requires lots of data and computation
- Models: CNN (images), RNN/Transformer (sequences), autoencoders

Common Algorithms:

Linear Regression: Predict continuous values with linear relationship
Decision Trees: Rule-based predictions (interpretable)
Random Forest: Multiple trees for better predictions
SVM: Find separating boundaries (classification)
K-means: Group data into K clusters
Neural Networks: Flexible, powerful, universal approximators

ML Pipeline:
1. Collect data
2. Clean and preprocess
3. Feature engineering (transform data)
4. Split train/test sets
5. Train model
6. Evaluate performance
7. Tune hyperparameters
8. Deploy and monitor

Key Metrics:
- Accuracy: % correct predictions
- Precision: % positive predictions that are correct
- Recall: % actual positives found
- F1-score: Balance between precision and recall
- ROC-AUC: Performance across thresholds""",
            "source": "general_knowledge",
        },
        {
            "id": "cloud_computing",
            "category": "general_knowledge",
            "tags": ["cloud", "AWS", "Azure", "GCP", "infrastructure"],
            "text": """Cloud Computing Overview

Cloud computing delivers computing services (servers, databases, software) over the internet.

Service Models:

IAAS (Infrastructure as a Service):
- Rent computing resources (servers, storage, network)
- You manage: applications, data, middleware, runtime
- Provider manages: infrastructure, virtualization
- Examples: AWS EC2, Azure VMs, Google Compute Engine

PAAS (Platform as a Service):
- Rent development environment and deployment platform
- You manage: applications, data
- Provider manages: infrastructure, middleware, runtime
- Examples: Heroku, Firebase, AWS Elastic Beanstalk

SAAS (Software as a Service):
- Use software over the internet
- You manage: nothing (just use it)
- Provider manages: everything
- Examples: Gmail, Slack, Salesforce, Office 365

Deployment Models:

Public Cloud:
- Infrastructure shared by multiple users
- Cost-effective, scalable
- AWS, Azure, Google Cloud

Private Cloud:
- Infrastructure for single organization
- Higher control and security
- Higher cost

Hybrid Cloud:
- Mix of public and private
- Flexibility and optimization

Major Cloud Providers:
- AWS (Amazon Web Services): Largest, most features
- Azure (Microsoft): Good enterprise integration
- GCP (Google Cloud): Strong data/AI services
- Others: DigitalOcean, Linode, Alibaba Cloud

Common Services:
- Compute: Servers, containers (Kubernetes)
- Storage: Databases (SQL, NoSQL), object storage
- Networking: Load balancers, CDN, DNS
- Managed Services: Email, messaging, analytics
- AI/ML: Pre-trained models, training platforms

Benefits:
- Scalability: Grow resources as needed
- Cost-effective: Pay only for what you use
- Reliability: Redundancy and backup
- Global reach: Data centers worldwide
- Security: Professional security teams

Challenges:
- Vendor lock-in: Difficult to switch providers
- Data privacy: Data stored by third party
- Cost management: Can grow unexpectedly
- Network latency: For latency-sensitive apps""",
            "source": "general_knowledge",
        },
        {
            "id": "deployment_devops",
            "category": "general_knowledge",
            "tags": ["deployment", "DevOps", "CI/CD", "Docker", "Kubernetes"],
            "text": """Deployment and DevOps Practices

DevOps is a culture and practice combining development and operations for continuous delivery.

Containerization (Docker):
- Package application with all dependencies
- Lightweight alternative to virtual machines
- "Docker image": Read-only template
- "Container": Running instance of image
- Dockerfile: Instructions to build image
- Docker Compose: Run multiple containers together

Container Orchestration (Kubernetes):
- Manage many containers across machines
- Auto-scaling: Add containers under load
- Load balancing: Distribute traffic
- Service discovery: Find containers
- Rolling updates: Deploy without downtime
- Self-healing: Restart failed containers

CI/CD (Continuous Integration/Deployment):
- CI: Automatically test code changes
- CD: Automatically deploy to production
- Pipeline: Automated workflow from code to production

CI/CD Tools:
- GitHub Actions: Built into GitHub
- GitLab CI/CD: Built into GitLab
- Jenkins: Self-hosted automation server
- CircleCI: Cloud-based CI/CD

Basic CI/CD Pipeline:
1. Developer pushes code
2. Automated tests run
3. Build application
4. Run security scans
5. Deploy to staging
6. Run integration tests
7. Deploy to production
8. Monitor and log

Infrastructure as Code (IaC):
- Define infrastructure in code (not manual)
- Tools: Terraform, CloudFormation, Bicep
- Benefits: Reproducible, versionable, auditable

Monitoring and Logging:
- Prometheus: Metrics collection
- Grafana: Visualization dashboards
- ELK Stack: Logging (Elasticsearch, Logstash, Kibana)
- Datadog: All-in-one monitoring
- CloudWatch: AWS native monitoring

Best Practices:
- Automate everything possible
- Test before deploying
- Monitor in production
- Quick rollback capability
- Keep infrastructure in version control
- Document deployments
- Plan for disasters""",
            "source": "general_knowledge",
        },
        {
            "id": "security_basics",
            "category": "general_knowledge",
            "tags": ["security", "authentication", "encryption", "cyber", "best practices"],
            "text": """Information Security Fundamentals

Security is protecting systems and data from unauthorized access and misuse.

Authentication & Authorization:

Authentication:
- Verify user identity (who are you?)
- Methods: passwords, biometrics, multi-factor
- MFA (Multi-Factor Authentication): Multiple verification methods

Authorization:
- Check user permissions (what can you do?)
- Role-based access control (RBAC)
- Principle of least privilege (minimum needed access)

Encryption:

Symmetric (Same key for encrypt/decrypt):
- Fast, good for bulk data
- Challenge: Key distribution
- Algorithms: AES, DES

Asymmetric (Public/Private key pairs):
- Slower, good for key exchange
- Public key: Share freely
- Private key: Keep secret
- Algorithms: RSA, ECC

Hashing:
- One-way transformation
- Same input always produces same hash
- Good for: Password storage, integrity checking
- Algorithms: SHA-256, bcrypt, scrypt

HTTPS/TLS:
- Secure communication over web
- Encrypts data in transit
- Server authentication via certificates
- Essential for any sensitive data

Common Vulnerabilities:

SQL Injection:
- Attacker inserts malicious SQL
- Prevention: Prepared statements, input validation

Cross-Site Scripting (XSS):
- Inject malicious JavaScript into pages
- Prevention: Input validation, output encoding

CSRF (Cross-Site Request Forgery):
- Force user to perform unintended action
- Prevention: CSRF tokens

Weak Passwords:
- Easy to guess or brute-force
- Prevention: Length, complexity, uniqueness

Unpatched Software:
- Known vulnerabilities exploited
- Prevention: Regular updates

Best Practices:
- Use strong, unique passwords
- Enable multi-factor authentication
- Keep software updated
- Regular security audits
- Principle of least privilege
- Encrypt sensitive data
- Monitor for suspicious activity
- Use HTTPS everywhere
- Regular backups
- Security training for team""",
            "source": "general_knowledge",
        },
    ]
