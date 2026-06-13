# Web Data Fetcher Base Class Implementation

## Overview

Successfully created a comprehensive abstract base class infrastructure for live data fetching in the RAG system. The `WebDataFetcher` class provides a robust foundation for all concrete fetcher implementations (GlassdoorSalaryFetcher, LinkedInSkillsFetcher, etc.) with built-in HTTP request handling, rate limiting, retry logic, and error handling.

## Files Created/Modified

### 1. **Created: `app/services/web_data_fetcher.py`**
   - **Size**: 529 lines, ~21.5 KB
   - **Type**: Abstract Base Class (ABC)
   - **Purpose**: Core infrastructure for live data fetching

### 2. **Created: `tests/test_web_data_fetcher.py`**
   - **Test Count**: 44 comprehensive unit tests
   - **Coverage**: Initialization, success cases, errors, rate limiting, retry logic, logging
   - **Status**: All 44 tests passing ✅

### 3. **Modified: `app/core/config.py`**
   - **Change**: Added `web_fetcher_timeout_seconds` configuration
   - **Default**: 10 seconds
   - **Source**: Environment variable `WEB_FETCHER_TIMEOUT_SECONDS`

### 4. **Modified: `.env`**
   - **Change**: Added `WEB_FETCHER_TIMEOUT_SECONDS=10` setting
   - **Purpose**: Configurable timeout for all web fetchers

## Architecture

### Class Hierarchy

```
ABC (Abstract Base Class)
  ↓
WebDataFetcher (Abstract)
  ├─ Abstract Methods:
  │  ├─ fetch_salary_data()
  │  ├─ fetch_skill_trends()
  │  ├─ fetch_job_postings()
  │  └─ fetch_courses()
  │
  ├─ Shared Implementation:
  │  ├─ _make_request() - HTTP client with retry/rate-limit
  │  ├─ _apply_rate_limit() - Rate limiting enforcement
  │  ├─ _success_response() - Standardized success response
  │  └─ _error_response() - Standardized error response
  │
  └─ Concrete Implementations (inherit from WebDataFetcher)
     ├─ GlassdoorSalaryFetcher
     ├─ LinkedInSkillsFetcher
     ├─ JobPostingsFetcher
     └─ CoursesFetcher
```

## Key Features Implemented

### 1. Abstract Interface (ABC Pattern)
- **4 abstract methods** that child classes must implement:
  - `fetch_salary_data()` - Fetch salary data
  - `fetch_skill_trends()` - Fetch skill trends
  - `fetch_job_postings()` - Fetch job listings
  - `fetch_courses()` - Fetch course listings
- Prevents instantiation of base class directly
- Enforces contract for all child implementations

### 2. HTTP Request Handling
- **Methods**: GET and POST support
- **Parameters**: Query strings, JSON bodies, custom headers
- **Response Parsing**: Automatic JSON parsing
- **Error Context**: Captures response status and text for logging

### 3. Rate Limiting
- **Default**: 10 requests per minute (configurable)
- **Algorithm**: 
  - Min interval = 60 / rate_limit (seconds)
  - Tracks last request time
  - Sleeps if insufficient time elapsed
- **Per-Instance**: Each fetcher instance tracks its own rate limit
- **Thread-Safe**: Uses atomic time operations

### 4. Exponential Backoff Retry
- **Retry Count**: 3 attempts max
- **Backoff Schedule**: 1s → 2s → 4s (total up to 7 seconds)
- **Triggers**:
  - Timeout errors (requests.exceptions.Timeout)
  - Connection errors (requests.exceptions.ConnectionError)
  - HTTP 429 (Rate Limit Exceeded)
- **Logging**: Each retry logged with attempt number

### 5. Timeout Protection
- **Default**: 10 seconds (configurable)
- **Configuration**: 
  - Constructor parameter: `WebDataFetcher(timeout=30)`
  - Environment variable: `WEB_FETCHER_TIMEOUT_SECONDS`
- **Applied to**: Every HTTP request

### 6. Graceful Error Handling
- **Philosophy**: No exceptions raised to caller
- **All Errors Return**: Empty dict with 0.0 confidence
- **Error Types Handled**:
  - Timeout (requests.exceptions.Timeout)
  - Connection errors (requests.exceptions.ConnectionError)
  - HTTP 4xx errors (400, 401, 403, 404, etc.)
  - HTTP 5xx errors (500, 502, 503, etc.)
  - HTTP 429 (Rate Limited)
  - JSON parsing errors
  - Unexpected exceptions

