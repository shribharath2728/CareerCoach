# RAG Hallucination with Live Data Integration — Bugfix Design

## Overview

The SkillLens reasoning agent currently returns outdated 2023 career data (salaries, skills, companies, courses) because the RAG knowledge base is entirely hardcoded static data. Users receive career recommendations grounded in old market conditions, reducing trust and accuracy. This design specifies a two-layer data strategy: live web-scraped data sources (job boards, LinkedIn, course platforms) feeding into a cached knowledge layer, combined with improved Azure Foundry IQ integration to surface current market reality. The fix maintains backward compatibility while enabling fresh, cited responses.

## Glossary

- **Bug_Condition (C)**: User queries about current market data (salaries, skills, jobs, courses) are answered exclusively using hardcoded 2023 static KNOWLEDGE_BASE without any live data sources or freshness indicators
- **Property (P)**: When the bug condition is detected (live data is available and fresh), the reasoning agent SHALL retrieve and cite current market data instead of defaulting to static 2023 data
- **Preservation**: Queries that cannot be answered with live data, offline scenarios, and existing API signatures continue to work unchanged
- **Live_Data_Source**: External data providers including job boards (LinkedIn Jobs, Indeed), skill demand trackers (LinkedIn Skills, HackerRank), course platforms (Coursera, Udemy), and salary databases (Glassdoor, Levels.fyi)
- **Foundry_IQ_Layer**: The `FoundryIQLayer` class in `foundry_iq.py` that provides semantic grounding and reasoning over retrieved knowledge
- **RAG_Context**: The combined set of knowledge chunks (live + cached + static) returned by `rag_service.retrieve_context()` and formatted by `retrieve_context_text()`
- **Citation_Metadata**: Structure containing source_url, retrieval_date, confidence_score, and data_freshness_hours that flows from retrieval → reasoning → response
- **Data_Cache**: Persistent storage of scraped live data with TTL (time-to-live) to enable graceful degradation when live sources are unavailable

## Bug Details

### Bug Condition

The bug manifests when a user queries about current market conditions (salary trends, in-demand skills, hiring patterns, course recommendations) and the RAG system responds with information from the hardcoded KNOWLEDGE_BASE without indicating that the data is from 2023 or offering any live alternatives. The `rag_knowledge.py` module contains only static documents, and even though `rag_service.py` extends this with a database layer, there is no mechanism to fetch and integrate live web data sources or Azure Foundry knowledge APIs.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UserQuery
  OUTPUT: boolean
  
  RETURN input.queryType IN ['salary_inquiry', 'skill_demand', 'job_market', 'course_recommendation']
         AND input.userAskingAbout IN ['current', 'today', 'now', '2024', '2025']
         AND NOT liveDataAvailableFor(input.queryCategory)
         AND ALL_RESPONSE_TEXT contains staticKnowledgeBaseOnly
         AND NO_CITATIONS_PROVIDED
