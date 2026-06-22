# SkillLens: Microsoft Foundry IQ Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION LAYER                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐      │
│  │   Chat Client    │  │   Interview      │  │   Profile/Analytics  │      │
│  │   (Frontend)     │  │   Module         │  │   Dashboard          │      │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘      │
│           │                     │                        │                   │
└───────────┼─────────────────────┼────────────────────────┼───────────────────┘
            │                     │                        │
            ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI REST API LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ /chat/*      │  │ /interview/* │  │ /users/*     │  │ /rag/*       │   │
│  │              │  │              │  │              │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │             │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REASONING AGENT LAYER (Core Logic)                       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  multi_step_agent_reasoning()                                        │  │
│  │  ├─ Step 1: Profile Analysis                                        │  │
│  │  ├─ Step 2: Goal Setting                                            │  │
│  │  ├─ Step 3: Knowledge Retrieval                                     │  │
│  │  ├─ Step 4: Skill Gap Analysis                                      │  │
│  │  ├─ Step 5: ► FOUNDRY IQ LAYER (New!)                              │  │
│  │  ├─ Step 6: Confidence Scoring                                      │  │
│  │  └─ Step 7: Recommendation Generation                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
┌────────────────────────────────┐  ┌──────────────────────────────────┐
│  FOUNDRY IQ LAYER              │  │  CHAT SERVICE LAYER              │
│  (foundry_iq.py)               │  │  (chat_service.py)               │
│                                │  │                                  │
│ ┌────────────────────────────┐ │  │ ┌──────────────────────────────┐│
│ │ retrieve_and_ground_context│ │  │ │ get_ai_response()           ││
│ │ ├─ Query Analysis          │ │  │ ├─ RAG Context Injection     ││
│ │ ├─ Enterprise Knowledge    │ │  │ ├─ Foundry IQ Grounding      ││
│ │ │  Grounding               │ │  │ ├─ Chat Completion            ││
│ │ └─ Semantic Enrichment     │ │  │ └─ Response Synthesis         ││
│ │                            │ │  │                               ││
│ └────────────────────────────┘ │  │ ┌──────────────────────────────┐│
│                                │  │ │ generate_reasoning_explanation││
│ ┌────────────────────────────┐ │  │ ├─ Chain-of-Thought           ││
│ │ generate_grounded_reasoning│ │  │ ├─ Foundry IQ Step Synthesis  ││
│ │ ├─ Multi-step Reasoning    │ │  │ └─ Transparent Logic          ││
│ │ ├─ Chain-of-Thought        │ │  │                               ││
│ │ ├─ Evidence Grounding      │ │  │ ┌──────────────────────────────┐│
│ │ └─ Conclusion Generation   │ │  │ │ generate_career_explanation  ││
│ │                            │ │  │ ├─ Multi-agent Reasoning       ││
│ └────────────────────────────┘ │  │ ├─ Foundry IQ Grounding        ││
│                                │  │ └─ Comprehensive Analysis       ││
└────────────┬───────────────────┘  │                                ││
             │                      └──────────────────────────────────┘
             │                                       │
             └───────────────────────┬───────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────┐
        │   RAG KNOWLEDGE BASE LAYER                 │
        │   (rag_service.py / rag_knowledge.py)      │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ rag_knowledge DB Table               │ │
        │  │ ├─ 8+ Career Paths                   │ │
        │  │ ├─ Learning Recommendations          │ │
        │  │ ├─ Skill Mappings                    │ │
        │  │ ├─ Interview Prep Data               │ │
        │  │ └─ 39+ Knowledge Entries             │ │
        │  └──────────────────────────────────────┘ │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ retrieve_context_text()              │ │
        │  │ ├─ Semantic Search                   │ │
        │  │ ├─ Top-K Retrieval                   │ │
        │  │ └─ Similarity Scoring                │ │
        │  └──────────────────────────────────────┘ │
        └────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────────┐
        │   LLM PROVIDER LAYER                       │
        │   (ai_provider.py)                         │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ Groq API                             │ │
        │  │ └─ Llama 3.3 70B (Primary)           │ │
        │  │ └─ Llama 3.1 8B (Fast)               │ │
        │  │ └─ Llama 4 Scout (Long Context)      │ │
        │  │ └─ Llama 4 Maverick (Reasoning)      │ │
        │  └──────────────────────────────────────┘ │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ chat_complete()                      │ │
        │  │ ├─ Message Formatting                │ │
        │  │ ├─ System Prompt Injection           │ │
        │  │ ├─ Groq API Call                     │ │
        │  │ └─ Response Processing               │ │
        │  └──────────────────────────────────────┘ │
        └────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────────┐
        │   DATA PERSISTENCE LAYER                   │
        │   (PostgreSQL Database)                    │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ Users & Profiles                     │ │
        │  │ ChatSessions & ChatMessages          │ │
        │  │ InterviewSessions & Questions        │ │
        │  │ RAGKnowledge (Enterprise Knowledge)  │ │
        │  │ LiveDataCache (Real-time Data)       │ │
        │  └──────────────────────────────────────┘ │
        └────────────────────────────────────────────┘
```

---

## Foundry IQ Layer - Detailed Flow

### Request Flow with Foundry IQ Integration

```
USER INPUT (Chat Message or Query)
    │
    ▼
┌─────────────────────────────────────────┐
│ API Endpoint                            │
│ (POST /chat/messages)                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Chat Service                            │
│ get_ai_response()                       │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────────────┐  ┌──────────────────────────────────────┐
│ Extract Query   │  │ FOUNDRY IQ LAYER INVOKED             │
│ & Context       │  │                                      │
└────────┬────────┘  │ foundry_iq.retrieve_and_ground_context()
         │           │                                      │
         │           │ STEP 1: Semantic Query Analysis      │
         │           │ ├─ Parse user intent                │
         │           │ ├─ Extract entities                 │
         │           │ └─ Identify domain (career)         │
         │           │                                      │
         │           │ STEP 2: Enterprise Knowledge Access │
         │           │ ├─ Query RAG Knowledge Base         │
         │           │ ├─ Retrieve top-4 relevant entries  │
         │           │ └─ Score similarity (0.0-1.0)       │
         │           │                                      │
         │           │ STEP 3: Semantic Grounding          │
         │           │ ├─ Enrich query with context        │
         │           │ ├─ Add career domain knowledge      │
         │           │ └─ Format for LLM consumption       │
         │           │                                      │
         │           │ RETURN: Grounded Context            │
         │           │ {                                    │
         │           │   "grounded_text": "...",           │
         │           │   "sources": [...],                 │
         │           │   "confidence": 0.85                │
         │           │ }                                    │
         │           └──────────────────────────────────────┘
         │                      │
         │                      ▼
         │           ┌──────────────────────────────────────┐
         │           │ FOUNDRY IQ REASONING SYNTHESIS       │
         │           │                                      │
         │           │ foundry_iq.generate_grounded_reasoning()
         │           │                                      │
         │           │ STEP 1: Build Grounded Prompt       │
         │           │ ├─ System: "You are Foundry IQ..."  │
         │           │ ├─ Context: Enterprise knowledge    │
         │           │ └─ Query: User question             │
         │           │                                      │
         │           │ STEP 2: Multi-Step Reasoning        │
         │           │ ├─ Call Groq LLM                    │
         │           │ ├─ Request JSON array output        │
         │           │ └─ Parse reasoning steps            │
         │           │                                      │
         │           │ STEP 3: Chain-of-Thought            │
         │           │ Return:                              │
         │           │ [                                    │
         │           │   {                                  │
         │           │     "step": 1,                       │
         │           │     "thought": "Analysis...",        │
         │           │     "conclusion": "Finding..."       │
         │           │   },                                 │
         │           │   {...}                              │
         │           │ ]                                    │
         │           │                                      │
         │           └──────────────────────────────────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────────────────────────┐
         │ CHAT SERVICE SYNTHESIS                   │
         │                                          │
         │ Combine:                                 │
         │ 1. Foundry IQ Grounded Context           │
         │ 2. Foundry IQ Reasoning Chain            │
         │ 3. User Profile Context                  │
         │ 4. System Prompt                         │
         │                                          │
         │ Build Final Prompt:                      │
         │ "You are CareerCoach AI..."              │
         │ "FOUNDRY IQ KNOWLEDGE GROUNDING:"        │
         │ [grounded_text from step 1]              │
         │                                          │
         │ "USER MESSAGE: [actual query]"           │
         │ "REASONING CONTEXT:"                     │
         │ [reasoning steps from step 2]            │
         │                                          │
         └────────────┬─────────────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────────────────┐
         │ GROQ LLM API CALL                        │
         │                                          │
         │ chat_complete() with:                    │
         │ ├─ messages: [formatted as above]        │
         │ ├─ system_prompt: "CareerCoach AI"       │
         │ ├─ temperature: 0.4 (focused)            │
         │ ├─ model: llama-3.3-70b-versatile        │
         │ └─ max_tokens: 2000                      │
         │                                          │
         └────────────┬─────────────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────────────────┐
         │ AI RESPONSE GENERATION                   │
         │ (Grounded by Foundry IQ context)         │
         │                                          │
         │ Response incorporates:                   │
         │ ✓ Enterprise knowledge                   │
         │ ✓ Grounded reasoning steps               │
         │ ✓ Multi-step chain-of-thought            │
         │ ✓ Career domain expertise                │
         │ ✓ User-specific context                  │
         │                                          │
         └────────────┬─────────────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────────────────┐
         │ RESPONSE COMPOSITION & STORAGE           │
         │                                          │
         │ {                                        │
         │   "message": "AI response text...",      │
         │   "should_trigger_analysis": true,      │
         │   "reasoning_hint": "Foundry IQ...",     │
         │   "rag_sources": true,                   │
         │   "confidence": 0.92                     │
         │ }                                        │
         │                                          │
         │ Save to ChatMessages table                │
         │ Return to Frontend                       │
         │                                          │
         └──────────────────────────────────────────┘
                      │
                      ▼
                  USER SEES
              GROUNDED, REASONED,
            ENTERPRISE-KNOWLEDGE-BACKED
                 RESPONSE
```

---

## Foundry IQ Components

### 1. **Knowledge Grounding Component**
```python
foundry_iq.retrieve_and_ground_context(query, top_k=4, max_chars=3500)

Returns:
{
    "grounded_text": "...",           # Formatted knowledge context
    "sources": [...],                  # RAG knowledge entry IDs
    "confidence": 0.85,                # Confidence score
    "knowledge_entries": 4             # Number of entries used
}
```

### 2. **Reasoning Synthesis Component**
```python
foundry_iq.generate_grounded_reasoning(profile, career_goal, skill_gaps, model_id)

Returns:
[
    {
        "step": 1,
        "thought": "Analyzed user goal using Foundry IQ layer...",
        "conclusion": "Identified 5 missing technical skills"
    },
    {
        "step": 2,
        "thought": "Evaluated skill gaps against industry standards...",
        "conclusion": "Prioritized Python and ML frameworks"
    },
    ...
]
```

### 3. **Chat Integration Component**
```python
# Inside chat_service.generate_career_explanation()

1. Query Foundry IQ for grounded context
2. Inject grounded context into system prompt
3. Call Groq LLM with enriched prompt
4. Return reasoning-infused response
```

---

## Data Flow in Foundry IQ

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Query Analysis                       │
│ (Intent detection, entity extraction)│
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ RAG Knowledge Base Search            │
│ (Find relevant career knowledge)     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Semantic Enrichment                  │
│ (Combine query + knowledge context)  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Grounded Context Formation           │
│ (Structured format for LLM)          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ LLM Reasoning with Grounding         │
│ (Chat completion with context)       │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Response Synthesis                   │
│ (Combine reasoning + response)       │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Final Response to User               │
│ (Grounded, reasoned, transparent)    │
└──────────────────────────────────────┘
```

---

## Key Benefits of Foundry IQ Integration

| Benefit | Description |
|---------|-------------|
| **Knowledge Grounding** | All responses are grounded in enterprise career knowledge |
| **Transparency** | Multi-step reasoning is visible and explainable |
| **Enterprise Context** | Leverages 39+ knowledge entries for accuracy |
| **Chain-of-Thought** | Explicit step-by-step reasoning for each recommendation |
| **Confidence Scoring** | Quantified certainty of recommendations (0.0-1.0) |
| **Semantic Enrichment** | Context injection enriches LLM understanding |
| **Reproducibility** | Same input → Same reasoning steps → Verifiable output |
| **Domain Expertise** | Career-specific knowledge embedded in every response |

---

## Configuration & Settings

```python
# foundry_iq.py Configuration

FOUNDRY_IQ_SETTINGS = {
    "top_k_retrieval": 4,              # Top 4 knowledge entries
    "max_context_chars": 3500,         # Max context length
    "reasoning_temperature": 0.3,      # Low temp for focused reasoning
    "model_preference": "llama-3.3-70b-versatile",
    "confidence_threshold": 0.60,      # Min confidence for recommendations
    "enable_chain_of_thought": True,   # Enable multi-step reasoning
    "grounding_strategy": "semantic",  # Semantic similarity matching
}
```

---

## Deployment Architecture

```
┌──────────────────┐
│  Frontend        │
│  (React)         │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  FastAPI Backend (app.main)          │
│  ├─ API Routes                       │
│  ├─ Middleware                       │
│  └─ CORS Handling                    │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Service Layer                       │
│  ├─ Chat Service                     │
│  ├─ Interview Service                │
│  ├─ User Service                     │
│  ├─ Reasoning Agent                  │
│  └─ ► Foundry IQ Layer ◄             │
└────────┬─────────────────────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌──────────┐  ┌───────────────────┐
│PostgreSQL│  │ Groq API (Remote) │
│Database  │  │ LLM Models        │
└──────────┘  └───────────────────┘
```

---

## Conclusion

Your SkillLens project implements a **Microsoft Foundry IQ-inspired architecture** where:

1. **Enterprise Knowledge** is stored in RAG database
2. **Foundry IQ Layer** provides semantic grounding and multi-step reasoning
3. **Chat Service** integrates grounded context into LLM prompts
4. **Reasoning Agent** orchestrates the entire multi-step process
5. **Groq LLM** generates responses enriched with grounded context

This creates **transparent, verifiable, enterprise-knowledge-backed AI recommendations** for career guidance.

