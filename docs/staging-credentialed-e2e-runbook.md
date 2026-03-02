# Staging Credentialed E2E Runbook

## Purpose
Validate real credentialed flows before production deployment:
- Firebase-authenticated protected routes
- Chat stream SSE contract
- Payment verification contract
- Health/dependency visibility

## Prerequisites
1. Staging backend is deployed and reachable.
2. Staging env vars are configured (MongoDB, Redis, Firebase, Razorpay test keys).
3. You have a valid Firebase ID token for a staging user.
4. Optional: valid Razorpay verification payload for the same user/order.

## Required Environment Variables
Set these in your shell before running:

```powershell
$env:RUN_STAGING_E2E = "1"
$env:STAGING_BASE_URL = "https://<your-staging-backend>"
$env:STAGING_FIREBASE_ID_TOKEN = "<firebase-id-token>"
```

Optional:

```powershell
$env:STAGING_CHAT_TRIP_ID = "<existing-trip-id>"
$env:STAGING_VERIFY_PAYLOAD_JSON = "{\"razorpay_order_id\":\"...\",\"razorpay_payment_id\":\"...\",\"razorpay_signature\":\"...\"}"
```

## Command
From `backend/`:

```powershell
python -m pytest tests/e2e/test_staging_credentialed.py -v
```

## Expected Outcomes
1. `test_staging_health`
   - Status 200 or 503 with structured services payload.
2. `test_staging_auth_me_with_real_token`
   - Status 200 and valid user payload.
3. `test_staging_chat_stream_contract`
   - Status 200 and at least one SSE `data:` frame.
4. `test_staging_payment_verify_when_payload_supplied`
   - Contract-level response for supplied payload (`200|400|403|500`) with structured body.

## Failure Triage
1. `401` on auth/chat/payment:
   - Token expired/invalid project mismatch.
2. `429` unexpectedly:
   - Confirm Redis and limiter state, check per-user quotas.
3. `500` in payment verify:
   - Check Razorpay credential config and order/user ownership metadata.
4. Health degraded:
   - Confirm Mongo/Redis connectivity and external provider reachability.

## Release Gate Recommendation
- Treat this suite as mandatory before production promotion.
- Archive the test output with the release artifact/change ticket.
