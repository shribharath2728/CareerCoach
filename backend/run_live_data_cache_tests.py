"""
Standalone test runner for LiveDataCache
Runs without external dependencies (no pytest required)
"""

import sys
import time
from datetime import datetime, timedelta
from threading import Thread
from app.services.live_data_cache import LiveDataCache


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name):
        self.passed += 1
        print(f"✓ {test_name}")

    def record_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"✗ {test_name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"Failed tests: {self.failed}")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*60}\n")
        return self.failed == 0


results = TestResults()


def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(f"Expected {expected}, got {actual}. {message}")


def assert_true(condition, message=""):
    if not condition:
        raise AssertionError(f"Expected True, got {condition}. {message}")


def assert_false(condition, message=""):
    if condition:
        raise AssertionError(f"Expected False, got {condition}. {message}")


def assert_none(value, message=""):
    if value is not None:
        raise AssertionError(f"Expected None, got {value}. {message}")


def assert_not_none(value, message=""):
    if value is None:
        raise AssertionError(f"Expected non-None value. {message}")


def assert_raises(exception_type, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        raise AssertionError(f"Expected {exception_type.__name__} to be raised")
    except exception_type:
        pass  # Expected


# Test 1: Cache and retrieve valid data
def test_cache_and_retrieve_valid_data():
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
    assert_not_none(result)
    assert_equal(result["data"], test_data)
    assert_equal(result["source"], "bureau_of_labor")
    assert_equal(result["confidence_score"], 0.95)
    # Note: ttl is stored internally as ttl_seconds
    assert_equal(result["ttl_seconds"], 24 * 3600)


# Test 2: Retrieve nonexistent key returns None
def test_retrieve_nonexistent_key_returns_none():
    cache = LiveDataCache()
    result = cache.get_cached("nonexistent_key")
    assert_none(result)


# Test 3: Cache multiple entries
def test_cache_multiple_entries():
    cache = LiveDataCache()
    
    cache.cache_live_data("salary", {"avg": 90000}, 24, "indeed", 0.9)
    cache.cache_live_data("skills", {"top": ["Python", "Java"]}, 12, "linkedin", 0.85)
    cache.cache_live_data("jobs", {"count": 500}, 6, "glassdoor", 0.88)
    
    assert_not_none(cache.get_cached("salary"))
    assert_not_none(cache.get_cached("skills"))
    assert_not_none(cache.get_cached("jobs"))


# Test 4: Valid entry not expired
def test_valid_entry_not_expired():
    cache = LiveDataCache()
    cache.cache_live_data("fresh_data", {"status": "valid"}, 24, "source", 0.9)
    assert_false(cache.is_expired("fresh_data"))


# Test 5: Expired entry returns None
def test_expired_entry_returns_none():
    cache = LiveDataCache()
    cache.cache_live_data("expire_test", {"data": "value"}, 0.0005, "source", 0.9)
    time.sleep(2.5)  # Sleep for 2.5 seconds (ttl_seconds is 1.8, so this ensures expiry)
    result = cache.get_cached("expire_test")
    assert_none(result)


# Test 6: Clear expired removes stale entries
def test_clear_expired_removes_stale_entries():
    cache = LiveDataCache()
    
    cache.cache_live_data("old", {"val": 1}, 0.0005, "source", 0.9)
    time.sleep(2.5)  # Sleep for 2.5 seconds to ensure expiry
    cache.cache_live_data("fresh", {"val": 2}, 24, "source", 0.9)
    
    removed_count = cache.clear_expired()
    assert_equal(removed_count, 1)
    assert_not_none(cache.get_cached("fresh"))


# Test 7: None key raises ValueError
def test_none_key_raises_valueerror():
    cache = LiveDataCache()
    assert_raises(ValueError, cache.cache_live_data, None, {"data": 1}, 24, "source", 0.9)


# Test 8: Zero TTL raises ValueError
def test_zero_ttl_raises_valueerror():
    cache = LiveDataCache()
    assert_raises(ValueError, cache.cache_live_data, "key", {"data": 1}, 0, "source", 0.9)


# Test 9: Negative TTL raises ValueError
def test_negative_ttl_raises_valueerror():
    cache = LiveDataCache()
    assert_raises(ValueError, cache.cache_live_data, "key", {"data": 1}, -5, "source", 0.9)


# Test 10: Non-dict data raises TypeError
def test_non_dict_data_raises_typeerror():
    cache = LiveDataCache()
    assert_raises(TypeError, cache.cache_live_data, "key", "not a dict", 24, "source", 0.9)
    assert_raises(TypeError, cache.cache_live_data, "key", [1, 2, 3], 24, "source", 0.9)


# Test 11: Invalid confidence score
def test_invalid_confidence_score():
    cache = LiveDataCache()
    assert_raises(ValueError, cache.cache_live_data, "key", {"data": 1}, 24, "source", -0.1)
    assert_raises(ValueError, cache.cache_live_data, "key", {"data": 1}, 24, "source", 1.5)


# Test 12: Valid boundary confidence scores
def test_valid_boundary_confidence_scores():
    cache = LiveDataCache()
    
    cache.cache_live_data("key1", {"data": 1}, 24, "source", 0.0)
    cache.cache_live_data("key2", {"data": 2}, 24, "source", 1.0)
    cache.cache_live_data("key3", {"data": 3}, 24, "source", 0.5)
    
    assert_not_none(cache.get_cached("key1"))
    assert_not_none(cache.get_cached("key2"))
    assert_not_none(cache.get_cached("key3"))


# Test 13: Get all for source returns correct entries
def test_get_all_for_source_returns_correct_entries():
    cache = LiveDataCache()
    
    cache.cache_live_data("salary", {"avg": 90000}, 24, "linkedin", 0.9)
    cache.cache_live_data("skills", {"top": ["Python"]}, 24, "linkedin", 0.85)
    cache.cache_live_data("jobs", {"count": 500}, 24, "indeed", 0.88)
    
    linkedin_entries = cache.get_all_for_source("linkedin")
    assert_equal(len(linkedin_entries), 2)
    
    indeed_entries = cache.get_all_for_source("indeed")
    assert_equal(len(indeed_entries), 1)


# Test 14: Get all for source excludes expired entries
def test_get_all_for_source_excludes_expired():
    cache = LiveDataCache()
    
    cache.cache_live_data("old", {"data": 1}, 0.0005, "source_a", 0.9)
    time.sleep(2.5)  # Sleep for 2.5 seconds to ensure expiry
    cache.cache_live_data("fresh", {"data": 2}, 24, "source_a", 0.9)
    
    entries = cache.get_all_for_source("source_a")
    assert_equal(len(entries), 1)
    assert_equal(entries[0]["data"]["data"], 2)


# Test 15: Cache stats reports correct counts
def test_cache_stats_reports_correct_counts():
    cache = LiveDataCache()
    
    cache.cache_live_data("data1", {"v": 1}, 24, "source_a", 0.9)
    cache.cache_live_data("data2", {"v": 2}, 24, "source_b", 0.9)
    cache.cache_live_data("data3", {"v": 3}, 24, "source_a", 0.85)
    
    stats = cache.get_cache_stats()
    
    assert_equal(stats["total_entries"], 3)
    assert_equal(stats["non_expired_entries"], 3)
    assert_equal(stats["expired_entries"], 0)
    assert_equal(stats["by_source"]["source_a"], 2)
    assert_equal(stats["by_source"]["source_b"], 1)


# Test 16: Entry stores correct metadata
def test_entry_stores_correct_metadata():
    cache = LiveDataCache()
    
    cache.cache_live_data("metadata_test", {"test": "data"}, 12, "test_source", 0.75)
    result = cache.get_cached("metadata_test")
    
    assert_equal(result["key"], "metadata_test")
    assert_equal(result["data"], {"test": "data"})
    assert_equal(result["source"], "test_source")
    assert_equal(result["ttl_seconds"], 12 * 3600)  # 12 hours in seconds
    assert_equal(result["confidence_score"], 0.75)


# Test 17: Concurrent cache operations
def test_concurrent_cache_operations():
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

    if errors:
        raise AssertionError(f"Concurrency errors: {errors}")


# Test 18: Full workflow cache → retrieve → expire → cleanup
def test_full_workflow():
    cache = LiveDataCache()
    
    cache.cache_live_data("salary_2024", {"avg": 95000}, 0.0005, "bureau", 0.95)
    cache.cache_live_data("salary_2025", {"avg": 98000}, 24, "bureau", 0.92)
    
    result_2024 = cache.get_cached("salary_2024")
    assert_not_none(result_2024)
    
    time.sleep(2.5)  # Sleep for 2.5 seconds to ensure expiry
    
    assert_true(cache.is_expired("salary_2024"))
    result_2024_after = cache.get_cached("salary_2024")
    assert_none(result_2024_after)
    
    removed = cache.clear_expired()
    assert_true(removed >= 1)
    
    assert_not_none(cache.get_cached("salary_2025"))


# Test 19: Real-world scenario market data
def test_real_world_scenario_market_data():
    cache = LiveDataCache()
    
    cache.cache_live_data("python_salary_linkedin", {"avg": 95000}, 6, "linkedin", 0.9)
    cache.cache_live_data("python_salary_indeed", {"avg": 92000}, 6, "indeed", 0.88)
    cache.cache_live_data("top_skills_2024", {"skills": ["Python", "JS", "Go"]}, 12, "linkedin", 0.92)
    cache.cache_live_data("python_jobs_available", {"count": 5000}, 3, "indeed", 0.85)
    
    assert_not_none(cache.get_cached("python_salary_linkedin"))
    assert_equal(len(cache.get_all_for_source("linkedin")), 2)
    assert_equal(len(cache.get_all_for_source("indeed")), 2)
    
    stats = cache.get_cache_stats()
    assert_equal(stats["total_entries"], 4)
    assert_true("linkedin" in stats["by_source"])
    assert_true("indeed" in stats["by_source"])


# Test 20: Cache overwrites existing key
def test_cache_overwrites_existing_key():
    cache = LiveDataCache()
    
    cache.cache_live_data("data_key", {"version": 1}, 24, "source1", 0.9)
    first_result = cache.get_cached("data_key")
    assert_equal(first_result["data"]["version"], 1)
    
    cache.cache_live_data("data_key", {"version": 2}, 24, "source2", 0.95)
    second_result = cache.get_cached("data_key")
    assert_equal(second_result["data"]["version"], 2)
    assert_equal(second_result["source"], "source2")


# Run all tests
def run_all_tests():
    tests = [
        ("Cache and retrieve valid data", test_cache_and_retrieve_valid_data),
        ("Retrieve nonexistent key returns None", test_retrieve_nonexistent_key_returns_none),
        ("Cache multiple entries", test_cache_multiple_entries),
        ("Valid entry not expired", test_valid_entry_not_expired),
        ("Expired entry returns None", test_expired_entry_returns_none),
        ("Clear expired removes stale entries", test_clear_expired_removes_stale_entries),
        ("None key raises ValueError", test_none_key_raises_valueerror),
        ("Zero TTL raises ValueError", test_zero_ttl_raises_valueerror),
        ("Negative TTL raises ValueError", test_negative_ttl_raises_valueerror),
        ("Non-dict data raises TypeError", test_non_dict_data_raises_typeerror),
        ("Invalid confidence score", test_invalid_confidence_score),
        ("Valid boundary confidence scores", test_valid_boundary_confidence_scores),
        ("Get all for source returns correct entries", test_get_all_for_source_returns_correct_entries),
        ("Get all for source excludes expired", test_get_all_for_source_excludes_expired),
        ("Cache stats reports correct counts", test_cache_stats_reports_correct_counts),
        ("Entry stores correct metadata", test_entry_stores_correct_metadata),
        ("Concurrent cache operations", test_concurrent_cache_operations),
        ("Full workflow", test_full_workflow),
        ("Real-world scenario market data", test_real_world_scenario_market_data),
        ("Cache overwrites existing key", test_cache_overwrites_existing_key),
    ]

    print("="*60)
    print("LiveDataCache Test Suite")
    print("="*60)
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.record_pass(test_name)
        except Exception as e:
            results.record_fail(test_name, str(e))

    success = results.summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
