"""
RAG Knowledge Schemas
====================
Pydantic models for RAG knowledge endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RAGKnowledgeCreate(BaseModel):
    """Request to create a new knowledge entry."""
    category: str = Field(..., description="Category (e.g., 'career_path', 'learning_path')")
    content: str = Field(..., description="Full text content of the knowledge")
    tags: List[str] = Field(default_factory=list, description="Tags for retrieval (e.g., ['Python', 'AI'])")
    source: str = Field(default="user", description="Source of knowledge")


class RAGKnowledgeUpdate(BaseModel):
    """Request to update a knowledge entry."""
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RAGKnowledgeResponse(BaseModel):
    """Response model for a knowledge entry."""
    id: int
    category: str
    tags: List[str]
    content: str
    source: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_row(cls, row):
        """Convert SQLAlchemy row to response model."""
        return cls(
            id=row.id,
            category=row.category,
            tags=row.tags.split(",") if row.tags else [],
            content=row.content,
            source=row.source,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at
        )


class RAGRetrievalRequest(BaseModel):
    """Request for RAG context retrieval."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    max_chars: int = Field(default=4000, ge=500, le=10000, description="Max output characters")


class RAGRetrievalResponse(BaseModel):
    """Response with retrieved context."""
    query: str
    results_count: int
    context: str
    retrieved_documents: List[dict]


class RAGStats(BaseModel):
    """Statistics about the RAG knowledge base."""
    total_entries: int
    active_entries: int
    categories: dict  # {category: count}
    cache_status: str
    cache_timestamp: Optional[str] = None
