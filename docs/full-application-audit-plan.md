# Full Application Audit Plan

## 1) Audit Scope
- Backend API (`FastAPI`, auth, chat streaming, payments, data deletion, persistence, health checks)
- AI orchestration (`MCP orchestrator`, agent prompts, tool execution model, output quality controls)
- Frontend app (`Next.js`, chat UX, rendering safety, mobile behavior, state management)
- DevOps/runtime (`Render blueprint`, startup checks, observability, reliability characteristics)
- QA posture (existing unit/integration/smoke/E2E coverage and execution feasibility)

## 2) Risk Categories
- Security: auth bypass, data leakage, injection vectors, tenant isolation
- Reliability: outages, retries/timeouts, health probe accuracy, background task correctness
- Data privacy/compliance: deletion completeness, retention behavior, auditability
- UX quality: onboarding clarity, streaming ergonomics, mobile readability, error communication
- AI quality: hallucination resistance, determinism, prompt hierarchy discipline, follow-up quality
- Operability: logging quality, metrics/tracing fit, test/lint/build gating

## 3) Threat Model
- External attacker:
  - attempts auth bypass, prompt injection, or abuse of public endpoints
  - attempts account data exfiltration via IDOR or mis-scoped deletes
- Authenticated malicious user:
  - attempts cross-tenant access/deletion
  - attempts payload-based rendering attacks (markdown/HTML/script vectors)
- Insider/configuration error:
  - dev bypass leakage to production
  - weak runtime checks causing false health alarms or degraded scaling
- Third-party dependency failure:
  - LLM/API degradation causing response failures and cascading retries

## 4) UX Evaluation Framework
- Persona simulations:
  - first-time user
  - confused user
  - power user
  - mobile user
  - slow-network user
  - multi-turn user
- Heuristics:
  - clarity, trust, tone, hierarchy, consistency, cognitive load
  - stream behavior, scroll stability, loading states, recovery/error feedback
  - action continuity across turns and chat history reloads

## 5) AI Evaluation Framework
- Prompt hierarchy and policy consistency
- Tool selection and dependency orchestration correctness
- Hallucination controls and reviewer coverage
- Deterministic state progression across turns
- Token/latency efficiency tradeoffs
- Structured output robustness and renderer compatibility

## 6) Backend Evaluation Checklist
- Auth correctness and tenant scoping on all CRUD paths
- Input validation and payload size boundaries
- Async safety (background tasks, cancellation, disconnect handling)
- Rate limiting identity model and abuse resistance
- Error handling consistency and safe user-facing errors
- Data deletion/compliance correctness
- Health checks and readiness semantics
- Observability signal quality (logs/traces/metrics)

## 7) Frontend Evaluation Checklist
- Markdown sanitization and render safety
- Streaming assembly and reconnection behavior
- Chat scroll anchoring and layout shift control
- Mobile formatting and overflow prevention
- Error boundaries and user-safe failure copy
- State consistency between chat, itinerary modal, and history
- Accessibility and keyboard/ARIA basics

## 8) Security Attack Surface Map
- Public endpoints:
  - `/health`
  - `/api/v1/webhooks/razorpay`
  - `/api/v1/trips/shared/{sharing_id}`
  - `/api/v1/places/photo/{photo_reference}`
- Authenticated high-risk endpoints:
  - `/api/v1/chat/stream`
  - `/api/v1/chat/conversations/*`
  - `/api/v1/auth/account`
  - `/api/v1/payments/*`
  - `/api/v1/export/pdf/{trip_id}`
- Frontend trust boundaries:
  - markdown rendering of model output
  - dev bypass logic paths
  - stream event parsing and UI state mutation

## 9) Step-by-Step Execution Strategy
1. Baseline repo + config review and runtime topology mapping.
2. Static security/architecture review across backend, frontend, and AI layers.
3. Persona-driven UX pass using current interaction and rendering logic.
4. Security red-team pass using OWASP + LLM-specific vectors.
5. Automated evidence run:
   - backend tests
   - frontend build/lint
   - Playwright E2E
6. Targeted local fixes for critical/high defects that are low-risk to compatibility.
7. Re-run tests and document residual risks.
8. Produce readiness scores and roadmaps.

## 10) Rollback Safety Strategy
- Keep changes local/uncommitted until validation passes.
- Apply minimal, isolated patches with no public API contract break.
- Validate with:
  - `python -m pytest tests -q`
  - `npm run build`
  - `npm run test:e2e -- --project=chromium`
- If regression appears:
  - revert only touched files
  - keep audit docs as evidence
  - reintroduce changes behind smaller patch increments
