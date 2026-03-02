# Full Code Audit Report

Date: 2026-03-02
Repository: Watchout
Branch: audit/code-review-20260302-190146
Auditor: Codex (Staff-level engineering/security/devops review)

## Executive Summary

This repository has strong foundational architecture (typed FastAPI routes, Firebase auth dependency, ownership checks in most trip/chat paths, structured error envelopes, and initial observability hooks). However, several critical production risks were identified in authorization boundaries, payment verification trust, route/runtime correctness, and deployment reliability.

Most critical findings are concentrated in payment and profile update flows where client input can influence subscription state. There are also high-impact runtime correctness issues (undefined symbol, duplicate route declaration, wrong config attribute) that can cause endpoint failure or API ambiguity under production traffic.

Overall risk score: **8/10 (High)** before fixes.

## Scope

- Backend: FastAPI app, auth, payments, webhooks, chat, trips, services, db layer
- Frontend: Next.js API client/auth/payment integration and runtime configuration
- Infra: Render deployment blueprints and production startup assumptions
- Security: OWASP Top 10, secrets handling, authz, input validation, injection vectors, CORS, rate limiting
- Production readiness: health, shutdown, retries, scheduler safety, observability readiness

## Critical Issues

1. **Privilege escalation via profile update** (Critical)
- File: `backend/app/api/routes/auth.py`
- Issue: `/auth/me` permits direct write to `subscription_tier` from client input.
- Risk: Any authenticated user can self-upgrade without payment.
- Category: Broken Access Control (OWASP A01).

2. **Payment tier trusts client `plan_id`** (Critical)
- File: `backend/app/api/routes/payments.py`
- Issue: `/payments/verify` uses `plan_id` from request body to set DB subscription tier.
- Risk: User can pay lower tier (or replay) and claim higher tier.
- Category: Integrity/authz flaw.

3. **Payment verification lacks strict server-side order consistency checks** (Critical)
- File: `backend/app/api/routes/payments.py`
- Issue: Signature check occurs, but tier/user assignment is not fully derived from trusted order metadata.
- Risk: Business logic tampering and inconsistent payment-state mapping.
- Category: Broken business logic.

4. **Duplicate route declaration for same path** (Critical)
- File: `backend/app/api/routes/trips.py`
- Issue: `/trips/shared/{sharing_id}` is declared twice with different response models.
- Risk: Contract ambiguity, unexpected handler precedence, client breakage.
- Category: API contract/runtime correctness.

## High Severity Findings

1. **Undefined symbol in chat cancel endpoint** (High)
- File: `backend/app/api/routes/chat.py`
- Issue: `get_supervisor()` referenced without import in current orchestrator-based route module.
- Risk: Runtime failure on `/chat/cancel`.

2. **Wrong settings attribute in `__main__` startup** (High)
- File: `backend/app/main.py`
- Issue: `settings.environment` used, but config defines `app_env`.
- Risk: Startup failure in direct-run mode and inconsistency in local/dev operations.

3. **Rate limiting not applied to sensitive payment/login/tool endpoints** (High)
- Files: `backend/app/api/routes/payments.py`, `backend/app/api/routes/auth.py`, `backend/app/api/routes/tools.py`
- Risk: Abuse, brute-force, expensive endpoint exhaustion.

4. **Screenshot analysis endpoint unauthenticated and unbounded input** (High)
- File: `backend/app/api/routes/tools.py`
- Risk: Cost amplification, memory pressure, abuse DoS.

5. **Render pre-deploy command references missing test directory** (High)
- Files: `render.yaml`, `infra/render/*`
- Issue: `pytest tests/ -v` but backend `tests/` was absent.
- Risk: Deployment pipeline failures and blocked production/staging deploys.

6. **Payment idempotency race condition** (High)
- File: `backend/app/services/idempotency_service.py`
- Issue: `find_one` then `insert_one` non-atomic without unique key enforcement in db init.
- Risk: Duplicate order creation under concurrent retries.

7. **Payment index key mismatch with stored fields** (High)
- File: `backend/app/db/mongo.py` and `backend/app/api/routes/payments.py`
- Issue: index on `razorpay_order_id`; writes primarily use `order_id`.
- Risk: uniqueness guarantees not enforced as intended.

8. **Scheduler duplication risk with multi-worker Render config** (High)
- Files: `backend/app/services/payment_reconciliation.py`, `infra/render/render-prod.yaml`
- Issue: APScheduler starts in each worker; prod uses 4 workers.
- Risk: duplicate reconciliation processing and race updates.

## Medium Severity Findings

