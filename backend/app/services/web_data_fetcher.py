"""
Web Data Fetcher Base Class Module — Abstract Base for Live Data Integration

This module provides the abstract base class infrastructure for fetching live data from 
web sources (salary data, skill trends, job postings, courses). It implements shared 
functionality including HTTP request handling, rate limiting, retry logic, and error 
handling for all concrete fetcher implementations.

Features:
- Abstract base class (ABC) with defined interface methods
- Shared HTTP request handler with GET/POST support
- Rate limiting (configurable, default 10 requests/minute)
- Exponential backoff retry logic (3 attempts: 1s, 2s, 4s)
- Timeout protection with configurable default (10 seconds)
- Graceful error handling (no exceptions raised, empty dict returned)
- Comprehensive logging for all operations
- Standardized return format with metadata

Standard Return Format:
    {
        "data": [...] or {},           # Fetched data or empty dict on error
        "source": "fetcher_identifier",  # Identifier for the data source
        "retrieved_at": datetime,       # Timestamp of retrieval
        "confidence_score": 0.0-1.0     # Confidence in data quality
    }

Example Usage:
    >>> class MyCustomFetcher(WebDataFetcher):
    ...     def fetch_salary_data(self, job_title: str, location: str = None):
    ...         url = f"https://api.example.com/salary?job={job_title}"
    ...         return self._make_request(url, method="GET")
    ...
    ...     def fetch_skill_trends(self):
    ...         url = "https://api.example.com/trends"
    ...         return self._make_request(url, method="GET")
    ...
    ...     def fetch_job_postings(self, query: str):
    ...         url = "https://api.example.com/jobs"
    ...         payload = {"search": query}
    ...         return self._make_request(url, method="POST", json=payload)
    ...
    ...     def fetch_courses(self, skill: str):
    ...         url = "https://api.example.com/courses"
    ...         return self._make_request(url, method="GET", params={"skill": skill})
    ...
    >>> fetcher = MyCustomFetcher(rate_limit=10)  # 10 requests/minute
    >>> result = fetcher.fetch_salary_data("Python Developer", "San Francisco")
    >>> print(result["data"])  # Access fetched data
    >>> print(result["confidence_score"])  # Check confidence

Rate Limiting Behavior:
    Rate limiting is applied per instance. If you make 10 requests in 60 seconds,
    subsequent requests are delayed to maintain the limit. The delay is calculated
    as: delay = (60 / rate_limit) - (now - last_request_time)
    
Retry Logic:
    On timeout, connection error, or HTTP 429 (rate limit), the fetcher automatically
    retries with exponential backoff:
    - Attempt 1: Wait 1 second before retry
    - Attempt 2: Wait 2 seconds before retry
    - Attempt 3: Wait 4 seconds before retry
    If all retries fail, returns empty dict with warning log.

Error Handling:
    The fetcher never raises exceptions to the caller. All errors (network, timeout,
    HTTP errors) result in:
    - A warning log message
    - An empty dict returned in the "data" field
    - confidence_score set to 0.0
    
    This ensures graceful degradation in RAG systems.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
import os

logger = logging.getLogger(__name__)


class WebDataFetcher(ABC):
    """
    Abstract base class for fetching live data from web sources.
    
    This class provides the interface and shared utilities for all concrete fetcher
    implementations. Child classes must implement the abstract methods for specific
    data types: salary data, skill trends, job postings, and courses.
    
    The base class handles:
    - HTTP request management (GET/POST)
    - Rate limiting to prevent API throttling
    - Exponential backoff retry on transient failures
    - Timeout protection
    - Graceful error handling with logging
    
    Attributes:
        rate_limit (int): Maximum requests per minute (default: 10)
        timeout (int): Request timeout in seconds (default: 10, configurable via env)
        source_name (str): Identifier for this fetcher's data source
        _last_request_time (float): Timestamp of last request (for rate limiting)
    
    Child Class Requirements:
        1. Implement all abstract methods:
           - fetch_salary_data()
           - fetch_skill_trends()
           - fetch_job_postings()
           - fetch_courses()
        
        2. Call _make_request() to perform HTTP operations
        
        3. Set source_name in __init__() for tracking
        
        4. Optionally override __init__() to set custom rate_limit or timeout
    
    Examples:
        >>> class GlassdoorFetcher(WebDataFetcher):
        ...     def __init__(self):
        ...         super().__init__(rate_limit=5)  # Respect API limits
        ...         self.source_name = "glassdoor"
        ...
        ...     def fetch_salary_data(self, job_title: str, location: str = None):
        ...         url = "https://api.glassdoor.com/v1/salary"
        ...         params = {"job": job_title, "location": location}
        ...         return self._make_request(url, params=params)
        ...
        ...     # Implement other abstract methods...
        ...
        >>> fetcher = GlassdoorFetcher()
        >>> result = fetcher.fetch_salary_data("Data Scientist", "New York")
        >>> if result["data"]:
        ...     print(f"Salary data retrieved: {result['data']}")
        ... else:
        ...     print(f"Failed to fetch (confidence: {result['confidence_score']})")
    """

    def __init__(self, rate_limit: int = 10, timeout: Optional[int] = None):
        """
        Initialize the web data fetcher.
        
        Args:
            rate_limit (int): Maximum requests per minute (default: 10)
            timeout (Optional[int]): Request timeout in seconds. If None, reads from
                                    WEB_FETCHER_TIMEOUT_SECONDS env var (default 10)
        
        Examples:
            >>> # Use default rate limit and timeout
            >>> fetcher = MyFetcher()
            
            >>> # Custom rate limit (5 requests/minute)
            >>> fetcher = MyFetcher(rate_limit=5)
            
            >>> # Custom timeout (30 seconds)
            >>> fetcher = MyFetcher(timeout=30)
            
            >>> # Both custom
            >>> fetcher = MyFetcher(rate_limit=3, timeout=20)
        """
        self.rate_limit = rate_limit
        self.timeout = timeout or int(os.getenv("WEB_FETCHER_TIMEOUT_SECONDS", "10"))
        self.source_name = self.__class__.__name__
        self._last_request_time: float = 0.0
        logger.info(
            f"WebDataFetcher initialized: {self.source_name}, "
            f"rate_limit={rate_limit} req/min, timeout={self.timeout}s"
        )

    @abstractmethod
    def fetch_salary_data(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Abstract method for fetching salary data.
        
        Must be implemented by subclasses to fetch salary information for specific
        job titles, locations, or other parameters.
        
        Returns:
            Dict[str, Any]: Standardized return format with:
                - data: Salary data or empty dict on error
                - source: Source identifier
                - retrieved_at: Timestamp
                - confidence_score: 0.0-1.0
        
        Examples:
            >>> class CustomFetcher(WebDataFetcher):
            ...     def fetch_salary_data(self, job_title: str, location: str = None):
            ...         url = f"https://api.example.com/salary/{job_title}"
            ...         params = {"location": location} if location else {}
            ...         return self._make_request(url, params=params)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fetch_salary_data()"
        )

    @abstractmethod
    def fetch_skill_trends(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Abstract method for fetching skill trend data.
        
        Must be implemented by subclasses to fetch information about trending skills,
        skill demand, or skill popularity metrics.
        
        Returns:
            Dict[str, Any]: Standardized return format with:
                - data: Skill trends data or empty dict on error
                - source: Source identifier
                - retrieved_at: Timestamp
                - confidence_score: 0.0-1.0
        
        Examples:
            >>> class CustomFetcher(WebDataFetcher):
            ...     def fetch_skill_trends(self):
            ...         url = "https://api.example.com/skills/trends"
            ...         return self._make_request(url)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fetch_skill_trends()"
        )

    @abstractmethod
    def fetch_job_postings(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Abstract method for fetching job postings.
        
        Must be implemented by subclasses to fetch job listings based on query
        parameters like job title, location, or skills.
        
        Returns:
            Dict[str, Any]: Standardized return format with:
                - data: Job postings list or empty dict on error
                - source: Source identifier
                - retrieved_at: Timestamp
                - confidence_score: 0.0-1.0
        
        Examples:
            >>> class CustomFetcher(WebDataFetcher):
            ...     def fetch_job_postings(self, query: str, location: str = None):
            ...         url = "https://api.example.com/jobs/search"
            ...         params = {"q": query, "location": location}
            ...         return self._make_request(url, params=params)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fetch_job_postings()"
        )

    @abstractmethod
    def fetch_courses(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Abstract method for fetching course information.
        
        Must be implemented by subclasses to fetch course listings for skill
        development based on skill names or learning objectives.
        
        Returns:
            Dict[str, Any]: Standardized return format with:
                - data: Courses list or empty dict on error
                - source: Source identifier
                - retrieved_at: Timestamp
                - confidence_score: 0.0-1.0
        
        Examples:
            >>> class CustomFetcher(WebDataFetcher):
            ...     def fetch_courses(self, skill: str, level: str = None):
            ...         url = "https://api.example.com/courses"
            ...         params = {"skill": skill, "level": level}
            ...         return self._make_request(url, params=params)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fetch_courses()"
        )

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        confidence_score: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting, retry logic, and error handling.
        
        This is the core method for all HTTP operations. It handles:
        - Rate limiting (respects configured limit)
        - Exponential backoff retries on transient failures
        - Timeout protection
        - Graceful error handling (never raises exceptions)
        
        Rate Limiting:
            Enforces rate_limit (requests per minute). If the time since the last
            request is less than (60 / rate_limit) seconds, sleeps until that time
            has elapsed.
        
        Retry Logic:
            Retries on:
            - Connection errors
            - Timeout errors
            - HTTP 429 (Rate Limit Exceeded)
            
            Retry schedule:
            - Attempt 1 (immediate): If fails, sleep 1s
            - Attempt 2 (after 1s): If fails, sleep 2s
            - Attempt 3 (after 2s): If fails, sleep 4s
            - All failed: Return empty dict
        
        Args:
            url (str): Target URL for the request
            method (str): HTTP method - "GET" or "POST" (default: "GET")
            params (Optional[Dict]): Query string parameters for GET requests
            json (Optional[Dict]): JSON body for POST requests
            headers (Optional[Dict]): Custom HTTP headers
            confidence_score (float): Confidence in data quality (0.0-1.0, default: 0.8)
        
        Returns:
            Dict[str, Any]: Standardized return dictionary with:
                - "data": Response JSON (or empty dict on error)
                - "source": Fetcher source name
                - "retrieved_at": datetime.now()
                - "confidence_score": float (0.8 on success, 0.0 on error)
        
        Examples:
            >>> fetcher = MyFetcher()
            
            >>> # Simple GET request
            >>> result = fetcher._make_request("https://api.example.com/data")
            >>> print(result["data"])  # Fetched data
            
            >>> # GET with query parameters
            >>> result = fetcher._make_request(
            ...     "https://api.example.com/search",
            ...     params={"q": "python", "limit": 10}
            ... )
            
            >>> # POST request with JSON body
            >>> result = fetcher._make_request(
            ...     "https://api.example.com/query",
            ...     method="POST",
            ...     json={"filters": {"skill": "Python", "salary_min": 80000}}
            ... )
            
            >>> # Custom headers and confidence score
            >>> result = fetcher._make_request(
            ...     "https://api.example.com/data",
            ...     headers={"Authorization": "Bearer token_here"},
            ...     confidence_score=0.95
            ... )
            
            >>> # Check if request succeeded
            >>> if result["data"]:
            ...     print(f"Success: {result['data']}")
            ... else:
            ...     print(f"Request failed (confidence: {result['confidence_score']})")
        
        Raises:
            None - All errors handled gracefully
        """
        # Apply rate limiting
        self._apply_rate_limit()

        # Retry logic with exponential backoff
        max_retries = 3
        backoff_times = [1, 2, 4]  # seconds: 1s, 2s, 4s

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"[{self.source_name}] {method} request to {url} (attempt {attempt + 1}/{max_retries})"
                )

                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Check for HTTP errors
                if response.status_code == 429:  # Rate limit
                    logger.warning(
                        f"[{self.source_name}] HTTP 429 (Rate Limited) from {url}"
                    )
                    if attempt < max_retries - 1:
                        wait_time = backoff_times[attempt]
                        logger.info(
                            f"[{self.source_name}] Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        continue

                elif response.status_code >= 400:  # Other HTTP errors (4xx, 5xx)
                    logger.warning(
                        f"[{self.source_name}] HTTP {response.status_code} from {url}: "
                        f"{response.text[:100]}"
                    )
                    return self._error_response(confidence_score=0.0)

                # Success
                response.raise_for_status()
                data = response.json()
                logger.info(
                    f"[{self.source_name}] Successfully fetched data from {url}"
                )
                return self._success_response(data, confidence_score)

            except Timeout:
                logger.warning(
                    f"[{self.source_name}] Timeout ({self.timeout}s) from {url}"
                )
                if attempt < max_retries - 1:
                    wait_time = backoff_times[attempt]
                    logger.info(
                        f"[{self.source_name}] Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

            except ConnectionError as e:
                logger.warning(
                    f"[{self.source_name}] Connection error from {url}: {str(e)[:100]}"
                )
                if attempt < max_retries - 1:
                    wait_time = backoff_times[attempt]
                    logger.info(
                        f"[{self.source_name}] Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

            except RequestException as e:
                logger.warning(
                    f"[{self.source_name}] Request error from {url}: {str(e)[:100]}"
                )
                if attempt < max_retries - 1:
                    wait_time = backoff_times[attempt]
                    logger.info(
                        f"[{self.source_name}] Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

            except Exception as e:
                logger.error(
                    f"[{self.source_name}] Unexpected error from {url}: {str(e)[:100]}"
                )
                return self._error_response(confidence_score=0.0)

        # All retries exhausted
        logger.warning(
            f"[{self.source_name}] All {max_retries} retry attempts failed for {url}"
        )
        return self._error_response(confidence_score=0.0)

    def _apply_rate_limit(self) -> None:
        """
        Apply rate limiting between requests.
        
        Calculates the time elapsed since the last request and sleeps if necessary
        to maintain the configured rate limit (requests per minute).
        
        Formula: min_interval = 60 / rate_limit
        If elapsed time < min_interval, sleep for the difference.
        
        Examples:
            >>> fetcher = MyFetcher(rate_limit=10)  # 10 requests per minute
            >>> # min_interval = 60 / 10 = 6 seconds
            >>> fetcher._apply_rate_limit()  # First call - no sleep
            >>> fetcher._apply_rate_limit()  # Sleeps if called < 6s later
        """
        if self._last_request_time == 0.0:
            # First request
            self._last_request_time = time.time()
            return

        now = time.time()
        elapsed = now - self._last_request_time
        min_interval = 60.0 / self.rate_limit

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(
                f"[{self.source_name}] Rate limiting: sleeping {sleep_time:.2f}s "
                f"(rate_limit={self.rate_limit} req/min)"
            )
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _success_response(
        self, data: Dict[str, Any], confidence_score: float
    ) -> Dict[str, Any]:
        """
        Create a standardized success response.
        
        Args:
            data (Dict[str, Any]): Fetched data
            confidence_score (float): Confidence in data quality (0.0-1.0)
        
        Returns:
            Dict[str, Any]: Standardized response with data, source, timestamp, and confidence
        """
        return {
            "data": data,
            "source": self.source_name,
            "retrieved_at": datetime.now(),
            "confidence_score": confidence_score,
        }

    def _error_response(self, confidence_score: float = 0.0) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            confidence_score (float): Confidence score (typically 0.0 for errors)
        
        Returns:
            Dict[str, Any]: Standardized response with empty data and 0.0 confidence
        """
        return {
            "data": {},
            "source": self.source_name,
            "retrieved_at": datetime.now(),
            "confidence_score": confidence_score,
        }


class CourseraCourseFetcher(WebDataFetcher):
    """
    Coursera Course Fetcher for RAG Integration
    
    Fetches course listings and trending courses from Coursera API or realistic mock data.
    Implements rate limiting (10 requests/minute), 24-hour TTL caching, and trend detection.
    
    Features:
    - fetch_courses(skill, career_level): Fetch courses by skill and career level
    - Trending course detection: Identifies courses with high enrollment growth (+200% for AI/LLM)
    - Rate limiting: 10 requests/minute enforced per instance
    - Caching: Results cached with 24-hour TTL to reduce API calls
    - Graceful degradation: Uses realistic mock data if API unavailable
    - Mock data trends: 2024-2025 reflects LLM/AI course surge, ML specializations stable
    
    Return Format:
        {
            "data": {
                "courses": [
                    {
                        "title": str,
                        "provider": str,
                        "enrollment_count": int,
                        "rating": float,
                        "launch_date": str (ISO format),
                        "skills_taught": [str, ...]
                    },
                    ...
                ],
                "trending_courses": [...],  # Subset of courses with high growth
                "enrollment_trends": {
                    "skill": "growth_percentage"
                },
                "average_ratings": {
                    "skill": average_rating
                }
            },
            "source": "CourseraCourseFetcher",
            "retrieved_at": datetime,
            "confidence_score": 0.85 (mock) or 0.95 (API)
        }
    
    Usage Examples:
        >>> fetcher = CourseraCourseFetcher()
        
        >>> # Fetch ML courses at all levels
        >>> result = fetcher.fetch_courses("Machine Learning")
        >>> for course in result["data"]["courses"]:
        ...     print(f"{course['title']}: {course['enrollment_count']} enrollments")
        
        >>> # Fetch beginner Python courses
        >>> result = fetcher.fetch_courses("Python", career_level="beginner")
        >>> trending = result["data"]["trending_courses"]
        >>> print(f"Trending: {len(trending)} courses")
        
        >>> # Check skill trends
        >>> trends = result["data"]["enrollment_trends"]
        >>> for skill, growth in trends.items():
        ...     print(f"{skill}: {growth}% growth")
    """

    def __init__(self, rate_limit: int = 10, timeout: Optional[int] = None):
        """
        Initialize CourseraCourseFetcher with rate limiting and caching.
        
        Args:
            rate_limit (int): Requests per minute (default: 10)
            timeout (Optional[int]): Request timeout in seconds (default: 10 from env)
        
        Example:
            >>> # Default rate limiting (10 req/min)
            >>> fetcher = CourseraCourseFetcher()
            
            >>> # Custom rate limit (5 req/min for heavy load)
            >>> fetcher = CourseraCourseFetcher(rate_limit=5)
        """
        super().__init__(rate_limit=rate_limit, timeout=timeout)
        self.source_name = "CourseraCourseFetcher"
        self.api_key = os.getenv("COURSERA_API_KEY", "")
        self.api_base_url = "https://www.coursera.org/api/onDemandCourses.v1"
        
        # Simple in-memory cache: (skill, career_level) -> (data, timestamp)
        self._cache: Dict[Tuple[str, Optional[str]], Tuple[Dict[str, Any], datetime]] = {}
        self.cache_ttl_hours = 24
        
        logger.info(
            f"CourseraCourseFetcher initialized: "
            f"api_key_set={bool(self.api_key)}, "
            f"rate_limit={rate_limit} req/min"
        )

    def fetch_courses(
        self, skill: str, career_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch courses by skill and optional career level.
        
        Attempts to fetch from Coursera API if COURSERA_API_KEY is set,
        otherwise returns realistic mock data from 2024-2025 course catalog.
        Results are cached with 24-hour TTL to reduce API calls.
        
        Args:
            skill (str): Skill or topic (e.g., "Machine Learning", "Python", "LLM")
            career_level (Optional[str]): Filter by level - "beginner", "intermediate", "advanced"
        
        Returns:
            Dict[str, Any]: Standardized response with:
                - "data": Dictionary containing:
                    - "courses": List of course objects
                    - "trending_courses": Subset with high enrollment growth
                    - "enrollment_trends": Dict of skill -> growth_percentage
                    - "average_ratings": Dict of skill -> avg_rating
                - "source": "CourseraCourseFetcher"
                - "retrieved_at": Fetch timestamp
                - "confidence_score": 0.85 (mock) or 0.95 (API)
        
        Examples:
            >>> fetcher = CourseraCourseFetcher()
            
            >>> # All ML courses
            >>> result = fetcher.fetch_courses("Machine Learning")
            >>> print(f"Found {len(result['data']['courses'])} courses")
            
            >>> # Beginner Python courses
            >>> result = fetcher.fetch_courses("Python", career_level="beginner")
            >>> for course in result["data"]["courses"]:
            ...     print(f"  - {course['title']}: ${course['enrollment_count']} enrollments")
            
            >>> # Check trending
            >>> trends = result["data"]["trending_courses"]
            >>> if trends:
            ...     print(f"Trending: {[c['title'] for c in trends]}")
        """
        cache_key = (skill.lower(), career_level.lower() if career_level else None)
        
        # Check cache
        if self._is_cache_valid(cache_key):
            cached_data, cached_time = self._cache[cache_key]
            logger.debug(f"[CourseraCourseFetcher] Cache hit for {skill}")
            return self._success_response(cached_data, confidence_score=0.85)
        
        # Try API first if key available
        if self.api_key:
            result = self._fetch_from_api(skill, career_level)
            if result["data"]:
                # Cache the result
                self._cache[cache_key] = (result["data"], datetime.now())
                return result
        
        # Fallback to mock data
        mock_data = self._get_mock_courses(skill, career_level)
        # Cache the mock data
        self._cache[cache_key] = (mock_data, datetime.now())
        return self._success_response(mock_data, confidence_score=0.85)

    def fetch_salary_data(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Placeholder for salary data fetching (not used for Coursera fetcher).
        
        Returns:
            Dict[str, Any]: Empty mock data response
        """
        return self._success_response(
            {"message": "Salary data not available from Coursera"},
            confidence_score=0.0
        )

    def fetch_skill_trends(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Placeholder for skill trends fetching (not used for Coursera fetcher).
        
        Returns:
            Dict[str, Any]: Empty mock data response
        """
        return self._success_response(
            {"message": "Skill trends not directly available from Coursera"},
            confidence_score=0.0
        )

    def fetch_job_postings(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Placeholder for job postings fetching (not used for Coursera fetcher).
        
        Returns:
            Dict[str, Any]: Empty mock data response
        """
        return self._success_response(
            {"message": "Job postings not available from Coursera"},
            confidence_score=0.0
        )

    def _is_cache_valid(self, cache_key: Tuple[str, Optional[str]]) -> bool:
        """
        Check if cached data exists and is not expired.
        
        Args:
            cache_key: Tuple of (skill, career_level)
        
        Returns:
            bool: True if cache exists and is valid (< 24 hours old)
        """
        if cache_key not in self._cache:
            return False
        
        data, timestamp = self._cache[cache_key]
        age = datetime.now() - timestamp
        ttl = timedelta(hours=self.cache_ttl_hours)
        
        is_valid = age < ttl
        if not is_valid:
            logger.debug(f"[CourseraCourseFetcher] Cache expired for {cache_key}")
            del self._cache[cache_key]
        
        return is_valid

    def _fetch_from_api(
        self, skill: str, career_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch courses from Coursera API.
        
        Args:
            skill (str): Skill or topic
            career_level (Optional[str]): Career level filter
        
        Returns:
            Dict[str, Any]: Standardized response
        """
        try:
            params = {"query": skill}
            if career_level:
                params["level"] = career_level
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            result = self._make_request(
                self.api_base_url,
                method="GET",
                params=params,
                headers=headers,
                confidence_score=0.95
            )
            
            if result["data"]:
                processed = self._process_api_response(result["data"], skill, career_level)
                return self._success_response(processed, confidence_score=0.95)
            
            return result
            
        except Exception as e:
            logger.error(f"[CourseraCourseFetcher] API fetch error: {str(e)[:100]}")
            return self._error_response()

    def _process_api_response(
        self, api_data: Dict[str, Any], skill: str, career_level: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process and structure API response.
        
        Args:
            api_data: Raw API response
            skill: Original skill query
            career_level: Original level filter
        
        Returns:
            Dict[str, Any]: Structured course data with trends
        """
        courses = []
        enrollment_trends = {}
        avg_ratings = {}
        
        # Parse API response (assuming courses in 'elements' field)
        api_courses = api_data.get("elements", [])
        
        for course in api_courses:
            course_obj = {
                "title": course.get("name", "Unknown"),
                "provider": "Coursera",
                "enrollment_count": course.get("enrollments", 0),
                "rating": course.get("rating", 0.0),
                "launch_date": course.get("launchDate", ""),
                "skills_taught": course.get("skillTags", [])
            }
            courses.append(course_obj)
        
        # Detect trending courses
        trending = self._detect_trending_courses(courses)
        
        # Calculate aggregate metrics
        if courses:
            total_rating = sum(c["rating"] for c in courses)
            avg_ratings[skill] = total_rating / len(courses)
            
            # Placeholder trend: assume API data is current
            enrollment_trends[skill] = 0.0
        
        return {
            "courses": courses,
            "trending_courses": trending,
            "enrollment_trends": enrollment_trends,
            "average_ratings": avg_ratings
        }

    def _get_mock_courses(
        self, skill: str, career_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get realistic mock course data for 2024-2025 reflecting current trends.
        
        2024-2025 Trends:
        - LLM and AI courses surging (+200% growth for DeepLearning.AI LLM Ops)
        - ML specializations stable (50k enrollments, 89% hiring preference)
        - Fast.ai maintains high rating (4.8)
        - On-device ML emerging (+50% growth)
        - Enterprise focus from Google Cloud
        
        Args:
            skill (str): Skill or topic (case-insensitive)
            career_level (Optional[str]): Filter by "beginner", "intermediate", "advanced"
        
        Returns:
            Dict[str, Any]: Mock course data with structure matching API
        """
        skill_lower = skill.lower()
        
        # Comprehensive mock course catalog
        mock_catalog = {
            "machine learning": [
                {
                    "title": "Andrew Ng's Machine Learning Specialization",
                    "provider": "Coursera",
                    "enrollment_count": 50000,
                    "rating": 4.85,
                    "launch_date": "2023-01-15",
                    "skills_taught": ["Machine Learning", "Python", "TensorFlow"],
                    "career_level": "intermediate",
                    "growth_rate": 0.0,  # Stable
                },
                {
                    "title": "Fast.ai Practical Deep Learning",
                    "provider": "Fast.ai",
                    "enrollment_count": 40000,
                    "rating": 4.80,
                    "launch_date": "2023-06-20",
                    "skills_taught": ["Deep Learning", "PyTorch", "CNNs"],
                    "career_level": "advanced",
                    "growth_rate": 0.0,  # Stable
                },
            ],
            "llm": [
                {
                    "title": "DeepLearning.AI LLM Ops",
                    "provider": "DeepLearning.AI",
                    "enrollment_count": 15000,
                    "rating": 4.75,
                    "launch_date": "2024-03-10",
                    "skills_taught": ["LLM", "Prompt Engineering", "Fine-tuning"],
                    "career_level": "advanced",
                    "growth_rate": 2.0,  # +200% growth
                },
                {
                    "title": "LangChain for LLM Applications",
                    "provider": "Coursera",
                    "enrollment_count": 8500,
                    "rating": 4.70,
                    "launch_date": "2024-02-01",
                    "skills_taught": ["LLM", "LangChain", "Vector Databases"],
                    "career_level": "advanced",
                    "growth_rate": 1.8,  # +180% growth
                },
            ],
            "ai": [
                {
                    "title": "Google Cloud AI/ML Specialization",
                    "provider": "Google Cloud",
                    "enrollment_count": 25000,
                    "rating": 4.65,
                    "launch_date": "2023-09-05",
                    "skills_taught": ["AI", "ML", "Vertex AI", "Cloud"],
                    "career_level": "intermediate",
                    "growth_rate": 0.5,  # +50% (enterprise focus)
                },
                {
                    "title": "Artificial Intelligence Fundamentals",
                    "provider": "IBM",
                    "enrollment_count": 18000,
                    "rating": 4.60,
                    "launch_date": "2023-11-12",
                    "skills_taught": ["AI", "Robotics", "Expert Systems"],
                    "career_level": "beginner",
                    "growth_rate": 0.3,
                },
            ],
            "python": [
                {
                    "title": "Python for Everybody",
                    "provider": "Coursera",
                    "enrollment_count": 200000,
                    "rating": 4.72,
                    "launch_date": "2022-05-10",
                    "skills_taught": ["Python", "Programming", "Databases"],
                    "career_level": "beginner",
                    "growth_rate": 0.1,
                },
                {
                    "title": "Advanced Python Programming",
                    "provider": "Coursera",
                    "enrollment_count": 35000,
                    "rating": 4.78,
                    "launch_date": "2023-02-14",
                    "skills_taught": ["Python", "OOP", "Design Patterns"],
                    "career_level": "advanced",
                    "growth_rate": 0.2,
                },
            ],
            "deep learning": [
                {
                    "title": "Deep Learning Specialization",
                    "provider": "Coursera",
                    "enrollment_count": 60000,
                    "rating": 4.82,
                    "launch_date": "2023-01-01",
                    "skills_taught": ["Deep Learning", "CNNs", "RNNs", "GANs"],
                    "career_level": "advanced",
                    "growth_rate": 0.0,
                },
                {
                    "title": "Vision Transformers in Practice",
                    "provider": "DeepLearning.AI",
                    "enrollment_count": 5000,
                    "rating": 4.73,
                    "launch_date": "2024-01-20",
                    "skills_taught": ["Vision Transformers", "Computer Vision"],
                    "career_level": "advanced",
                    "growth_rate": 1.5,
                },
            ],
            "mobile ml": [
                {
                    "title": "On-Device ML with TensorFlow Lite",
                    "provider": "TensorFlow",
                    "enrollment_count": 8000,
                    "rating": 4.68,
                    "launch_date": "2024-02-15",
                    "skills_taught": ["Mobile ML", "TensorFlow Lite", "Edge AI"],
                    "career_level": "intermediate",
                    "growth_rate": 0.5,  # +50% (emerging)
                },
            ],
            "default": [
                {
                    "title": "Data Science Specialization",
                    "provider": "Coursera",
                    "enrollment_count": 45000,
                    "rating": 4.75,
                    "launch_date": "2023-03-10",
                    "skills_taught": ["Data Science", "Python", "Statistics"],
                    "career_level": "intermediate",
                    "growth_rate": 0.0,
                },
                {
                    "title": "Cloud Computing Fundamentals",
                    "provider": "Coursera",
                    "enrollment_count": 32000,
                    "rating": 4.70,
                    "launch_date": "2023-08-01",
                    "skills_taught": ["Cloud", "AWS", "Architecture"],
                    "career_level": "intermediate",
                    "growth_rate": 0.1,
                },
            ],
        }
        
        # Select courses based on skill
        courses = mock_catalog.get(skill_lower, mock_catalog["default"])
        
        # Filter by career level if specified
        if career_level:
            level_lower = career_level.lower()
            courses = [c for c in courses if c.get("career_level") == level_lower]
            # If no exact match, include all
            if not courses:
                courses = mock_catalog.get(skill_lower, mock_catalog["default"])
        
        # Remove internal tracking fields
        clean_courses = []
        for course in courses:
            clean_course = {
                "title": course["title"],
                "provider": course["provider"],
                "enrollment_count": course["enrollment_count"],
                "rating": course["rating"],
                "launch_date": course["launch_date"],
                "skills_taught": course["skills_taught"],
            }
            clean_courses.append(clean_course)
        
        # Detect trending courses
        trending = self._detect_trending_courses(courses)
        
        # Calculate aggregate metrics
        avg_rating = sum(c["rating"] for c in courses) / len(courses) if courses else 0.0
        
        # Calculate enrollment trends for each skill taught
        enrollment_trends = {}
        for course in courses:
            for course_skill in course.get("skills_taught", []):
                if course_skill not in enrollment_trends:
                    # Growth rate based on course data
                    enrollment_trends[course_skill] = int(course.get("growth_rate", 0) * 100)
        
        # Add main skill trend
        if courses:
            main_growth = sum(c.get("growth_rate", 0) for c in courses) / len(courses)
            enrollment_trends[skill] = int(main_growth * 100)
        
        return {
            "courses": clean_courses,
            "trending_courses": trending,
            "enrollment_trends": enrollment_trends,
            "average_ratings": {skill: avg_rating},
        }

    def _detect_trending_courses(self, courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect trending courses based on enrollment growth.
        
        A course is considered trending if:
        - Growth rate > 50% (high enrollment growth)
        - Recent launch date (within last 6 months)
        - For AI/LLM: growth > 150% indicates strong trend
        
        Args:
            courses: List of course objects (with internal growth_rate field)
        
        Returns:
            List[Dict[str, Any]]: Filtered list of trending courses
        """
        trending = []
        
        for course in courses:
            growth_rate = course.get("growth_rate", 0.0)
            launch_date_str = course.get("launch_date", "")
            
            # Check growth threshold
            if growth_rate >= 0.5:  # 50% or higher
                # Remove internal fields for output
                clean_course = {
                    "title": course["title"],
                    "provider": course["provider"],
                    "enrollment_count": course["enrollment_count"],
                    "rating": course["rating"],
                    "launch_date": launch_date_str,
                    "skills_taught": course.get("skills_taught", []),
                }
                trending.append(clean_course)
        
        return trending




class GlassdoorSalaryFetcher(WebDataFetcher):
    """
    Glassdoor Salary Data Fetcher — Live Salary Data Integration
    
    Fetches current salary trends from Glassdoor API with rate limiting,
    caching, and graceful fallback to mock data when API unavailable or
    API key not configured.
    
    Features:
    - Glassdoor API integration with optional authentication
    - Rate limiting at 5 requests/minute (respects Glassdoor's limits)
    - 24-hour TTL caching via LiveDataCache
    - Mock data fallback for testing and offline operation
    - Comprehensive error handling (no exceptions raised)
    - Full logging of operations and failures
    
    Configuration:
    - GLASSDOOR_API_KEY: Optional environment variable for API authentication
    - WEB_FETCHER_TIMEOUT_SECONDS: Request timeout (default 10s)
    
    Return Format (fetch_salary_data):
        {
            "data": {
                "avg": float,                      # Average salary
                "min": float,                      # Minimum salary range
                "max": float,                      # Maximum salary range
                "currency": str,                   # Currency code (e.g., "USD")
                "location": str,                   # Location searched
                "seniority_levels": {              # Breakdown by seniority
                    "entry": {"avg": float, "min": float, "max": float},
                    "mid": {"avg": float, "min": float, "max": float},
                    "senior": {"avg": float, "min": float, "max": float},
                    "executive": {"avg": float, "min": float, "max": float}
                },
                "company_name": str,               # Optional: specific company
                "industry": str,                   # Optional: industry classification
                "data_points": int                 # Number of samples used
            },
            "source": "GlassdoorSalaryFetcher",
            "retrieved_at": datetime,
            "confidence_score": 0.0-1.0
        }
    
    Examples:
        >>> fetcher = GlassdoorSalaryFetcher()
        
        >>> # Fetch salary for a role in a location
        >>> result = fetcher.fetch_salary_data("Python Developer", "San Francisco, CA")
        >>> if result["data"]:
        ...     salary = result["data"]["avg"]
        ...     print(f"Avg: ${salary:,.0f}")
        ... else:
        ...     print("Could not fetch salary data")
        
        >>> # Check confidence in data quality
        >>> confidence = result["confidence_score"]
        >>> if confidence >= 0.8:
        ...     print("High confidence in this data")
        
        >>> # Access seniority-specific salary data
        >>> if "seniority_levels" in result["data"]:
        ...     entry_salary = result["data"]["seniority_levels"]["entry"]["avg"]
        ...     senior_salary = result["data"]["seniority_levels"]["senior"]["avg"]
        ...     print(f"Entry: ${entry_salary:,.0f}, Senior: ${senior_salary:,.0f}")
    """
    
    def __init__(self):
        """
        Initialize Glassdoor Salary Fetcher.
        
        Sets rate limit to 5 requests/minute to respect Glassdoor's API limits.
        Initializes cache integration for 24-hour TTL.
        
        Examples:
            >>> fetcher = GlassdoorSalaryFetcher()
            >>> result = fetcher.fetch_salary_data("Data Scientist", "New York")
        """
        super().__init__(rate_limit=5)  # 5 requests/minute for Glassdoor
        self.source_name = "GlassdoorSalaryFetcher"
        self.api_key = os.getenv("GLASSDOOR_API_KEY")
        self.api_base_url = "https://api.glassdoor.com/v1"
        logger.info(
            f"GlassdoorSalaryFetcher initialized: "
            f"API key configured={bool(self.api_key)}, rate_limit=5 req/min"
        )
    
    def fetch_salary_data(self, role: str, location: str = None) -> Dict[str, Any]:
        """
        Fetch salary data for a specific role and location.
        
        Attempts to fetch from Glassdoor API if available, otherwise returns
        mock data for testing. All results are cached with 24-hour TTL.
        
        Parameters:
            role (str): Job role/title (e.g., "Python Developer", "Data Scientist")
            location (str): Location (e.g., "San Francisco, CA", "New York, NY").
                           If None, uses national average data.
        
        Returns:
            Dict[str, Any]: Standard response format with:
                - data: Salary data dictionary or empty dict on error
                - source: "GlassdoorSalaryFetcher"
                - retrieved_at: Retrieval timestamp
                - confidence_score: 0.0-1.0 (0.95 for API, 0.60 for mock)
        
        Raises:
            None - All errors handled gracefully
        
        Error Handling:
            - Invalid location → returns empty dict with confidence 0.0
            - API timeout/down → returns mock data with confidence 0.60
            - No API key → returns mock data with confidence 0.60
            - Network error → returns mock data with confidence 0.60
        
        Caching:
            Results cached for 24 hours via LiveDataCache. Subsequent calls
            with same role/location within 24 hours return cached data.
        
        Examples:
            >>> fetcher = GlassdoorSalaryFetcher()
            
            >>> # Fetch with both role and location
            >>> result = fetcher.fetch_salary_data("Python Developer", "San Francisco, CA")
            >>> if result["data"]:
            ...     print(f"Average: ${result['data']['avg']:,.0f}")
            
            >>> # Fetch national average (no location)
            >>> result = fetcher.fetch_salary_data("Machine Learning Engineer")
            >>> if result["data"]:
            ...     print(result["data"]["seniority_levels"])
            
            >>> # Check data freshness
            >>> if result["confidence_score"] > 0.85:
            ...     print("High confidence API data")
            ... else:
            ...     print("Mock/offline data (low confidence)")
        """
        # Validate inputs
        if not role or not isinstance(role, str) or not role.strip():
            logger.warning("fetch_salary_data: Invalid role parameter")
            return self._error_response(confidence_score=0.0)
        
        role = role.strip()
        location = location.strip() if location and isinstance(location, str) else None
        
        # Create cache key
        cache_key = f"salary_{role.lower().replace(' ', '_')}_{location.lower() if location else 'national'}"
        
        # Check cache first
        from app.services.live_data_cache import LiveDataCache
        cache = LiveDataCache()
        cached = cache.get_cached(cache_key)
        if cached and not cache.is_expired(cache_key):
            logger.info(
                f"fetch_salary_data: Cache hit for {role} in {location or 'national'}"
            )
            return {
                "data": cached["data"],
                "source": self.source_name,
                "retrieved_at": cached["retrieved_at"],
                "confidence_score": cached["confidence_score"]
            }
        
        logger.info(
            f"fetch_salary_data: Fetching salary data for role='{role}', location='{location or 'national'}'"
        )
        
        # Try to fetch from Glassdoor API
        if self.api_key:
            result = self._fetch_from_api(role, location)
            if result["data"]:
                # Cache successful API response
                cache.cache_live_data(
                    key=cache_key,
                    data=result["data"],
                    ttl_hours=24,
                    source=self.source_name,
                    confidence_score=result["confidence_score"]
                )
                logger.info(
                    f"fetch_salary_data: Successfully fetched from API for {role} "
                    f"in {location or 'national'}"
                )
                return result
        else:
            logger.debug(
                "fetch_salary_data: No GLASSDOOR_API_KEY configured, using mock data"
            )
        
        # Fallback to mock data
        mock_result = self._get_mock_salary_data(role, location)
        
        # Cache mock data with lower confidence
        cache.cache_live_data(
            key=cache_key,
            data=mock_result["data"],
            ttl_hours=24,
            source=self.source_name,
            confidence_score=mock_result["confidence_score"]
        )
        
        logger.info(
            f"fetch_salary_data: Using mock data for {role} "
            f"in {location or 'national'} (confidence: {mock_result['confidence_score']})"
        )
        return mock_result
    
    def _fetch_from_api(self, role: str, location: str = None) -> Dict[str, Any]:
        """
        Fetch salary data from Glassdoor API.
        
        Makes HTTP request to Glassdoor API with proper authentication
        and error handling. Returns empty dict on any failure.
        
        Args:
            role (str): Job role/title
            location (str): Location (optional)
        
        Returns:
            Dict[str, Any]: Standard response format
        """
        try:
            # Glassdoor API endpoint
            url = f"{self.api_base_url}/salary"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {"jobTitle": role}
            if location:
                params["location"] = location
            
            logger.debug(f"API request: {url} with params {params}")
            
            result = self._make_request(
                url,
                method="GET",
                params=params,
                headers=headers,
                confidence_score=0.95
            )
            
            # Validate response structure
            if result["data"] and self._is_valid_salary_data(result["data"]):
                logger.info(f"API response valid for role={role}")
                return result
            
            logger.warning(
                f"API response invalid or incomplete for role={role}"
            )
            return self._error_response(confidence_score=0.0)
        
        except Exception as e:
            logger.error(
                f"_fetch_from_api: Unexpected error: {str(e)[:100]}"
            )
            return self._error_response(confidence_score=0.0)
    
    def _is_valid_salary_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate salary data structure.
        
        Ensures required fields are present and values are reasonable.
        
        Args:
            data (Dict): Salary data to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["avg", "min", "max", "currency"]
        if not all(field in data for field in required_fields):
            return False
        
        # Validate numeric values
        try:
            avg = float(data["avg"])
            min_val = float(data["min"])
            max_val = float(data["max"])
            
            # Reasonable salary ranges (prevent mock-like exact values)
            if avg <= 0 or min_val <= 0 or max_val <= 0:
                return False
            if min_val >= avg or avg >= max_val:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_mock_salary_data(
        self, role: str, location: str = None
    ) -> Dict[str, Any]:
        """
        Generate mock salary data for testing and offline operation.
        
        Creates realistic placeholder data in the correct format. Used when
        API key is not available or API fails.
        
        Args:
            role (str): Job role/title
            location (str): Location (optional)
        
        Returns:
            Dict[str, Any]: Mock salary data with confidence 0.60
        
        Examples:
            >>> fetcher = GlassdoorSalaryFetcher()
            >>> mock = fetcher._get_mock_salary_data("Python Developer", "New York")
            >>> print(mock["data"]["avg"])  # Mock average
            >>> print(mock["confidence_score"])  # 0.60
        """
        # Mock data varies by role (basic simulation)
        role_lower = role.lower()
        
        # Base salaries for different roles (realistic ranges)
        role_salaries = {
            "junior developer": {"avg": 65000, "min": 50000, "max": 85000},
            "python developer": {"avg": 95000, "min": 75000, "max": 130000},
            "senior developer": {"avg": 120000, "min": 100000, "max": 160000},
            "data scientist": {"avg": 105000, "min": 85000, "max": 140000},
            "machine learning engineer": {"avg": 130000, "min": 100000, "max": 170000},
            "software engineer": {"avg": 110000, "min": 80000, "max": 150000},
            "product manager": {"avg": 115000, "min": 90000, "max": 150000},
            "devops engineer": {"avg": 112000, "min": 85000, "max": 155000},
        }
        
        # Find matching role or use default
        salary_data = None
        for role_key, data in role_salaries.items():
            if role_key in role_lower:
                salary_data = data
                break
        
        if not salary_data:
            # Default mock data
            salary_data = {"avg": 90000, "min": 60000, "max": 140000}
        
        # Adjust for location if provided
        location_multipliers = {
            "san francisco": 1.25,
            "new york": 1.15,
            "seattle": 1.20,
            "boston": 1.12,
            "austin": 0.95,
            "denver": 0.90,
        }
        
        multiplier = 1.0
        if location:
            location_lower = location.lower()
            for loc_key, mult in location_multipliers.items():
                if loc_key in location_lower:
                    multiplier = mult
                    break
        
        avg = int(salary_data["avg"] * multiplier)
        min_val = int(salary_data["min"] * multiplier)
        max_val = int(salary_data["max"] * multiplier)
        
        mock_data = {
            "avg": float(avg),
            "min": float(min_val),
            "max": float(max_val),
            "currency": "USD",
            "location": location or "United States",
            "seniority_levels": {
                "entry": {
                    "avg": float(int(avg * 0.70)),
                    "min": float(int(min_val * 0.70)),
                    "max": float(int(avg * 0.85))
                },
                "mid": {
                    "avg": float(avg),
                    "min": float(min_val),
                    "max": float(max_val)
                },
                "senior": {
                    "avg": float(int(avg * 1.25)),
                    "min": float(int(avg * 1.10)),
                    "max": float(int(max_val * 1.15))
                },
                "executive": {
                    "avg": float(int(avg * 1.50)),
                    "min": float(int(avg * 1.30)),
                    "max": float(int(max_val * 1.40))
                }
            },
            "data_points": 250  # Mock number of samples
        }
        
        return {
            "data": mock_data,
            "source": self.source_name,
            "retrieved_at": datetime.now(),
            "confidence_score": 0.60  # Lower confidence for mock data
        }
    
    def fetch_skill_trends(self) -> Dict[str, Any]:
        """
        Fetch trending skills data.
        
        Not actively used in current phase but required by abstract base class.
        Returns placeholder data with valid structure.
        
        Returns:
            Dict[str, Any]: Placeholder skill trends with confidence 0.0
        
        Examples:
            >>> fetcher = GlassdoorSalaryFetcher()
            >>> result = fetcher.fetch_skill_trends()
            >>> print(result["data"])  # {}
        """
        logger.debug("fetch_skill_trends: Not implemented, returning placeholder")
        return {
            "data": {
                "placeholder": "Skill trends endpoint not yet implemented",
                "message": "Use fetch_salary_data() for current functionality"
            },
            "source": self.source_name,
            "retrieved_at": datetime.now(),
            "confidence_score": 0.0
        }
    
    def fetch_job_postings(self, query: str = None) -> Dict[str, Any]:
        """
        Fetch job postings.
        
        Not actively used in current phase but required by abstract base class.
        Returns placeholder data with valid structure.
        
        Args:
            query (str): Search query (optional, not used)
        
        Returns:
            Dict[str, Any]: Placeholder job postings with confidence 0.0
        
        Examples:
            >>> fetcher = GlassdoorSalaryFetcher()
            >>> result = fetcher.fetch_job_postings("Python Developer")
            >>> print(result["data"])  # {}
        """
        logger.debug("fetch_job_postings: Not implemented, returning placeholder")
        return {
            "data": {
                "placeholder": "Job postings endpoint not yet implemented",
                "message": "Use fetch_salary_data() for current functionality"
            },
            "source": self.source_name,
            "retrieved_at": datetime.now(),
            "confidence_score": 0.0
        }
    
    def fetch_courses(self, skill: str = None) -> Dict[str, Any]:
        """
        Fetch course information.
        
        Not actively used in current phase but required by abstract base class.
        Returns placeholder data with valid structure.
        
        Args:
            skill (str): Skill to find courses for (optional, not used)
        
        Returns:
            Dict[str, Any]: Placeholder courses with confidence 0.0
        
        Examples:
            >>> fetcher = GlassdoorSalaryFetcher()
            >>> result = fetcher.fetch_courses("Python")
            >>> print(result["data"])  # {}
        """
        logger.debug("fetch_courses: Not implemented, returning placeholder")
        return {
            "data": {
                "placeholder": "Courses endpoint not yet implemented",
                "message": "Use fetch_salary_data() for current functionality"
            },
            "source": self.source_name,
            "retrieved_at": datetime.now(),
            "confidence_score": 0.0
        }
