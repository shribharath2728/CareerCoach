"""
RAG Knowledge Management Routes
================================
Endpoints for managing the RAG knowledge base.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.rag_knowledge import RAGKnowledge
from app.schemas.rag import (
    RAGKnowledgeCreate,
    RAGKnowledgeResponse,
    RAGRetrievalRequest,
    RAGRetrievalResponse,
    RAGStats,
)
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])
logger = logging.getLogger(__name__)


@router.post("/knowledge", response_model=dict)
def add_knowledge(
    req: RAGKnowledgeCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new knowledge entry to the RAG knowledge base.
    
    This entry will be immediately available for retrieval in chat sessions.
    """
    try:
        result = rag_service.add_knowledge(
            db=db,
            category=req.category,
            content=req.content,
            tags=req.tags,
            source=req.source
        )
        return {
            "success": True,
            "message": "Knowledge entry added successfully",
            "entry": result
        }
    except Exception as e:
        logger.error(f"Failed to add knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve", response_model=RAGRetrievalResponse)
def retrieve_context(
    req: RAGRetrievalRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieve context from the RAG knowledge base for a given query.
    
    Returns the most relevant documents and formatted context text
    ready for injection into LLM prompts.
    """
    try:
        # Load fresh knowledge from DB
        rag_service.load_knowledge_base(db)
        
        # Retrieve context
        docs = rag_service.retrieve_context(req.query, top_k=req.top_k)
        context_text = rag_service.retrieve_context_text(
            req.query, 
            top_k=req.top_k, 
            max_chars=req.max_chars
        )
        
        # Format response
        return RAGRetrievalResponse(
            query=req.query,
            results_count=len(docs),
            context=context_text,
            retrieved_documents=[
                {
                    "id": doc["id"],
                    "category": doc["category"],
                    "tags": doc.get("tags", []),
                    "score": doc.get("score", 0),
                    "preview": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"]
                }
                for doc in docs
            ]
        )
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/refresh", response_model=dict)
def refresh_cache(db: Session = Depends(get_db)):
    """
    Manually refresh the in-memory cache from the database.
    
    Useful after bulk updates or to force synchronization.
    """
    try:
        result = rag_service.refresh_cache(db)
        return {
            "success": True,
            "message": "Cache refreshed successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge", response_model=list[RAGKnowledgeResponse])
def list_knowledge(
    category: str = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List all knowledge entries in the RAG knowledge base.
    
    Supports filtering by category and pagination.
    """
    try:
        query = db.query(RAGKnowledge).filter(RAGKnowledge.is_active == True)
        
        if category:
            query = query.filter(RAGKnowledge.category == category)
        
        entries = query.offset(skip).limit(limit).all()
        
        return [
            RAGKnowledgeResponse(
                id=e.id,
                category=e.category,
                tags=e.tags.split(",") if e.tags else [],
                content=e.content,
                source=e.source,
                is_active=e.is_active,
                created_at=e.created_at,
                updated_at=e.updated_at
            )
            for e in entries
        ]
    except Exception as e:
        logger.error(f"Failed to list knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{knowledge_id}", response_model=RAGKnowledgeResponse)
def get_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific knowledge entry by ID."""
    entry = db.query(RAGKnowledge).filter(RAGKnowledge.id == knowledge_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    return RAGKnowledgeResponse(
        id=entry.id,
        category=entry.category,
        tags=entry.tags.split(",") if entry.tags else [],
        content=entry.content,
        source=entry.source,
        is_active=entry.is_active,
        created_at=entry.created_at,
        updated_at=entry.updated_at
    )


@router.delete("/knowledge/{knowledge_id}", response_model=dict)
def delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft-delete a knowledge entry (mark as inactive).
    
    Data is preserved but won't be used in RAG retrieval.
    """
    entry = db.query(RAGKnowledge).filter(RAGKnowledge.id == knowledge_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    entry.is_active = False
    db.commit()
    
    # Invalidate cache
    rag_service.load_knowledge_base(db)
    
    return {
        "success": True,
        "message": f"Knowledge entry {knowledge_id} deactivated"
    }


@router.get("/stats", response_model=RAGStats)
def get_stats(db: Session = Depends(get_db)):
    """Get statistics about the RAG knowledge base."""
    try:
        total = db.query(func.count(RAGKnowledge.id)).scalar() or 0
        active = db.query(func.count(RAGKnowledge.id)).filter(
            RAGKnowledge.is_active == True
        ).scalar() or 0
        
        # Count by category
        categories_raw = db.query(
            RAGKnowledge.category,
            func.count(RAGKnowledge.id)
        ).filter(RAGKnowledge.is_active == True).group_by(
            RAGKnowledge.category
        ).all()
        
        categories = {cat: count for cat, count in categories_raw}
        
        from datetime import datetime
        cache_info = rag_service._CACHE_TIMESTAMP
        
        return RAGStats(
            total_entries=total,
            active_entries=active,
            categories=categories,
            cache_status="loaded" if cache_info else "empty",
            cache_timestamp=str(cache_info) if cache_info else None
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/populate-defaults", response_model=dict)
def populate_defaults(db: Session = Depends(get_db)):
    """
    Populate the knowledge base with default career knowledge.
    
    Useful for initial setup. Only adds if not already present.
    """
    try:
        count_before = db.query(func.count(RAGKnowledge.id)).scalar() or 0
        
        defaults = rag_service._get_default_knowledge_base()
        added = 0
        
        for default in defaults:
            # Check if already exists
            existing = db.query(RAGKnowledge).filter(
                RAGKnowledge.id == default.get("id")
            ).first()
            
            if not existing:
                entry = RAGKnowledge(
                    id=default.get("id"),
                    category=default["category"],
                    tags=",".join(default.get("tags", [])),
                    content=default["text"],
                    source=default.get("source", "default"),
                    is_active=True
                )
                db.add(entry)
                added += 1
        
        db.commit()
        
        # Refresh cache
        rag_service.load_knowledge_base(db)
        
        count_after = db.query(func.count(RAGKnowledge.id)).scalar() or 0
        
        return {
            "success": True,
            "message": f"Populated defaults: added {added} entries",
            "total_before": count_before,
            "total_after": count_after
        }
    except Exception as e:
        logger.error(f"Failed to populate defaults: {e}")
        raise HTTPException(status_code=500, detail=str(e))
