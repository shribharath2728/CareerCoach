# RAG Hallucination with Live Data Integration — Implementation Tasks

## Task Execution Strategy

This task DAG is organized into 5 implementation phases with parallel execution where possible:
- **Phase 1**: Data caching and citation infrastructure (foundation - must complete first)
- **Phase 2**: Web data fetchers (can be built in parallel)
- **Phase 3**: Azure Foundry connector (depends on Phase 1)
- **Phase 4**: Enhanced RAG service (depends on Phases 1, 2, 3)
- **Phase 5**: Integration and testing (final phase)

### Task Dependency Graph
```
Phase 1: Infrastructure (Tasks 1.1-1.3)
    ↓
Phase 2: Web Fetchers (Tasks 2.1-2.5) [PARALLEL]
Phase 3: Foundry Connector (Task 3.1)   [PARALLEL]
    ↓
Phase 4: Enhanced RAG (Tasks 4.1-4.4)
    ↓
Phase 5: Integration (Tasks 5.1-5.3)
```

---

## Phase 1: Data Caching & Citation Infrastructure

### Task 1.1: Create live_data_cache Module

**ID**: task-1-1  
**Status**: not_started  
**Depends on**: none  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `app/services/live_data_cache.py` module created with `LiveDataCache` class
- Methods implemented: `cache_live_data(key, data, ttl_hours, source, confidence_score)`, `get_cached(key)`, `is_expired(key)`, `clear_expired()`, `get_all_for_source(source)`
- TTL-based expiration logic working (compares `retrieved_at + ttl_hours` against current time)
- Clean expired entries on `clear_expired()` call
- Error handling for None values and invalid keys
- Comprehensive docstrings for public methods
- _Requirements: 2.1, 2.3, 2.5, 2.6_

**Files to create/modify**:
- Create: `app/services/live_data_cache.py` (150-200 lines)
- Add to: `app/services/__init__.py` (import statement)

**Verification**: 
- Unit test file creates instance, caches data with TTL, retrieves valid data, returns None for expired entries
- Test edge cases: None keys, zero TTL, negative TTL (should error), concurrent access

**Subtasks**:
- [ ] 1.1a - Implement `LiveDataCache` class with cache dictionary
- [ ] 1.1b - Implement TTL expiration logic
- [ ] 1.1c - Add error handling and validation
- [ ] 1.1d - Write unit tests (test_live_data_cache.py)

---

### Task 1.2: Create citation_tracker Module

**ID**: task-1-2  
**Status**: not_started  
**Depends on**: task-1-1  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `app/services/citation_tracker.py` module created with `Citation` dataclass and `CitationManager` class
- `Citation` dataclass includes: `source_url: Optional[str]`, `retrieval_date: Optional[datetime]`, `confidence_score: Optional[float]`, `data_age_hours: Optional[int]`, `source: str`
- `CitationManager` methods: `create_citation(source, source_url, confidence_score)`, `attach_citation_to_chunk(chunk, citation)`, `add_citations_to_chunks(chunks, citation)`
- Citation metadata correctly injected into chunk dictionaries
- No modification to chunk structure beyond adding optional citation fields (backward compatible)
- Comprehensive docstrings and examples
- _Requirements: 2.6, 3.4_

**Files to create/modify**:
- Create: `app/services/citation_tracker.py` (100-150 lines)
- Add to: `app/services/__init__.py` (import statement)

**Verification**:
- Unit tests verify citation creation, attachment to chunks, and serialization
- Test that original chunk fields remain unchanged
- Test citation presence/absence scenarios

**Subtasks**:
- [ ] 1.2a - Define `Citation` dataclass with all fields
- [ ] 1.2b - Implement `CitationManager` class
- [ ] 1.2c - Implement citation injection logic
- [ ] 1.2d - Write unit tests (test_citation_tracker.py)

---

### Task 1.3: Create ORM Models and Database Migrations

