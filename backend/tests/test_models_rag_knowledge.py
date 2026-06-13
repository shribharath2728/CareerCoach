"""
Unit Tests for RAG Knowledge ORM Models and Migrations

Comprehensive test suite covering:
- LiveDataCache ORM model operations
- LiveDataSources ORM model operations
- Database schema creation and migrations
- Data persistence and retrieval
- TTL expiration logic at database level
- Backward compatibility with existing RAG tables
- Index creation and query performance
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import Base
from app.models.rag_knowledge import RAGKnowledge, LiveDataCache, LiveDataSources
from app.db.ensure_schema import ensure_schema


# Use in-memory SQLite for testing
@pytest.fixture
def test_engine():
    """Create a test database engine using in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


class TestLiveDataCacheModel:
    """Test LiveDataCache ORM model"""

    def test_live_data_cache_model_creation(self, test_session):
        """Test creating a LiveDataCache entry in the database"""
        entry = LiveDataCache(
            key="salary_python_2024",
            data={"avg_salary": 95000, "min": 60000, "max": 150000},
            source="bureau_of_labor",
            ttl_hours=24,
            confidence_score=0.95
        )
        
        test_session.add(entry)
        test_session.commit()
        
        # Verify the entry was created
        assert entry.id is not None
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_live_data_cache_unique_key_constraint(self, test_session):
        """Test that duplicate keys violate unique constraint"""
        entry1 = LiveDataCache(
            key="unique_key",
            data={"version": 1},
            source="source1",
            ttl_hours=24,
            confidence_score=0.9
        )
        entry2 = LiveDataCache(
            key="unique_key",
            data={"version": 2},
            source="source2",
            ttl_hours=24,
            confidence_score=0.85
        )
        
        test_session.add(entry1)
        test_session.commit()
        
        test_session.add(entry2)
        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_live_data_cache_retrieve_by_key(self, test_session):
        """Test retrieving LiveDataCache entry by key"""
        data = {"avg": 90000, "count": 100}
        entry = LiveDataCache(
            key="test_cache_key",
            data=data,
            source="indeed",
            ttl_hours=12,
            confidence_score=0.88
        )
        
        test_session.add(entry)
        test_session.commit()
        
        # Retrieve by key
        retrieved = test_session.query(LiveDataCache).filter_by(key="test_cache_key").first()
        assert retrieved is not None
        assert retrieved.data == data
        assert retrieved.source == "indeed"
        assert retrieved.ttl_hours == 12
        assert retrieved.confidence_score == 0.88

    def test_live_data_cache_query_by_source(self, test_session):
        """Test querying LiveDataCache entries by source"""
        test_session.add(LiveDataCache(key="k1", data={"v": 1}, source="linkedin", ttl_hours=24, confidence_score=0.9))
        test_session.add(LiveDataCache(key="k2", data={"v": 2}, source="linkedin", ttl_hours=24, confidence_score=0.85))
        test_session.add(LiveDataCache(key="k3", data={"v": 3}, source="indeed", ttl_hours=24, confidence_score=0.88))
        test_session.commit()
        
        linkedin_entries = test_session.query(LiveDataCache).filter_by(source="linkedin").all()
        assert len(linkedin_entries) == 2
        
        indeed_entries = test_session.query(LiveDataCache).filter_by(source="indeed").all()
        assert len(indeed_entries) == 1

    def test_live_data_cache_query_expired_entries(self, test_session):
        """Test querying for expired cache entries"""
        now = datetime.utcnow()
        
        # Create a fresh entry
        fresh_entry = LiveDataCache(
            key="fresh",
            data={"status": "valid"},
            source="source",
            ttl_hours=24,
            confidence_score=0.9,
            retrieved_at=now
        )
        
        # Create an expired entry (retrieved 25 hours ago with 24-hour TTL)
        expired_entry = LiveDataCache(
            key="expired",
            data={"status": "stale"},
            source="source",
            ttl_hours=24,
            confidence_score=0.8,
            retrieved_at=now - timedelta(hours=25)
        )
        
        test_session.add(fresh_entry)
        test_session.add(expired_entry)
        test_session.commit()
        
        # Query for entries that should be expired
        expiration_threshold = now - timedelta(hours=24)
        expired_entries = test_session.query(LiveDataCache).filter(
            LiveDataCache.retrieved_at < expiration_threshold
        ).all()
        
        assert len(expired_entries) == 1
        assert expired_entries[0].key == "expired"

    def test_live_data_cache_update(self, test_session):
        """Test updating a LiveDataCache entry"""
        entry = LiveDataCache(
            key="update_test",
            data={"version": 1},
            source="source1",
            ttl_hours=12,
            confidence_score=0.8
        )
        
        test_session.add(entry)
        test_session.commit()
        
        # Update the entry
        entry.data = {"version": 2}
        entry.ttl_hours = 24
        entry.confidence_score = 0.95
        test_session.commit()
        
        # Verify the update
        retrieved = test_session.query(LiveDataCache).filter_by(key="update_test").first()
        assert retrieved.data == {"version": 2}
        assert retrieved.ttl_hours == 24
        assert retrieved.confidence_score == 0.95

    def test_live_data_cache_is_expired_method(self, test_session):
        """Test the is_expired() method on LiveDataCache model"""
        now = datetime.utcnow()
        
        # Fresh entry
        fresh = LiveDataCache(
            key="fresh",
            data={"test": "data"},
            source="source",
            ttl_hours=24,
            confidence_score=0.9,
            retrieved_at=now
        )
        
        # Expired entry
        expired = LiveDataCache(
            key="expired",
            data={"test": "data"},
            source="source",
            ttl_hours=1,
            confidence_score=0.9,
            retrieved_at=now - timedelta(hours=2)
        )
        
        assert fresh.is_expired() is False
        assert expired.is_expired() is True

    def test_live_data_cache_default_values(self, test_session):
        """Test that default values are properly set"""
        entry = LiveDataCache(
            key="defaults_test",
            data={"test": "data"},
            source="test_source"
        )
        
        test_session.add(entry)
        test_session.commit()
        
        retrieved = test_session.query(LiveDataCache).filter_by(key="defaults_test").first()
        assert retrieved.ttl_hours == 24  # Default TTL
        assert retrieved.confidence_score == 0.5  # Default confidence
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None