END FUNCTION
```

### Examples

**Example 1: Salary Query (Bug Manifestation)**
- User asks: "What's the current salary for a Data Scientist in India?"
- Current system returns: "Fresher salary (India): ₹5-10 LPA" (from rag_knowledge.py, hardcoded 2023 data)
- Expected behavior: Should retrieve from live salary database API (Glassdoor API, Levels.fyi scrape, or internal Foundry knowledge) and respond: "According to Glassdoor (updated Jan 2025), Data Scientists in India earn ₹8-14 LPA for freshers, with recent market movement towards senior-level roles commanding ₹18-40 LPA"
- Impact: User receives outdated information, may make career decisions based on 2023 market conditions

**Example 2: Trending Skills Query (Bug Manifestation)**
- User asks: "What technologies are most in-demand for ML engineers right now?"
- Current system returns: "Core skills: Python, TensorFlow or PyTorch, MLOps, Vector Databases, LLMs (GPT/Llama)" (static 2023 list)
- Expected behavior: Should fetch current job postings and LinkedIn skills data and respond: "According to 2024 job market analysis, demand is highest for: Python (95% of ML roles), PyTorch (becoming dominant over TensorFlow), LangChain/LlamaIndex (RAG frameworks +40% growth), and domain-specific models (Anthropic Claude, Mistral) alongside GPT"
- Impact: Students may learn outdated tools, reducing their competitiveness

**Example 3: Course Recommendation Query (Bug Manifestation)**
- User asks: "What courses should I take to become an ML engineer in 2025?"
- Current system returns: "Resources: fast.ai Practical Deep Learning (free), DeepLearning.AI Specializations" (2023 course list)
- Expected behavior: Should query live Coursera API and Indeed job postings to identify trending skills and respond: "Most sought courses in 2024: Andrew Ng's ML Specialization (89% hiring preference), DeepLearning.AI's new LLM Ops course (trending +200%), and practical on-device ML courses (mobile ML +50% growth)"
- Impact: User invests time in courses that may not align with current market demand

**Example 4: Company Hiring Trends (Bug Manifestation)**
- User asks: "Which companies are actively hiring AI engineers in India right now?"
- Current system returns: "Google, Microsoft, Amazon, Flipkart, Juspay, Sarvam AI, CRED, Ola, startups in GenAI space" (static 2023 list, outdated for some companies)
- Expected behavior: Should query Indeed, LinkedIn Jobs, AngelList APIs and respond: "Active hiring (last 30 days): Anthropic and OpenAI hiring globally, Sarvam AI and IIT-M Pravartak expanding in India, Meta aggressively hiring for AI/ML (500+ open roles), Google still leading but more selective post-cutbacks"
- Impact: User applies to companies no longer hiring, wastes effort on closed applications

**Edge Case: Unavailable Live Data (Preservation)**
- Scenario: Live data source API is down, rate limit hit, or data is stale
- System behavior: Fall back to cached live data from last successful fetch, or use static knowledge base
- Expected: No crash, graceful degradation with transparency ("Latest live data unavailable, showing cached data from Jan 15")

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
1. Existing `retrieve_context(query, top_k)` function signature and return format (`List[Dict[str, Any]]`) must remain compatible with existing callers in reasoning_agent.py and other services
2. Existing `retrieve_context_text(query, top_k, max_chars)` convenience function must continue to work for all existing code paths
3. All existing database queries and ORM operations in `rag_service.py` continue to function without schema breaking changes
4. When users query about non-time-sensitive topics (general career path descriptions, how to prepare for interviews, portfolio tips), the system continues to return high-quality static knowledge as before
5. Queries that use filters like "For someone with 2 years experience" or "Interview preparation" should continue working with existing logic
6. The reasoning agent integration with Foundry IQ layer continues to work without modification to calling code
7. Fallback to static knowledge works seamlessly when live data sources are temporarily unavailable or rate-limited
8. Offline mode: System continues to function using only cached data and static knowledge if all live data sources are unavailable
9. Existing caching layer in `rag_service.py` continues to be leveraged for performance

**Scope:**
All user queries that are NOT about current market data (queries about evergreen career path structures, learning methodologies, portfolio building strategies, motivation, productivity tips) should be completely unaffected by this fix and continue using the static knowledge base. This includes:
- General career path overviews (what skills does an ML engineer need)
- Learning resources and study techniques
- Interview preparation guidance
- Motivation and productivity advice
- Historical facts about tech careers

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Monolithic Static Knowledge Base**: The KNOWLEDGE_BASE in `rag_knowledge.py` is hardcoded at module load time and never updates. Documents have publish dates embedded in text (2023) but no actual data freshness metadata. There's no mechanism to fetch live data or refresh based on TTL.

2. **No Live Data Integration Pipeline**: There is no web scraping layer, no API wrappers for job boards or salary databases, and no scheduled job to fetch fresh market data. The `rag_service.py` adds a database layer but still only caches static knowledge from KNOWLEDGE_BASE.

3. **Missing Azure Foundry API Integration**: While `foundry_iq.py` exists as a Foundry IQ simulation, it only calls `rag_service.retrieve_context()` which itself only returns static or database-cached data. There's no call to actual Azure Foundry knowledge-retrieval APIs or permission token handling for live knowledge sources.

4. **No Citation / Metadata Flow**: Retrieved chunks have `{id, category, tags, text}` but no `source_url`, `retrieval_date`, or `confidence_score`. The reasoning agent has no way to cite where information came from or indicate data recency.

5. **Single Source of Truth Problem**: Foundry IQ and reasoning agent have no way to know if retrieved context is live or stale. They treat all knowledge equally, so users can't distinguish between "this is from Glassdoor today" vs "this is a 2023 guess."

6. **Backward Compatibility Barrier**: Changing the return format of `retrieve_context()` would break all existing callers. New citation metadata needs to be added without breaking the API.

## Correctness Properties

Property 1: Bug Condition - Live Data Preference

_For any_ user query where the bug condition holds (queryType is about current market data AND live data source is available AND data is fresher than 24 hours), the fixed RAG system SHALL:
1. Fetch data from live sources (job boards, salary databases, course platforms, Azure Foundry)
2. Include citation metadata (source_url, retrieval_date, confidence_score)
3. Present the information with explicit freshness indicator ("Updated: Jan 2025")
4. Return context chunks that include both structured metadata and readable text

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**

Property 2: Preservation - Non-Current-Data Queries and Offline Scenarios

_For any_ input where the bug condition does NOT hold (query is about evergreen topics OR live data is unavailable), the fixed system SHALL:
1. Continue using static knowledge base and cached data exactly as before
2. Return results in the same format as original `retrieve_context()` function
3. Maintain full compatibility with existing reasoning agent code
4. Function without errors even if all live data sources are down
5. Preserve the existing `retrieve_context()` and `retrieve_context_text()` API signatures

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Hypothesized Root Cause Analysis

The current system fails to provide live data because:

1. **rag_knowledge.py** contains only a static KNOWLEDGE_BASE dictionary initialized at module load, with no live data sources
2. **rag_service.py** extends this with a database caching layer but still only caches data from the original static knowledge base or manually added entries
3. **foundry_iq.py** calls `rag_service.retrieve_context()` but receives no live data because the underlying retrieval has no live sources
4. No web scraping infrastructure exists for job boards, LinkedIn, Glassdoor, course platforms
5. No Azure Foundry API integration exists for knowledge retrieval with proper token handling
6. No citation metadata is tracked through the retrieval pipeline
7. The API contracts prevent adding new metadata fields without breaking changes

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix requires building a live data pipeline that supplements (not replaces) the static knowledge base, with proper citations and graceful degradation.

**Module Structure:**

```
app/services/
├── rag_knowledge.py          [UNCHANGED - static knowledge base]
├── rag_service.py            [ENHANCED - add live data layer, caching, citations]
├── web_data_fetcher.py       [NEW - web scraping and API integration]
├── foundry_iq_connector.py   [NEW - Azure Foundry API wrapper]
├── live_data_cache.py        [NEW - caching layer for live data with TTL]
└── citation_tracker.py       [NEW - metadata management for citations]
```

### Implementation Phases

#### Phase 1: Data Caching & Citation Infrastructure (Foundation)

**File**: `app/services/live_data_cache.py` (NEW)

**Functionality**:
- `LiveDataCache` class with TTL-based expiration
- Store: `{ "key": "salary_ds_india_2025", "data": {...}, "retrieved_at": timestamp, "ttl_hours": 24, "source": "glassdoor_api" }`
- Methods: `cache_live_data(key, data, ttl_hours)`, `get_cached(key)`, `is_expired(key)`, `clear_expired()`
- Database schema: `live_data_cache` table with columns: key, data (JSON), retrieved_at, ttl_hours, source, confidence_score

**File**: `app/services/citation_tracker.py` (NEW)

**Functionality**:
- `Citation` dataclass: `{ source_url: str, retrieval_date: datetime, confidence_score: float, data_age_hours: int }`
- `CitationManager` class to attach metadata to knowledge chunks
- Methods to inject citations into retrieved context chunks: `add_citation_to_chunk(chunk, citation)`
- Serialize citations for API responses: `chunk.to_dict_with_citation()`

**Changes to `app/models/rag_knowledge.py` (Database Model)**:
- Add new ORM model for live_data_cache table
- Schema includes: id, key, data (JSON), retrieved_at, ttl_hours, source, confidence_score, created_at, updated_at

#### Phase 2: Web Data Fetcher & API Wrappers (Live Source Integration)

**File**: `app/services/web_data_fetcher.py` (NEW)

**Functionality**:
- `WebDataFetcher` base class with interface: `fetch_salary_data()`, `fetch_skill_trends()`, `fetch_job_postings()`, `fetch_courses()`
- Implementations:
  - `GlassdoorSalaryFetcher`: Scrape or API call to Glassdoor salary data (with rate limiting, error handling)
  - `LinkedInSkillsFetcher`: Fetch trending skills from LinkedIn Jobs or LinkedIn Learning APIs
  - `IndeedJobFetcher`: Query Indeed API for active job postings by skill/role
  - `CourseraCourseFetcher`: Call Coursera API for trending courses and enroll trends
  - `LevelsFyiFetcher`: Scrape Levels.fyi salary data (more granular, role-level)

**Key Features**:
- Rate limiting (respect API limits, exponential backoff)
- Error handling (API down → return None, trigger fallback)
- Caching decorator: `@cache_result(ttl_hours=24)` automatically caches responses
- Structured return format: `{ "data": [...], "source": "glassdoor_api", "retrieved_at": timestamp, "confidence_score": 0.9 }`
- Async/await support for parallel fetching: `async def fetch_salary_and_skills(query: str)`

#### Phase 3: Foundry IQ Connector (Azure Integration)

**File**: `app/services/foundry_iq_connector.py` (NEW)

**Functionality**:
- `FoundryIQConnector` class wrapping Azure Foundry knowledge-retrieval API
- Methods:
  - `query_foundry_knowledge(query: str, domain: str) -> Dict`: Call Azure API, handle auth
  - `get_permission_token() -> str`: Retrieve/refresh auth token from Azure AD (or config)
  - `parse_foundry_response(response) -> List[Dict]`: Convert Foundry API response to standard chunk format
- Timeout & retry logic:
  - Timeout: 5 seconds for Foundry API calls
  - Retry: 3 attempts with exponential backoff (1s, 2s, 4s)
  - Fallback: If Foundry unavailable, use web fetchers or static knowledge

**Integration with FoundryIQLayer**:
- `FoundryIQLayer.retrieve_and_ground_context()` now calls `FoundryIQConnector.query_foundry_knowledge()` first
- If Foundry returns results, prioritize them and add Foundry citations
- Fall back to `rag_service.retrieve_context()` if Foundry is unavailable

#### Phase 4: Enhanced RAG Service (Unified Retrieval)

**Changes to `app/services/rag_service.py`**:

**New Functions**:
1. `retrieve_context_with_live(query: str, top_k: int = 4, use_live: bool = True) -> List[Dict[str, Any]]`
   - Call web fetchers based on query type detection (salary → GlassdoorFetcher, skills → LinkedInFetcher, etc.)
   - Merge live results with static knowledge, ranked by recency + relevance
   - Attach citation metadata to each chunk
   - Return format: Backward-compatible (same as original `retrieve_context()` but with additional citation fields)

2. `_detect_query_type(query: str) -> str`
   - Returns: "salary_inquiry" | "skill_demand" | "job_market" | "course_recommendation" | "general"
   - Uses keyword matching: "salary", "earn", "pay" → salary_inquiry; "trending", "demand", "skill" → skill_demand, etc.

3. `_fetch_live_data_for_query_type(query_type: str, query: str) -> List[Dict]`
   - Route to appropriate fetcher based on query_type
   - Handle errors gracefully, return empty list if live source fails

4. `_merge_live_and_static(live_chunks: List, static_chunks: List, top_k: int) -> List`
   - Rank: live (freshness + relevance) > cached live (age penalty) > static (relevance boost for evergreen)
   - Deduplicate by content hash
   - Return top_k

**Preserve Original API**:
- Original `retrieve_context(query, top_k)` remains unchanged, now delegates to `retrieve_context_with_live(query, top_k, use_live=False)` when live is disabled
- Or, keep original and add new optional parameter `use_live=True` to existing `retrieve_context()` with backward compatibility

**New Parameters to Chunks**:
```python
{
    "id": str,
    "category": str,
    "tags": List[str],
    "text": str,
    # NEW CITATION FIELDS:
    "source": str,  # "glassdoor_api" | "linkedin_api" | "static_knowledge"
    "source_url": Optional[str],  # URL to source for verification
    "retrieval_date": Optional[datetime],  # When this data was fetched
    "confidence_score": Optional[float],  # 0.0-1.0 confidence
    "data_age_hours": Optional[int],  # How fresh is this data
}
```

#### Phase 5: Integration Points (Wiring)

**Update `app/services/foundry_iq.py`**:
```python
def retrieve_and_ground_context(self, query: str, ...):
    # Try Foundry first (if configured)
    foundry_chunks = self.foundry_connector.query_foundry_knowledge(query)
    if foundry_chunks:
        return foundry_chunks
    
    # Fallback to rag_service with live data enabled
    return rag_service.retrieve_context_with_live(query, ...)
