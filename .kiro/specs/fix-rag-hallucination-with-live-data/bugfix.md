# RAG Hallucination Bug Fix — Live Market Data Integration

## Introduction

The reasoning agent's RAG (Retrieval-Augmented Generation) system returns outdated static knowledge from 2023 instead of current market data. When users query about career paths, salary expectations, or skill demand, the system grounds its answers in hardcoded 2023 information, causing hallucinations of "current" data that is actually years old. This impacts user trust and the quality of career recommendations. The fix integrates live web data sources and proper Azure Foundry integration to ensure AI responses reflect current job market reality.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user queries about current job market salary data for a role (e.g., "What's the current salary for a Data Scientist in India?") THEN the system returns 2023 salary ranges from the hardcoded knowledge base (e.g., ₹5-10 LPA fresher) without indication that this data is outdated

1.2 WHEN a user asks about trending skills or technologies needed for a career path THEN the system returns static 2023 skill lists (e.g., "TensorFlow or PyTorch") without including current market leaders or emerging tools

1.3 WHEN a user queries about job opportunities, company hiring trends, or top companies in a field THEN the system returns a static 2023 company list (e.g., "Google, Microsoft, Flipkart") without reflecting current hiring patterns or new market entrants

1.4 WHEN a user asks about course recommendations, certifications, or learning resources THEN the system returns outdated 2023 course references without including current platforms or trends

1.5 WHEN the reasoning agent generates career recommendations THEN the recommendations are grounded entirely in the static `KNOWLEDGE_BASE` from `rag_knowledge.py` with no mechanism to fetch live data or current market trends

1.6 WHEN a user receives AI-generated career advice THEN there is no way to verify where the information came from or when it was last updated (no grounding/citation mechanism)

### Expected Behavior (Correct)

2.1 WHEN a user queries about current job market salary data THEN the system SHALL retrieve and return current salary trends from live web sources (e.g., job boards, company databases) with proper indication of data freshness and source

2.2 WHEN a user asks about trending skills or technologies THEN the system SHALL fetch current skill demand data from sources like job postings, LinkedIn trends, or developer surveys to reflect what's actually in demand now

2.3 WHEN a user queries about job opportunities and company hiring THEN the system SHALL retrieve current hiring data from live job boards or Azure Foundry knowledge base to reflect actual current market activity

2.4 WHEN a user asks about courses and certifications THEN the system SHALL fetch current course catalogs, enrollment trends, and recently launched learning resources instead of returning 2023 static references

2.5 WHEN the reasoning agent generates career recommendations THEN the recommendations SHALL be grounded in a combination of live web data and verified knowledge sources, with fallback to curated static knowledge only when live data is unavailable

2.6 WHEN a user receives AI-generated career advice THEN the response SHALL include clear citations showing the source and recency of the information used to generate the recommendation

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the system receives a query that cannot be answered with live data THEN the system SHALL CONTINUE TO use curated static knowledge as a fallback without degrading functionality

3.2 WHEN the system is offline or live data sources are unavailable THEN the system SHALL CONTINUE TO provide recommendations using cached static knowledge without crashing or returning errors

3.3 WHEN users interact with existing features like profile analysis, skill gap detection, or roadmap generation THEN the system SHALL CONTINUE TO work exactly as before, with improved data quality from live sources

3.4 WHEN the reasoning agent calls the RAG retrieval function THEN the API signature and return format SHALL CONTINUE TO be compatible with existing code (no breaking changes to `retrieve_context()` and `retrieve_context_text()`)

3.5 WHEN Azure Foundry is unavailable or not configured THEN the system SHALL CONTINUE TO function using fallback strategies (caching, static knowledge) without requiring re-authentication or special handling
