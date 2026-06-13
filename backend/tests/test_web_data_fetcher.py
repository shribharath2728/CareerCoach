"""
Comprehensive Unit Tests for WebDataFetcher Base Class

Tests cover:
- Successful HTTP requests (GET and POST)
- Timeout handling and retry logic
- Rate limit (429) responses and retry behavior
- Network connection errors
- All HTTP error codes (4xx, 5xx)
- Exponential backoff timing
- Return format validation
- Logging verification
- Graceful error handling (no exceptions raised)
"""

import logging
import time
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from app.services.web_data_fetcher import WebDataFetcher


class ConcreteWebDataFetcher(WebDataFetcher):
    """Concrete implementation for testing abstract base class."""

    def fetch_salary_data(self, job_title: str = None, location: str = None):
        """Fetch salary data."""
        url = "https://api.example.com/salary"
        params = {}
        if job_title:
            params["job_title"] = job_title
        if location:
            params["location"] = location
        return self._make_request(url, params=params)

    def fetch_skill_trends(self):
        """Fetch skill trends."""
        url = "https://api.example.com/trends"
        return self._make_request(url)

    def fetch_job_postings(self, query: str = None):
        """Fetch job postings."""
        url = "https://api.example.com/jobs"
        params = {"query": query} if query else {}
        return self._make_request(url, params=params)

    def fetch_courses(self, skill: str = None):
        """Fetch courses."""
        url = "https://api.example.com/courses"
        params = {"skill": skill} if skill else {}
        return self._make_request(url, params=params)