```

**Update `app/api/rag_routes.py`** (if exists):
- Expose new endpoint: `POST /api/rag/retrieve-with-live` that returns chunks with citation metadata
- Keep existing endpoints unchanged for backward compatibility

**Update `app/services/reasoning_agent.py`** (if it calls RAG):
- No changes needed if using `retrieve_context()` — it continues to work
- Optionally update to use `retrieve_context_with_live()` and display citations in responses

### Configuration & Environment

**New `.env` variables** (optional):
```
# Live Data Fetchers
GLASSDOOR_API_KEY=...  # If using Glassdoor official API
LINKEDIN_API_KEY=...
INDEED_API_KEY=...
COURSERA_API_KEY=...

# Azure Foundry
AZURE_FOUNDRY_ENDPOINT=https://api.azure.foundryiq.com/...
AZURE_FOUNDRY_TENANT_ID=...
AZURE_FOUNDRY_CLIENT_ID=...
AZURE_FOUNDRY_CLIENT_SECRET=...

# Scraping (if using BeautifulSoup instead of APIs)
SCRAPER_USER_AGENT=...
SCRAPER_RATE_LIMIT_DELAY_SECONDS=2

# Cache & Timeouts
LIVE_DATA_CACHE_TTL_HOURS=24
FOUNDRY_API_TIMEOUT_SECONDS=5
WEB_FETCHER_TIMEOUT_SECONDS=10
```

### Data Model Changes

**New ORM Models in `app/models/rag_knowledge.py`**:
```python
class LiveDataCache(Base):
    __tablename__ = "live_data_cache"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)  # e.g., "salary_ds_india_2025_jan"
    data = Column(JSON)  # Raw fetched data
    source = Column(String)  # e.g., "glassdoor_api"
    retrieved_at = Column(DateTime, index=True)
    ttl_hours = Column(Integer, default=24)
    confidence_score = Column(Float, default=0.9)  # 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LiveDataSources(Base):
    __tablename__ = "live_data_sources"
    id = Column(Integer, primary_key=True)
    name = Column(String)  # e.g., "glassdoor", "linkedin_skills"
    endpoint = Column(String)
    api_key_env = Column(String)  # Environment variable name
    enabled = Column(Boolean, default=True)
    rate_limit_per_minute = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (responses with outdated data, no citations), then verify the fix works correctly (live data retrieved with citations) and preserves existing behavior (offline/evergreen queries work unchanged).

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm the root cause: hardcoded static 2023 data with no live sources, no citations.

