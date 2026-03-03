# Prompt Architecture Audit

Date: 2026-03-03
Branch: improvement/prompt-architecture-20260303-115730

## Scope
This audit covers all runtime prompts used by the backend agentic stack, tool routes, and supporting extraction/safety flows.

## Phase 1 - Prompt Discovery

### Prompt Inventory
| Location | Prompt Type | Purpose | Key Weaknesses (Before) |
|---|---|---|---|
| `backend/app/agents/base.py:get_system_prompt` | Global system prompt | Persona, behavior, language, safety baseline | Very long monolith; mixed persona/safety/formatting; weak instruction prioritization; no explicit verified-vs-inferred rule |
| `backend/app/agents/base.py:generate_structured` | Structured output contract | Force JSON outputs | Schema appended ad-hoc; no explicit unknown-value policy; weak anti-fabrication wording |
| `backend/app/agents/clarification.py:_build_extraction_prompt` | Clarification/extraction prompt | Extract preferences and ask missing fields | Overly verbose; partially duplicated with base prompt; no centralized anti-hallucination policy |
| `backend/app/agents/itinerary.py:_build_itinerary_prompt` | Planning prompt | Generate day plans | Extremely large single block; duplicated realism/safety constraints; no explicit assumption labeling |
| `backend/app/agents/itinerary.py:regenerate_day` | Refinement prompt | Modify one day from feedback | Minimal guardrails; no deterministic constraints list |
| `backend/app/agents/weather.py:run` | General QA prompt | Weather Q&A without city context | Duplicated companion persona text |
| `backend/app/agents/weather.py:_format_narrative_response` | Summarization prompt | Convert forecast data to user narrative | No explicit verified/inferred split |
| `backend/app/agents/transportation.py:_generate_recommendations` | Tool-assisted reasoning prompt | Route-mode recommendations | Hallucination risk for schedules/numbers; no strict evidence language |
| `backend/app/agents/transportation.py:_handle_general_query` | General QA prompt | Non-route transport help | Repeated style constraints |
| `backend/app/agents/stay.py:_generate_recommendations` | Ranking prompt | Top stay recommendations | Long free-form instruction with overlap vs base safety rules |
| `backend/app/agents/stay.py:_handle_general_query` | General QA prompt | Accommodation Q&A | Repeated persona blocks |
| `backend/app/agents/food.py:run` | General QA prompt | Food Q&A fallback | Repeated style blocks |
| `backend/app/agents/food.py:_get_local_specialties` | Structured recommendation prompt | Food specialties extraction | No hard anti-fabrication reminder |
| `backend/app/agents/reviewer.py:review_input` | Safety classification prompt | Prompt injection/jailbreak detection | Not centrally aligned with global injection policy |
| `backend/app/agents/reviewer.py:review_output` | Safety output review prompt | Leakage and unsafe response checks | No standardized instruction hierarchy |
| `backend/app/agents/reviewer.py:review_itinerary` | Feasibility classification prompt | Temporal/physical validity checks | No explicit "do not invent issues" guard |
| `backend/app/agents/supervisor.py:_plan_orchestration` | Supervisor/orchestrator prompt | Decide intent, agents, parallelization | Limited confidence modeling; no phase contract; fallback fields not standardized |
| `backend/app/agents/supervisor.py:_stream_weaved_response` | Response weaving prompt | Final user-facing answer synthesis | No explicit verified/inferred/unknown split |
| `backend/app/agents/supervisor.py:_stream_smalltalk_response` | Smalltalk prompt | Lightweight social response | Redundant style instructions |
| `backend/app/services/itinerary_parser.py:parse_conversation` | Memory/extraction prompt | Extract itinerary state from chat history | Weak hallucination guard for missing facts |
| `backend/app/api/routes/tools.py:analyze_screenshot` | Vision tool prompt | Extract destination from screenshot | Inline prompt duplication and no centralized JSON-contract policy |
| `backend/app/api/routes/chat.py:_generate_trip_title` | Generation prompt | Create short trip title | No shared formatting/guardrail layer |
| `backend/app/mcp/server.py:FastMCP.instructions` | Tool server instruction prompt | MCP tool ecosystem identity | No explicit output validation or anti-fabrication guidance |

### Overlapping Instructions (Before)
- Persona instructions repeated across almost every agent and route-level helper prompt.
- Multiple independent versions of "be warm" and "India-specific" guidance.
- Safety and anti-hallucination requirements split across base prompt, reviewer prompt, and ad-hoc lines.