**ID**: task-1-3  
**Status**: not_started  
**Depends on**: none  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- ORM models `LiveDataCache` and `LiveDataSources` added to `app/models/rag_knowledge.py`
- `LiveDataCache` model includes columns: id, key (unique), data (JSON), source, retrieved_at (indexed), ttl_hours, confidence_score, created_at, updated_at
- `LiveDataSources` model includes columns: id, name, endpoint, api_key_env, enabled, rate_limit_per_minute, created_at
- Database migration SQL created in `app/db/migrations/` (or inline in ensure_schema.py)
- Migration is non-breaking (only adds new tables, no column deletions/renames)
- Models tested with SQLAlchemy session
- _Requirements: 3.1, 3.2_

**Files to create/modify**:
- Modify: `app/models/rag_knowledge.py` (add ORM models)
- Modify: `app/db/ensure_schema.py` or create migration file
- Create: `tests/test_models_rag_knowledge.py` (if needed)

**Verification**:
- Create test database session, create tables, insert/query records successfully
- Verify schema matches design specification
- Ensure backward compatibility with existing RAG knowledge tables

**Subtasks**:
- [ ] 1.3a - Add ORM models to rag_knowledge.py
- [ ] 1.3b - Create database migration/schema update
- [ ] 1.3c - Test model creation and queries
- [ ] 1.3d - Verify backward compatibility

---

## Phase 2: Web Data Fetcher & API Wrappers

### Task 2.1: Create web_data_fetcher Base Class

**ID**: task-2-1  
**Status**: not_started  
**Depends on**: task-1-1  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `app/services/web_data_fetcher.py` module created with abstract `WebDataFetcher` base class
- Base class defines interface: `fetch_salary_data()`, `fetch_skill_trends()`, `fetch_job_postings()`, `fetch_courses()`
- Each method signature specified with return type `Dict[str, Any]` containing keys: `data`, `source`, `retrieved_at`, `confidence_score`
- Base class includes: `_make_request(url, params, timeout, retry_count)` with rate limiting and exponential backoff
- Error handling: timeouts return empty dict with error flag, 429 (rate limit) triggers backoff
- Request timeout: 10 seconds default, configurable via env variable `WEB_FETCHER_TIMEOUT_SECONDS`
- Retry logic: max 3 attempts with exponential backoff (1s, 2s, 4s)
- Comprehensive docstrings and usage examples
- _Requirements: 2.1, 2.2, 2.3, 2.4_

**Files to create/modify**:
- Create: `app/services/web_data_fetcher.py` (200-250 lines)
- Modify: `app/services/__init__.py` (import)
- Modify: `.env` file (add optional `WEB_FETCHER_TIMEOUT_SECONDS=10`)

**Verification**:
- Unit tests with mocked HTTP requests (pytest + responses library)
- Test successful request, timeout handling, rate limit retry, all exceptions
- Test backoff logic with mock sleep

**Subtasks**:
- [ ] 2.1a - Define abstract `WebDataFetcher` base class
- [ ] 2.1b - Implement `_make_request()` with rate limiting
- [ ] 2.1c - Implement retry and backoff logic
- [ ] 2.1d - Write unit tests (test_web_data_fetcher.py)

---

### Task 2.2: Implement GlassdoorSalaryFetcher

**ID**: task-2-2  
**Status**: not_started  
**Depends on**: task-2-1  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `GlassdoorSalaryFetcher` class created extending `WebDataFetcher`
- `fetch_salary_data(role: str, location: str) -> Dict` method implemented
- Returns salary ranges with fields: `base_salary_min`, `base_salary_max`, `currency`, `location`, `seniority_levels`, `source_url`, `retrieved_at`
- Uses Glassdoor API (if available via `GLASSDOOR_API_KEY`) or web scraping fallback with user-agent
- Rate limiting: max 5 requests/minute (respects Glassdoor limits)
- Error handling: invalid location → empty result, API down → empty result (no exception)
- Caching: results cached via `LiveDataCache` with TTL of 24 hours
- Returns mock data for testing (when API key not configured)
- Comprehensive error logging
- _Requirements: 2.1, 2.2_

