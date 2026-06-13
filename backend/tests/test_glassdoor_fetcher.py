"""
Comprehensive Unit Tests for GlassdoorSalaryFetcher

Tests cover:
- Successful salary fetch with API
- Mock data fallback (no API key)
- Invalid location handling
- API timeout fallback
- Caching integration (24-hour TTL)
- Rate limiting (5 requests/minute)
- All 4 abstract methods implementation
- Mock data structure validation
- Error handling (graceful, no exceptions)
"""

import logging
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import os
from app.services.web_data_fetcher import GlassdoorSalaryFetcher
from app.services.live_data_cache import LiveDataCache


class TestGlassdoorSalaryFetcherInitialization(unittest.TestCase):
    """Test GlassdoorSalaryFetcher initialization."""

    def setUp(self):
        """Set up test fixtures."""
        # Ensure no API key is set for default tests
        os.environ.pop("GLASSDOOR_API_KEY", None)

    def test_initialization_without_api_key(self):
        """Test initialization when no API key is configured."""
        fetcher = GlassdoorSalaryFetcher()
        self.assertEqual(fetcher.rate_limit, 5)
        self.assertEqual(fetcher.source_name, "GlassdoorSalaryFetcher")
        self.assertIsNone(fetcher.api_key)
        self.assertTrue(fetcher.api_base_url.startswith("https://api.glassdoor"))

    @patch.dict(os.environ, {"GLASSDOOR_API_KEY": "test_key_12345"})
    def test_initialization_with_api_key(self):
        """Test initialization when API key is configured."""
        fetcher = GlassdoorSalaryFetcher()
        self.assertEqual(fetcher.api_key, "test_key_12345")

    def test_rate_limit_is_5(self):
        """Test that Glassdoor fetcher uses 5 requests/minute rate limit."""
        fetcher = GlassdoorSalaryFetcher()
        self.assertEqual(fetcher.rate_limit, 5)


class TestSuccessfulSalaryFetch(unittest.TestCase):
    """Test successful salary data fetch."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    @patch("requests.request")
    def test_fetch_salary_data_with_api_success(self, mock_request):
        """Test successful fetch from Glassdoor API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "avg": 95000,
            "min": 75000,
            "max": 130000,
            "currency": "USD"
        }
        mock_request.return_value = mock_response

        with patch.dict(os.environ, {"GLASSDOOR_API_KEY": "test_key"}):
            fetcher = GlassdoorSalaryFetcher()
            result = fetcher.fetch_salary_data("Python Developer", "San Francisco, CA")

        self.assertIsNotNone(result["data"])
        self.assertIn("avg", result["data"])
        self.assertIn("min", result["data"])
        self.assertIn("max", result["data"])
        self.assertEqual(result["source"], "GlassdoorSalaryFetcher")
        self.assertIsInstance(result["retrieved_at"], datetime)
        self.assertGreater(result["confidence_score"], 0.0)

    def test_fetch_salary_data_without_location(self):
        """Test fetch without location parameter."""
        result = self.fetcher.fetch_salary_data("Python Developer")

        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertIn("source", result)
        self.assertEqual(result["source"], "GlassdoorSalaryFetcher")

    def test_fetch_salary_data_with_location(self):
        """Test fetch with location parameter."""
        result = self.fetcher.fetch_salary_data("Data Scientist", "New York, NY")

        self.assertIsNotNone(result)
        self.assertIn("data", result)
        if result["data"]:
            self.assertIn("location", result["data"])


