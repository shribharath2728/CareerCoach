# Requirements Document

## Introduction

This feature integrates Microsoft Foundry as the primary AI backbone of the SkillLens reasoning
agent and layers three complementary intelligence components on top of it:

- **Foundry IQ** — Agentic enterprise knowledge retrieval with citation, permission enforcement, and
  grounding, replacing the existing TF-IDF RAG module for grounded answers.
- **Work IQ** — Contextual memory derived from Microsoft 365 signals (emails, meetings, chats,
  documents) that enriches the reasoning agent with work-graph awareness of the authenticated user.
- **Fabric IQ** — Semantic intelligence layer that maps enterprise data in Microsoft Fabric to
  business ontologies and knowledge graphs, enabling the reasoning agent to reason over real
  business concepts rather than raw tabular data.

The integration must preserve full backward-compatibility with the existing Groq-backed AI provider
path so that deployments without Microsoft credentials continue to work without modification.

## Glossary

- **Reasoning_Agent**: The multi-step career analysis pipeline at
  `backend/app/services/reasoning_agent.py`.
- **AI_Provider**: The unified AI-provider abstraction at `backend/app/core/ai_provider.py`.
- **Foundry_Client**: The new Microsoft Azure AI Foundry SDK client introduced by this feature.
- **Foundry_IQ_Service**: The service layer that wraps the Azure AI Foundry knowledge-retrieval
  endpoint and returns cited, grounded answers.
- **Work_IQ_Service**: The service layer that connects to the Microsoft Graph API and synthesises
  a work-context payload for the authenticated user.
- **Fabric_IQ_Service**: The service layer that queries Microsoft Fabric semantic models via
  the Fabric REST API and returns ontology-enriched context.
- **IQ_Layer**: The composite intelligence layer comprising Foundry_IQ_Service,
  Work_IQ_Service, and Fabric_IQ_Service.
- **IQ_Context**: The structured payload produced by the IQ_Layer and injected into the
  Reasoning_Agent prompt pipeline.
- **Citation**: A reference returned by Foundry_IQ_Service identifying the enterprise source
  document or data item that supports a specific claim.
- **Work_Graph**: The network of people, relationships, meetings, and documents built from
  Microsoft 365 signals by Work_IQ_Service.
- **Fabric_Ontology**: The set of named business concepts, entities, and relationships defined in
  Microsoft Fabric semantic models and surfaced by Fabric_IQ_Service.
- **Permission_Token**: The OAuth 2.0 bearer token used to enforce data-access permissions when
  the Foundry_IQ_Service queries enterprise sources.
- **Groq_Provider**: The existing Groq-backed AI provider that continues to be used when
  Microsoft credentials are not configured.
- **Config**: The application settings object at `backend/app/core/config.py`.
- **Agent_Route**: The FastAPI router at `backend/app/api/agent_routes.py` that exposes the
  reasoning pipeline over HTTP.

---

## Requirements

### Requirement 1: Microsoft Foundry AI Provider Integration

**User Story:** As a SkillLens platform operator, I want the reasoning agent to call Microsoft Azure AI Foundry models so that I can leverage enterprise-grade AI inference with Microsoft's model catalogue.

#### Acceptance Criteria

1. THE AI_Provider SHALL support Microsoft Azure AI Foundry as a named provider alongside the existing Groq provider.
2. IF `AZURE_FOUNDRY_ENDPOINT` and `AZURE_FOUNDRY_API_KEY` environment variables are both present and non-empty, THEN THE AI_Provider SHALL route `chat_complete()` calls to the Azure AI Foundry inference endpoint by default.
3. IF `AZURE_FOUNDRY_ENDPOINT` or `AZURE_FOUNDRY_API_KEY` is absent or empty, THEN THE AI_Provider SHALL fall back to the Groq provider without raising an error.
4. THE Foundry_Client SHALL authenticate to Azure AI Foundry using the credential supplied via `AZURE_FOUNDRY_API_KEY`.
5. THE AI_Provider SHALL expose a `resolve_model()` function that accepts an optional model identifier string and returns `("foundry", model_id)` when the Foundry provider is active.
6. WHEN the Foundry provider is inactive, THE `resolve_model()` function SHALL return `("groq", model_id)` using the existing Groq resolution logic.
7. IF a requested model identifier is not available in the Azure AI Foundry model catalogue, THEN THE AI_Provider SHALL fall back to the value of `azure_foundry_default_model` (defaulting to `"gpt-4o"` if unset) and log a WARNING entry.
8. THE Config SHALL be extended with `azure_foundry_endpoint`, `azure_foundry_api_key`, and `azure_foundry_default_model` settings loaded from environment variables, each optional with a `None` default.
9. IF the Azure AI Foundry inference endpoint returns an HTTP error or raises a network exception during a `chat_complete()` call, THEN THE AI_Provider SHALL log a WARNING entry containing the error class and HTTP status code (with no credential data) and raise the exception to the caller unchanged.
10. THE AI_Provider SHALL preserve the existing `chat_complete(messages, system_prompt, model_hint, temperature, max_tokens)` function signature so that all existing callers in Reasoning_Agent and other services require zero parameter changes to operate.

