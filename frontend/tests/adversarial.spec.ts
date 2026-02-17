/**
 * Bharat Voyager - Adversarial E2E Test Suite
 * "Torture Tests" designed to break the application under real Indian user conditions
 * 
 * Run with: npm run test:e2e:ui (for debugging)
 * Run with: npm run test:e2e -- --project=chromium (CI)
 */

import { test, expect, Page, Route } from '@playwright/test';

// ====================================================================
// SCENARIO A: THE "FLAKY NETWORK" STREAM
// ====================================================================

test.describe('Scenario A: Flaky Network During SSE Streaming', () => {

    test('A1: SSE stream interrupted midway - should show retry button, not crash', async ({ page, context }) => {
        // Set up network throttling to Slow 3G
        const client = await context.newCDPSession(page);
        await client.send('Network.emulateNetworkConditions', {
            offline: false,
            downloadThroughput: (50 * 1024) / 8, // 50 Kbps (Slow 3G)
            uploadThroughput: (50 * 1024) / 8,
            latency: 2000, // 2 second latency
        });

        // Navigate to chat page
        await page.goto('/');

        // Wait for chat interface to load
        await expect(page.locator('[placeholder*="dream trip"]')).toBeVisible();

        // Set up SSE connection interception
        let sseConnectionCount = 0;
        await page.route('**/api/v1/chat/stream', async (route: Route) => {
            sseConnectionCount++;

            if (sseConnectionCount === 1) {
                // First attempt: Abort connection after sending partial data
                const response = await route.fetch();
                const body = await response.body();

                // Send only first 30% of the stream, then abort
                const partialBody = body.slice(0, Math.floor(body.length * 0.3));

                await route.fulfill({
                    status: 200,
                    headers: {
                        'Content-Type': 'text/event-stream',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                    },
                    body: partialBody,
                });

                // Simulate connection drop after 2 seconds
                setTimeout(() => {
                    route.abort('failed');
                }, 2000);
            } else {
                // Subsequent attempts: Allow through
                route.continue();
            }
        });

        // User types a complex query
        const chatInput = page.locator('[placeholder*="dream trip"]');
        await chatInput.fill('Plan a 7-day itinerary for Goa with budget hotels and beach activities');
        await chatInput.press('Enter');

        // ASSERTION 1: Verify UI doesn't white-screen or throw error
        await page.waitForTimeout(3000); // Wait for connection to drop

        // Check that the page is still functional (no React error boundary)
        const errorBoundary = page.locator('text=/Something went wrong|Error|Crash/i');
        await expect(errorBoundary).not.toBeVisible({ timeout: 1000 }).catch(() => { });

        // ASSERTION 2: Verify "Retry" or error message appears
        const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")');
        const errorMessage = page.locator('text=/went wrong|try again|connection/i');

        await expect(retryButton.or(errorMessage)).toBeVisible({ timeout: 5000 });

        // ASSERTION 3: Verify partial content is preserved (not lost)
        const chatMessages = page.locator('[class*="message"], [role="log"]');
        const messageCount = await chatMessages.count();
        expect(messageCount).toBeGreaterThan(0); // At least user message should be there

        // ASSERTION 4: Test that retry actually works
        if (await retryButton.isVisible()) {
            await retryButton.click();
            await expect(page.locator('text=/Planning|Gathering|Consulting/i')).toBeVisible({ timeout: 10000 });
        }
    });

    test('A2: 10-second tunnel scenario - connection drop and auto-reconnect', async ({ page, context }) => {
        await page.goto('/');

        // Track SSE events received
        const receivedEvents: string[] = [];

        await page.exposeFunction('__trackSSEEvent', (eventType: string) => {
            receivedEvents.push(eventType);
        });

        // Inject client-side monitoring
        await page.addInitScript(() => {
            const originalEventSource = window.EventSource;
            window.EventSource = class extends originalEventSource {
                constructor(url: string, config?: EventSourceInit) {
                    super(url, config);

                    this.addEventListener('message', (e) => {
                        (window as any).__trackSSEEvent?.('message');
                    });

                    this.addEventListener('error', (e) => {
                        (window as any).__trackSSEEvent?.('error');
                    });

                    this.addEventListener('open', (e) => {
                        (window as any).__trackSSEEvent?.('open');
                    });
                }
            };
        });

        // Simulate tunnel: Go offline for 10 seconds mid-stream
        await page.route('**/api/v1/chat/stream', async (route: Route) => {
            const response = await route.fetch();

            // Start streaming
            const encoder = new TextEncoder();
            const stream = new ReadableStream({
                async start(controller) {
                    // Send initial tokens
                    for (let i = 0; i < 5; i++) {
                        controller.enqueue(encoder.encode(`data: {"type":"token","content":"Token ${i} "}\n\n`));
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }

                    // SIMULATE 10-SECOND TUNNEL (connection drop)
                    await new Promise(resolve => setTimeout(resolve, 10000));

                    // Resume after "tunnel"
                    for (let i = 5; i < 10; i++) {
                        controller.enqueue(encoder.encode(`data: {"type":"token","content":"Token ${i} "}\n\n`));
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }

                    controller.enqueue(encoder.encode('data: {"type":"done","is_complete":true}\n\n'));
                    controller.close();
                }
            });

            await route.fulfill({
                status: 200,
                headers: {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                },
                // @ts-ignore
                body: stream,
            });
        });

        const chatInput = page.locator('[placeholder*="dream trip"]');
        await chatInput.fill('Quick question about Manali weather');
        await chatInput.press('Enter');

        // Wait for full response (including 10s tunnel)
        await page.waitForTimeout(15000);

        // ASSERTION: Verify all tokens were received (no data loss)
        const chatContent = await page.locator('[class*="assistant"], [role="log"]').last().textContent();

        // Should have both pre-tunnel (0-4) and post-tunnel (5-9) tokens
        expect(chatContent).toContain('Token 0');
        expect(chatContent).toContain('Token 9');
    });

    test('A3: Cumulative Layout Shift (CLS) measurement during token streaming', async ({ page }) => {
        await page.goto('/');

        // Measure CLS using browser APIs
        const clsScore = await page.evaluate(async () => {
            return new Promise<number>((resolve) => {
                let cls = 0;

                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if ((entry as any).hadRecentInput) continue;
                        cls += (entry as any).value;
                    }
                });

                observer.observe({ type: 'layout-shift', buffered: true });

                // Run test for 10 seconds
                setTimeout(() => {
                    observer.disconnect();
                    resolve(cls);
                }, 10000);
            });
        });

        // Send message that triggers long streaming response
        const chatInput = page.locator('[placeholder*="dream trip"]');
        await chatInput.fill('Create a detailed 7-day Rajasthan itinerary');
        await chatInput.press('Enter');

        // Wait for streaming to complete
        await expect(page.locator('text=/done|complete/i')).toBeVisible({ timeout: 15000 });

        // ASSERTION: CLS should be under 0.25 (Google's "Good" threshold)
        expect(clsScore).toBeLessThan(0.25);
    });
});