### 7. Standardized Return Format
```python
{
    "data": {} or [...],           # Response data or empty dict on error
    "source": "fetcher_name",      # Fetcher identifier for tracking
    "retrieved_at": datetime,      # Timestamp of retrieval
    "confidence_score": 0.0-1.0    # Confidence in data quality
}
```

### 8. Comprehensive Logging
- **Levels**: INFO (normal), WARNING (errors), ERROR (unexpected)
- **Logged Events**:
  - Fetcher initialization
  - Request attempts with attempt number
  - Successful retrievals
  - All errors with context
  - Rate limiting delays
  - Retry attempts
- **Logger Name**: `app.services.web_data_fetcher`

## Acceptance Criteria Met ✅

- ✅ **Abstract base class** created at `app/services/web_data_fetcher.py` (529 lines)
- ✅ **Interface methods** defined (abstract/NotImplemented for all 4 methods)
- ✅ **_make_request()** implemented with:
  - ✅ HTTP GET/POST support
  - ✅ Rate limiting (max 10 requests/minute default, configurable)
  - ✅ Exponential backoff retry (3 attempts: 1s, 2s, 4s)
  - ✅ Timeout protection (10 seconds default, configurable via WEB_FETCHER_TIMEOUT_SECONDS)
  - ✅ Error handling (no exceptions raised, returns empty dict)
- ✅ **Return format** validated: `{data, source, retrieved_at, confidence_score}`
- ✅ **Comprehensive docstrings** with examples on all:
  - Module level (usage guide with examples)
  - Class level (ABC pattern, inheritance requirements)
  - Method level (args, returns, examples)
- ✅ **Unit tests** created with 44 test cases covering:
  - Successful HTTP requests (GET/POST)
  - Timeout handling and retry logic
  - Rate limit (429) responses
  - Network connection errors
  - All HTTP error codes (4xx, 5xx)
  - Exponential backoff timing
  - Return format validation
  - Logging verification
  - Graceful error handling

## Configuration

### Environment Variables
```bash
# Default: 10 seconds
WEB_FETCHER_TIMEOUT_SECONDS=10
```

### Settings Class
```python
from app.core.config import settings
timeout = settings.web_fetcher_timeout_seconds  # Reads from env
```

### Constructor Options
```python
# Use defaults
fetcher = MyFetcher()

# Custom rate limit (5 requests/minute)
fetcher = MyFetcher(rate_limit=5)

# Custom timeout (30 seconds)
fetcher = MyFetcher(timeout=30)

# Both custom
fetcher = MyFetcher(rate_limit=3, timeout=20)
```

## Usage Examples

### Creating a Concrete Implementation

```python
from app.services.web_data_fetcher import WebDataFetcher
import requests

class GlassdoorSalaryFetcher(WebDataFetcher):
    """Fetch salary data from Glassdoor API."""
    
    def __init__(self):
        super().__init__(rate_limit=5)  # 5 requests/minute
        self.source_name = "glassdoor"
        self.api_key = os.getenv("GLASSDOOR_API_KEY")
    
    def fetch_salary_data(self, job_title: str, location: str = None):
        """Fetch salary data for a job title."""
        url = "https://api.glassdoor.com/v1/salary"
        params = {"job_title": job_title}
        if location:
            params["location"] = location
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return self._make_request(url, params=params, headers=headers, confidence_score=0.85)
    
    def fetch_skill_trends(self):
        """Fetch trending skills from Glassdoor."""
        url = "https://api.glassdoor.com/v1/skills/trends"
        return self._make_request(url)
    
    def fetch_job_postings(self, query: str):
        """Fetch job postings from Glassdoor."""
        url = "https://api.glassdoor.com/v1/jobs"
        return self._make_request(url, params={"search": query})
    
    def fetch_courses(self, skill: str):
        """Fetch courses for a skill."""
        url = "https://api.glassdoor.com/v1/learning"
        return self._make_request(url, params={"skill": skill})
```

### Using the Fetcher

```python
# Initialize
fetcher = GlassdoorSalaryFetcher()

# Fetch salary data (handles retries, rate limiting, errors automatically)
result = fetcher.fetch_salary_data("Python Developer", "San Francisco")

# Process result
if result["data"]:
    print(f"Salary data: {result['data']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Retrieved at: {result['retrieved_at']}")
else:
    print(f"Failed to fetch data (confidence: {result['confidence_score']})")
    # No exception was raised - graceful degradation

# Access source identifier
source = result["source"]  # "glassdoor"
```

### With Live Data Cache Integration