---

### Requirement 2: Foundry IQ — Agentic Enterprise Knowledge Retrieval

**User Story:** As a career guidance user, I want the reasoning agent to answer questions using grounded enterprise knowledge with source citations so that I receive reliable, hallucination-reduced career guidance.

#### Acceptance Criteria

1. THE Foundry_IQ_Service SHALL connect to the Azure AI Foundry knowledge-retrieval API to query enterprise knowledge sources configured by the platform operator.
2. WHEN the Reasoning_Agent requires knowledge context, THE Foundry_IQ_Service SHALL return a structured payload containing the retrieved text, a list of Citations (each with `source`, `url`, and `excerpt` string fields), and a confidence score in the range [0.0, 1.0].
3. THE Foundry_IQ_Service SHALL enforce data-access permissions by forwarding a valid Permission_Token as a Bearer token in the `Authorization` header of every knowledge-retrieval request.
4. IF the Foundry_IQ_Service receives an HTTP 401 or 403 response from the upstream API, THEN THE Foundry_IQ_Service SHALL return an empty context payload and log the error at WARNING level without propagating an exception to the Reasoning_Agent.
5. IF the Foundry_IQ_Service receives a non-auth upstream error (HTTP 5xx, network timeout, or connection refused), THEN THE Foundry_IQ_Service SHALL return an empty context payload and log the error class and HTTP status at WARNING level without propagating an exception.
6. IF the Foundry provider is active, THEN THE Reasoning_Agent SHALL call `Foundry_IQ_Service.retrieve()` instead of `rag_knowledge.retrieve_context_text()`, so that grounded answers replace TF-IDF retrieval.
7. IF the Foundry provider is inactive, THEN THE Reasoning_Agent SHALL continue to call `rag_knowledge.retrieve_context_text()` as before, preserving full backward-compatibility.
8. THE Foundry_IQ_Service SHALL expose a `retrieve(query: str, permission_token: str, top_k: int) -> IQ_Context` function where `top_k` is in the range [1, 20] inclusive.
9. WHEN citations are present in an IQ_Context, THE Agent_Route SHALL include them in the JSON response body under a `citations` key. WHEN no citations are present, THE Agent_Route SHALL include an empty `citations` list (not `null`) in the response body.

---

### Requirement 3: Work IQ — Microsoft 365 Work-Context Memory

**User Story:** As an authenticated SkillLens user connected to a Microsoft 365 account, I want the reasoning agent to understand my work context (calendar, emails, skills signals from Teams and documents) so that career recommendations are personalised to my actual work situation.

#### Acceptance Criteria

1. THE Work_IQ_Service SHALL connect to the Microsoft Graph API using an OAuth 2.0 access token scoped to `User.Read`, `Mail.Read`, `Calendars.Read`, `Files.Read`, and `Chat.Read`.
2. WHEN a Microsoft Graph access token is provided by the caller, THE Work_IQ_Service SHALL retrieve up to 50 emails from the last 30 days, up to 50 calendar events from the last 30 days, and up to 50 recent files to construct a Work_Graph for the user.
3. THE Work_IQ_Service SHALL extract skill signals from email subjects, meeting titles, and document names and add them to the Work_Graph without reading full email or document body content beyond metadata.
4. THE Work_IQ_Service SHALL serialise the Work_Graph into a structured `WorkContext` object containing `recent_topics`, `collaborators`, `skill_signals`, and `active_projects`.
5. WHEN the Reasoning_Agent receives a `WorkContext` payload and the injection into the system prompt fails, THE Reasoning_Agent SHALL treat the failure as a recoverable error, continue processing with any `WorkContext` fields that were successfully populated before the failure, and log the failure at WARNING level.
6. IF the Microsoft Graph API returns an error or the caller provides no access token, THEN THE Work_IQ_Service SHALL return an empty `WorkContext` and log the error at WARNING level without raising an exception.
7. IF the provided access token is missing one or more of the required OAuth scopes, THEN THE Work_IQ_Service SHALL return an empty `WorkContext` and log a WARNING entry identifying the missing scopes.
8. THE Work_IQ_Service SHALL cache the Work_Graph keyed by the user identity claim extracted from the token (not the token string itself) for 15 minutes, measured from the time the entry was created, and SHALL serve the cached value for any request arriving before the 15-minute mark has elapsed.
9. THE Work_IQ_Service SHALL expose a `build_work_context(graph_token: str) -> WorkContext` function.