**Files to create/modify**:
- Modify: `app/services/web_data_fetcher.py` (add GlassdoorSalaryFetcher class)
- Modify: `.env` (add `GLASSDOOR_API_KEY=` optional parameter)

**Verification**:
- Unit tests with mocked Glassdoor API responses
- Test valid role/location, invalid role, API down scenarios
- Test caching and cache hit/miss
- Test response format matches expected structure

**Subtasks**:
- [ ] 2.2a - Implement `GlassdoorSalaryFetcher` class
- [ ] 2.2b - Implement salary data parsing
- [ ] 2.2c - Add caching integration
- [ ] 2.2d - Write unit tests (test_glassdoor_fetcher.py)

---

### Task 2.3: Implement LinkedInSkillsFetcher

**ID**: task-2-3  
**Status**: not_started  
**Depends on**: task-2-1  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `LinkedInSkillsFetcher` class created extending `WebDataFetcher`
- `fetch_skill_trends(role: str, experience_level: str) -> Dict` method implemented
- Returns trending skills with fields: `top_skills`, `trending_growth_percent`, `job_postings_with_skill`, `seniority_breakdown`, `retrieved_at`, `source_url`
- Fetches from LinkedIn Jobs API (if available) or scrapes public job data as fallback
- Rate limiting: max 10 requests/minute
- Error handling: graceful fallback, empty results if unavailable
- Caching: 24-hour TTL
- Returns realistic 2024-2025 skill trends (Python, PyTorch, LangChain, LlamaIndex, etc.)
- _Requirements: 2.2, 2.3_

**Files to create/modify**:
- Modify: `app/services/web_data_fetcher.py` (add LinkedInSkillsFetcher class)
- Modify: `.env` (add `LINKEDIN_API_KEY=` optional parameter)

**Verification**:
- Unit tests with mocked LinkedIn API
- Test valid/invalid roles, seniority levels
- Test caching behavior
- Test response includes trending skills and growth percentages

**Subtasks**:
- [ ] 2.3a - Implement `LinkedInSkillsFetcher` class
- [ ] 2.3b - Implement skill trend parsing
- [ ] 2.3c - Add caching integration
- [ ] 2.3d - Write unit tests (test_linkedin_fetcher.py)

---

### Task 2.4: Implement IndeedJobFetcher

**ID**: task-2-4  
**Status**: not_started  
**Depends on**: task-2-1  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `IndeedJobFetcher` class created extending `WebDataFetcher`
- `fetch_job_postings(role: str, location: str, days_posted: int) -> Dict` method implemented
- Returns job postings with fields: `total_postings`, `active_hiring_companies`, `required_skills_distribution`, `salary_range_from_postings`, `retrieved_at`
- Filters postings by `days_posted` (default: last 30 days)
- Rate limiting: max 5 requests/minute
- Caching: 24-hour TTL
- Error handling: graceful fallback
- Returns aggregated data (not individual postings) for privacy
- _Requirements: 2.3_

**Files to create/modify**:
- Modify: `app/services/web_data_fetcher.py` (add IndeedJobFetcher class)
- Modify: `.env` (add `INDEED_API_KEY=` optional parameter)

**Verification**:
- Unit tests with mocked Indeed API
- Test date filtering, location filtering
- Test aggregation logic (totals, distributions)
- Test caching

**Subtasks**:
- [ ] 2.4a - Implement `IndeedJobFetcher` class
- [ ] 2.4b - Implement job postings aggregation
- [ ] 2.4c - Add caching integration
- [ ] 2.4d - Write unit tests (test_indeed_fetcher.py)

---

### Task 2.5: Implement CourseraCourseFetcher

