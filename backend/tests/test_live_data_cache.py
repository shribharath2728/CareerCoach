"""
Unit Tests for LiveDataCache Module

Comprehensive test suite covering:
- Cache operations (store, retrieve, expire)
- TTL expiration logic
- Edge cases (None keys, invalid TTL, concurrent access)
- Data source filtering
- Cache cleanup operations
"""

import pytest
import time
from datetime import datetime, timedelta
from threading import Thread

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.live_data_cache import LiveDataCache


class TestLiveDataCacheBasicOperations:
    """Test basic cache operations: store, retrieve, delete"""

    def test_cache_and_retrieve_valid_data(self):
        """Test storing and retrieving valid cached data"""
        cache = LiveDataCache()
        
        test_data = {"avg_salary": 95000, "min": 60000, "max": 150000}
        cache.cache_live_data(
            key="salary_python_2024",
            data=test_data,
            ttl_hours=24,
            source="bureau_of_labor",
            confidence_score=0.95
        )
        
        result = cache.get_cached("salary_python_2024")
        assert result is not None
        assert result["data"] == test_data
        assert result["source"] == "bureau_of_labor"
        assert result["confidence_score"] == 0.95
        assert result["ttl_seconds"] == 24 * 3600  # 24 hours in seconds

    def test_retrieve_nonexistent_key_returns_none(self):
        """Test retrieving a key that doesn't exist returns None"""
        cache = LiveDataCache()
        result = cache.get_cached("nonexistent_key")
        assert result is None

    def test_cache_multiple_entries(self):
        """Test caching and retrieving multiple entries"""
        cache = LiveDataCache()
        
        cache.cache_live_data("salary", {"avg": 90000}, 24, "indeed", 0.9)
        cache.cache_live_data("skills", {"top": ["Python", "Java"]}, 12, "linkedin", 0.85)
        cache.cache_live_data("jobs", {"count": 500}, 6, "glassdoor", 0.88)
        
        assert cache.get_cached("salary") is not None
        assert cache.get_cached("skills") is not None
        assert cache.get_cached("jobs") is not None

    def test_cache_overwrites_existing_key(self):
        """Test that caching with same key overwrites old data"""
        cache = LiveDataCache()
        
        cache.cache_live_data("data_key", {"version": 1}, 24, "source1", 0.9)
        first_result = cache.get_cached("data_key")
        assert first_result["data"]["version"] == 1
        
        cache.cache_live_data("data_key", {"version": 2}, 24, "source2", 0.95)
        second_result = cache.get_cached("data_key")
        assert second_result["data"]["version"] == 2
        assert second_result["source"] == "source2"


class TestLiveDataCacheTTLExpiration:
    """Test TTL expiration logic and cache cleanup"""

    def test_valid_entry_not_expired(self):
        """Test that recently cached entry is not expired"""
        cache = LiveDataCache()
        cache.cache_live_data("fresh_data", {"status": "valid"}, 24, "source", 0.9)
        
        assert cache.is_expired("fresh_data") is False

    def test_expired_entry_returns_none(self):
        """Test that expired entry returns None on retrieval"""
        cache = LiveDataCache()
        
        # Cache with very small TTL (0.0005 hours = 1.8 seconds)
        cache.cache_live_data("expire_test", {"data": "value"}, 0.0005, "source", 0.9)
        
        # Wait for expiration (500ms to be safe)
        time.sleep(0.5)
        
        result = cache.get_cached("expire_test")
        assert result is None

    def test_is_expired_returns_true_for_expired_entry(self):
        """Test is_expired() correctly identifies expired entries"""
        cache = LiveDataCache()
        
        cache.cache_live_data("old_data", {"value": 1}, 0.001, "source", 0.9)
        time.sleep(0.1)
        
        assert cache.is_expired("old_data") is True

    def test_is_expired_returns_true_for_nonexistent_key(self):
        """Test is_expired() returns True for keys not in cache"""
        cache = LiveDataCache()
        assert cache.is_expired("nonexistent") is True

    def test_clear_expired_removes_stale_entries(self):
        """Test clear_expired() removes only expired entries"""
        cache = LiveDataCache()
        
        # Add entries with different TTLs
        cache.cache_live_data("old", {"val": 1}, 0.0005, "source", 0.9)
        time.sleep(0.5)
        cache.cache_live_data("fresh", {"val": 2}, 24, "source", 0.9)
        
        # Verify both exist before clear
        assert cache.get_cached("old") is None  # Already expired
        assert cache.get_cached("fresh") is not None
        
        # Clear expired
        removed_count = cache.clear_expired()
        assert removed_count == 1
        
        # Fresh entry should still exist
        assert cache.get_cached("fresh") is not None

    def test_clear_expired_returns_count_of_removed_entries(self):
        """Test clear_expired() returns correct count of removed entries"""
        cache = LiveDataCache()
        
        cache.cache_live_data("exp1", {"v": 1}, 0.001, "source", 0.9)
        cache.cache_live_data("exp2", {"v": 2}, 0.001, "source", 0.9)
        cache.cache_live_data("fresh", {"v": 3}, 24, "source", 0.9)
        
        time.sleep(0.1)
        
        removed_count = cache.clear_expired()
        assert removed_count == 2