---

### Requirement 4: Fabric IQ — Semantic Enterprise Data Intelligence

**User Story:** As a SkillLens enterprise user, I want the reasoning agent to reason over business concepts from my organisation's Microsoft Fabric data so that skill-gap analysis and career recommendations are grounded in real organisational role definitions and workforce data.

#### Acceptance Criteria

1. THE Fabric_IQ_Service SHALL connect to the Microsoft Fabric REST API using the caller-provided token when supplied; otherwise it SHALL use the value of `FABRIC_BEARER_TOKEN`. IF neither is available or both are empty, THEN THE Fabric_IQ_Service SHALL follow the failure path defined in Criterion 8.
2. WHEN `FABRIC_WORKSPACE_ID` and `FABRIC_SEMANTIC_MODEL_ID` are both configured, THE Fabric_IQ_Service SHALL query the Fabric_Ontology to retrieve up to 50 entity definitions whose names or descriptions contain at least one term from the career goal or skill query string.
3. THE Fabric_IQ_Service SHALL map retrieved Fabric entities to the `CAREER_SKILL_MAP` vocabulary used by the Reasoning_Agent, annotating existing entries with business definitions from the Fabric_Ontology.
4. THE Fabric_IQ_Service SHALL return a `FabricContext` object containing `entity_definitions`, `related_roles`, and `data_sources` fields, each of which SHALL be an empty list (not `null`) when no data is available.
5. WHEN a `FabricContext` with non-empty `entity_definitions` is available, THE Reasoning_Agent SHALL include those definitions in the prompt for the gap-detection and roadmap-generation steps to ground skill recommendations in organisational terminology.
6. WHEN the Fabric REST API is unavailable and a `FabricContext` cached within the last 60 minutes for the same `career_goal` and `skill_query` combination exists, THE Reasoning_Agent SHALL use the cached data rather than skipping enrichment.
7. IF the Fabric_IQ_Service encounters a network error, HTTP 5xx, HTTP 401/403, or a connection timeout exceeding 10 seconds, THEN THE Fabric_IQ_Service SHALL return an empty `FabricContext` and log the error class and HTTP status at WARNING level without propagating an exception to the Reasoning_Agent.
8. IF `FABRIC_WORKSPACE_ID` or `FABRIC_SEMANTIC_MODEL_ID` is absent or empty, THEN THE Fabric_IQ_Service SHALL return an empty `FabricContext` and log a WARNING entry identifying the missing variable.
9. THE Fabric_IQ_Service SHALL expose a `enrich(career_goal: str, skill_query: str, token: str) -> FabricContext` function.

---

### Requirement 5: IQ Layer Orchestration

**User Story:** As the SkillLens reasoning agent, I want a single orchestration entry point that assembles all three IQ components into a unified IQ_Context so that each reasoning step receives the right intelligence without duplicating orchestration logic across multiple functions.

#### Acceptance Criteria

1. THE IQ_Layer SHALL expose an `assemble(query: str, career_goal: str, permission_token: str, graph_token: str, fabric_token: str) -> IQ_Context` function that calls Foundry_IQ_Service, Work_IQ_Service, and Fabric_IQ_Service concurrently using `asyncio.gather`.
2. WHEN all three services return successfully, THE IQ_Layer SHALL merge their outputs into a single `IQ_Context` object with `knowledge`, `work_context`, `fabric_context`, and `citations` fields.
3. WHEN one or more IQ services fail or return empty results, THE IQ_Layer SHALL populate `IQ_Context` with the results that were successfully returned and set the fields for failed services to `null`.
4. THE IQ_Layer `assemble()` function SHALL apply a per-service timeout of 4 seconds using `asyncio.wait_for`; services that exceed 4 seconds SHALL be treated as failed per Criterion 3.
5. THE Reasoning_Agent SHALL call `IQ_Layer.assemble()` exactly once per analysis request, before the profile-analysis step, and SHALL pass the returned `IQ_Context` as a parameter to each subsequent reasoning step.
6. THE IQ_Layer SHALL expose an `is_available() -> bool` function that returns `True` when both `AZURE_FOUNDRY_ENDPOINT` and `AZURE_FOUNDRY_API_KEY` are set to non-empty values, and `False` otherwise.

---

### Requirement 6: API Surface and Frontend Compatibility

**User Story:** As a SkillLens frontend developer, I want the existing agent API endpoints to continue working with the same request and response shapes so that no frontend changes are required for the core reasoning flow.

#### Acceptance Criteria