**ID**: task-2-5  
**Status**: not_started  
**Depends on**: task-2-1  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- `CourseraCourseFetcher` class created extending `WebDataFetcher`
- `fetch_courses(skill: str, career_level: str) -> Dict` method implemented
- Returns course data with fields: `courses`, `trending_courses`, `enrollment_trends`, `average_ratings`, `retrieved_at`
- Each course includes: title, provider, enrollment_count, rating, launch_date, skills_taught
- Fetches from Coursera API or scrapes public catalog as fallback
- Rate limiting: max 10 requests/minute
- Caching: 24-hour TTL
- Error handling: graceful fallback
- Returns trending courses (high recent enrollment growth)
- _Requirements: 2.4_

**Files to create/modify**:
- Modify: `app/services/web_data_fetcher.py` (add CourseraCourseFetcher class)
- Modify: `.env` (add `COURSERA_API_KEY=` optional parameter)

**Verification**:
- Unit tests with mocked Coursera API
- Test skill/career level filtering
- Test trending course detection
- Test caching

**Subtasks**:
- [ ] 2.5a - Implement `CourseraCourseFetcher` class
- [ ] 2.5b - Implement course data aggregation
- [ ] 2.5c - Implement trending detection
- [ ] 2.5d - Write unit tests (test_coursera_fetcher.py)

---

## Phase 3: Azure Foundry Connector

### Task 3.1: Create foundry_iq_connector Module

**ID**: task-3-1  
**Status**: not_started  
**Depends on**: task-1-1  
**Time estimate**: 3 hours  
**Acceptance Criteria**:
- `app/services/foundry_iq_connector.py` module created with `FoundryIQConnector` class
- `query_foundry_knowledge(query: str, domain: str) -> Dict` method implemented
- Method calls Azure Foundry API endpoint with proper authentication
- Timeout: 5 seconds (configurable via `FOUNDRY_API_TIMEOUT_SECONDS`)
- Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
- Authentication: uses Azure AD token from env variables (`AZURE_FOUNDRY_TENANT_ID`, `AZURE_FOUNDRY_CLIENT_ID`, `AZURE_FOUNDRY_CLIENT_SECRET`)
- Token refresh: automatic when expired
- Response parsing: converts Foundry API response to standard chunk format with `source="foundry_iq"`
- Error handling: timeouts and auth errors return empty list, no exceptions raised
- Fallback: if Foundry unavailable, returns empty list (caller uses fallback strategy)
- Response includes citation metadata: source_url (Foundry endpoint), retrieval_date, confidence_score
- Comprehensive error logging
- _Requirements: 2.1, 2.3_

**Files to create/modify**:
- Create: `app/services/foundry_iq_connector.py` (250-300 lines)
- Modify: `app/services/__init__.py` (import)
- Modify: `.env` (add Azure Foundry config parameters)

**Verification**:
- Unit tests with mocked Azure API responses
- Test successful query, timeout handling, auth token refresh, all error scenarios
- Test response format conversion to standard chunk format
- Test caching of results (30-min TTL for Foundry)

**Subtasks**:
- [ ] 3.1a - Implement `FoundryIQConnector` class with auth
- [ ] 3.1b - Implement Foundry API query method
- [ ] 3.1c - Implement retry and backoff logic
- [ ] 3.1d - Implement response parsing and citation injection
- [ ] 3.1e - Write unit tests (test_foundry_connector.py)

---

## Phase 4: Enhanced RAG Service

### Task 4.1: Add Query Type Detection to rag_service

