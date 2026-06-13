# Bugfix Requirements Document

## Introduction

The multi-provider AI model selection is broken in three distinct areas. First, the onboarding/signup config step only shows Groq models and defaults to a Groq model, making Gemini completely unavailable during signup. Second, several backend services fail to forward the user's selected `ai_model` to the AI provider, so all calls silently fall through to the system default regardless of user preference. Third, `DEPRECATED_GROQ_MODELS` in `groq_models.py` incorrectly remaps valid Llama 4 model IDs as if they were broken/deprecated, silently overriding the user's selection.

Together these bugs mean a user who selects a Gemini model — or a Llama 4 model — will not get that model used by the system, defeating the purpose of the model-preference feature.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a new user reaches the onboarding config step THEN the system shows only Groq model options (imported from `GROQ_MODEL_OPTIONS`) and no Gemini models are listed

1.2 WHEN a new user completes the onboarding config step THEN the system initialises `ai_model` to `llama-3.3-70b-versatile` instead of `gemini-2.0-flash`

1.3 WHEN `opportunity_service.get_suggested_opportunities()` is called for a user with no `field_of_study` set THEN the system calls `groq_services.suggest_career_opportunities()` without passing `model`, ignoring the user's `ai_model` preference entirely

1.4 WHEN any backend service calls `chat_complete()` without a `model_hint` THEN the system resolves the model from environment-variable defaults, not from the user's stored `ai_model` preference

1.5 WHEN a user selects `meta-llama/llama-4-scout-17b-16e-instruct` or `meta-llama/llama-4-maverick-17b-128e-instruct` THEN the system remaps it to `llama-3.3-70b-versatile` via `DEPRECATED_GROQ_MODELS`, silently discarding the user's choice

1.6 WHEN `SettingsPage` normalises a model ID using `normalizeGroqModel()` THEN the function name misleadingly implies Groq-only validation even though it validates all models (Gemini + Groq)

### Expected Behavior (Correct)

2.1 WHEN a new user reaches the onboarding config step THEN the system SHALL display both Gemini and Groq model options (from `ALL_MODEL_OPTIONS`) grouped by provider

2.2 WHEN a new user completes the onboarding config step THEN the system SHALL initialise `ai_model` to `gemini-2.0-flash` as the default, consistent with `DEFAULT_MODEL` in `groqModels.js`

2.3 WHEN `opportunity_service.get_suggested_opportunities()` is called for a user with no `field_of_study` set THEN the system SHALL pass `model=user.ai_model` to `suggest_career_opportunities()` so the user's provider preference is honoured

2.4 WHEN any backend service needs to call an AI provider on behalf of a user THEN the system SHALL forward the user's `ai_model` as `model_hint` to `chat_complete()` so the correct provider and model are selected

2.5 WHEN a user selects `meta-llama/llama-4-scout-17b-16e-instruct` or `meta-llama/llama-4-maverick-17b-128e-instruct` THEN the system SHALL use those model IDs as-is and SHALL NOT remap them through `DEPRECATED_GROQ_MODELS`

2.6 WHEN model IDs are normalised/validated for any provider (Gemini or Groq) THEN the system SHALL use a function named `normalizeAIModel` (or equivalent provider-agnostic name) to accurately reflect its multi-provider scope

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user selects a genuinely deprecated Groq model (e.g. `mixtral-8x7b-32768`, `llama3-70b-8192`) THEN the system SHALL CONTINUE TO remap it to the current default Groq model

3.2 WHEN no `model_hint` is provided to `chat_complete()` THEN the system SHALL CONTINUE TO fall back to the environment-configured default (Gemini if `GEMINI_API_KEY` is set, otherwise Groq)

3.3 WHEN a provider fails mid-request THEN the system SHALL CONTINUE TO cascade to the other available provider automatically

3.4 WHEN a logged-in user with an already-saved valid model preference opens `SettingsPage` THEN the system SHALL CONTINUE TO display and persist that model preference correctly

3.5 WHEN `resume_routes.py` calls `groq_services.analyze_resume_vs_jd()` with `model=user.ai_model` THEN the system SHALL CONTINUE TO honour that model for JD analysis (this path already works correctly and must not regress)

3.6 WHEN `interview_service.py` calls `groq_services.generate_interview_question()` and `evaluate_interview_answer()` with `model=model` THEN the system SHALL CONTINUE TO honour the user's model for interview sessions (this path already works correctly and must not regress)