class TestLiveDataSourcesModel:
    """Test LiveDataSources ORM model"""

    def test_live_data_sources_model_creation(self, test_session):
        """Test creating a LiveDataSources entry in the database"""
        source = LiveDataSources(
            name="linkedin_jobs",
            endpoint="https://api.linkedin.com/v2/jobs",
            api_key_env="LINKEDIN_API_KEY",
            enabled=True,
            rate_limit_per_minute=60
        )
        
        test_session.add(source)
        test_session.commit()
        
        assert source.id is not None
        assert source.created_at is not None
        assert source.updated_at is not None

    def test_live_data_sources_unique_name_constraint(self, test_session):
        """Test that duplicate names violate unique constraint"""
        source1 = LiveDataSources(
            name="linkedin",
            endpoint="https://api.linkedin.com/v2",
            enabled=True,
            rate_limit_per_minute=60
        )
        source2 = LiveDataSources(
            name="linkedin",
            endpoint="https://api.linkedin.com/v3",
            enabled=True,
            rate_limit_per_minute=30
        )
        
        test_session.add(source1)
        test_session.commit()
        
        test_session.add(source2)
        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_live_data_sources_query_by_name(self, test_session):
        """Test retrieving LiveDataSources entry by name"""
        source = LiveDataSources(
            name="indeed",
            endpoint="https://api.indeed.com/jobs",
            api_key_env="INDEED_API_KEY",
            enabled=True,
            rate_limit_per_minute=120
        )
        
        test_session.add(source)
        test_session.commit()
        
        retrieved = test_session.query(LiveDataSources).filter_by(name="indeed").first()
        assert retrieved is not None
        assert retrieved.endpoint == "https://api.indeed.com/jobs"
        assert retrieved.rate_limit_per_minute == 120

    def test_live_data_sources_query_enabled(self, test_session):
        """Test querying enabled/disabled sources"""
        test_session.add(LiveDataSources(name="source1", endpoint="http://s1", enabled=True, rate_limit_per_minute=60))
        test_session.add(LiveDataSources(name="source2", endpoint="http://s2", enabled=False, rate_limit_per_minute=30))
        test_session.add(LiveDataSources(name="source3", endpoint="http://s3", enabled=True, rate_limit_per_minute=90))
        test_session.commit()
        
        enabled_sources = test_session.query(LiveDataSources).filter_by(enabled=True).all()
        assert len(enabled_sources) == 2
        
        disabled_sources = test_session.query(LiveDataSources).filter_by(enabled=False).all()
        assert len(disabled_sources) == 1

    def test_live_data_sources_update(self, test_session):
        """Test updating a LiveDataSources entry"""
        source = LiveDataSources(
            name="glassdoor",
            endpoint="https://api.glassdoor.com/v1",
            enabled=True,
            rate_limit_per_minute=60
        )
        
        test_session.add(source)
        test_session.commit()
        
        # Update the source
        source.enabled = False
        source.rate_limit_per_minute = 30
        test_session.commit()
        
        # Verify the update
        retrieved = test_session.query(LiveDataSources).filter_by(name="glassdoor").first()
        assert retrieved.enabled is False
        assert retrieved.rate_limit_per_minute == 30

    def test_live_data_sources_default_values(self, test_session):
        """Test that default values are properly set"""
        source = LiveDataSources(
            name="coursera",
            endpoint="https://api.coursera.com"
        )
        
        test_session.add(source)
        test_session.commit()
        
        retrieved = test_session.query(LiveDataSources).filter_by(name="coursera").first()
        assert retrieved.enabled is True  # Default enabled
        assert retrieved.rate_limit_per_minute == 60  # Default rate limit
        assert retrieved.api_key_env is None  # Optional field

    def test_live_data_sources_multiple_entries(self, test_session):
        """Test creating and querying multiple LiveDataSources entries"""
        sources_data = [
            ("linkedin", "https://api.linkedin.com", "LINKEDIN_API_KEY", True, 60),
            ("indeed", "https://api.indeed.com", "INDEED_API_KEY", True, 120),
            ("glassdoor", "https://api.glassdoor.com", "GLASSDOOR_API_KEY", True, 90),
            ("coursera", "https://api.coursera.com", "COURSERA_API_KEY", False, 50),
        ]
        
        for name, endpoint, api_key_env, enabled, rate_limit in sources_data:
            source = LiveDataSources(
                name=name,
                endpoint=endpoint,
                api_key_env=api_key_env,
                enabled=enabled,
                rate_limit_per_minute=rate_limit
            )
            test_session.add(source)
        
        test_session.commit()
        
        # Verify all entries
        all_sources = test_session.query(LiveDataSources).all()
        assert len(all_sources) == 4
        
        # Verify specific queries
        linkedin = test_session.query(LiveDataSources).filter_by(name="linkedin").first()
        assert linkedin.endpoint == "https://api.linkedin.com"


