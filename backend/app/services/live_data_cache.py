"""
Live Data Cache Module — TTL-based Caching Layer for RAG Integration

This module provides a caching layer for live market data (salary, skills, jobs, courses)
with TTL (Time-To-Live) expiration. It supports concurrent access and maintains data 
freshness for RAG (Retrieval-Augmented Generation) systems.

Features:
- TTL-based expiration logic
- Concurrent access handling
- Data source tracking
- Confidence scoring
- Automatic cleanup of stale entries
"""

import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class LiveDataCache:
    """
    TTL-based in-memory cache for live market data.
    
    This cache stores data with configurable time-to-live (TTL) expiration. Expired
    entries are lazily removed on access or actively cleaned via clear_expired().
    
    Thread-safe for concurrent operations using a lock mechanism.
    
    Attributes:
        _cache (Dict): Internal dictionary storing cached data entries
        _lock (Lock): Thread lock for concurrent access control
    
    Examples:
        >>> cache = LiveDataCache()
        >>> cache.cache_live_data(
        ...     key="salary_data_python_2024",
        ...     data={"avg_salary": 95000, "min": 60000, "max": 150000},
        ...     ttl_hours=24,
        ...     source="bureau_of_labor",
        ...     confidence_score=0.95
        ... )
        >>> result = cache.get_cached("salary_data_python_2024")
        >>> print(result["data"]["avg_salary"])  # Output: 95000
        
        >>> cache.cache_live_data("skills_data", {"top_skills": ["Python", "ML"]}, 6, "linkedin", 0.85)
        >>> cache.is_expired("skills_data")  # Output: False (if within 6 hours)
        >>> cache.clear_expired()  # Remove all stale entries
        >>> all_skills = cache.get_all_for_source("linkedin")  # Get all entries from specific source
    """

    def __init__(self):
        """Initialize the cache with empty storage and a thread lock."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        logger.info("LiveDataCache initialized")

    def cache_live_data(
        self,
        key: str,
        data: Dict[str, Any],
        ttl_hours: int,
        source: str,
        confidence_score: float,
    ) -> None:
        """
        Cache live data with TTL expiration.
        
        Stores data in the cache with metadata including source and confidence score.
        The entry will be considered expired after ttl_hours from the current time.
        
        Args:
            key (str): Unique cache key identifier
            data (Dict[str, Any]): Data to cache (must be a dictionary)
            ttl_hours (int): Time-to-live in hours (must be positive)
            source (str): Data source identifier (e.g., "linkedin", "bureau_of_labor", "coursera")
            confidence_score (float): Confidence score of the data (0.0 - 1.0)
        
        Raises:
            ValueError: If key is None, ttl_hours <= 0, or confidence_score is invalid
            TypeError: If data is not a dictionary
        
        Examples:
            >>> cache = LiveDataCache()
            >>> cache.cache_live_data(
            ...     key="salary_python",
            ...     data={"avg": 95000, "median": 90000},
            ...     ttl_hours=24,
            ...     source="indeed",
            ...     confidence_score=0.92
            ... )
            
            >>> # Invalid examples:
            >>> cache.cache_live_data(None, {}, 24, "source", 0.5)  # Raises ValueError
            >>> cache.cache_live_data("key", {}, 0, "source", 0.5)  # Raises ValueError (ttl_hours must be positive)
            >>> cache.cache_live_data("key", {}, -5, "source", 0.5)  # Raises ValueError (ttl_hours must be positive)
        """
        # Input validation
        if key is None:
            raise ValueError("Cache key cannot be None")
        
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Cache key must be a non-empty string")
        
        if ttl_hours <= 0:
            raise ValueError(f"TTL hours must be positive, got {ttl_hours}")
        
        if not isinstance(data, dict):
            raise TypeError(f"Data must be a dictionary, got {type(data).__name__}")
        
        if not (0.0 <= confidence_score <= 1.0):
            raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {confidence_score}")
        
        with self._lock:
            self._cache[key] = {
                "key": key,
                "data": data,
                "source": source,
                "retrieved_at": datetime.now(),
                "ttl_seconds": ttl_hours * 3600,  # Store as seconds for precise calculation
                "confidence_score": confidence_score,
            }
            logger.info(
                f"Cached data: key='{key}', source='{source}', "
                f"ttl_hours={ttl_hours}, confidence={confidence_score:.2f}"
            )

    def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data if it exists and is not expired.
        
        Returns the cached data entry if the key exists and has not expired.
        Expired entries return None and are not automatically removed (use clear_expired() to clean them).
        
        Args:
            key (str): Cache key to retrieve
        
        Returns:
            Dict[str, Any]: Dictionary with keys {data, source, retrieved_at, ttl_hours, confidence_score}
                           or None if key doesn't exist or is expired
        
        Examples:
            >>> cache = LiveDataCache()
            >>> cache.cache_live_data("skill_trends", {"python": 0.95}, 1, "source", 0.85)
            >>> result = cache.get_cached("skill_trends")
            >>> if result:
            ...     print(result["data"])  # Output: {"python": 0.95}
            ...     print(result["confidence_score"])  # Output: 0.85
            
            >>> # After expiration:
            >>> result = cache.get_cached("expired_key")
            >>> print(result)  # Output: None
        """
        if key is None:
            return None
        
        with self._lock:
            if key not in self._cache:
                logger.debug(f"Cache miss: key='{key}'")
                return None
            
            entry = self._cache[key]
            
            if self._is_entry_expired(entry):
                logger.info(f"Cache expired: key='{key}', source='{entry['source']}'")
                return None
            
            logger.debug(f"Cache hit: key='{key}', source='{entry['source']}'")
            return entry

    def is_expired(self, key: str) -> bool:
        """
        Check if a cached entry is expired.
        
        Determines whether the entry with the given key has exceeded its TTL.
        Returns True if the key doesn't exist, meaning it's no longer available.
        
        Args:
            key (str): Cache key to check
        
        Returns:
            bool: True if expired or doesn't exist, False if valid and not expired
        
        Examples:
            >>> cache = LiveDataCache()
            >>> cache.cache_live_data("job_data", {"jobs": 150}, 2, "glassdoor", 0.88)
            >>> cache.is_expired("job_data")  # Output: False (within 2 hours)
            
            >>> cache.is_expired("nonexistent_key")  # Output: True (not in cache)
        """
        if key is None:
            return True
        
        with self._lock:
            if key not in self._cache:
                return True
            
            entry = self._cache[key]
            return self._is_entry_expired(entry)

    def clear_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Iterates through all cached entries and removes those that have exceeded
        their TTL. Useful for maintenance and memory management.
        
        Returns:
            int: Number of entries removed
        
        Examples:
            >>> cache = LiveDataCache()
            >>> cache.cache_live_data("old_salary", {"avg": 80000}, 1, "source1", 0.8)
            >>> cache.cache_live_data("recent_salary", {"avg": 95000}, 24, "source2", 0.9)
            >>> # After 2 hours, clear_expired() will remove the first entry
            >>> removed_count = cache.clear_expired()
            >>> print(f"Removed {removed_count} expired entries")
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_entry_expired(entry)
            ]
            
            for key in expired_keys:
                entry = self._cache[key]
                logger.info(
                    f"Removing expired entry: key='{key}', source='{entry['source']}'"
                )
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)

    def get_all_for_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Retrieve all non-expired cached entries from a specific source.
        
        Returns a list of all valid (non-expired) cache entries associated with
        a particular data source. Useful for batch operations or source-specific queries.
        
        Args:
            source (str): Source identifier to filter by (e.g., "linkedin", "indeed")
        
        Returns:
            List[Dict[str, Any]]: List of cache entries from the specified source
        
        Examples:
            >>> cache = LiveDataCache()
            >>> cache.cache_live_data("salary_data", {"avg": 90000}, 6, "linkedin", 0.9)
            >>> cache.cache_live_data("skill_data", {"top": ["Python", "JS"]}, 6, "linkedin", 0.85)
            >>> cache.cache_live_data("job_data", {"count": 500}, 6, "indeed", 0.88)
            >>> linkedin_entries = cache.get_all_for_source("linkedin")
            >>> print(len(linkedin_entries))  # Output: 2
            
            >>> indeed_entries = cache.get_all_for_source("indeed")
            >>> print(len(indeed_entries))  # Output: 1
        """
        with self._lock:
            entries = [
                entry for entry in self._cache.values()
                if entry["source"] == source and not self._is_entry_expired(entry)
            ]
            
            logger.debug(
                f"Retrieved {len(entries)} non-expired entries from source='{source}'"
            )
            return entries

    def _is_entry_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Internal method to check if an entry has exceeded its TTL.
        
        Args:
            entry (Dict[str, Any]): Cache entry with retrieved_at and ttl_seconds
        
        Returns:
            bool: True if entry has expired, False otherwise
        """
        retrieved_at = entry["retrieved_at"]
        ttl_seconds = entry["ttl_seconds"]
        expiration_time = retrieved_at + timedelta(seconds=ttl_seconds)
        return datetime.now() > expiration_time

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache state.
        
        Returns a summary of cache usage including total entries, expired entries,
        and breakdown by source.
        
        Returns:
            Dict[str, Any]: Cache statistics with keys:
                - total_entries: Total number of entries
                - non_expired_entries: Count of valid entries
                - expired_entries: Count of expired entries
                - by_source: Dictionary with count per source
        
        Examples:
            >>> cache = LiveDataCache()
            >>> cache.cache_live_data("data1", {"x": 1}, 24, "source_a", 0.9)
            >>> cache.cache_live_data("data2", {"x": 2}, 24, "source_b", 0.8)
            >>> stats = cache.get_cache_stats()
            >>> print(stats["total_entries"])  # Output: 2
            >>> print(stats["by_source"])  # Output: {'source_a': 1, 'source_b': 1}
        """
        with self._lock:
            total = len(self._cache)
            expired_count = sum(
                1 for entry in self._cache.values()
                if self._is_entry_expired(entry)
            )
            non_expired = total - expired_count
            
            by_source = {}
            for entry in self._cache.values():
                if not self._is_entry_expired(entry):
                    source = entry["source"]
                    by_source[source] = by_source.get(source, 0) + 1
            
            return {
                "total_entries": total,
                "non_expired_entries": non_expired,
                "expired_entries": expired_count,
                "by_source": by_source,
            }