class TestWebDataFetcherInitialization(unittest.TestCase):
    """Test WebDataFetcher initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        fetcher = ConcreteWebDataFetcher()
        self.assertEqual(fetcher.rate_limit, 10)
        self.assertEqual(fetcher.timeout, 10)
        self.assertEqual(fetcher.source_name, "ConcreteWebDataFetcher")
        self.assertEqual(fetcher._last_request_time, 0.0)

    def test_custom_rate_limit(self):
        """Test initialization with custom rate limit."""
        fetcher = ConcreteWebDataFetcher(rate_limit=5)
        self.assertEqual(fetcher.rate_limit, 5)

    def test_custom_timeout(self):
        """Test initialization with custom timeout."""
        fetcher = ConcreteWebDataFetcher(timeout=30)
        self.assertEqual(fetcher.timeout, 30)

    def test_both_custom_parameters(self):
        """Test initialization with both custom rate limit and timeout."""
        fetcher = ConcreteWebDataFetcher(rate_limit=3, timeout=20)
        self.assertEqual(fetcher.rate_limit, 3)
        self.assertEqual(fetcher.timeout, 20)

    @patch.dict("os.environ", {"WEB_FETCHER_TIMEOUT_SECONDS": "25"})
    def test_timeout_from_env(self):
        """Test timeout read from environment variable."""
        fetcher = ConcreteWebDataFetcher()
        self.assertEqual(fetcher.timeout, 25)


class TestSuccessfulRequests(unittest.TestCase):
    """Test successful HTTP requests."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    def test_successful_get_request(self, mock_request):
        """Test successful GET request."""
        expected_data = {"salary": 95000, "currency": "USD"}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertIsNotNone(result["data"])
        self.assertEqual(result["data"], expected_data)
        self.assertEqual(result["source"], "ConcreteWebDataFetcher")
        self.assertEqual(result["confidence_score"], 0.8)
        self.assertIsInstance(result["retrieved_at"], datetime)
        mock_request.assert_called_once()

    @patch("requests.request")
    def test_successful_post_request(self, mock_request):
        """Test successful POST request."""
        expected_data = {"jobs": [{"title": "Python Dev"}]}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_request.return_value = mock_response

        payload = {"filters": {"skill": "Python"}}
        result = self.fetcher._make_request(
            "https://api.example.com/search", method="POST", json=payload
        )

        self.assertEqual(result["data"], expected_data)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["method"], "POST")
        self.assertEqual(call_args[1]["json"], payload)

    @patch("requests.request")
    def test_successful_request_with_custom_confidence(self, mock_request):
        """Test successful request with custom confidence score."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        result = self.fetcher._make_request(
            "https://api.example.com/data", confidence_score=0.95
        )

        self.assertEqual(result["confidence_score"], 0.95)

    @patch("requests.request")
    def test_request_with_query_parameters(self, mock_request):
        """Test GET request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_request.return_value = mock_response

        params = {"job_title": "Data Scientist", "location": "New York"}
        result = self.fetcher._make_request(
            "https://api.example.com/search", params=params
        )

        self.assertEqual(result["data"], {"results": []})
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["params"], params)

    @patch("requests.request")
    def test_request_with_custom_headers(self, mock_request):
        """Test request with custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token123"}
        result = self.fetcher._make_request(
            "https://api.example.com/data", headers=headers
        )

        self.assertEqual(result["data"]["data"], "test")
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["headers"], headers)


class TestTimeoutHandling(unittest.TestCase):
    """Test timeout handling and retry logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher(timeout=5)

    @patch("requests.request")
    @patch("time.sleep")
    def test_timeout_retry_success_on_second_attempt(self, mock_sleep, mock_request):
        """Test successful retry after timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}

        # First call raises timeout, second succeeds
        mock_request.side_effect = [
            Exception("Timeout"),
            mock_response,
        ]

        # Patch to handle both Timeout and generic Exception
        from requests.exceptions import Timeout

        mock_request.side_effect = [Timeout(), mock_response]

        result = self.fetcher._make_request("https://api.example.com/data")

        # Should call sleep for exponential backoff (1 second first attempt)
        mock_sleep.assert_called()
        self.assertEqual(result["data"], {"data": "success"})

    @patch("requests.request")
    @patch("time.sleep")
    def test_timeout_all_retries_fail(self, mock_sleep, mock_request):
        """Test all retry attempts fail due to timeout."""
        from requests.exceptions import Timeout

        mock_request.side_effect = Timeout()

        result = self.fetcher._make_request("https://api.example.com/data")

        # Should have 3 retry attempts with exponential backoff
        self.assertEqual(mock_request.call_count, 3)
        # Should sleep 1s, then 2s for the two retries
        self.assertEqual(mock_sleep.call_count, 2)
        sleep_calls = [call(1), call(2)]
        mock_sleep.assert_has_calls(sleep_calls)

        # Should return empty data with 0 confidence
        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)

    @patch("requests.request")
    @patch("time.sleep")
    def test_timeout_exponential_backoff_timing(self, mock_sleep, mock_request):
        """Test exponential backoff timing (1s, 2s, 4s)."""
        from requests.exceptions import Timeout

        mock_request.side_effect = Timeout()

        result = self.fetcher._make_request("https://api.example.com/data")

        # Verify exponential backoff: 1s, 2s (4s not reached as only 3 attempts total)
        sleep_calls = mock_sleep.call_args_list
        self.assertEqual(len(sleep_calls), 2)
        self.assertEqual(sleep_calls[0][0][0], 1)  # First backoff: 1s
        self.assertEqual(sleep_calls[1][0][0], 2)  # Second backoff: 2s


class TestRateLimitHandling(unittest.TestCase):
    """Test rate limit (HTTP 429) handling and retry logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher(rate_limit=10)

    @patch("requests.request")
    @patch("time.sleep")
    def test_http_429_retry_success(self, mock_sleep, mock_request):
        """Test successful retry after HTTP 429."""
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": "success"}

        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.text = "Rate limit exceeded"

        # First call returns 429, second succeeds
        mock_request.side_effect = [rate_limit_response, success_response]

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {"data": "success"})
        mock_sleep.assert_called()

    @patch("requests.request")
    @patch("time.sleep")
    def test_http_429_all_retries_fail(self, mock_sleep, mock_request):
        """Test all retry attempts fail due to HTTP 429."""
        response = Mock()
        response.status_code = 429
        response.text = "Rate limit exceeded"
        response.json.side_effect = Exception("JSON parsing failed")

        mock_request.return_value = response

        result = self.fetcher._make_request("https://api.example.com/data")

        # Should have 3 retry attempts
        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)