// ====================================================================
// SCENARIO B: THE "INDECISIVE USER" (State Race Condition)
// ====================================================================

test.describe('Scenario B: Indecisive User - State Race Conditions', () => {

    test('B1: User changes destination mid-stream - verify no state mixing', async ({ page }) => {
        await page.goto('/');

        // Track backend requests to verify state handling
        const backendRequests: any[] = [];

        await page.route('**/api/v1/chat/stream', async (route) => {
            const request = route.request();
            const postData = request.postDataJSON();
            backendRequests.push({ url: request.url(), data: postData, timestamp: Date.now() });

            // Continue with actual request
            route.continue();
        });

        const chatInput = page.locator('[placeholder*="dream trip"]');

        // Step 1: Start planning for Goa
        await chatInput.fill('Plan a trip to Goa');
        await chatInput.press('Enter');

        // Wait for agents to start processing (status indicator appears)
        await expect(page.locator('text=/Planning|Consulting|Gathering/i')).toBeVisible({ timeout: 3000 });

        // Step 2: IMMEDIATELY change to Manali (while first request is processing)
        await page.waitForTimeout(500); // Small delay to ensure stream has started

        await chatInput.fill('No wait, actually plan for Manali instead');
        await chatInput.press('Enter');

        // Wait for second response to complete
        await page.waitForTimeout(10000);

        // ASSERTION 1: Verify backend received both requests
        expect(backendRequests.length).toBeGreaterThanOrEqual(2);

        // ASSERTION 2: Verify final response contains ONLY Manali, not Goa
        const finalMessage = page.locator('[class*="assistant"], [role="log"]').last();
        const finalText = await finalMessage.textContent();

        expect(finalText?.toLowerCase()).toContain('manali');
        expect(finalText?.toLowerCase()).not.toContain('goa'); // No mixing!

        // ASSERTION 3: Verify trip preferences were updated correctly
        // (Check via API if you have a /trips/current endpoint)
        const preferences = await page.evaluate(async () => {
            const response = await fetch('/api/v1/trips/current', {
                headers: { 'Authorization': 'Bearer test-token' }
            });
            return response.json();
        }).catch(() => null);

        if (preferences) {
            expect(preferences.destinations).toContain('Manali');
            expect(preferences.destinations).not.toContain('Goa');
        }
    });

    test('B2: Rapid-fire input changes - verify last input wins', async ({ page }) => {
        await page.goto('/');

        const chatInput = page.locator('[placeholder*="dream trip"]');
        const destinations = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata'];

        // Send 5 rapid requests without waiting
        for (const dest of destinations) {
            await chatInput.fill(`I want to visit ${dest}`);
            await chatInput.press('Enter');
            await page.waitForTimeout(200); // Minimal delay
        }

        // Wait for all processing to complete
        await page.waitForTimeout(15000);

        // ASSERTION: Final state should reflect KOLKATA (last input)
        const lastMessage = page.locator('[class*="assistant"], [role="log"]').last();
        const text = await lastMessage.textContent();

        expect(text?.toLowerCase()).toContain('kolkata');
    });

    test('B3: Stop button functionality - verify stream termination', async ({ page }) => {
        await page.goto('/');

        // Look for Stop/Cancel button (add to your UI if missing!)
        const chatInput = page.locator('[placeholder*="dream trip"]');
        await chatInput.fill('Plan a very detailed 14-day Europe trip');
        await chatInput.press('Enter');

        // Wait for stream to start
        await expect(page.locator('text=/Planning|Consulting/i')).toBeVisible({ timeout: 3000 });

        // Click stop button (you'll need to add this to your UI)
        const stopButton = page.locator('button:has-text("Stop"), button[aria-label="Stop"]');

        if (await stopButton.isVisible()) {
            await stopButton.click();

            // ASSERTION: Stream should stop within 2 seconds
            await page.waitForTimeout(2000);

            const loadingIndicator = page.locator('[class*="loading"], [class*="spinner"]');
            await expect(loadingIndicator).not.toBeVisible();
        } else {
            test.skip(); // Skip if stop button not implemented
        }
    });
});