1. CORS policy mixes wildcard development behavior with credentials mode complexity (backend/main).
2. Health endpoint performs third-party API dependency checks by default (`/health`), increasing probe latency/rate-limit risk.
3. PDF service uses private Jinja API (`Template._render`) instead of public `render`.
4. Frontend API client default tier (`premium`) mismatches backend accepted tiers (`adventure`, `ultimate`).
5. Legacy dead/duplicate code paths present (`auth_deletion.py`, legacy supervisor path not fully removed).
6. Service-worker static cache list includes `/index.html` in Next app context (likely stale/nonexistent path).

## Low Severity Findings

1. Inconsistent naming (`premium` legacy wording in some frontend profile text).
2. Minor dependency hygiene drift (playwright usage vs dependency alignment in backend requirements).
3. Some manual CORS preflight handling duplicates global middleware behavior.
4. Optional observability setup defaults may be noisy in production if not tuned.

## Security Findings (OWASP-focused)

- **A01 Broken Access Control**: direct subscription tier mutation, payment tier trust from client.
- **A04 Insecure Design**: weak payment verification binding between verified payment and applied entitlements.
- **A05 Security Misconfiguration**: missing per-endpoint rate limits in sensitive paths.
- **A06 Vulnerable/Outdated Components**: dependency pinning is broad; no lock/scan policy demonstrated for backend.
- **A09 Logging/Monitoring Failures**: error handling exists, but no robust alert hooks tied to payment verification anomalies.
- **A10 SSRF/Injection**: no direct SSRF primitives found in user-controlled URL fetches; prompt-injection mitigations partially present in supervisor path.

Additional checks:
- No hardcoded production secrets found in current tracked files.
- Secrets-in-history audit was not performed exhaustively across all commits in this pass.
- CSRF risk is limited due bearer-token pattern and no cookie session auth.

## Logical Errors

- Duplicate shared-trip route registration (`trips.py`).
- Undefined reference in cancel endpoint (`chat.py`).
- `settings.environment` typo (`main.py`).
- API contract mismatch for default paid plan (`frontend api.ts` vs backend pricing map).

## Architectural Issues

- Payment verification/business entitlement logic mixes request payload trust with persistence updates.
- Scheduler lifecycle and multi-worker coordination not explicit.
- Idempotency storage not designed atomically for concurrent requests.

## Performance Risks

- Deep health checks to external APIs on standard probe path.
- Expensive screenshot endpoint without throttling/auth in current design.
- Potential duplicate scheduler jobs increase unnecessary API/DB load.

## Deployment Risks

- Auto-deploy pipelines can fail due missing test directory referenced in Render preDeploy commands.
- Multi-worker production startup may execute singleton-style jobs multiple times.
- Frontend/backend plan naming drift can produce checkout failures under production traffic.

## API Contract Analysis

- **Mismatch**: frontend defaults to `premium`, backend accepts `adventure|ultimate`.
- **Ambiguity**: duplicate `/trips/shared/{sharing_id}` handlers.
- **Status consistency**: most endpoints use expected status codes; payment verify semantics are overloaded (immediate success state vs reconciliation model).
- **Validation gaps**: screenshot payload size/type constraints are weak.

## Recommended Refactors

1. Centralize entitlement writes into a payment service that only accepts trusted payment-provider derived metadata.
2. Normalize trip/public-sharing routes and response models; eliminate duplicate handlers.
3. Add centralized request validation helpers for large base64/file-like payloads.
4. Enforce atomic idempotency with unique indexes and duplicate-key handling.
5. Introduce configurable health check depth (`liveness` vs `readiness` split).
6. Add distributed lock for scheduled reconciliation jobs.

## Production Readiness Checklist

- [ ] Strict entitlement enforcement (server-derived tier only)
- [ ] Payment/order/tier integrity checks
- [ ] Sensitive endpoint rate limiting
- [ ] Auth required for expensive AI tools
- [ ] Atomic idempotency + unique index
- [ ] Scheduler single-execution protection in multi-worker deployments
- [ ] Deterministic API contract alignment between frontend/backend
- [ ] Deployment pre-check commands aligned to existing test paths
- [ ] Health endpoint tuned for probe safety
- [ ] Graceful shutdown for background scheduler

## Risk Score

- Before fixes: **8/10**
- Target after applied patch set in this branch: **5/10** (remaining medium/low risks documented)

## Immediate Fix Priority List

1. Block client-side subscription tier escalation in `/auth/me`.
2. Harden `/payments/verify` to derive tier from trusted order metadata only.
3. Fix duplicate shared route and undefined cancel endpoint dependency.
4. Apply rate limits to auth/payment/tool-critical endpoints.
5. Add screenshot payload bounds and auth requirement.
6. Make idempotency atomic and enforce index support.
7. Resolve Render test-path deployment failure by adding backend smoke tests.
8. Add scheduler lock + graceful shutdown handling.
9. Fix frontend default plan constant mismatch.
10. Correct startup config typo and improve health-check depth behavior.