class TestLiveDataCacheEdgeCases:
    """Test edge cases and error handling"""

    def test_none_key_raises_valueerror(self):
        """Test that None key raises ValueError"""
        cache = LiveDataCache()
        
        with pytest.raises(ValueError):
            cache.cache_live_data(None, {"data": 1}, 24, "source", 0.9)

    def test_empty_string_key_raises_valueerror(self):
        """Test that empty string key raises ValueError"""
        cache = LiveDataCache()
        
        with pytest.raises(ValueError):
            cache.cache_live_data("", {"data": 1}, 24, "source", 0.9)

    def test_zero_ttl_raises_valueerror(self):
        """Test that zero TTL raises ValueError"""
        cache = LiveDataCache()
        
        with pytest.raises(ValueError):
            cache.cache_live_data("key", {"data": 1}, 0, "source", 0.9)

    def test_negative_ttl_raises_valueerror(self):
        """Test that negative TTL raises ValueError"""
        cache = LiveDataCache()
        
        with pytest.raises(ValueError):
            cache.cache_live_data("key", {"data": 1}, -5, "source", 0.9)

    def test_non_dict_data_raises_typeerror(self):
        """Test that non-dict data raises TypeError"""
        cache = LiveDataCache()
        
        with pytest.raises(TypeError):
            cache.cache_live_data("key", "not a dict", 24, "source", 0.9)
        
        with pytest.raises(TypeError):
            cache.cache_live_data("key", [1, 2, 3], 24, "source", 0.9)
        
        with pytest.raises(TypeError):
            cache.cache_live_data("key", 12345, 24, "source", 0.9)

    def test_invalid_confidence_score_below_zero(self):
        """Test that confidence score below 0.0 raises ValueError"""
        cache = LiveDataCache()
        
        with pytest.raises(ValueError):
            cache.cache_live_data("key", {"data": 1}, 24, "source", -0.1)

    def test_invalid_confidence_score_above_one(self):
        """Test that confidence score above 1.0 raises ValueError"""
        cache = LiveDataCache()
        
        with pytest.raises(ValueError):
            cache.cache_live_data("key", {"data": 1}, 24, "source", 1.5)

    def test_valid_boundary_confidence_scores(self):
        """Test that valid boundary confidence scores are accepted"""
        cache = LiveDataCache()
        
        # Boundary values should work
        cache.cache_live_data("key1", {"data": 1}, 24, "source", 0.0)
        cache.cache_live_data("key2", {"data": 2}, 24, "source", 1.0)
        cache.cache_live_data("key3", {"data": 3}, 24, "source", 0.5)
        
        assert cache.get_cached("key1") is not None
        assert cache.get_cached("key2") is not None
        assert cache.get_cached("key3") is not None

    def test_none_key_in_get_cached_returns_none(self):
        """Test that get_cached(None) returns None"""
        cache = LiveDataCache()
        result = cache.get_cached(None)
        assert result is None

    def test_none_key_in_is_expired_returns_true(self):
        """Test that is_expired(None) returns True"""
        cache = LiveDataCache()
        assert cache.is_expired(None) is True