class TestConnectionErrors(unittest.TestCase):
    """Test network connection error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    @patch("time.sleep")
    def test_connection_error_retry_success(self, mock_sleep, mock_request):
        """Test successful retry after connection error."""
        from requests.exceptions import ConnectionError

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": "success"}

        # First call raises ConnectionError, second succeeds
        mock_request.side_effect = [ConnectionError(), success_response]

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {"data": "success"})

    @patch("requests.request")
    @patch("time.sleep")
    def test_connection_error_all_retries_fail(self, mock_sleep, mock_request):
        """Test all retry attempts fail due to connection error."""
        from requests.exceptions import ConnectionError

        mock_request.side_effect = ConnectionError()

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)


class TestHTTPErrorHandling(unittest.TestCase):
    """Test HTTP error code handling (4xx, 5xx)."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    def test_http_400_bad_request(self, mock_request):
        """Test HTTP 400 Bad Request."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        # Should not retry for 4xx errors (not transient)
        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)

    @patch("requests.request")
    def test_http_401_unauthorized(self, mock_request):
        """Test HTTP 401 Unauthorized."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)

    @patch("requests.request")
    def test_http_403_forbidden(self, mock_request):
        """Test HTTP 403 Forbidden."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {})

    @patch("requests.request")
    def test_http_404_not_found(self, mock_request):
        """Test HTTP 404 Not Found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {})

    @patch("requests.request")
    def test_http_500_server_error(self, mock_request):
        """Test HTTP 500 Server Error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        # 5xx errors are transient, but handled as errors on first attempt
        self.assertEqual(result["data"], {})

    @patch("requests.request")
    def test_http_502_bad_gateway(self, mock_request):
        """Test HTTP 502 Bad Gateway."""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad gateway"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {})

    @patch("requests.request")
    def test_http_503_service_unavailable(self, mock_request):
        """Test HTTP 503 Service Unavailable."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        self.assertEqual(result["data"], {})