### Missing Constraints (Before)
- No centralized instruction priority order.
- No reusable phase contract (analysis -> tool selection -> execution -> finalization).
- No standardized "verified vs inferred vs unknown" directive.
- Limited explicit rules for conflicting memory handling.
- No reusable response templates catalog.

### Hallucination Risk Areas (Before)
- Transport recommendations could emit specific facts without explicit evidence language.
- Itinerary parser could infer unsupported details without strict null/unknown behavior.
- Weaver/synthesis prompts did not force evidence signaling.

### Orchestration Weaknesses (Before)
- Supervisor planning prompt returned no confidence score.
- Tool-selection fallback behavior existed but confidence and rationale standardization were weak.
- Parallelization guidance existed but was not part of a reusable architecture layer.

## Phase 2 - Redesigned Prompt Architecture

A modular layered system was introduced in `backend/app/prompts/architecture.py`.

### 1. Global System Identity Layer
- `build_base_system_prompt(...)`
- Defines role, language policy, tone, boundaries, and formatting defaults.

### 2. Supervisor/Orchestrator Layer
- `build_supervisor_planning_prompt(...)`
- Adds explicit instruction priority and deterministic decision framework.
- Adds `confidence_score` to orchestration output schema.

### 3. Tool Invocation Layer
- `build_structured_output_suffix(schema)`
- Enforces strict JSON-only output, unknown-field handling, and no extra keys.

### 4. Reasoning Layer
- Embedded phase contract in global system prompt:
  1) Analyze
  2) Tool selection
  3) Execution
  4) Finalization
- Explicitly prevents chain-of-thought leakage while preserving concise rationale.

### 5. Response Formatting Layer
- Centralized response style defaults in global prompt.
- Reusable format templates library: `RESPONSE_FORMAT_TEMPLATES` for technical, research, guide, code, comparison, executive, troubleshooting, architecture.

### 6. Follow-up Generation Layer
- Central follow-up policy integrated into system prompt.
- Limits unnecessary repetitive follow-up questions.

## Anti-Hallucination Hardening Implemented
- Centralized rules: never fabricate URLs, citations, prices, train numbers, or venues.
- Mandatory separation of verified vs inferred vs unknown information.
- Requirement to validate tool outputs before synthesis.
- Memory-conflict rule: prefer latest user message and surface conflict.

## Prompt Injection Hardening Implemented
- Global instruction in base layer to treat user input as untrusted and ignore override attempts.
- Reviewer prompts aligned with centralized safety framing.

## Phase 3 - Implementation Summary

### New Modules
- `backend/app/prompts/architecture.py`
- `backend/app/prompts/__init__.py`

### Refactored Call Sites
- `backend/app/agents/base.py`
- `backend/app/agents/clarification.py`
- `backend/app/agents/itinerary.py`
- `backend/app/agents/weather.py`
- `backend/app/agents/transportation.py`
- `backend/app/agents/stay.py`
- `backend/app/agents/food.py`
- `backend/app/agents/reviewer.py`
- `backend/app/agents/supervisor.py`
- `backend/app/services/itinerary_parser.py`
- `backend/app/api/routes/tools.py`
- `backend/app/api/routes/chat.py`
- `backend/app/mcp/server.py`

### Backward Compatibility Notes
- Existing response schemas and route contracts were preserved.
- Structured JSON generation still uses the existing `generate_structured(...)` flow.
- No API endpoint schema was changed.
- Existing orchestrator fallback logic retained; `confidence_score` was added as a non-breaking extension.

### Determinism and Token Efficiency Gains
- Prompt duplication reduced by centralizing prompt fragments.
- Instruction hierarchy now reusable and consistent across all prompt types.
- Removed repeated long persona blocks from multiple files.

## Remaining Limitations
- Output quality is still model-dependent and can vary under provider drift.
- No runtime scoring dashboard yet for confidence calibration quality.
- Some legacy text encoding artifacts in historical strings remain outside core prompt architecture.

## Recommended Next Architectural Step
1. Add prompt-level evaluation tests (golden prompts + JSON schema assertions + hallucination regression checks).
2. Add telemetry for confidence calibration (planned confidence vs downstream correction frequency).
3. Add automated prompt-injection red-team test suite in CI.