class TestRAGKnowledgeModel:
    """Test RAGKnowledge ORM model (backward compatibility)"""

    def test_rag_knowledge_model_still_works(self, test_session):
        """Test that RAGKnowledge model continues to work (backward compatibility)"""
        entry = RAGKnowledge(
            category="career_path",
            tags="Python,Machine Learning,AI",
            content="Python is a key skill for ML engineers",
            source="default",
            is_active=True
        )
        
        test_session.add(entry)
        test_session.commit()
        
        assert entry.id is not None
        assert entry.created_at is not None

    def test_rag_knowledge_query(self, test_session):
        """Test querying RAGKnowledge entries"""
        test_session.add(RAGKnowledge(
            category="learning_path",
            tags="Python",
            content="Learn Python basics",
            source="user",
            is_active=True
        ))
        test_session.add(RAGKnowledge(
            category="interview",
            tags="Python,Data Structures",
            content="Interview tips",
            source="default",
            is_active=False
        ))
        test_session.commit()
        
        active_entries = test_session.query(RAGKnowledge).filter_by(is_active=True).all()
        assert len(active_entries) == 1
        
        all_entries = test_session.query(RAGKnowledge).all()
        assert len(all_entries) == 2


class TestDatabaseIndexes:
    """Test that indexes are properly created"""

    def test_live_data_cache_indexes_exist(self, test_engine):
        """Test that LiveDataCache indexes are created"""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("live_data_cache")
        
        index_names = {idx["name"] for idx in indexes}
        
        # SQLite uses slightly different index naming, but we should have indexes on key columns
        assert any("key" in name.lower() or "KEY" in str(indexes) for name in index_names)

    def test_live_data_sources_indexes_exist(self, test_engine):
        """Test that LiveDataSources indexes are created"""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("live_data_sources")
        
        # Verify indexes exist
        assert len(indexes) > 0