class TestReturnFormatValidation(unittest.TestCase):
    """Test standardized return format validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    def test_success_return_format(self, mock_request):
        """Test return format on success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"salary": 95000}
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        # Verify all required fields
        self.assertIn("data", result)
        self.assertIn("source", result)
        self.assertIn("retrieved_at", result)
        self.assertIn("confidence_score", result)

        # Verify field types
        self.assertIsInstance(result["data"], dict)
        self.assertIsInstance(result["source"], str)
        self.assertIsInstance(result["retrieved_at"], datetime)
        self.assertIsInstance(result["confidence_score"], float)

        # Verify field values
        self.assertEqual(result["source"], "ConcreteWebDataFetcher")
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)

    @patch("requests.request")
    def test_error_return_format(self, mock_request):
        """Test return format on error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_request.return_value = mock_response

        result = self.fetcher._make_request("https://api.example.com/data")

        # Verify all required fields
        self.assertIn("data", result)
        self.assertIn("source", result)
        self.assertIn("retrieved_at", result)
        self.assertIn("confidence_score", result)

        # Error should have empty data and 0 confidence
        self.assertEqual(result["data"], {})
        self.assertEqual(result["confidence_score"], 0.0)


class TestRateLimitingBehavior(unittest.TestCase):
    """Test rate limiting behavior between requests."""

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limiting_no_sleep_on_first_request(
        self, mock_time, mock_sleep
    ):
        """Test no sleep on first request."""
        mock_time.return_value = 100.0

        fetcher = ConcreteWebDataFetcher(rate_limit=10)
        fetcher._apply_rate_limit()

        # First request should not sleep
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limiting_enforces_interval(self, mock_time, mock_sleep):
        """Test rate limiting enforces minimum interval between requests."""
        # rate_limit=10 means 10 requests/min = 6 second interval
        # Each call to _apply_rate_limit:
        #   - First call: _last_request_time == 0, sets it to 100.0
        #   - Second call: 
        #     - now = time.time() = 102.0
        #     - elapsed = 102.0 - 100.0 = 2.0
        #     - min_interval = 6.0
        #     - elapsed < min_interval, so sleep for (6.0 - 2.0) = 4.0
        #     - then _last_request_time = time.time() = 108.0
        times = [100.0, 102.0, 108.0]
        mock_time.side_effect = times

        fetcher = ConcreteWebDataFetcher(rate_limit=10)
        fetcher._apply_rate_limit()  # First request
        fetcher._apply_rate_limit()  # Second request (should sleep ~4s)

        # Should sleep for approximately (6 - 2) = 4 seconds
        mock_sleep.assert_called_once()
        sleep_duration = mock_sleep.call_args[0][0]
        self.assertAlmostEqual(sleep_duration, 4.0, delta=0.01)

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limiting_no_sleep_when_interval_exceeded(
        self, mock_time, mock_sleep
    ):
        """Test no sleep when minimum interval exceeded."""
        # rate_limit=10 means 6 second interval
        # First call: sets _last_request_time to 100.0
        # Second call: 
        #   - now = 107.0
        #   - elapsed = 107.0 - 100.0 = 7.0
        #   - min_interval = 6.0
        #   - elapsed >= min_interval, so no sleep
        #   - then _last_request_time = time.time() = 107.0
        times = [100.0, 107.0, 107.0]
        mock_time.side_effect = times

        fetcher = ConcreteWebDataFetcher(rate_limit=10)
        fetcher._apply_rate_limit()  # First request
        fetcher._apply_rate_limit()  # Second request (no sleep, 7s > 6s)

        # Should not sleep
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_custom_rate(self, mock_time, mock_sleep):
        """Test rate limiting with custom rate limit."""
        # rate_limit=5 means 5 requests/min = 12 second interval
        # First call: sets _last_request_time to 100.0
        # Second call:
        #   - now = 102.0
        #   - elapsed = 102.0 - 100.0 = 2.0
        #   - min_interval = 12.0
        #   - sleep_time = 12.0 - 2.0 = 10.0
        #   - then _last_request_time = time.time() = 112.0
        times = [100.0, 102.0, 112.0]
        mock_time.side_effect = times

        fetcher = ConcreteWebDataFetcher(rate_limit=5)
        fetcher._apply_rate_limit()  # First request
        fetcher._apply_rate_limit()  # Second request

        mock_sleep.assert_called_once()
        sleep_duration = mock_sleep.call_args[0][0]
        # min_interval = 60.0 / 5 = 12.0
        # sleep_time = 12.0 - 2.0 = 10.0
        self.assertAlmostEqual(sleep_duration, 10.0, delta=0.01)


class TestAbstractMethods(unittest.TestCase):
    """Test abstract method enforcement."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that WebDataFetcher cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            WebDataFetcher()

    def test_concrete_implementation_required(self):
        """Test that concrete class must implement all abstract methods."""

        class IncompleteFetcher(WebDataFetcher):
            """Incomplete implementation missing abstract methods."""

            def fetch_salary_data(self):
                return {}

        # Should raise TypeError on instantiation
        with self.assertRaises(TypeError):
            IncompleteFetcher()

    def test_fetch_salary_data_not_implemented(self):
        """Test NotImplementedError when calling abstract method."""
        fetcher = ConcreteWebDataFetcher()

        # Manually calling the parent abstract method should raise
        with self.assertRaises(NotImplementedError):
            WebDataFetcher.fetch_salary_data(fetcher)