**Test Plan**: Write unit tests that query the current `retrieve_context()` for known market-data questions, capture responses, and verify they are:
1. From static knowledge base (no live sources)
2. Contain 2023 dates or outdated references
3. Have no citation metadata (no source_url, retrieval_date)

**Test Cases**:
1. **Salary Data Query Test**: Call `retrieve_context("What's the current salary for Data Scientists?")` on unfixed code → observe response contains "₹5-10 LPA" (2023 static) → confirm bug
2. **Trending Skills Query Test**: Call `retrieve_context("What skills are trending for ML engineers?")` → observe response lists "TensorFlow or PyTorch" (2023 list) without mentioning LangChain/RAG frameworks → confirm bug
3. **Course Recommendation Test**: Call `retrieve_context("What courses should I take?")` → observe response lists 2023 courses without current Coursera enrollment trends → confirm bug
4. **Company Hiring Test**: Call `retrieve_context("Which companies are hiring AI engineers?")` → observe static 2023 company list → confirm bug
5. **Citation Absence Test**: Call `retrieve_context()` and verify returned chunks have NO `source_url`, `retrieval_date`, or `confidence_score` fields → confirm bug

**Expected Counterexamples on Unfixed Code**:
- All responses are from `KNOWLEDGE_BASE` in `rag_knowledge.py` (confirmed by tracing execution)
- Metadata shows no retrieval_date field, or it's empty
- No live data sources are called
- Possible causes confirmed: no web fetcher module, no Foundry API integration, static knowledge base only

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (current market data queries with live source available), the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL query WHERE isBugCondition(query) DO
  result := retrieve_context_with_live(query)
  ASSERT len(result) > 0
  ASSERT exists chunk WHERE source IN ["glassdoor_api", "linkedin_api", "indeed_api", "coursera_api", "foundry_iq"]
  ASSERT chunk.retrieval_date IS NOT NULL
  ASSERT chunk.source_url IS NOT NULL
  ASSERT chunk.confidence_score >= 0.8
  ASSERT chunk.data_age_hours < 48  // Live data is recent