**ID**: task-4-1  
**Status**: not_started  
**Depends on**: task-1-1, task-1-2  
**Time estimate**: 1.5 hours  
**Acceptance Criteria**:
- Function `_detect_query_type(query: str) -> str` added to `rag_service.py`
- Returns one of: `"salary_inquiry"`, `"skill_demand"`, `"job_market"`, `"course_recommendation"`, `"general"`
- Detection logic uses keyword matching:
  - Salary: keywords like "salary", "earn", "pay", "compensation", "lpa", "salary range"
  - Skills: keywords like "trending", "demand", "skill", "technologies", "tools", "requirements"
  - Jobs: keywords like "hiring", "company", "job", "opportunity", "companies", "recruiting"
  - Courses: keywords like "course", "learn", "certification", "training", "platform"
  - Fallback to `"general"` if no keywords match
- Case-insensitive matching
- Returns highest-priority match if multiple keywords match
- Comprehensive docstring with examples
- _Requirements: 2.1, 2.2_

**Files to create/modify**:
- Modify: `app/services/rag_service.py` (add _detect_query_type function)

**Verification**:
- Unit tests with diverse query examples
- Test each query type with multiple keyword variations
- Test ambiguous queries (fallback to general)
- Test edge cases (empty string, special characters)

**Subtasks**:
- [ ] 4.1a - Implement query type detection logic
- [ ] 4.1b - Define keyword mappings
- [ ] 4.1c - Write unit tests (test_query_type_detection.py)

---

### Task 4.2: Implement Live Data Fetching Router

**ID**: task-4-2  
**Status**: not_started  
**Depends on**: task-4-1, task-2-2, task-2-3, task-2-4, task-2-5  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- Function `_fetch_live_data_for_query_type(query_type: str, query: str) -> List[Dict]` added to `rag_service.py`
- Routes query to appropriate fetcher:
  - `"salary_inquiry"` → `GlassdoorSalaryFetcher.fetch_salary_data(role, location)`
  - `"skill_demand"` → `LinkedInSkillsFetcher.fetch_skill_trends(role, experience_level)`
  - `"job_market"` → `IndeedJobFetcher.fetch_job_postings(role, location, days_posted=30)`
  - `"course_recommendation"` → `CourseraCourseFetcher.fetch_courses(skill, career_level)`
  - `"general"` → returns empty list (no live data needed)
- Parses query to extract parameters (role, location, skill) using simple keyword extraction
- Handles fetcher errors gracefully: catches exceptions, logs errors, returns empty list
- Adds citation metadata to all results
- Returns list of chunk dicts in standard format
- _Requirements: 2.1, 2.2, 2.3, 2.4_

**Files to create/modify**:
- Modify: `app/services/rag_service.py` (add _fetch_live_data_for_query_type function)

**Verification**:
- Unit tests with mocked fetchers
- Test each query type routing correctly
- Test parameter extraction
- Test error handling (fetcher down, invalid params)
- Test citation attachment

**Subtasks**:
- [ ] 4.2a - Implement fetcher routing logic
- [ ] 4.2b - Implement query parameter extraction
- [ ] 4.2c - Implement error handling
- [ ] 4.2d - Write unit tests (test_live_data_routing.py)

---

### Task 4.3: Implement Live and Static Data Merging

**ID**: task-4-3  
**Status**: not_started  
**Depends on**: task-4-1, task-4-2  
**Time estimate**: 2.5 hours  
**Acceptance Criteria**:
- Function `_merge_live_and_static(live_chunks: List, static_chunks: List, top_k: int) -> List` added to `rag_service.py`
- Ranking logic:
  - Live data (< 24 hours old) ranks highest
  - Cached live data (24-72 hours old) ranks medium
  - Static knowledge (evergreen content) ranks lowest
  - Within same age tier, rank by relevance score
- Deduplication: removes duplicate chunks by content hash (prevent showing same info twice)
- Returns exactly top_k chunks, prioritizing live data
- Preserves chunk structure including citation metadata
- Handles edge cases: empty live list, empty static list, fewer than top_k total chunks
- Comprehensive docstring explaining ranking logic
- _Requirements: 2.1, 2.5_

**Files to create/modify**:
- Modify: `app/services/rag_service.py` (add _merge_live_and_static function)

