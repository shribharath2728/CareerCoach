#!/usr/bin/env python3
"""
Setup script for SkillLens RAG Knowledge Base initialization.

This script initializes the RAG knowledge base with default career knowledge
entries and tests the RAG retrieval system.

Usage:
    python setup_rag.py
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path.parent / ".env")

from app.db.database import Base, engine, SessionLocal
from app.models import RAGKnowledge
from app.services import rag_service

def setup_database():
    """Create all tables in the database."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created")


def initialize_rag_defaults():
    """Populate the RAG knowledge base with default entries."""
    logger.info("Initializing RAG knowledge base...")
    
    db = SessionLocal()
    try:
        # Check existing count
        existing_count = db.query(RAGKnowledge).count()
        logger.info(f"Existing RAG knowledge entries: {existing_count}")
        
        if existing_count > 20:
            logger.info("✓ RAG knowledge base already has enough entries")
            return
        
        # Add defaults
        defaults = rag_service._get_default_knowledge_base()
        added = 0
        
        for default in defaults:
            # Check if already exists
            existing = db.query(RAGKnowledge).filter_by(id=default.get("id")).first()
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
        logger.info(f"✓ Added {added} default RAG knowledge entries")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize RAG knowledge: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def test_rag_retrieval():
    """Test the RAG retrieval system."""
    logger.info("\nTesting RAG retrieval system...")
    
    test_queries = [
        "machine learning career path",
        "full stack developer learning",
        "how to get ready for interviews",
        "Python skills for AI engineers",
    ]
    
    db = SessionLocal()
    try:
        # Load knowledge base
        rag_service.load_knowledge_base(db)
        
        for query in test_queries:
            logger.info(f"\n  Query: '{query}'")
            results = rag_service.retrieve_context(query, top_k=3)
            logger.info(f"  → Found {len(results)} results")
            for i, doc in enumerate(results, 1):
                logger.info(f"    {i}. {doc['category']} (score: {doc.get('score', 0):.2f})")
        
        logger.info("\n✓ RAG retrieval test passed")
        
    except Exception as e:
        logger.error(f"✗ RAG retrieval test failed: {e}")
        raise
    finally:
        db.close()


def print_stats():
    """Print RAG knowledge base statistics."""
    logger.info("\nRAG Knowledge Base Statistics:")
    
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        total = db.query(func.count(RAGKnowledge.id)).scalar() or 0
        active = db.query(func.count(RAGKnowledge.id)).filter(
            RAGKnowledge.is_active == True
        ).scalar() or 0
        
        categories = db.query(
            RAGKnowledge.category,
            func.count(RAGKnowledge.id)
        ).filter(RAGKnowledge.is_active == True).group_by(
            RAGKnowledge.category
        ).all()
        
        logger.info(f"  Total entries: {total}")
        logger.info(f"  Active entries: {active}")
        logger.info(f"  Categories:")
        for category, count in categories:
            logger.info(f"    - {category}: {count}")
        
    except Exception as e:
        logger.warning(f"Could not retrieve stats: {e}")
    finally:
        db.close()


def main():
    """Run all setup steps."""
    logger.info("=" * 60)
    logger.info("SkillLens RAG Knowledge Base Setup")
    logger.info("=" * 60)
    
    try:
        # Step 1: Create tables
        setup_database()
        
        # Step 2: Initialize defaults
        initialize_rag_defaults()
        
        # Step 3: Test retrieval
        test_rag_retrieval()
        
        # Step 4: Print stats
        print_stats()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Setup completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Start your backend: python -m uvicorn app.main:app --reload")
        logger.info("2. Your AI will now retrieve context for career-related queries")
        logger.info("3. Add custom knowledge: POST /rag/knowledge with career expertise")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"\n✗ Setup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
