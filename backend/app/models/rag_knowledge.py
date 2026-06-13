"""
RAG Knowledge Base ORM Models
==============================
Stores dynamic knowledge entries and live data cache for RAG retrieval.

Models:
- RAGKnowledge: Dynamic knowledge base entries for RAG retrieval
- LiveDataCache: Cached live data from external sources with TTL expiration
- LiveDataSources: Configuration for live data providers
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, JSON, Float, TIMESTAMP, func
from app.db.database import Base


class RAGKnowledge(Base):
    """
    Dynamic knowledge base entries for RAG retrieval.
    
    Attributes:
        id: Primary key
        category: Type of knowledge (career_path, learning_path, interview, projects, etc.)
        tags: Comma-separated tags for filtering (e.g., "Python,Machine Learning,AI")
        content: Full text content of the knowledge
        source: Where this knowledge came from (user, admin, api, default)
        is_active: Whether this entry is used in RAG retrieval
        created_at: When this entry was created
        updated_at: When this entry was last updated
    """
    __tablename__ = "rag_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(String(500), nullable=True)  # CSV format: "tag1,tag2,tag3"
    content = Column(Text, nullable=False)
    source = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for faster retrieval
    __table_args__ = (
        Index("idx_rag_category_active", "category", "is_active"),
        Index("idx_rag_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<RAGKnowledge(id={self.id}, category={self.category}, source={self.source})>"


class LiveDataCache(Base):
    """
    Cached live data from external sources with TTL expiration.
    
    Stores serialized JSON data retrieved from live sources (Glassdoor, LinkedIn, Indeed, Coursera, etc.)
    with time-to-live (TTL) metadata for automatic expiration. Supports confidence scoring for
    data quality assessment and efficient cleanup via retrieved_at indexing.
    
    This ORM model persists the in-memory cache to the database for durability and querying.
    
    Attributes:
        id: Primary key
        key: Unique cache key identifier (indexed for fast lookups)
        data: Serialized JSON data from the live source
        source: Data source identifier (e.g., "linkedin", "glassdoor", "indeed", "coursera")
        retrieved_at: Timestamp when data was retrieved (indexed for TTL cleanup queries)
        ttl_hours: Time-to-live in hours for this cache entry
        confidence_score: Confidence score of the data (0.0 - 1.0)
        created_at: When this cache entry was created in the database
        updated_at: When this cache entry was last updated
    
    Examples:
        >>> # Create a cached entry for salary data
        >>> entry = LiveDataCache(
        ...     key="salary_data_python_2024",
        ...     data={"avg_salary": 95000, "min": 60000, "max": 150000},
        ...     source="bureau_of_labor",
        ...     retrieved_at=datetime.utcnow(),
        ...     ttl_hours=24,
        ...     confidence_score=0.95
        ... )
        >>> # Query expired entries for cleanup
        >>> from sqlalchemy import and_
        >>> from datetime import datetime, timedelta
        >>> expired_cutoff = datetime.utcnow() - timedelta(hours=24)
        >>> expired_entries = session.query(LiveDataCache).filter(
        ...     LiveDataCache.retrieved_at < expired_cutoff
        ... ).all()
    """
    __tablename__ = "live_data_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    source = Column(String(100), nullable=False, index=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ttl_hours = Column(Integer, nullable=False, default=24)
    confidence_score = Column(Float, nullable=False, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for efficient TTL cleanup queries (source + retrieved_at)
    __table_args__ = (
        Index("idx_live_data_cache_source_retrieved", "source", "retrieved_at"),
        Index("idx_live_data_cache_key", "key"),
    )
    
    def __repr__(self):
        return f"<LiveDataCache(id={self.id}, key={self.key}, source={self.source}, ttl_hours={self.ttl_hours})>"
    
    def is_expired(self) -> bool:
        """
        Check if this cache entry has exceeded its TTL.
        
        Returns:
            bool: True if the entry has expired, False otherwise
        """
        expiration_time = self.retrieved_at + datetime.timedelta(hours=self.ttl_hours)
        return datetime.utcnow() > expiration_time


class LiveDataSources(Base):
    """
    Configuration table for live data provider sources.
    
    Stores configuration metadata for live data providers (Glassdoor, LinkedIn, Indeed, Coursera, etc.)
    including endpoint URLs, API credentials (via environment variable references), rate limiting,
    and enabled/disabled status. This allows dynamic management of data sources without code changes.
    
    Attributes:
        id: Primary key
        name: Source name identifier (e.g., "linkedin", "glassdoor", "indeed", "coursera")
        endpoint: API endpoint URL for this source
        api_key_env: Environment variable name for API credentials (e.g., "LINKEDIN_API_KEY")
        enabled: Whether this source is currently enabled for data retrieval
        rate_limit_per_minute: Rate limit in requests per minute for this source
        created_at: When this source configuration was created
        updated_at: When this source configuration was last updated
    
    Examples:
        >>> # Create a new data source configuration
        >>> source = LiveDataSources(
        ...     name="linkedin_jobs",
        ...     endpoint="https://api.linkedin.com/v2/jobs",
        ...     api_key_env="LINKEDIN_API_KEY",
        ...     enabled=True,
        ...     rate_limit_per_minute=60
        ... )
        >>> # Query all enabled sources
        >>> session.add(source)
        >>> session.commit()
        >>> enabled = session.query(LiveDataSources).filter_by(enabled=True).all()
        >>> for source in enabled:
        ...     print(f"{source.name}: {source.rate_limit_per_minute} req/min")
    """
    __tablename__ = "live_data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    endpoint = Column(String(500), nullable=False)
    api_key_env = Column(String(100), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    rate_limit_per_minute = Column(Integer, nullable=False, default=60)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index for efficient filtering of enabled sources
    __table_args__ = (
        Index("idx_live_data_sources_enabled", "enabled"),
        Index("idx_live_data_sources_name", "name"),
    )
    
    def __repr__(self):
        return f"<LiveDataSources(id={self.id}, name={self.name}, enabled={self.enabled}, rate_limit={self.rate_limit_per_minute})>"
