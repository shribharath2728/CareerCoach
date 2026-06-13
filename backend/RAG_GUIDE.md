# RAG (Retrieval-Augmented Generation) Implementation Guide

## Overview

Your SkillLens AI now has a fully functional RAG system that retrieves relevant career knowledge and injects it into AI responses. This ensures the AI provides grounded, accurate career advice based on your knowledge base.

## What Changed

### 1. **New RAG Service** (`app/services/rag_service.py`)
- Improved knowledge base retrieval with TF-IDF + tag matching scoring
- Database persistence for dynamic knowledge management
- In-memory caching for fast retrieval
- Comprehensive retrieval scoring algorithm

### 2. **Database Model** (`app/models/rag_knowledge.py`)
- New `RAGKnowledge` table to store knowledge entries
- Supports categories, tags, and full text search
- Tracks knowledge source (default, user, admin, api)
- Active/inactive flags for soft deletes

### 3. **RAG Management Endpoints** (`app/api/rag_routes.py`)
Endpoints to manage your knowledge base:
- `POST /rag/knowledge` - Add new knowledge entries
- `GET /rag/knowledge` - List knowledge entries
- `POST /rag/retrieve` - Test RAG context retrieval
- `GET /rag/stats` - View knowledge base statistics
- `POST /rag/cache/refresh` - Manually refresh cache
- `POST /rag/populate-defaults` - Load default career knowledge

### 4. **Enhanced Chat Service** (`app/services/chat_service.py`)
- Automatically retrieves RAG context for user queries
- Injects relevant knowledge into system prompt
- Logs RAG context usage for debugging

### 5. **Foundry IQ Integration** (`app/services/foundry_iq.py`)
- Now uses the new `rag_service` instead of hardcoded knowledge
- Maintains reasoning layer with grounded context

## Setup Instructions

### Step 1: Initialize the Database

Run the setup script to create tables and populate default knowledge:

```bash
cd backend
python setup_rag.py
```

This will:
- Create the `rag_knowledge` table
- Load 8 default career knowledge entries
- Test the RAG retrieval system
- Print statistics

### Step 2: Verify RAG is Working

Check the logs when your backend starts:

```
INFO: Loaded X knowledge entries from database
DEBUG: Retrieved Y documents for query: '...'
INFO: AI response generated (Z chars)
```

### Step 3: Add Custom Knowledge (Optional)

Add your own career knowledge entries via the API:

```bash
curl -X POST http://localhost:8000/rag/knowledge \
  -H "Content-Type: application/json" \
  -d {
    "category": "career_path",
    "content": "DevOps Engineer role...",
    "tags": ["DevOps", "cloud", "kubernetes"],
    "source": "admin"
  }
```

## How RAG Works in Your AI

### User Message Flow

```
User: "How do I become an AI engineer?"
         ↓
[Extract Query]
         ↓
[RAG Retrieval] → Search knowledge base for "AI engineer", "machine learning"
         ↓
[Retrieved Context] → "AI Engineer Career Overview", "AI Learning Path", etc.
         ↓
[Inject into System Prompt] → AI now has grounded knowledge
         ↓
[Generate Response] → References actual career paths, skills, timelines
```

### Retrieval Scoring

The system scores documents using:

1. **Tag Matching** (highest weight) - Direct keyword matches in tags
2. **Category Matching** - Relevant category names
3. **TF-IDF Scoring** - Term frequency across the knowledge base

Example: Query "Python machine learning"
- `Tags: ["Python", "AI", "ML"]` → High score (tags match)
- `Category: "learning_path"` → Medium score
- `Content: frequent mentions of "Python" and "models"` → Added score

## Knowledge Base Structure

### Default Categories

- **career_path** - Career overview, roles, salaries, companies
- **learning_path** - Step-by-step learning roadmaps
- **interview** - Interview preparation guides
- **projects** - Portfolio project ideas
- **certification** - Certification recommendations
- **career_strategy** - Job search, placement strategies
- **faq** - Frequently asked questions

### Default Knowledge Entries

1. **ai_eng_overview** - AI Engineer career path
2. **ai_learning_path** - AI/ML learning roadmap
3. **fullstack_overview** - Full Stack Developer career
4. **cloud_devops_overview** - Cloud/DevOps engineering
5. **data_scientist_overview** - Data Science career
6. **interview_prep** - Technical interview guide
7. **placement_strategy** - Job search strategy
8. **rag_projects** - RAG project ideas

## API Endpoints Reference

### Retrieve Context
```bash
POST /rag/retrieve
Content-Type: application/json

{
  "query": "machine learning career path",
  "top_k": 5,
  "max_chars": 4000
}

Response:
{
  "query": "machine learning career path",
  "results_count": 3,
  "context": "[CAREER_PATH — AI engineer...]\n\n[LEARNING_PATH — ...",
  "retrieved_documents": [
    {
      "id": "ai_eng_overview",
      "category": "career_path",
      "tags": ["AI engineer", "machine learning"],
      "score": 12.5,
      "preview": "An AI Engineer designs..."
    }
  ]
}
```