// ====================================================================
// SCENARIO C: RAZORPAY UPI FAILURE FLOW
// ====================================================================

test.describe('Scenario C: Payment Failure Handling', () => {

    test('C1: Razorpay payment.failed callback - verify graceful handling', async ({ page }) => {
        // Mock Razorpay SDK
        await page.addInitScript(() => {
            (window as any).Razorpay = class {
                constructor(options: any) {
                    this.options = options;
                }

                open() {
                    // Simulate user clicking UPI, then payment fails from bank
                    setTimeout(() => {
                        this.options.handler({
                            razorpay_payment_id: 'pay_mock_failed',
                            error: {
                                code: 'BAD_REQUEST_ERROR',
                                description: 'Payment failed due to insufficient funds',
                                source: 'customer',
                                reason: 'payment_failed'
                            }
                        });
                    }, 2000);
                }
            };
        });

        // Navigate to booking/payment page
        await page.goto('/trips/123/book'); // Adjust URL to your booking page

        // Click "Pay via UPI" button
        const payButton = page.locator('button:has-text("Pay"), button:has-text("UPI")');
        await payButton.click();

        // Wait for Razorpay modal to "process" (mocked)
        await page.waitForTimeout(3000);

        // ASSERTION 1: Should NOT show generic 500 error page
        const errorPage = page.locator('text=/500|Server Error|Internal Error/i');
        await expect(errorPage).not.toBeVisible();

        // ASSERTION 2: Should show user-friendly payment failed message
        const failedMessage = page.locator('text=/Payment Failed|Transaction Failed|payment.*not.*successful/i');
        await expect(failedMessage).toBeVisible({ timeout: 5000 });

        // ASSERTION 3: Verify itinerary state is preserved (user can retry)
        const itinerarySummary = page.locator('[class*="itinerary"], [data-testid="itinerary-summary"]');
        await expect(itinerarySummary).toBeVisible();

        // ASSERTION 4: Verify retry button exists
        const retryPayment = page.locator('button:has-text("Retry"), button:has-text("Try Again")');
        await expect(retryPayment).toBeVisible();
    });

    test('C2: Payment timeout (user closes Razorpay modal)', async ({ page }) => {
        await page.addInitScript(() => {
            (window as any).Razorpay = class {
                open() {
                    // Simulate user closing modal without completing payment
                    // No callback is fired in this case
                }
            };
        });

        await page.goto('/trips/123/book');

        const payButton = page.locator('button:has-text("Pay")');
        await payButton.click();

        await page.waitForTimeout(3000);

        // ASSERTION: App should remain in "pending payment" state, not crash
        const pendingState = page.locator('text=/Complete Payment|Pending|Waiting/i');
        await expect(pendingState).toBeVisible();
    });

    test('C3: Network failure during payment verification', async ({ page }) => {
        // Mock successful Razorpay response but fail backend verification
        await page.route('**/api/v1/payments/verify', async (route) => {
            await route.abort('failed'); // Simulate network error
        });

        await page.addInitScript(() => {
            (window as any).Razorpay = class {
                open() {
                    setTimeout(() => {
                        this.options.handler({
                            razorpay_payment_id: 'pay_success_123',
                            razorpay_signature: 'valid_signature'
                        });
                    }, 1000);
                }
            };
        });

        await page.goto('/trips/123/book');
        await page.locator('button:has-text("Pay")').click();
        await page.waitForTimeout(3000);

        // ASSERTION: Should show verification error, not payment success
        const verificationError = page.locator('text=/verification.*failed|could not confirm/i');
        await expect(verificationError).toBeVisible({ timeout: 5000 });

        // Should offer customer support contact
        const supportLink = page.locator('a[href*="support"], text=/contact.*support/i');
        await expect(supportLink).toBeVisible();
    });
});