class TestLiveDataCacheSourceFiltering:
    """Test data source filtering and retrieval"""

    def test_get_all_for_source_returns_correct_entries(self):
        """Test get_all_for_source() returns only entries from specified source"""
        cache = LiveDataCache()
        
        cache.cache_live_data("salary", {"avg": 90000}, 24, "linkedin", 0.9)
        cache.cache_live_data("skills", {"top": ["Python"]}, 24, "linkedin", 0.85)
        cache.cache_live_data("jobs", {"count": 500}, 24, "indeed", 0.88)
        
        linkedin_entries = cache.get_all_for_source("linkedin")
        assert len(linkedin_entries) == 2
        
        indeed_entries = cache.get_all_for_source("indeed")
        assert len(indeed_entries) == 1

    def test_get_all_for_source_excludes_expired_entries(self):
        """Test get_all_for_source() does not include expired entries"""
        cache = LiveDataCache()
        
        cache.cache_live_data("old", {"data": 1}, 0.0005, "source_a", 0.9)
        time.sleep(0.5)
        cache.cache_live_data("fresh", {"data": 2}, 24, "source_a", 0.9)
        
        entries = cache.get_all_for_source("source_a")
        assert len(entries) == 1
        assert entries[0]["data"]["data"] == 2

    def test_get_all_for_source_empty_for_nonexistent_source(self):
        """Test get_all_for_source() returns empty list for non-existent source"""
        cache = LiveDataCache()
        
        cache.cache_live_data("data", {"val": 1}, 24, "source_a", 0.9)
        
        entries = cache.get_all_for_source("nonexistent_source")
        assert entries == []

    def test_get_all_for_source_returns_multiple_entries(self):
        """Test get_all_for_source() returns all matching entries"""
        cache = LiveDataCache()
        
        for i in range(5):
            cache.cache_live_data(f"data_{i}", {"val": i}, 24, "target_source", 0.9)
        
        cache.cache_live_data("other", {"val": 999}, 24, "other_source", 0.9)
        
        entries = cache.get_all_for_source("target_source")
        assert len(entries) == 5


