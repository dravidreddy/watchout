# Frontend Rendering Audit

Date: 2026-03-03  
Branch: `audit/frontend-rendering-20260303-124700`

## Scope
- Frontend chat rendering pipeline (`/chat`) and itinerary UI surfaces.
- Frontend/backend SSE contract (`/api/v1/chat/stream`).
- Markdown rendering, structured content rendering, streaming stability, and error states.
- Conversational clarification framing templates in backend prompts.

## Findings (Pre-Fix)

### High
1. **Itinerary schema mismatch caused missing activity times**
- Frontend itinerary UIs expected `stop.time`.
- Backend itinerary objects commonly provided `stop.arrival_time`.
- Impact: day timelines rendered with blank or broken timing context.

2. **Chat history preview mismatch**
- Frontend expected `conversation.messages[-1]`.
- Backend returns `last_message`.
- Impact: history list showed "No messages" even when content existed.

3. **Streaming retry could duplicate content/side effects**
- Chat stream default retries could resend the same message request.
- Impact: duplicate assistant text and potential duplicate persisted turns when network was unstable.

### Medium
4. **Chat markdown rendering lacked robust structured output support**
- Tables were not consistently rendered from markdown table syntax.
- Link safety constraints were not consistently enforced in active chat page renderer.

5. **Stream error/cancel events were not user-visible enough**
- Error events were logged but not clearly surfaced inside chat message flow.
- Impact: users saw failed interactions without reliable in-thread explanation.

6. **Auto-scroll behavior could jitter during streaming**
- Smooth scrolling on every message update produced instability during token streaming.

7. **Potential JSON/raw object leakage into chat bubble**
- If assistant output was structured JSON text, UI could display raw blobs directly.

### Low
8. **Dead/legacy code in active chat page**
- Unused state and stale exploratory comments increased maintenance risk.

## Fixes Implemented

### Rendering + Contract Hardening
- Added itinerary normalization utility: `frontend/src/lib/itinerary.ts`.
- Standardized itinerary consumption in:
  - `frontend/src/app/(authenticated)/chat/page.tsx`
  - `frontend/src/components/chat/ItineraryModal.tsx`
  - `frontend/src/components/chat/ItineraryPreview.tsx`
- Normalization now:
  - maps `arrival_time`/`departure_time` to display time fallback,
  - handles budget aliases,
  - deduplicates duplicate day entries and resequences day numbers.

### Markdown + Structured Output
- Added safe markdown renderer with table support and safe-link policy:
  - `frontend/src/components/chat/MarkdownRenderer.tsx`
- Integrated renderer in active chat message bubble.
- Added structured-content coercion guard to reduce raw JSON leakage in assistant bubbles.

### Streaming Stability + UX
- Chat stream retries disabled for `/chat/stream` calls (`maxRetries=0`) to prevent duplicate generations.
- Added explicit in-thread handling for `error` and `cancelled` stream events.
- Added pending assistant loading state (`Thinking...`) for active stream bubble.
- Reworked auto-scroll:
  - only auto-scrolls when user is near bottom or while actively streaming,
  - reduces flicker/layout instability during token updates.

### Chat History Correctness
- Updated history card mapping to backend payload (`last_message`).
- Corrected trip selection/highlight logic and action menu ID handling.

### Conversational Framing Improvements
- Updated clarification prompt contract:
  - one primary question at a time,
  - concise numbered options,
  - tighter length/style constraints.
- Updated clarification fallback wording to structured, natural option-based prompt.

## Playwright Coverage Added
- Config updated to use `frontend/tests/e2e`.
- Added `frontend/tests/e2e/chat-rendering.spec.ts` covering:
  - streaming markdown with lists + table rendering,
  - follow-up framing visibility,
  - itinerary rendering from streamed structured payload,
  - no obvious raw JSON leakage assertions,
  - slow-stream loading-state behavior,
  - stream error state rendering without layout collapse,
  - console/page error checks for unhandled runtime failures.

## Severity Summary
- High: 3 issues
- Medium: 4 issues
- Low: 1 issue

## Residual Risks
- Markdown table parsing is custom and intentionally minimal; complex edge-case tables may still need a full GFM parser.
- E2E tests use mocked SSE streams; production network/proxy SSE behaviors should still be validated in staging.
- Some legacy chat components remain in repo and are not active route owners.

## Overall Assessment
- Frontend rendering pipeline is materially improved for streaming, structured markdown, itinerary schema drift, and error visibility.
- Backend clarification framing now better matches natural, structured ChatGPT-like clarification flow.
- With build/test validation passing, this branch is substantially safer for production UX than baseline.