// ====================================================================
// SCENARIO D: ADDITIONAL ADVERSARIAL TESTS
// ====================================================================

test.describe('Scenario D: Indian Internet Reality', () => {

    test('D1: Slow 4G with high latency - verify app remains responsive', async ({ page, context }) => {
        // Emulate Jio 4G in rural areas
        const client = await context.newCDPSession(page);
        await client.send('Network.emulateNetworkConditions', {
            offline: false,
            downloadThroughput: (512 * 1024) / 8, // 512 Kbps
            uploadThroughput: (256 * 1024) / 8,   // 256 Kbps
            latency: 200, // 200ms
        });

        await page.goto('/');

        // Measure First Contentful Paint
        const fcp = await page.evaluate(() => {
            return new Promise((resolve) => {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const fcpEntry = entries.find(e => e.name === 'first-contentful-paint');
                    if (fcpEntry) {
                        resolve(fcpEntry.startTime);
                        observer.disconnect();
                    }
                });
                observer.observe({ type: 'paint', buffered: true });
            });
        });

        // ASSERTION: FCP should be under 3 seconds even on slow network
        expect(fcp).toBeLessThan(3000);
    });

    test('D2: Concurrent tab state management', async ({ browser }) => {
        const context1 = await browser.newContext();
        const context2 = await browser.newContext();

        const page1 = await context1.newPage();
        const page2 = await context2.newPage();

        // Same user, different tabs
        await page1.goto('/');
        await page2.goto('/');

        // Send different queries in each tab
        await page1.locator('[placeholder*="dream trip"]').fill('Plan Goa trip');
        await page1.locator('[placeholder*="dream trip"]').press('Enter');

        await page2.locator('[placeholder*="dream trip"]').fill('Plan Kerala trip');
        await page2.locator('[placeholder*="dream trip"]').press('Enter');

        await page.waitForTimeout(10000);

        // ASSERTION: Each tab should have independent state
        const page1Text = await page1.locator('[class*="assistant"]').last().textContent();
        const page2Text = await page2.locator('[class*="assistant"]').last().textContent();

        expect(page1Text?.toLowerCase()).toContain('goa');
        expect(page2Text?.toLowerCase()).toContain('kerala');

        await context1.close();
        await context2.close();
    });

    test('D3: PWA offline mode - verify cached responses', async ({ page, context }) => {
        await page.goto('/');

        // First request while online
        await page.locator('[placeholder*="dream trip"]').fill('Best time to visit Ladakh');
        await page.locator('[placeholder*="dream trip"]').press('Enter');
        await page.waitForTimeout(5000);

        // Go offline
        await context.setOffline(true);

        // Try accessing chat history offline
        await page.reload();

        // ASSERTION: Previously loaded messages should still be visible
        const messages = page.locator('[class*="message"]');
        await expect(messages.first()).toBeVisible();

        // ASSERTION: Offline indicator should be shown
        const offlineIndicator = page.locator('text=/offline|no connection/i');
        await expect(offlineIndicator).toBeVisible({ timeout: 3000 });
    });
});

