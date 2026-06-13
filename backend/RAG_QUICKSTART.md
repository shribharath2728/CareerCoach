# RAG Quick Start Guide

## Get Your AI Working with RAG in 3 Steps

### Step 1: Initialize RAG Knowledge Base

```bash
cd backend
python setup_rag.py
```

Expected output:
```
Creating database tables...
✓ Database tables created

Initializing RAG knowledge base...
✓ Added 8 default RAG knowledge entries

Testing RAG retrieval system...
  Query: 'machine learning career path'
  → Found 3 results
    1. career_path (score: 12.54)
    2. learning_path (score: 8.32)
    3. projects (score: 5.20)

✓ RAG retrieval test passed

RAG Knowledge Base Statistics:
  Total entries: 8
  Active entries: 8
  Categories:
    - career_path: 4
    - learning_path: 1
    - projects: 1
    - interview: 2

✓ Setup completed successfully!
```

### Step 2: Start Your Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Look for this message in logs:
```
INFO: Loaded 8 knowledge entries from database
```

### Step 3: Test in Chat

Send a message in your chat interface:

**User**: "How do I become an AI engineer?"

**AI Response** (now grounded in RAG): "Great question! I can help you with that. Based on career knowledge, becoming an AI Engineer typically takes 8-12 months of focused learning. Here's the path:

**Core Skills You'll Need:**
- Python, NumPy, Pandas, Scikit-learn
- TensorFlow or PyTorch
- MLOps fundamentals
- Understanding of Vector Databases and LLMs

**Learning Roadmap:**
Phase 1 (Months 1-2): Python & Math fundamentals
Phase 2 (Months 2-4): Core ML with Scikit-learn
Phase 3 (Months 4-6): Deep Learning with PyTorch
Phase 4 (Months 6-8): LLMs, RAG systems, Deployment

**Salary Expectations (India):**
- Fresher: ₹6-12 LPA
- Mid-level: ₹15-35 LPA
- Senior: ₹40-80+ LPA

**Top Companies:** Google, Microsoft, Amazon, Flipkart, AI startups..."

Notice how the response is now grounded in actual career knowledge!

## What's Different Now

### Before (Old System)
❌ Static hardcoded knowledge  
❌ Poor retrieval  
❌ AI sometimes doesn't reference current facts  
❌ No way to update knowledge  
❌ Context not properly integrated  

### After (New RAG System)
✅ Dynamic knowledge base in database  
✅ Smart TF-IDF scoring for retrieval  
✅ AI grounded in retrieved knowledge  
✅ Easy API to add/update knowledge  
✅ Context properly injected into prompts  
✅ Caching for fast retrieval  
✅ Full stats and monitoring  

## Add Your Own Knowledge

### Via API (Easy)

```bash
curl -X POST http://localhost:8000/rag/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "category": "career_path",
    "content": "DevOps Engineer Career: Modern infrastructure management using Kubernetes, Docker, Terraform, CI/CD pipelines. Salary: Fresher 5-10 LPA, Mid 14-28 LPA, Senior 30-65+ LPA. Top companies: Microsoft, Amazon, Google, startups.",
    "tags": ["DevOps", "cloud", "kubernetes", "career"],
    "source": "admin"
  }'
```

### Via Swagger UI

1. Go to http://localhost:8000/docs
2. Find `POST /rag/knowledge`
3. Click "Try it out"
4. Fill in the form:
   - **category**: `career_path`
   - **content**: Your knowledge text
   - **tags**: Comma-separated tags
   - **source**: `user` or `admin`
5. Click "Execute"

## Monitor RAG Performance

### Check Statistics

```bash
curl http://localhost:8000/rag/stats | jq
```

Response:
```json
{
  "total_entries": 8,
  "active_entries": 8,
  "categories": {
    "career_path": 4,
    "learning_path": 1,
    "interview": 2,
    "projects": 1
  },
  "cache_status": "loaded",
  "cache_timestamp": "2026-06-11T10:30:45.123456"
}
```

### Test Retrieval

```bash
curl -X POST http://localhost:8000/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning career",
    "top_k": 5,
    "max_chars": 4000
  }' | jq
```

### View Knowledge Entries

```bash
curl http://localhost:8000/rag/knowledge | jq
```

## Common Tasks

### Add New Career Path

```bash
curl -X POST http://localhost:8000/rag/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "category": "career_path",
    "content": "Full description of the career path...",
    "tags": ["tag1", "tag2", "tag3"],
    "source": "admin"
  }'
```

### Add Learning Roadmap

```bash
curl -X POST http://localhost:8000/rag/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "category": "learning_path",
    "content": "Step-by-step learning guide: Phase 1: ..., Phase 2: ...",
    "tags": ["learning", "skill_name"],
    "source": "admin"
  }'
```

### Add Interview Guide

```bash
curl -X POST http://localhost:8000/rag/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "category": "interview",
    "content": "Interview preparation tips, questions, answers...",
    "tags": ["interview", "preparation"],
    "source": "admin"
  }'
```

### Refresh Cache After Bulk Updates

```bash
curl -X POST http://localhost:8000/rag/cache/refresh
```

## Verify Everything Works

### Check Backend Logs

Look for these logs when starting:
```
INFO: Loaded 8 knowledge entries from database
INFO: Database tables + schema check complete.
```

When sending a chat message:
```
DEBUG: Retrieved RAG context (2847 chars) for query: 'machine learning'
INFO: AI response generated (1523 chars)
```

### Test Chat Integration

1. Open your frontend
2. Start a new chat
3. Ask: "What skills do I need for AI?"
4. Check backend logs for:
   - `DEBUG: Retrieved RAG context`
   - `INFO: AI response generated`
5. AI response should reference actual career data

## Troubleshooting

### Q: I don't see RAG context in logs

**A**: Check logs have `DEBUG` level enabled:
```python
# In main.py or app startup
logging.basicConfig(level=logging.DEBUG)
```

### Q: Database table doesn't exist

**A**: Run setup:
```bash
python setup_rag.py
```

### Q: Changes not reflecting in chat

**A**: Refresh cache:
```bash
curl -X POST http://localhost:8000/rag/cache/refresh
```

### Q: Retrieval returning empty results

**A**: 
1. Check knowledge base: `curl http://localhost:8000/rag/knowledge`
2. Test query directly: `curl -X POST http://localhost:8000/rag/retrieve -d '{"query": "...}'`
3. Verify database connection

## Next Steps

1. **Add More Knowledge** - Use the API to add company info, project ideas, etc.
2. **Monitor Stats** - Check `/rag/stats` regularly
3. **Improve Retrieval** - Adjust `top_k` and `max_chars` based on quality
4. **User Feedback** - Get students to rate AI responses, improve knowledge
5. **Read Full Guide** - Check `RAG_GUIDE.md` for advanced features

## API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rag/knowledge` | POST | Add new knowledge entry |
| `/rag/knowledge` | GET | List all knowledge |
| `/rag/knowledge/{id}` | GET | Get specific entry |
| `/rag/knowledge/{id}` | DELETE | Deactivate entry |
| `/rag/retrieve` | POST | Test RAG retrieval |
| `/rag/cache/refresh` | POST | Refresh cache |
| `/rag/stats` | GET | View statistics |
| `/rag/populate-defaults` | POST | Load defaults |

Enjoy your fully-functional RAG system! 🚀
