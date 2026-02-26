# Observability & Grafana Alerts Definition (OB6)

This document defines the PromQL queries and alert thresholds to be provisioned in Grafana for the Watchout system.

## 1. High API Error Rate
**Symptom:** More than 1% of HTTP requests return 5xx errors.
**PromQL:**
```promql
sum(rate(fastapi_responses_total{status=~"5.."}[5m])) 
/ 
sum(rate(fastapi_responses_total[5m])) > 0.01
```
**Duration:** 5 minutes
**Severity:** Critical
**Action:** Route to PagerDuty. Check MongoDB/Redis connection health.

## 2. API Latency Degradation (p95)
**Symptom:** 95th percentile request latency exceeds 8 seconds.
**PromQL:**
```promql
histogram_quantile(0.95, sum(rate(fastapi_requests_duration_seconds_bucket[5m])) by (le)) > 8
```
**Duration:** 10 minutes
**Severity:** Warning
**Action:** Indicates slow LLM generation or blocked async event loops.

## 3. High Groq API Cost Spike
**Symptom:** Sudden spike in external AI generation cost. Exceeds $5 in a 10-minute window.
**PromQL (requires custom metric export, currently tracked in structured logs OB4):**
```promql
sum(increase(llm_cost_usd_total[10m])) > 5
```
**Duration:** 0m
**Severity:** Warning
**Action:** Potential scraping/DDoS attack. Verify rate-limiter operations.

## 4. Degraded Agent Service Events
**Symptom:** High volume of SSE `degraded_service` events due to agent timeouts.
**Search (Logs):**
`@logger:"app.agents.supervisor" AND @msg:"Degraded agents in this request"`
**Threshold:** > 10 occurrences in 5 minutes
**Action:** Investigate Groq API status page for downstream outages.