END FOR
```

**Testing Approach**: Integration tests with mocked live data sources (pytest fixtures for API responses).

**Test Cases**:
1. **Salary Data Retrieval Test**: Mock Glassdoor API, query salary data → fixed code fetches from mock Glassdoor → returns chunk with source="glassdoor_api", retrieval_date set, confidence_score=0.92 → PASS
2. **Skills Trending Retrieval Test**: Mock LinkedIn API, query trending skills → returns current 2024-2025 skill list with citation → PASS
3. **Course Recommendation Test**: Mock Coursera API → returns trending courses with retrieval_date and source_url → PASS
4. **Multi-Source Merge Test**: Query general career data → system merges live Glassdoor + cached LinkedIn skills + static knowledge → live sources ranked first → PASS
5. **Foundry Integration Test**: Mock Azure Foundry endpoint → call `retrieve_context_with_live()` → verifies Foundry is called first, results included with "foundry_iq" source → PASS

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function, preserving existing behavior.

**Pseudocode:**
```
FOR ALL query WHERE NOT isBugCondition(query) DO
  result_original := retrieve_context_original(query)
  result_fixed := retrieve_context_with_live(query, use_live=False)
  ASSERT len(result_fixed) == len(result_original)
  ASSERT result_fixed[i].text == result_original[i].text (same content)
  ASSERT result_fixed[i].score == result_original[i].score (same ranking)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (evergreen queries, edge cases)
