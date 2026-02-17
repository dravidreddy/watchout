# Adversarial Test Suite - README

## 🎯 Purpose

This test suite is designed to **break** Bharat Voyager under real-world Indian user conditions. These are not happy-path tests—they simulate the chaotic reality of intermittent 4G networks, budget Android devices, and user behavior that exposes race conditions.

## 📁 Test Structure

```
tests/
├── adversarial.spec.ts      # Main torture test scenarios
├── helpers/
│   └── test-helpers.ts       # Utility functions for simulation
└── README.md                 # This file
```

## 🔥 Test Scenarios

### Scenario A: Flaky Network SSE Streaming
- **A1:** SSE interrupted midway - verify retry button, no crash
- **A2:** 10-second tunnel (connection drop + reconnect)
- **A3:** Cumulative Layout Shift measurement during streaming

### Scenario B: Indecisive User (State Races)
- **B1:** User changes destination mid-stream - no state mixing
- **B2:** Rapid-fire input changes - last input wins
- **B3:** Stop button functionality (stream termination)

### Scenario C: Payment Failures
- **C1:** Razorpay payment.failed callback handling
- **C2:** User closes Razorpay modal (timeout)
- **C3:** Network failure during payment verification

### Scenario D: Indian Internet Reality
- **D1:** Slow 4G with high latency (app responsiveness)
- **D2:** Concurrent tab state management
- **D3:** PWA offline mode caching

### Scenario E: Low-End Device Performance
- **E1:** CPU throttling (60ms interaction latency target)
- **E2:** Memory leak detection (long chat sessions)

## 🚀 Running Tests

### Debug Mode (Recommended for Development)
```bash
npm run test:e2e:ui
```
Opens Playwright UI with step-by-step debugging, time travel, and network inspection.

### Headless Mode (CI/CD)
```bash
npm run test:e2e
```

### Single Scenario
```bash
npx playwright test adversarial.spec.ts -g "A1:"
```

### With Network Throttling
```bash
npm run test:e2e:headed  # Watch tests run in real browser
```

### Generate HTML Report
```bash
npx playwright test adversarial.spec.ts --reporter=html
npx playwright show-report
```

## 🛠️ Test Helpers

The `test-helpers.ts` file provides utilities for:

### Network Simulation
```typescript
import { NetworkSimulator } from './helpers/test-helpers';

// Simulate Slow 3G (50 Kbps, 2000ms latency)
await NetworkSimulator.setSlow3G(page, context);

// Simulate rural India 4G (512 Kbps, 200ms latency)
await NetworkSimulator.setRuralIndia4G(page, context);

// Go offline/online
await NetworkSimulator.goOffline(context);
await NetworkSimulator.goOnline(context);
```

### Device Emulation
```typescript
import { DeviceEmulator } from './helpers/test-helpers';

// Simulate Redmi 9A (6x CPU slowdown)
await DeviceEmulator.setLowEndAndroid(page, context);
```

### Performance Monitoring
```typescript
import { PerformanceMonitor } from './helpers/test-helpers';

// Measure Cumulative Layout Shift
const cls = await PerformanceMonitor.measureCLS(page, 10000);

// Measure First Contentful Paint
const fcp = await PerformanceMonitor.measureFCP(page);

// Measure interaction latency
const latency = await PerformanceMonitor.measureInteractionLatency(
  page, 
  'button[type="submit"]', 
  'click'
);
```

### SSE Event Tracking
```typescript
import { SSETestHelper } from './helpers/test-helpers';

// Track all SSE events
await SSETestHelper.setupSSETracking(page);

// Get events
const events = await SSETestHelper.getSSEEvents(page);
console.log(`Received ${events.length} SSE events`);
```

### Payment Mocking
```typescript
import { RazorpayMocker } from './helpers/test-helpers';

// Mock successful payment
await RazorpayMocker.mockSuccess(page);

// Mock failed payment
await RazorpayMocker.mockFailure(page, 'insufficient_funds');

// Mock user dismissing modal
await RazorpayMocker.mockDismiss(page);
```

## 📊 Performance Benchmarks

Tests will automatically verify these metrics:

| Metric | Target | Current (Estimated) | Test |
|--------|--------|-------------------|------|
| **CLS** | <0.10 | ~0.30 | A3 |
| **FCP** | <3s on Slow 3G | Unknown | D1 |
| **Interaction Latency** | <60ms | Unknown | E1 |
| **Memory Growth** | <50MB per 20 msgs | Unknown | E2 |

## 🚨 Expected Failures (Before Fixes)

These tests **will fail** until you implement the improvements in the QA Critique:

1. **A1, A2** - No retry button, SSE doesn't handle disconnections
2. **A3** - CLS > 0.25 (word-level streaming causes excessive shifts)
3. **B1** - State mixing occurs when user changes mind
4. **B3** - No stop button implemented
5. **C1, C2, C3** - Payment errors not handled gracefully

## 🔧 Fixing the Tests

### Priority 1: Sentence-Level Streaming
```typescript
// frontend/src/lib/api.ts
let sentenceBuffer = '';
if (event.type === 'token') {
  sentenceBuffer += event.content;
  if (/[.!?]\s/.test(sentenceBuffer)) {
    appendToMessage(sentenceBuffer);
    sentenceBuffer = '';
  }
}
```

### Priority 2: SSE Heartbeat
```python
# backend/app/api/routes/chat.py
async def event_generator():
    last_heartbeat = time.time()
    event_id = 0
    
    async for event in supervisor.process_message(...):
        event_id += 1
        yield f"id: {event_id}\ndata: {json.dumps(event)}\n\n"
        
        if time.time() - last_heartbeat > 15:
            yield ": heartbeat\n\n"
            last_heartbeat = time.time()
```

### Priority 3: Task Cancellation
```python
# backend/app/agents/supervisor.py
self.active_tasks: Dict[str, asyncio.Task] = {}

async def process_message(self, user_id, ...):
    if user_id in self.active_tasks:
        self.active_tasks[user_id].cancel()
```

## 📈 Continuous Improvement

After implementing fixes:

1. Run full test suite: `npm run test:e2e`
2. Generate report: `npx playwright show-report`
3. Track metrics over time
4. Add new adversarial scenarios as bugs are discovered

## 🤝 Contributing

When adding new tests:

1. Follow the scenario structure (A, B, C, D, E...)
2. Add descriptive test names with scenario codes (e.g., "A4: ...")
3. Use test helpers for simulation
4. Document expected vs. actual behavior
5. Include assertions that verify user-visible outcomes

## 📚 References

- [QA Critique Document](../../../.gemini/antigravity/brain/.../qa_critique.md)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Web Vitals](https://web.dev/vitals/)

---

**Remember:** These tests are designed to fail initially. That's the point. Fix the underlying issues, not the tests.