class TestLogging(unittest.TestCase):
    """Test logging functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    @patch("app.services.web_data_fetcher.logger")
    def test_logging_on_success(self, mock_logger, mock_request):
        """Test logging on successful request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        self.fetcher._make_request("https://api.example.com/data")

        # Should have info level logs
        self.assertTrue(mock_logger.info.called)

    @patch("requests.request")
    @patch("app.services.web_data_fetcher.logger")
    def test_logging_on_timeout(self, mock_logger, mock_request):
        """Test logging on timeout."""
        from requests.exceptions import Timeout

        mock_request.side_effect = Timeout()

        with patch("time.sleep"):
            self.fetcher._make_request("https://api.example.com/data")

        # Should have warning logs
        self.assertTrue(mock_logger.warning.called)

    @patch("requests.request")
    @patch("app.services.web_data_fetcher.logger")
    def test_logging_on_http_error(self, mock_logger, mock_request):
        """Test logging on HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_request.return_value = mock_response

        self.fetcher._make_request("https://api.example.com/data")

        # Should have warning logs
        self.assertTrue(mock_logger.warning.called)


class TestConcreteImplementation(unittest.TestCase):
    """Test concrete fetcher methods using the base class."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    def test_fetch_salary_data_method(self, mock_request):
        """Test fetch_salary_data method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"avg_salary": 95000}
        mock_request.return_value = mock_response

        result = self.fetcher.fetch_salary_data("Python Developer", "New York")

        self.assertEqual(result["data"]["avg_salary"], 95000)
        self.assertGreater(result["confidence_score"], 0.0)

    @patch("requests.request")
    def test_fetch_skill_trends_method(self, mock_request):
        """Test fetch_skill_trends method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"trends": ["Python", "ML", "Cloud"]}
        mock_request.return_value = mock_response

        result = self.fetcher.fetch_skill_trends()

        self.assertIn("trends", result["data"])

    @patch("requests.request")
    def test_fetch_job_postings_method(self, mock_request):
        """Test fetch_job_postings method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": [{"title": "Python Dev"}]}
        mock_request.return_value = mock_response

        result = self.fetcher.fetch_job_postings("Python")

        self.assertIn("jobs", result["data"])

    @patch("requests.request")
    def test_fetch_courses_method(self, mock_request):
        """Test fetch_courses method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"courses": [{"title": "Python 101"}]}
        mock_request.return_value = mock_response

        result = self.fetcher.fetch_courses("Python")

        self.assertIn("courses", result["data"])


class TestGracefulErrorHandling(unittest.TestCase):
    """Test graceful error handling (no exceptions raised)."""

    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = ConcreteWebDataFetcher()

    @patch("requests.request")
    def test_no_exception_on_timeout(self, mock_request):
        """Test that timeout doesn't raise exception."""
        from requests.exceptions import Timeout

        mock_request.side_effect = Timeout()

        with patch("time.sleep"):
            # Should not raise any exception
            result = self.fetcher._make_request("https://api.example.com/data")
            self.assertIsNotNone(result)

    @patch("requests.request")
    def test_no_exception_on_connection_error(self, mock_request):
        """Test that connection error doesn't raise exception."""
        from requests.exceptions import ConnectionError

        mock_request.side_effect = ConnectionError()

        with patch("time.sleep"):
            # Should not raise any exception
            result = self.fetcher._make_request("https://api.example.com/data")
            self.assertIsNotNone(result)

    @patch("requests.request")
    def test_no_exception_on_http_error(self, mock_request):
        """Test that HTTP error doesn't raise exception."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_request.return_value = mock_response

        # Should not raise any exception
        result = self.fetcher._make_request("https://api.example.com/data")
        self.assertIsNotNone(result)

    @patch("requests.request")
    def test_no_exception_on_unexpected_error(self, mock_request):
        """Test that unexpected error doesn't raise exception."""
        mock_request.side_effect = Exception("Unexpected error")

        # Should not raise any exception
        result = self.fetcher._make_request("https://api.example.com/data")
        self.assertIsNotNone(result)
        self.assertEqual(result["confidence_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