class TestLiveDataCacheConcurrency:
    """Test thread-safe operations"""

    def test_concurrent_cache_operations(self):
        """Test that concurrent cache operations are thread-safe"""
        cache = LiveDataCache()
        errors = []

        def cache_worker(worker_id):
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_data_{i}"
                    cache.cache_live_data(
                        key,
                        {"worker": worker_id, "iteration": i},
                        24,
                        f"source_{worker_id}",
                        0.9
                    )
                    
                    # Retrieve immediately
                    result = cache.get_cached(key)
                    if result is None:
                        errors.append(f"Failed to retrieve {key}")
            except Exception as e:
                errors.append(str(e))

        threads = [Thread(target=cache_worker, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Concurrency errors: {errors}"

    def test_concurrent_clear_and_retrieve(self):
        """Test concurrent clear_expired() and get_cached() operations"""
        cache = LiveDataCache()

        def add_data():
            for i in range(20):
                cache.cache_live_data(f"add_{i}", {"val": i}, 24, "source", 0.9)

        def clear_data():
            for _ in range(5):
                cache.clear_expired()
                time.sleep(0.01)

        def retrieve_data():
            for i in range(20):
                cache.get_cached(f"add_{i}")

        threads = [
            Thread(target=add_data),
            Thread(target=clear_data),
            Thread(target=retrieve_data),
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should not crash or raise exceptions


class TestLiveDataCacheStatsAndMetadata:
    """Test cache statistics and metadata tracking"""

    def test_get_cache_stats_reports_correct_counts(self):
        """Test get_cache_stats() reports accurate cache statistics"""
        cache = LiveDataCache()
        
        cache.cache_live_data("data1", {"v": 1}, 24, "source_a", 0.9)
        cache.cache_live_data("data2", {"v": 2}, 24, "source_b", 0.9)
        cache.cache_live_data("data3", {"v": 3}, 24, "source_a", 0.85)
        
        stats = cache.get_cache_stats()
        
        assert stats["total_entries"] == 3
        assert stats["non_expired_entries"] == 3
        assert stats["expired_entries"] == 0
        assert stats["by_source"]["source_a"] == 2
        assert stats["by_source"]["source_b"] == 1

    def test_get_cache_stats_with_expired_entries(self):
        """Test get_cache_stats() correctly counts expired entries"""
        cache = LiveDataCache()
        
        cache.cache_live_data("expired", {"v": 1}, 0.0005, "source_a", 0.9)
        time.sleep(0.5)
        cache.cache_live_data("fresh", {"v": 2}, 24, "source_a", 0.9)
        
        stats = cache.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["non_expired_entries"] == 1
        assert stats["expired_entries"] == 1

    def test_entry_stores_correct_metadata(self):
        """Test that cached entries store all required metadata"""
        cache = LiveDataCache()
        
        now_before = datetime.now()
        cache.cache_live_data("metadata_test", {"test": "data"}, 12, "test_source", 0.75)
        now_after = datetime.now()
        
        result = cache.get_cached("metadata_test")
        
        assert result["key"] == "metadata_test"
        assert result["data"] == {"test": "data"}
        assert result["source"] == "test_source"
        assert result["ttl_hours"] == 12
        assert result["confidence_score"] == 0.75
        assert now_before <= result["retrieved_at"] <= now_after


class TestLiveDataCacheIntegration:
    """Integration tests combining multiple features"""

    def test_full_workflow_cache_retrieve_expire_cleanup(self):
        """Test complete workflow: cache → retrieve → expire → cleanup"""
        cache = LiveDataCache()
        
        # Step 1: Cache data
        cache.cache_live_data("salary_2024", {"avg": 95000}, 0.0005, "bureau", 0.95)
        cache.cache_live_data("salary_2025", {"avg": 98000}, 24, "bureau", 0.92)
        
        # Step 2: Retrieve fresh data
        result_2024 = cache.get_cached("salary_2024")
        assert result_2024 is not None
        
        # Step 3: Wait for expiration
        time.sleep(0.5)
        
        # Step 4: Verify expiration
        assert cache.is_expired("salary_2024") is True
        result_2024_after = cache.get_cached("salary_2024")
        assert result_2024_after is None
        
        # Step 5: Cleanup
        removed = cache.clear_expired()
        assert removed >= 1
        
        # Fresh data should still be available
        assert cache.get_cached("salary_2025") is not None

    def test_real_world_scenario_market_data(self):
        """Test realistic scenario: caching multiple types of market data"""
        cache = LiveDataCache()
        
        # Cache salary data from multiple sources
        cache.cache_live_data("python_salary_linkedin", {"avg": 95000}, 6, "linkedin", 0.9)
        cache.cache_live_data("python_salary_indeed", {"avg": 92000}, 6, "indeed", 0.88)
        
        # Cache skill trends
        cache.cache_live_data("top_skills_2024", {"skills": ["Python", "JS", "Go"]}, 12, "linkedin", 0.92)
        
        # Cache job data
        cache.cache_live_data("python_jobs_available", {"count": 5000}, 3, "indeed", 0.85)
        
        # Verify retrieval
        assert cache.get_cached("python_salary_linkedin") is not None
        assert len(cache.get_all_for_source("linkedin")) == 2
        assert len(cache.get_all_for_source("indeed")) == 2
        
        # Check stats
        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 4
        assert "linkedin" in stats["by_source"]
        assert "indeed" in stats["by_source"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