**Verification**:
- Unit tests with various live/static combinations
- Test ranking order (live before static)
- Test deduplication
- Test top_k limiting
- Test edge cases (all live, all static, partial results)

**Subtasks**:
- [ ] 4.3a - Implement ranking logic with age calculation
- [ ] 4.3b - Implement deduplication
- [ ] 4.3c - Implement top_k selection and fallback
- [ ] 4.3d - Write comprehensive unit tests (test_merge_logic.py)

---

### Task 4.4: Create retrieve_context_with_live Enhanced Function

**ID**: task-4-4  
**Status**: not_started  
**Depends on**: task-3-1, task-4-2, task-4-3  
**Time estimate**: 2 hours  
**Acceptance Criteria**:
- Function `retrieve_context_with_live(query: str, top_k: int = 4, use_live: bool = True) -> List[Dict]` added to `rag_service.py`
- When `use_live=True`: calls `_detect_query_type()` → `_fetch_live_data_for_query_type()` → `_merge_live_and_static()` → returns merged results with citations
- When `use_live=False`: calls original `retrieve_context()` logic (backward compatible)
- First tries `FoundryIQConnector.query_foundry_knowledge()` if available
- Falls back to web fetchers if Foundry unavailable
- All live fetches are cached via `LiveDataCache`
- Graceful degradation: if all live sources fail, returns static knowledge without errors
- Returns chunks with citation metadata attached
- CRITICAL: Maintain backward compatibility with existing `retrieve_context()` callers
- Comprehensive error handling and logging
- _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4_

**Files to create/modify**:
- Modify: `app/services/rag_service.py` (add retrieve_context_with_live function)
- Optionally modify: existing `retrieve_context()` to call `retrieve_context_with_live(query, top_k, use_live=False)` for unified code path

**Verification**:
- Integration tests covering:
  - Live data available: returns fresh data with citations
  - Live data unavailable: falls back to static knowledge
  - Query type detection for different query types
  - Citation metadata present in results
  - Backward compatibility: existing `retrieve_context()` still works unchanged
  - Error scenarios: all live sources down, Foundry unavailable, timeout handling

**Subtasks**:
- [ ] 4.4a - Implement main retrieve_context_with_live function
- [ ] 4.4b - Wire up Foundry connector and web fetchers
- [ ] 4.4c - Implement fallback and error handling
- [ ] 4.4d - Write integration tests (test_retrieve_context_with_live.py)
- [ ] 4.4e - Verify backward compatibility with existing code

---

## Phase 5: Integration & Testing

### Task 5.1: Update FoundryIQLayer to Use Live Data

**ID**: task-5-1  
**Status**: not_started  
**Depends on**: task-4-4  
**Time estimate**: 1.5 hours  
**Acceptance Criteria**:
- Modify `app/services/foundry_iq.py` to integrate live data pipeline
- Update `retrieve_and_ground_context()` method to call `retrieve_context_with_live()` instead of `retrieve_context()`
- Preserve existing method signature and return format for backward compatibility
- New grounded context now includes live data with citations
- Test integration with `generate_grounded_reasoning()` method
- Verify citations flow through to reasoning explanations
- _Requirements: 2.1, 2.5, 2.6, 3.4_

**Files to create/modify**:
- Modify: `app/services/foundry_iq.py` (update retrieve_and_ground_context method)

**Verification**:
- Unit test with mocked live data fetchers
- Verify Foundry layer calls retrieve_context_with_live
- Verify grounded text includes live data information
- Verify reasoning explanations reference fresh data

**Subtasks**:
- [ ] 5.1a - Update retrieve_and_ground_context method
- [ ] 5.1b - Verify integration with reasoning generation
- [ ] 5.1c - Write integration tests (test_foundry_iq_live.py)

---

### Task 5.2: Update API Routes (if applicable)

