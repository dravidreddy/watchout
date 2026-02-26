# Watchout Production SLAs (Service Level Agreements)

This document defines the strict Service Level Agreements (SLAs) for the Watchout production environment. These metrics are continuously monitored via Grafana and OpenTelemetry.

## 1. Availability (Uptime)
**Target:** 99.5% Uptime per calendar month.
- **Measurement:** Computed via external synthetic monitoring (e.g., BetterUptime) hitting the `/health` endpoint every 1 minute from multiple global regions.
- **Definition of Downtime:** The `/health` endpoint returns a non-200 HTTP status code or fails to respond within 10 seconds for more than 2 consecutive minutes.
- **Permitted Downtime:** ~3.6 hours per month.
- **Mitigation:** Multi-instance deployment on Render, MongoDB Atlas replica sets, and LLM Provider Fallback (Groq -> OpenAI).

## 2. Latency (Performance)
**Target:** 95th Percentile (P95) Latency < 8,000ms (8 seconds) for core AI streaming endpoints.
- **Measurement:** Tracked via OpenTelemetry spans (`BaseAgent.stream`) and Prometheus metrics (`http_request_duration_seconds`).
- **Scope:** Specifically applies to POST `/api/v1/chat/stream`. Regular CRUD operations (e.g., fetching trips) must maintain a P95 of < 500ms.
- **Rationale:** LLM generation is inherently slow, but the first token (Time To First Token - TTFT) must arrive quickly. 8s represents the 95th percentile for total request completion, assuming aggressive streaming.
- **Mitigation:** Dedicated connection pools, Groq hardware acceleration, and Redis caching.

## 3. Error Rate (Reliability)
**Target:** Global Error Rate < 1% of all requests.
- **Measurement:** Tracked via Prometheus metrics (`http_requests_total` where status >= 500).
- **Definition of Error:** Any HTTP 5xx response returned to the client. Note: HTTP 4xx responses (e.g., 400 Bad Request, 429 Too Many Requests) are considered client errors and do not count against this SLA.
- **Mitigation:** Circuit breakers (`pyfailsafe`) on external dependencies, global exception handlers, and input validation schemas.

## Incident Response
Alerts are configured in Grafana to fire to the engineering on-call rotation (via PagerDuty/Slack) when:
- Uptime drops below 99.9% over a 1-hour rolling window.
- P95 latency exceeds 10s for more than 5 minutes.
- Error rate exceeds 2% over a 5-minute window.
