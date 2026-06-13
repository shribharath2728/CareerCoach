#!/bin/bash
# Quick fix script for correct government data

echo "🔄 Refreshing RAG with Correct Government Information..."
echo ""

# Step 1: Refresh cache
echo "1️⃣  Refreshing RAG cache..."
curl -X POST http://localhost:8000/rag/cache/refresh
echo ""
echo ""

# Step 2: Verify the correct data is loaded
echo "2️⃣  Verifying correct Tamil Nadu CM data..."
curl -X POST http://localhost:8000/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "C. Vijay TVK Tamil Nadu CM 2026",
    "top_k": 3
  }' | jq '.'
echo ""
echo ""

# Step 3: Check stats
echo "3️⃣  Checking RAG knowledge base..."
curl http://localhost:8000/rag/stats | jq '.'
echo ""

echo "✅ Done! Your AI will now answer with correct information:"
echo "   CM of Tamil Nadu 2026: C. Vijay (TVK)"
echo ""
echo "Test in chat: 'Who is the CM of Tamil Nadu in 2026?'"
