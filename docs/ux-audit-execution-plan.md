# ChatGPT-Grade UX Audit Execution Plan

Date: 2026-03-03  
Branch: `audit/chatgpt-grade-ux-20260303-132402`

## Objective
Upgrade chat UX, conversational quality, itinerary formatting reliability, streaming stability, frontend security posture, and E2E confidence to ChatGPT-grade quality without risking production deployment.

## Step Sequence
1. Baseline audit
- Inspect frontend chat render pipeline, stream parser, markdown renderer, itinerary UI, and backend prompt/orchestrator flow.
- Identify UX gaps vs ChatGPT-style expectations (clarity, pacing, natural tone, structured follow-ups, no reasoning leakage).

2. Document UX gap analysis
- Create `/docs/chatgpt-ux-gap-analysis.md` with weaknesses, severity, and direct ChatGPT-style behavior comparisons.

3. Conversational framing rewrite
- Tighten clarification and response prompt contracts.
- Enforce context sentence + one clear question + structured options + gentle CTA pattern.
- Reduce robotic wording and question overload.

4. Itinerary output hardening
- Standardize itinerary markdown shape and section consistency.
- Ensure day headers, section bullets, and budget/stay details stay stable.
- Prevent duplicate day rendering through normalization and deterministic formatting helpers.

5. Streaming stability and render fixes
- Validate token accumulation, no duplicate assistant bubbles, no re-mount loops, stable auto-scroll, and graceful error handling.
- Ensure no tool/debug/raw JSON leaks in user-visible chat stream.

6. Full Playwright E2E implementation
- Expand test coverage in `/tests/e2e/`:
  - Basic conversation
  - Clarification structure
  - Itinerary generation formatting
  - Streaming stability under slow delivery
  - Backend error handling
  - Multi-turn memory continuity
  - Mobile readability

7. Frontend security hardening
- Audit markdown sanitization and ensure no unsafe HTML/script execution vectors.
- Remove/replace avoidable risky patterns (e.g., inline script injection patterns).
- Prevent stack/internal error exposure to end users.

8. Performance checks
- Reduce unnecessary re-renders/state churn in chat message rendering.
- Validate no severe layout thrashing during stream updates.

9. Validation gates
- Run lint/build/tests after major implementation groups.
- Fix regressions before concluding.

10. Delivery summary
- Provide modified files, UX deltas, E2E coverage, residual risks, confidence and readiness scores.

## Risk Analysis
1. Streaming contract regressions
- Risk: breaking SSE parsing or event ordering.
- Mitigation: keep event schema unchanged; add E2E stream assertions for token/status/error behavior.

2. Prompt over-constraint
- Risk: responses become rigid or unnatural.
- Mitigation: constrain structure for clarifications while keeping natural tone and concise style requirements.

3. Test flakiness
- Risk: unstable E2E due to live auth/backend dependencies.
- Mitigation: deterministic fetch mocking in Playwright init script; explicit waits and strict assertions.

4. UI regressions in existing chat flows
- Risk: modifications to message rendering impact edit/delete/history behavior.
- Mitigation: preserve existing APIs and validate key interactive paths in tests.

5. Deployment safety
- Risk: accidental push/merge to `main`.
- Mitigation: all work isolated on current audit branch only; no merge operations.

## Expected Breakpoints
1. Markdown rendering edge cases
- Table parsing and mixed markdown/stream chunks may expose malformed blocks.

2. Itinerary format normalization
- Partial or sparse itinerary payloads may miss expected fields.

3. Mobile rendering density
- Day sections and long bullet text can overflow without spacing constraints.

4. Auth bypass behavior in E2E
- Dev bypass flow can drift with env changes; tests should pin expected local bypass token behavior.

## Rollback Plan
1. Keep changes scoped by phase and file so each phase can be reverted independently with `git restore --source <commit>` on this branch.
2. If streaming behavior regresses, roll back only stream/parser and chat-page rendering commits first.
3. If prompt changes degrade response quality, roll back prompt-layer edits while retaining UI/security/e2e improvements.
4. If E2E changes destabilize CI locally, keep tests behind existing script entrypoint and revert only failing suite files.
5. Do not merge until lint/build/e2e checks pass on this branch.