- It catches cases where live data fetcher might incorrectly activate on non-market queries
- It provides strong guarantees that backward compatibility is maintained
- It tests the fallback path when live sources are unavailable

**Test Plan**: Observe behavior on current code for non-market queries, write property-based tests to verify this behavior continues.

**Test Cases**:
1. **Evergreen Content Preservation Test (Property-Based)**:
   - Generate 100 random interview/learning/motivation queries from corpus
   - For each: `result_original = retrieve_context(q)` vs `result_fixed = retrieve_context_with_live(q, use_live=False)`
   - Assert: same number of chunks, same content, same ranking
   - Property: "For all evergreen queries, output is identical"

2. **Offline Fallback Test**:
   - Simulate live data sources as DOWN (mock APIs to raise exceptions)
   - Query market data: "What's the salary?"
   - Fixed code should fall back to cached/static knowledge
   - Should NOT crash or raise errors
   - Assert: result is returned (may be stale but functional)

3. **Static Knowledge Base Unchanged Test**:
   - Verify KNOWLEDGE_BASE in `rag_knowledge.py` is not modified by fix
   - Call `retrieve_context("AI engineer overview")` → returns same chunk with same text
   - Backward compatibility verified

4. **API Signature Compatibility Test**:
   - Original: `retrieve_context(query: str, top_k: int = 4) -> List[Dict[str, Any]]`
   - Fixed: Must maintain exact same signature OR add optional param with default
   - Verify all existing callers work without modification
   - Assert: `reasoning_agent.py` and `rag_routes.py` callers do NOT need code changes