**ID**: task-5-2  
**Status**: not_started  
**Depends on**: task-4-4  
**Time estimate**: 1 hour  
**Acceptance Criteria**:
- Check `app/api/rag_routes.py` (if exists) and update endpoints to support live data
- Keep existing endpoints unchanged for backward compatibility
- Optionally add new endpoint: `POST /api/rag/retrieve-with-live?use_live=true` that returns chunks with citation metadata
- Response format includes citation fields: source_url, retrieval_date, confidence_score, data_age_hours
- Test endpoints work with existing client code
- Update any documentation/comments about RAG endpoints
- _Requirements: 3.4_

**Files to create/modify**:
- Check: `app/api/rag_routes.py` (if exists)
- Modify if needed: add live data support while preserving existing endpoints

**Verification**:
- Integration tests for RAG API endpoints
- Test backward compatibility
- Test new live data endpoint (if added)
- Test response formats

**Subtasks**:
- [ ] 5.2a - Review existing RAG routes
- [ ] 5.2b - Update if needed to support live data parameter
- [ ] 5.2c - Write API integration tests (test_rag_api.py)

---

### Task 5.3: End-to-End Integration Testing

**ID**: task-5-3  
**Status**: not_started  
**Depends on**: task-5-1, task-5-2  
**Time estimate**: 3 hours  
**Acceptance Criteria**:
- Full workflow test: User query → detect type → fetch live data → merge with static → attach citations → reasoning agent processes → response includes citations
- Test scenarios:
  1. **Salary Query with Live Data**: "What's the current salary for Data Scientists in India?" → returns current Glassdoor data with Jan 2025 date
  2. **Skills Query with Live Data**: "What technologies are trending for ML engineers?" → returns current job market data with recent trends
  3. **Offline Scenario**: All live sources down → system falls back to static knowledge without errors
  4. **Mixed Query Types**: Query requires multiple data sources → system fetches and merges appropriately
  5. **Backward Compatibility**: Existing feature calls still work unchanged (profile analysis, skill gaps, roadmaps)
  6. **Citation Flow**: Citations propagate from retrieval → reasoning → response formatting
- All tests pass with comprehensive error scenarios
- Performance acceptable (live data fetch < 2 seconds for most queries)
- _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5_

**Files to create/modify**:
- Create: `tests/test_e2e_live_data_integration.py` (comprehensive integration test suite)

**Verification**:
- Run full integration test suite
- Verify all 6 test scenarios pass
- Check performance metrics (response times < 2s for live data fetch)
- Verify no regression in existing features
- Manual testing with reasoning agent and user chat flows

**Subtasks**:
- [ ] 5.3a - Create E2E test suite with all scenarios
- [ ] 5.3b - Mock external APIs (Glassdoor, LinkedIn, Indeed, Coursera)
- [ ] 5.3c - Test live data retrieval and merging
- [ ] 5.3d - Test offline fallback behavior
- [ ] 5.3e - Test citation flow and response formatting
- [ ] 5.3f - Performance benchmarking and optimization
- [ ] 5.3g - Verify backward compatibility with existing features

---

## Environment Configuration

### New Environment Variables

Add to `.env` file:

```
# Live Data Fetchers - API Keys (optional, set if using official APIs)
GLASSDOOR_API_KEY=
LINKEDIN_API_KEY=
INDEED_API_KEY=
COURSERA_API_KEY=
LEVELS_FYI_API_KEY=

# Azure Foundry Integration (optional)
AZURE_FOUNDRY_ENDPOINT=https://api.azure.foundryiq.com/...
AZURE_FOUNDRY_TENANT_ID=
AZURE_FOUNDRY_CLIENT_ID=
AZURE_FOUNDRY_CLIENT_SECRET=

# Fetcher Timeouts (optional, defaults shown)
WEB_FETCHER_TIMEOUT_SECONDS=10
FOUNDRY_API_TIMEOUT_SECONDS=5

# Cache Configuration (optional, defaults shown)
LIVE_DATA_CACHE_TTL_HOURS=24
FOUNDRY_CACHE_TTL_MINUTES=30

# Scraper Settings (if using web scraping fallback)
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)
SCRAPER_RATE_LIMIT_DELAY_SECONDS=2
```