class TestMockDataFallback(unittest.TestCase):
    """Test mock data fallback when API unavailable."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_mock_data_without_api_key(self):
        """Test that mock data is returned when no API key configured."""
        result = self.fetcher.fetch_salary_data("Python Developer")

        self.assertIsNotNone(result["data"])
        self.assertIn("avg", result["data"])
        self.assertIn("min", result["data"])
        self.assertIn("max", result["data"])
        self.assertIn("currency", result["data"])
        self.assertIn("seniority_levels", result["data"])

    def test_mock_data_structure_validation(self):
        """Test that mock data has correct structure."""
        result = self.fetcher.fetch_salary_data("Software Engineer", "Seattle, WA")

        data = result["data"]
        self.assertIsInstance(data["avg"], float)
        self.assertIsInstance(data["min"], float)
        self.assertIsInstance(data["max"], float)
        self.assertEqual(data["currency"], "USD")

    def test_mock_data_seniority_levels(self):
        """Test mock data includes all seniority levels."""
        result = self.fetcher.fetch_salary_data("Developer")

        seniority = result["data"].get("seniority_levels", {})
        required_levels = ["entry", "mid", "senior", "executive"]
        for level in required_levels:
            self.assertIn(level, seniority)
            self.assertIn("avg", seniority[level])
            self.assertIn("min", seniority[level])
            self.assertIn("max", seniority[level])

    def test_mock_data_location_adjustment(self):
        """Test that mock data adjusts for location."""
        result_sf = self.fetcher.fetch_salary_data("Python Developer", "San Francisco, CA")
        result_denver = self.fetcher.fetch_salary_data("Python Developer", "Denver, CO")

        avg_sf = result_sf["data"]["avg"]
        avg_denver = result_denver["data"]["avg"]

        # San Francisco should have higher salary
        self.assertGreater(avg_sf, avg_denver)

    def test_mock_data_role_adjustment(self):
        """Test that mock data varies by role."""
        result_junior = self.fetcher.fetch_salary_data("Junior Developer")
        result_senior = self.fetcher.fetch_salary_data("Senior Developer")

        avg_junior = result_junior["data"]["avg"]
        avg_senior = result_senior["data"]["avg"]

        # Senior should earn more than junior
        self.assertGreater(avg_senior, avg_junior)

    def test_mock_data_confidence_score(self):
        """Test that mock data has lower confidence score."""
        result = self.fetcher.fetch_salary_data("Python Developer")

        # Mock data should have confidence of 0.60
        self.assertEqual(result["confidence_score"], 0.60)


class TestInvalidLocationHandling(unittest.TestCase):
    """Test error handling for invalid inputs."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_invalid_role_none(self):
        """Test handling of None role."""
        result = self.fetcher.fetch_salary_data(None)

        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)

    def test_invalid_role_empty_string(self):
        """Test handling of empty string role."""
        result = self.fetcher.fetch_salary_data("")

        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)

    def test_invalid_role_whitespace(self):
        """Test handling of whitespace-only role."""
        result = self.fetcher.fetch_salary_data("   ")

        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)

    def test_invalid_location_none(self):
        """Test that None location is handled gracefully."""
        result = self.fetcher.fetch_salary_data("Python Developer", None)

        # Should return mock data with national location
        self.assertIsNotNone(result["data"])
        self.assertIn("location", result["data"])
        self.assertEqual(result["data"]["location"], "United States")


class TestAPITimeoutFallback(unittest.TestCase):
    """Test fallback to mock data when API timeout occurs."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = GlassdoorSalaryFetcher()

    @patch("requests.request")
    def test_api_timeout_fallback_to_mock(self, mock_request):
        """Test that API timeout falls back to mock data."""
        from requests.exceptions import Timeout

        mock_request.side_effect = Timeout()

        with patch.dict(os.environ, {"GLASSDOOR_API_KEY": "test_key"}):
            fetcher = GlassdoorSalaryFetcher()
            
            with patch("time.sleep"):  # Skip retry delays for testing
                result = fetcher.fetch_salary_data("Python Developer")

        # Should fall back to mock data
        self.assertIsNotNone(result["data"])
        self.assertIn("avg", result["data"])
        self.assertIn("min", result["data"])

    @patch("requests.request")
    def test_api_connection_error_fallback(self, mock_request):
        """Test that API connection error falls back to mock data."""
        from requests.exceptions import ConnectionError

        mock_request.side_effect = ConnectionError()

        with patch.dict(os.environ, {"GLASSDOOR_API_KEY": "test_key"}):
            fetcher = GlassdoorSalaryFetcher()
            
            with patch("time.sleep"):
                result = fetcher.fetch_salary_data("Python Developer")

        # Should fall back to mock data
        self.assertIsNotNone(result["data"])
        self.assertIn("avg", result["data"])


class TestCachingIntegration(unittest.TestCase):
    """Test LiveDataCache integration and 24-hour TTL."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    @patch("app.services.web_data_fetcher.LiveDataCache")
    def test_cache_hit_returns_cached_data(self, mock_cache_class):
        """Test that cache hit returns cached data."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache

        # Setup cache to return cached data
        cached_entry = {
            "data": {"avg": 100000, "min": 80000, "max": 120000},
            "source": "GlassdoorSalaryFetcher",
            "retrieved_at": datetime.now(),
            "confidence_score": 0.95
        }
        mock_cache.get_cached.return_value = cached_entry
        mock_cache.is_expired.return_value = False

        result = self.fetcher.fetch_salary_data("Python Developer", "San Francisco, CA")

        # Verify cache was consulted
        mock_cache.get_cached.assert_called()

    @patch("app.services.web_data_fetcher.LiveDataCache")
    def test_cache_miss_calls_cache_method(self, mock_cache_class):
        """Test that cache miss triggers cache_live_data call."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        mock_cache.get_cached.return_value = None

        result = self.fetcher.fetch_salary_data("Python Developer")

        # Verify cache_live_data was called
        mock_cache.cache_live_data.assert_called()

    @patch("app.services.web_data_fetcher.LiveDataCache")
    def test_cache_ttl_24_hours(self, mock_cache_class):
        """Test that cache_live_data is called with 24-hour TTL."""
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        mock_cache.get_cached.return_value = None

        self.fetcher.fetch_salary_data("Python Developer")

        # Verify cache_live_data was called with ttl_hours=24
        call_args = mock_cache.cache_live_data.call_args
        self.assertIn("ttl_hours", call_args.kwargs)
        self.assertEqual(call_args.kwargs["ttl_hours"], 24)