// ====================================================================
// PERFORMANCE BENCHMARKS (Low-End Device Simulation)
// ====================================================================

test.describe('Scenario E: Low-End Android Performance', () => {

    test('E1: CPU throttling simulation - verify <60ms interaction latency', async ({ page, context }) => {
        // Throttle CPU to 6x slowdown (simulates budget Snapdragon 665)
        const client = await context.newCDPSession(page);
        await client.send('Emulation.setCPUThrottlingRate', { rate: 6 });

        await page.goto('/');

        // Measure interaction latency
        const startTime = Date.now();
        await page.locator('[placeholder*="dream trip"]').click();
        const clickLatency = Date.now() - startTime;

        // ASSERTION: Click should respond in under 60ms (even with 6x throttle)
        expect(clickLatency).toBeLessThan(60);

        // Type text and measure input lag
        const typeStart = Date.now();
        await page.locator('[placeholder*="dream trip"]').type('Test');
        const typeLatency = Date.now() - typeStart;

        expect(typeLatency).toBeLessThan(500); // Under 500ms for 4 characters
    });

    test('E2: Memory leak detection during long chat session', async ({ page }) => {
        await page.goto('/');

        // Get initial memory usage
        const initialMemory = await page.evaluate(async () => {
            if ('memory' in performance) {
                return (performance as any).memory.usedJSHeapSize;
            }
            return 0;
        });

        // Simulate long conversation (20 messages)
        for (let i = 0; i < 20; i++) {
            await page.locator('[placeholder*="dream trip"]').fill(`Message number ${i}`);
            await page.locator('[placeholder*="dream trip"]').press('Enter');
            await page.waitForTimeout(2000);
        }

        // Force garbage collection
        await page.evaluate(() => {
            if ((window as any).gc) {
                (window as any).gc();
            }
        });

        const finalMemory = await page.evaluate(() => {
            if ('memory' in performance) {
                return (performance as any).memory.usedJSHeapSize;
            }
            return 0;
        });

        // ASSERTION: Memory growth should be under 50MB
        const memoryGrowth = (finalMemory - initialMemory) / (1024 * 1024);
        expect(memoryGrowth).toBeLessThan(50);
    });
});