1. THE Agent_Route SHALL preserve all existing endpoint paths, HTTP methods, and request-body schemas defined before this feature without modification.
2. WHEN the IQ_Layer is active, THE Agent_Route SHALL accept an optional `iq_tokens` object in the request body of `/agent/analyze`, `/agent/simulate`, `/agent/chat`, and `/agent/job-readiness`, containing `permission_token`, `graph_token`, and `fabric_token` fields, all optional with `null` defaults. WHEN `iq_tokens` is absent from the request, all three token fields SHALL be treated as `null`.
3. THE Agent_Route SHALL include an `iq_available` boolean in every response body, including error responses with HTTP 4xx status codes, indicating whether the IQ_Layer was active for that request.
4. WHEN citations are present in an IQ_Context, THE Agent_Route SHALL include a `citations` list in the response body, where each citation contains `source` (string), `url` (string or `null`), and `excerpt` (string) fields. WHEN no citations are present, THE Agent_Route SHALL include an empty `citations` list.
5. THE Agent_Route SHALL expose a new `GET /agent/iq-status` endpoint that returns a JSON object with `foundry_iq`, `work_iq`, and `fabric_iq` boolean fields indicating whether each component is configured (credentials present and non-empty), without exposing any credential values.

---

### Requirement 7: Configuration and Credentials Management

**User Story:** As a SkillLens DevOps engineer, I want all Microsoft Foundry and IQ layer credentials managed through environment variables following the existing pattern so that secrets are never hard-coded and the application is deployable across environments.

#### Acceptance Criteria

1. THE Config SHALL load the following environment variables: `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`, `AZURE_FOUNDRY_DEFAULT_MODEL`, `AZURE_GRAPH_CLIENT_ID`, `AZURE_GRAPH_CLIENT_SECRET`, `AZURE_GRAPH_TENANT_ID`, `FABRIC_BEARER_TOKEN`, `FABRIC_WORKSPACE_ID`, and `FABRIC_SEMANTIC_MODEL_ID`.
2. THE Config SHALL treat all nine variables as optional so that the application reaches its ready state without raising an initialisation exception when none are set.
3. IF any of the nine variables is set to an empty string, THEN THE Config SHALL expose `None` for that attribute and not attempt to initialise the corresponding IQ service: `AZURE_FOUNDRY_ENDPOINT` and `AZURE_FOUNDRY_API_KEY` govern Foundry and Foundry_IQ_Service; `AZURE_GRAPH_CLIENT_ID`, `AZURE_GRAPH_CLIENT_SECRET`, and `AZURE_GRAPH_TENANT_ID` govern Work_IQ_Service; `FABRIC_BEARER_TOKEN`, `FABRIC_WORKSPACE_ID`, and `FABRIC_SEMANTIC_MODEL_ID` govern Fabric_IQ_Service.
4. THE Foundry_Client SHALL never log credential values at any log level.
5. THE application SHALL include a `.env.example` file at `backend/.env.example` documenting all nine new environment variable names with descriptive placeholder values in the form `your-<variable-description>-here` and inline comments explaining each variable's purpose.

---

### Requirement 8: Observability and Error Handling

**User Story:** As a SkillLens backend engineer, I want structured logging and graceful error handling across all IQ layer components so that I can diagnose integration issues in production without service downtime.

#### Acceptance Criteria

1. THE Foundry_IQ_Service, Work_IQ_Service, and Fabric_IQ_Service SHALL each emit a Python `logging` INFO record for every successful retrieval containing the fields: `service` (string), `query` (string), and `latency_ms` (integer).
2. WHEN an IQ service call fails, THE IQ_Layer SHALL emit a WARNING record containing: `service` (string), `error_class` (string), and `message` (string). The `message` field SHALL NOT contain any of the following: API keys, bearer tokens, client secrets, or full endpoint URLs with embedded credentials.
3. THE Reasoning_Agent SHALL emit a DEBUG record for every analysis request containing: `iq_available` (boolean), `citation_count` (integer), and `skill_signal_count` (integer).
4. IF the `asyncio.wait_for` timeout fires during `IQ_Layer.assemble()`, THEN THE IQ_Layer SHALL return a partial `IQ_Context` containing any results collected before the cutoff (with failed-service fields set to `null`) and emit a WARNING record containing: `service` (string), `error_class` (`"TimeoutError"`), and `message`.
5. WHEN cancellation of one or more pending service coroutines fails after a timeout, THE IQ_Layer SHALL emit an additional WARNING record identifying the uncancellable coroutine and continue returning the partial `IQ_Context`.
6. THE Agent_Route SHALL return HTTP 200 with `iq_available: false` in the response body rather than HTTP 500 when the IQ_Layer is unavailable or all three IQ services fail simultaneously.