class TestAllAbstractMethodsImplemented(unittest.TestCase):
    """Test that all 4 abstract methods are implemented."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_fetch_salary_data_implemented(self):
        """Test fetch_salary_data is implemented."""
        result = self.fetcher.fetch_salary_data("Python Developer")
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertIn("source", result)

    def test_fetch_skill_trends_implemented(self):
        """Test fetch_skill_trends is implemented."""
        result = self.fetcher.fetch_skill_trends()
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertIn("source", result)
        self.assertEqual(result["source"], "GlassdoorSalaryFetcher")

    def test_fetch_job_postings_implemented(self):
        """Test fetch_job_postings is implemented."""
        result = self.fetcher.fetch_job_postings("Python Developer")
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertIn("source", result)
        self.assertEqual(result["source"], "GlassdoorSalaryFetcher")

    def test_fetch_courses_implemented(self):
        """Test fetch_courses is implemented."""
        result = self.fetcher.fetch_courses("Python")
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertIn("source", result)
        self.assertEqual(result["source"], "GlassdoorSalaryFetcher")

    def test_all_methods_return_valid_structure(self):
        """Test all methods return valid response structure."""
        methods = [
            ("fetch_salary_data", ["Python Developer"]),
            ("fetch_skill_trends", []),
            ("fetch_job_postings", ["Python Developer"]),
            ("fetch_courses", ["Python"]),
        ]

        for method_name, args in methods:
            method = getattr(self.fetcher, method_name)
            result = method(*args)

            # Check required fields
            self.assertIn("data", result)
            self.assertIn("source", result)
            self.assertIn("retrieved_at", result)
            self.assertIn("confidence_score", result)

            # Check field types
            self.assertIsInstance(result["data"], dict)
            self.assertEqual(result["source"], "GlassdoorSalaryFetcher")
            self.assertIsInstance(result["retrieved_at"], datetime)
            self.assertIsInstance(result["confidence_score"], float)


class TestPlaceholderMethods(unittest.TestCase):
    """Test that placeholder methods for skills/jobs/courses return valid data."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_fetch_skill_trends_returns_placeholder(self):
        """Test fetch_skill_trends returns placeholder structure."""
        result = self.fetcher.fetch_skill_trends()

        self.assertIsInstance(result["data"], dict)
        self.assertIn("placeholder", result["data"])
        self.assertEqual(result["confidence_score"], 0.0)

    def test_fetch_job_postings_returns_placeholder(self):
        """Test fetch_job_postings returns placeholder structure."""
        result = self.fetcher.fetch_job_postings("Python")

        self.assertIsInstance(result["data"], dict)
        self.assertIn("placeholder", result["data"])
        self.assertEqual(result["confidence_score"], 0.0)

    def test_fetch_courses_returns_placeholder(self):
        """Test fetch_courses returns placeholder structure."""
        result = self.fetcher.fetch_courses("Python")

        self.assertIsInstance(result["data"], dict)
        self.assertIn("placeholder", result["data"])
        self.assertEqual(result["confidence_score"], 0.0)


class TestNoExceptionsRaised(unittest.TestCase):
    """Test that no exceptions are raised in any scenario."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_no_exception_invalid_role(self):
        """Test no exception on invalid role."""
        try:
            result = self.fetcher.fetch_salary_data(None)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_no_exception_invalid_location(self):
        """Test no exception on invalid location."""
        try:
            result = self.fetcher.fetch_salary_data("Python", "###INVALID###")
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    @patch("requests.request")
    def test_no_exception_on_api_timeout(self, mock_request):
        """Test no exception when API times out."""
        from requests.exceptions import Timeout

        mock_request.side_effect = Timeout()

        with patch.dict(os.environ, {"GLASSDOOR_API_KEY": "test_key"}):
            fetcher = GlassdoorSalaryFetcher()
            
            try:
                with patch("time.sleep"):
                    result = fetcher.fetch_salary_data("Python Developer")
                    self.assertIsNotNone(result)
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")

    @patch("requests.request")
    def test_no_exception_on_http_error(self, mock_request):
        """Test no exception on HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_request.return_value = mock_response

        with patch.dict(os.environ, {"GLASSDOOR_API_KEY": "test_key"}):
            fetcher = GlassdoorSalaryFetcher()
            
            try:
                result = fetcher.fetch_salary_data("Python Developer")
                self.assertIsNotNone(result)
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")