---

## Test Coverage Summary

| Phase | Module | Test Types | Coverage |
|-------|--------|-----------|----------|
| 1 | live_data_cache | Unit, TTL expiration | 90%+ |
| 1 | citation_tracker | Unit, dataclass, injection | 90%+ |
| 1 | ORM models | Integration, schema | 85%+ |
| 2 | web_data_fetcher | Unit, mock API, retry logic | 90%+ |
| 2 | GlassdoorSalaryFetcher | Unit, mock API, caching | 85%+ |
| 2 | LinkedInSkillsFetcher | Unit, mock API | 85%+ |
| 2 | IndeedJobFetcher | Unit, aggregation | 85%+ |
| 2 | CourseraCourseFetcher | Unit, trending detection | 85%+ |
| 3 | foundry_iq_connector | Unit, auth, retry, mock Azure | 90%+ |
| 4 | rag_service enhancements | Integration, fallback, backward compat | 90%+ |
| 5 | foundry_iq.py updates | Integration | 85%+ |
| 5 | E2E workflows | Integration, all scenarios | 95%+ |

---

## Risk Mitigation & Dependency Notes

### Critical Path
1. **Phase 1** (Infrastructure) must complete first — all other phases depend on it
2. **Phase 2 & 3** can proceed in parallel after Phase 1 completes
3. **Phase 4** (Enhanced RAG) cannot start until Phase 2 & 3 complete
4. **Phase 5** (Integration) cannot start until Phase 4 completes

### Backward Compatibility
- **CRITICAL**: Existing `retrieve_context()` API must remain unchanged
- New live data functionality is additive (new function `retrieve_context_with_live()`)
- All citation fields are optional in chunk dictionaries
- Existing callers in `foundry_iq.py`, `reasoning_agent.py`, `rag_routes.py` work without modification

### Error Handling & Resilience
- All web fetchers have timeout protection (10 seconds max)
- Foundry connector has retry logic (3 attempts, exponential backoff)
- Graceful degradation: if live sources fail, system falls back to static knowledge
- No single point of failure: system works offline using cached + static data

### Testing Strategy
- **Unit tests**: Each module tested independently with mocks
- **Integration tests**: Modules tested together (fetch + cache + merge)
- **E2E tests**: Full workflows tested with all components
- **Property-based tests** (recommended): Verify preservation behavior for non-market queries
- **Performance tests**: Verify live data fetching meets latency requirements

### Deployment Considerations
- Database migration must run before new code deploys (add LiveDataCache tables)
- Configuration can be optional (system works without API keys using mock data)
- Gradual rollout: enable live data for specific query types first
- Monitor cache hit rates and API latency in production

---

## Acceptance & Sign-Off

**Phases Completed Successfully When**:
- ✅ All unit tests pass (90%+ coverage per phase)
- ✅ All integration tests pass
- ✅ E2E tests pass with all 6 scenarios
- ✅ Backward compatibility verified (existing features work unchanged)
- ✅ Live data appears in reasoning agent responses with proper citations
- ✅ Offline fallback works (system functional when all live sources down)
- ✅ Performance acceptable (live data fetch < 2s, static knowledge < 500ms)
- ✅ No new critical security vulnerabilities introduced

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Tasks** | 15 main tasks + 35 subtasks |
| **Total Estimated Hours** | 28-32 hours |
| **Critical Path Duration** | ~20 hours (Phase 1 → 2/3 parallel → 4 → 5) |
| **Test Files to Create** | ~12-15 test modules |
| **New Lines of Code** | ~1,500-2,000 (services) + ~2,000-3,000 (tests) |
| **Backward Compatibility** | 100% - no breaking changes to existing APIs |