5. **Database Schema Backward Compatibility Test**:
   - Add new tables/columns for live data caching
   - Verify existing `rag_knowledge` table and ORM models are unchanged
   - Migration should be non-breaking (new tables only, no columns deleted/renamed)

### Unit Tests

- Test `_detect_query_type()` function with various inputs (salary queries, skill queries, etc.)
- Test `_fetch_live_data_for_query_type()` with mocked web fetchers (return mock data, handle errors)
- Test `_merge_live_and_static()` ranking and deduplication logic
- Test `LiveDataCache` TTL expiration and cleanup
- Test `FoundryIQConnector` token refresh and retry logic
- Test citation metadata injection into chunks
- Test each web fetcher module independently (Glassdoor, LinkedIn, Indeed, Coursera)

### Property-Based Tests

- **Property**: For all non-market queries, `retrieve_context_with_live(q, use_live=False)` output == `retrieve_context(q)` output
  - Generate random interview/learning/motivation queries
  - Verify preservation across 100+ random scenarios

- **Property**: For all market queries with live data available, result chunks have citation metadata
  - Generate salary/skill/job/course queries
  - Mock live API responses
  - Verify all results have source_url, retrieval_date, confidence_score

- **Property**: When live source times out, system falls back gracefully without crashing
  - Mock timeouts and exceptions on all live fetchers
  - Verify no unhandled exceptions, results still returned

- **Property**: Live data ranks higher than static, but only when fresh (< 24 hours)
  - Generate queries with both live and static results
  - Verify live results in top_k positions
  - Verify stale cached data is ranked lower than fresh static

### Integration Tests

- **Full Workflow Test**: User queries "Current salary for ML engineer" → system calls Glassdoor fetcher (mocked) → returns live result + static fallback → reasoning agent generates response with citations → user sees "According to Glassdoor (Jan 2025): ..."
- **Offline Scenario Test**: Live sources down → query still works → returns static knowledge → no crash
- **Foundry Integration Test**: Query → Foundry called (mocked) → result included with foundry_iq source → reasoning agent uses Foundry result
- **Citation Flow Test**: Live data retrieved → citations attached → response formatted → frontend displays citation links