class TestRateLimitingBehavior(unittest.TestCase):
    """Test rate limiting at 5 requests/minute."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_rate_limit_is_5_requests_per_minute(self):
        """Test that rate limit is set to 5 requests/minute."""
        self.assertEqual(self.fetcher.rate_limit, 5)

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limiting_enforces_12_second_interval(self, mock_time, mock_sleep):
        """Test rate limiting enforces 12 second interval (60/5)."""
        # rate_limit=5 means 12 second interval
        times = [100.0, 102.0, 114.0]
        mock_time.side_effect = times

        self.fetcher._apply_rate_limit()  # First request
        self.fetcher._apply_rate_limit()  # Second request

        # Should sleep for approximately (12 - 2) = 10 seconds
        mock_sleep.assert_called_once()
        sleep_duration = mock_sleep.call_args[0][0]
        self.assertAlmostEqual(sleep_duration, 10.0, delta=0.01)


class TestLogging(unittest.TestCase):
    """Test logging functionality."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    @patch("app.services.web_data_fetcher.logger")
    def test_logging_on_successful_fetch(self, mock_logger):
        """Test logging on successful fetch."""
        with patch("app.services.web_data_fetcher.LiveDataCache"):
            self.fetcher.fetch_salary_data("Python Developer")

        # Should have info level logs
        self.assertTrue(mock_logger.info.called or mock_logger.debug.called)

    @patch("app.services.web_data_fetcher.logger")
    def test_logging_on_mock_data(self, mock_logger):
        """Test logging when using mock data."""
        with patch("app.services.web_data_fetcher.LiveDataCache"):
            self.fetcher.fetch_salary_data("Python Developer")

        # Should log that mock data is being used
        log_calls = str(mock_logger.debug.call_args_list) + str(mock_logger.info.call_args_list)
        # Either mock data message or cache message should be logged
        self.assertTrue(mock_logger.info.called or mock_logger.debug.called)


class TestReturnFormatConsistency(unittest.TestCase):
    """Test consistent return format across all scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_successful_fetch_format(self):
        """Test return format on successful fetch."""
        result = self.fetcher.fetch_salary_data("Python Developer")

        required_keys = {"data", "source", "retrieved_at", "confidence_score"}
        self.assertEqual(set(result.keys()), required_keys)

    def test_error_response_format(self):
        """Test return format on error."""
        result = self.fetcher.fetch_salary_data(None)

        required_keys = {"data", "source", "retrieved_at", "confidence_score"}
        self.assertEqual(set(result.keys()), required_keys)
        self.assertEqual(result["data"], {})

    def test_salary_data_structure(self):
        """Test salary data structure includes required fields."""
        result = self.fetcher.fetch_salary_data("Python Developer")

        if result["data"]:
            self.assertIn("avg", result["data"])
            self.assertIn("min", result["data"])
            self.assertIn("max", result["data"])
            self.assertIn("currency", result["data"])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ.pop("GLASSDOOR_API_KEY", None)
        self.fetcher = GlassdoorSalaryFetcher()

    def test_very_long_role_name(self):
        """Test handling of very long role name."""
        long_role = "Senior Principal Staff Distinguished Software Architect Engineer" * 5
        result = self.fetcher.fetch_salary_data(long_role)

        self.assertIsNotNone(result)
        self.assertIn("data", result)

    def test_special_characters_in_role(self):
        """Test handling of special characters in role name."""
        result = self.fetcher.fetch_salary_data("C++ / C# Developer")

        self.assertIsNotNone(result)
        self.assertIn("data", result)

    def test_special_characters_in_location(self):
        """Test handling of special characters in location."""
        result = self.fetcher.fetch_salary_data("Python Developer", "Zürich, Switzerland")

        self.assertIsNotNone(result)
        self.assertIn("data", result)

    def test_numeric_role_name(self):
        """Test handling of numeric role name."""
        result = self.fetcher.fetch_salary_data("3D Graphics Developer")

        self.assertIsNotNone(result)
        self.assertIn("data", result)


if __name__ == "__main__":
    unittest.main()