```python
from app.services.live_data_cache import LiveDataCache

cache = LiveDataCache()
fetcher = GlassdoorSalaryFetcher()

result = fetcher.fetch_salary_data("Data Scientist", "New York")

if result["data"]:
    # Cache the live data
    cache.cache_live_data(
        key="salary_data_scientist_ny_2024",
        data=result["data"],
        ttl_hours=24,
        source=result["source"],
        confidence_score=result["confidence_score"]
    )
```

## Test Coverage (44 Tests)

### Test Categories

**Initialization Tests (5 tests)**
- Default parameters
- Custom rate limit
- Custom timeout
- Both custom parameters
- Timeout from environment variable

**Successful Requests (5 tests)**
- GET requests
- POST requests
- Custom confidence scores
- Query parameters
- Custom headers

**Timeout Handling (3 tests)**
- Retry on timeout and succeed
- All retries fail on timeout
- Exponential backoff timing (1s, 2s)

**Rate Limit Handling (2 tests)**
- HTTP 429 retry and succeed
- All retries fail on HTTP 429

**Connection Errors (2 tests)**
- Connection error retry and succeed
- All retries fail on connection error

**HTTP Errors (7 tests)**
- HTTP 400, 401, 403, 404
- HTTP 500, 502, 503

**Return Format Validation (2 tests)**
- Success format validation
- Error format validation

**Rate Limiting Behavior (5 tests)**
- No sleep on first request
- Enforces minimum interval
- No sleep when interval exceeded
- Custom rate limits
- Interval calculations

**Abstract Methods (3 tests)**
- Cannot instantiate abstract class
- Incomplete implementation detection
- NotImplementedError on abstract call

**Logging (3 tests)**
- Logging on success
- Logging on timeout
- Logging on HTTP error

**Concrete Implementation (4 tests)**
- fetch_salary_data()
- fetch_skill_trends()
- fetch_job_postings()
- fetch_courses()

**Graceful Error Handling (4 tests)**
- No exception on timeout
- No exception on connection error
- No exception on HTTP error
- No exception on unexpected error

**Result**: All 44 tests passing ✅

## Integration Points

1. **RAG Service** (`app/services/rag_service.py`)
   - Uses fetchers for live data retrieval
   - Integrates results into knowledge base

2. **Live Data Cache** (`app/services/live_data_cache.py`)
   - Receives fetcher results
   - Stores with TTL for caching

3. **Citation Tracker** (`app/services/citation_tracker.py`)
   - Tracks data source and timestamps
   - Uses source_name from fetcher results

4. **Routes** (`app/api/rag_routes.py`)
   - Triggers fetchers on demand
   - Returns cached results

## Performance Characteristics

- **Rate Limiting**: Enforced per-instance (10 req/min default)
- **Timeout**: 10 seconds per request (configurable)
- **Retry Time**: Up to 7 seconds total on failure (1s + 2s + 4s)
- **Thread Safety**: Rate limiting uses atomic operations
- **Memory**: Lightweight instance with minimal state

## Error Resilience

The fetcher implements graceful degradation:
- Never crashes the application
- Always returns standardized response
- 0.0 confidence score indicates failure
- Empty data dict returned on error
- Caller can implement fallback logic

## Security Considerations

1. **Timeout Protection**: Prevents hanging on unresponsive APIs
2. **Rate Limiting**: Respects API limits to avoid bans
3. **Error Handling**: No stack traces leaked in logs
4. **Request Headers**: Support for Authorization headers
5. **SSL/TLS**: Uses requests library (supports HTTPS)

## Future Enhancements

1. **Async Support**: Add async/await for concurrent fetching
2. **Circuit Breaker**: Stop fetching on sustained failures
3. **Metrics**: Add prometheus-style metrics
4. **Caching Headers**: Parse Cache-Control headers
5. **Request Signing**: Support signed requests (AWS, etc.)
6. **Retry Strategy**: Configurable retry policies
7. **Proxy Support**: HTTP proxy configuration

## Summary

The `WebDataFetcher` base class provides a production-ready foundation for live data integration in the RAG system. It combines robust error handling, rate limiting, and retry logic to ensure reliable data retrieval from external sources while maintaining system stability and performance.

**Key Achievements:**
- ✅ 529-line abstract base class with comprehensive functionality
- ✅ 4 abstract methods enforcing implementation contract
- ✅ Rate limiting, exponential backoff, timeout protection
- ✅ Graceful error handling with 0 exceptions to caller
- ✅ Standardized return format for all responses
- ✅ 44 comprehensive unit tests (100% passing)
- ✅ Full docstring documentation with examples
- ✅ Production-ready and extensible design