### Add Knowledge
```bash
POST /rag/knowledge
Content-Type: application/json

{
  "category": "career_path",
  "content": "Full text of the knowledge entry...",
  "tags": ["tag1", "tag2", "tag3"],
  "source": "user"
}

Response:
{
  "success": true,
  "message": "Knowledge entry added successfully",
  "entry": {
    "id": 42,
    "category": "career_path",
    "tags": ["tag1", "tag2", "tag3"],
    "content": "...",
    "created_at": "2026-06-11T..."
  }
}
```

### List Knowledge
```bash
GET /rag/knowledge?category=career_path&skip=0&limit=10

Response: [
  {
    "id": 1,
    "category": "career_path",
    "tags": ["..."],
    "content": "...",
    "source": "default",
    "is_active": true,
    "created_at": "..."
  }
]
```

### View Statistics
```bash
GET /rag/stats

Response:
{
  "total_entries": 42,
  "active_entries": 40,
  "categories": {
    "career_path": 15,
    "learning_path": 10,
    "projects": 8,
    ...
  },
  "cache_status": "loaded",
  "cache_timestamp": "2026-06-11T10:30:..."
}
```

### Refresh Cache
```bash
POST /rag/cache/refresh

Response:
{
  "success": true,
  "message": "Cache refreshed successfully",
  "data": {
    "cached_entries": 42,
    "timestamp": "2026-06-11T..."
  }
}
```

## Monitoring RAG Performance

### Check Chat Service Logs

The chat service logs RAG context retrieval:

```
DEBUG: Retrieved RAG context (2847 chars) for query: 'how to become an engineer'
```

### Test Retrieval Directly

Use the `/rag/retrieve` endpoint in Swagger UI to test specific queries:

1. Go to http://localhost:8000/docs
2. Find the `/rag/retrieve` endpoint
3. Try queries like:
   - "machine learning"
   - "interview preparation"
   - "full stack developer"
   - "job search strategy"

### Monitor Cache Status

Check if the cache is loaded:

```bash
GET /rag/stats
```

Expected response includes:
- `cache_status: "loaded"`
- `cache_timestamp`: Recent timestamp
- Entries count > 0

## Troubleshooting

### No Context Retrieved

**Problem**: `No RAG context found for query`

**Solution**:
1. Check if table exists: `SELECT COUNT(*) FROM rag_knowledge;`
2. Run `python setup_rag.py` to initialize defaults
3. Verify cache is loaded: `GET /rag/stats`

### Cache Not Updating

**Problem**: Recent additions not showing in responses

**Solution**:
```bash
POST /rag/cache/refresh
```

This reloads the knowledge base from database.

### Poor Retrieval Results

**Problem**: Irrelevant documents retrieved

**Solutions**:
1. Check tags are descriptive: `GET /rag/knowledge`
2. Add more knowledge entries with relevant tags
3. Adjust `top_k` parameter (default 5)
4. Adjust query specificity

### Database Connection Issues

**Problem**: `No RAG context found for query` (silently failing)

**Solution**:
1. Check DATABASE_URL in `.env`
2. Verify table exists: `\dt rag_knowledge` (psql)
3. Check RAG model import: `python -c "from app.models import RAGKnowledge"`

## Best Practices

### 1. Knowledge Organization

Use consistent tags for filtering:
```json
{
  "category": "career_path",
  "tags": ["AI engineer", "machine learning", "career", "Python"],
  "content": "..."
}
```

### 2. Content Quality

- Use clear, well-structured knowledge entries
- Include specific details (salaries, timelines, companies)
- Keep entries focused on one topic
- Use markdown for readability

### 3. Regular Updates

- Update knowledge entries quarterly
- Monitor logs for poor retrieval matches
- Add knowledge based on student feedback
- Archive outdated entries (soft delete)

### 4. Cache Management

- Refresh cache after bulk updates: `POST /rag/cache/refresh`
- Cache TTL is 1 hour by default
- Monitor cache hit rate in logs

## Integration with Chat

The RAG system automatically integrates with chat:

```python
# In chat_service.py
rag_context = rag_service.retrieve_context_text(
    user_query,
    top_k=5,
    max_chars=3500
)

# This context is injected into the system prompt
system_prompt = _build_system_prompt(rag_context)
```

The system prompt now includes:

```
## RETRIEVED CAREER KNOWLEDGE
Use this to ground your answers:
[Source: CAREER_PATH — AI engineer, machine learning, career]
AI Engineer Career Overview...

[Source: LEARNING_PATH — learning, courses]
Learning Roadmap...
```

## Performance Notes

- **Retrieval Speed**: < 10ms for 50 documents (in-memory)
- **Cache Reload**: < 100ms for 50 documents (from database)
- **Context Size**: Limited to 3500 chars to fit in LLM context
- **Max Docs**: Top 5 documents recommended (top_k=5)

## Future Enhancements

Potential improvements:
1. **Vector Embeddings** - Use embeddings for semantic similarity
2. **Advanced Filtering** - Filter by difficulty level, language
3. **Knowledge Graphs** - Link related topics
4. **User Feedback** - Rate helpful responses
5. **Analytics** - Track which knowledge is most helpful

## Support

For issues or questions:
1. Check logs: `tail -f backend.log`
2. Test RAG directly: Use `/rag/retrieve` endpoint
3. Verify setup: Run `python setup_rag.py`
4. Check documentation: This file and API docs