class TestDataPersistence:
    """Test data persistence and retrieval"""

    def test_live_data_cache_persistence(self, test_session):
        """Test that LiveDataCache data persists correctly"""
        original_data = {
            "salaries": {
                "min": 60000,
                "avg": 95000,
                "max": 150000
            },
            "source_info": {
                "date": "2024-01-15",
                "confidence": 0.95
            }
        }
        
        entry = LiveDataCache(
            key="complex_data",
            data=original_data,
            source="test",
            ttl_hours=24,
            confidence_score=0.95
        )
        
        test_session.add(entry)
        test_session.commit()
        
        # Retrieve and verify
        retrieved = test_session.query(LiveDataCache).filter_by(key="complex_data").first()
        assert retrieved.data == original_data
        assert retrieved.data["salaries"]["avg"] == 95000

    def test_multiple_models_coexist(self, test_session):
        """Test that RAGKnowledge, LiveDataCache, and LiveDataSources can coexist"""
        # Add RAGKnowledge
        rag = RAGKnowledge(
            category="learning",
            tags="Python",
            content="Learn Python",
            source="default",
            is_active=True
        )
        
        # Add LiveDataCache
        cache = LiveDataCache(
            key="salary_data",
            data={"avg": 90000},
            source="bureau",
            ttl_hours=24,
            confidence_score=0.9
        )
        
        # Add LiveDataSources
        source = LiveDataSources(
            name="indeed",
            endpoint="https://api.indeed.com",
            enabled=True,
            rate_limit_per_minute=60
        )
        
        test_session.add(rag)
        test_session.add(cache)
        test_session.add(source)
        test_session.commit()
        
        # Verify all exist
        assert test_session.query(RAGKnowledge).count() == 1
        assert test_session.query(LiveDataCache).count() == 1
        assert test_session.query(LiveDataSources).count() == 1


class TestEnsureSchemaFunction:
    """Test the ensure_schema migration function"""

    @pytest.mark.skip(reason="Requires PostgreSQL; SQLite doesn't support all features")
    def test_ensure_schema_creates_tables(self):
        """Test that ensure_schema creates the required tables"""
        # This test would require a real PostgreSQL instance
        # Skipped in unit tests, would be part of integration tests
        pass


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_live_data_cache_with_empty_json_data(self, test_session):
        """Test storing empty JSON data in LiveDataCache"""
        entry = LiveDataCache(
            key="empty_data",
            data={},
            source="test",
            ttl_hours=24,
            confidence_score=0.9
        )
        
        test_session.add(entry)
        test_session.commit()
        
        retrieved = test_session.query(LiveDataCache).filter_by(key="empty_data").first()
        assert retrieved.data == {}

    def test_live_data_cache_with_nested_json(self, test_session):
        """Test storing deeply nested JSON data"""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "values": [1, 2, 3],
                        "info": "deeply nested"
                    }
                }
            }
        }
        
        entry = LiveDataCache(
            key="nested_json",
            data=nested_data,
            source="test",
            ttl_hours=24,
            confidence_score=0.9
        )
        
        test_session.add(entry)
        test_session.commit()
        
        retrieved = test_session.query(LiveDataCache).filter_by(key="nested_json").first()
        assert retrieved.data == nested_data
        assert retrieved.data["level1"]["level2"]["level3"]["info"] == "deeply nested"

    def test_live_data_sources_with_optional_fields(self, test_session):
        """Test LiveDataSources with optional api_key_env field"""
        source_with_key = LiveDataSources(
            name="with_key",
            endpoint="https://api.example.com",
            api_key_env="API_KEY",
            enabled=True,
            rate_limit_per_minute=60
        )
        
        source_without_key = LiveDataSources(
            name="without_key",
            endpoint="https://api.example.com",
            api_key_env=None,
            enabled=True,
            rate_limit_per_minute=60
        )
        
        test_session.add(source_with_key)
        test_session.add(source_without_key)
        test_session.commit()
        
        retrieved_with = test_session.query(LiveDataSources).filter_by(name="with_key").first()
        retrieved_without = test_session.query(LiveDataSources).filter_by(name="without_key").first()
        
        assert retrieved_with.api_key_env == "API_KEY"
        assert retrieved_without.api_key_env is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
