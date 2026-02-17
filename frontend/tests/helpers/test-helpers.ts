/**
 * Test Helpers for Adversarial Testing
 * Utility functions for network simulation, device emulation, and performance monitoring
 */

import { Page, BrowserContext } from '@playwright/test';

export class NetworkSimulator {
    /**
     * Simulate slow 3G network conditions (50 Kbps, 2000ms latency)
     */
    static async setSlow3G(page: Page, context: BrowserContext) {
        const client = await context.newCDPSession(page);
        await client.send('Network.emulateNetworkConditions', {
            offline: false,
            downloadThroughput: (50 * 1024) / 8,
            uploadThroughput: (50 * 1024) / 8,
            latency: 2000,
        });
    }

    /**
     * Simulate Jio 4G in rural areas (512 Kbps, 200ms latency)
     */
    static async setRuralIndia4G(page: Page, context: BrowserContext) {
        const client = await context.newCDPSession(page);
        await client.send('Network.emulateNetworkConditions', {
            offline: false,
            downloadThroughput: (512 * 1024) / 8,
            uploadThroughput: (256 * 1024) / 8,
            latency: 200,
        });
    }

    /**
     * Simulate complete offline mode
     */
    static async goOffline(context: BrowserContext) {
        await context.setOffline(true);
    }

    /**
     * Restore online mode
     */
    static async goOnline(context: BrowserContext) {
        await context.setOffline(false);
    }
}

export class DeviceEmulator {
    /**
     * Simulate low-end Android device (Redmi 9A equivalent)
     * 6x CPU slowdown, limited memory
     */
    static async setLowEndAndroid(page: Page, context: BrowserContext) {
        const client = await context.newCDPSession(page);
        await client.send('Emulation.setCPUThrottlingRate', { rate: 6 });
    }

    /**
     * Remove CPU throttling
     */
    static async removeThrottling(page: Page, context: BrowserContext) {
        const client = await context.newCDPSession(page);
        await client.send('Emulation.setCPUThrottlingRate', { rate: 1 });
    }
}

export class PerformanceMonitor {
    /**
     * Measure Cumulative Layout Shift (CLS)
     */
    static async measureCLS(page: Page, durationMs: number = 10000): Promise<number> {
        return await page.evaluate(async (duration) => {
            return new Promise<number>((resolve) => {
                let cls = 0;

                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!(entry as any).hadRecentInput) {
                            cls += (entry as any).value;
                        }
                    }
                });

                observer.observe({ type: 'layout-shift', buffered: true });

                setTimeout(() => {
                    observer.disconnect();
                    resolve(cls);
                }, duration);
            });
        }, durationMs);
    }

    /**
     * Measure First Contentful Paint (FCP)
     */
    static async measureFCP(page: Page): Promise<number> {
        return await page.evaluate(() => {
            return new Promise<number>((resolve) => {
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
    }

    /**
     * Measure interaction latency
     */
    static async measureInteractionLatency(
        page: Page,
        selector: string,
        action: 'click' | 'type' = 'click',
        text?: string
    ): Promise<number> {
        const start = Date.now();
        const element = page.locator(selector);

        if (action === 'click') {
            await element.click();
        } else if (action === 'type' && text) {
            await element.type(text);
        }

        return Date.now() - start;
    }

    /**
     * Get current memory usage (if available)
     */
    static async getMemoryUsage(page: Page): Promise<number> {
        return await page.evaluate(() => {
            if ('memory' in performance) {
                return (performance as any).memory.usedJSHeapSize;
            }
            return 0;
        });
    }
}

export class SSETestHelper {
    /**
     * Track SSE events for testing
     */
    static async setupSSETracking(page: Page): Promise<void> {
        await page.addInitScript(() => {
            const originalEventSource = window.EventSource;

            (window as any).__sseEvents = [];

            // @ts-ignore - EventSource constructor type mismatch
            window.EventSource = class extends originalEventSource {
                constructor(url: string | URL, config?: EventSourceInit) {
                    super(url as string, config);

                    this.addEventListener('message', (e) => {
                        (window as any).__sseEvents.push({
                            type: 'message',
                            data: e.data,
                            timestamp: Date.now()
                        });
                    });

                    this.addEventListener('error', (e) => {
                        (window as any).__sseEvents.push({
                            type: 'error',
                            timestamp: Date.now()
                        });
                    });

                    this.addEventListener('open', (e) => {
                        (window as any).__sseEvents.push({
                            type: 'open',
                            timestamp: Date.now()
                        });
                    });
                }
            };
        });
    }

    /**
     * Get all tracked SSE events
     */
    static async getSSEEvents(page: Page): Promise<any[]> {
        return await page.evaluate(() => {
            return (window as any).__sseEvents || [];
        });
    }

    /**
     * Clear tracked SSE events
     */
    static async clearSSEEvents(page: Page): Promise<void> {
        await page.evaluate(() => {
            (window as any).__sseEvents = [];
        });
    }
}

export class AuthHelper {
    /**
     * Mock Firebase authentication for testing
     */
    static async mockFirebaseAuth(page: Page, userId: string = 'test-user-123') {
        await page.addInitScript((uid) => {
            (window as any).__mockAuthToken = `mock-token-${uid}`;

            // Mock Firebase Auth
            (window as any).firebase = {
                auth: () => ({
                    currentUser: {
                        uid: uid,
                        email: 'test@example.com',
                        getIdToken: async () => `mock-token-${uid}`
                    }
                })
            };
        }, userId);
    }
}

export class RazorpayMocker {
    /**
     * Mock successful Razorpay payment
     */
    static mockSuccess(page: Page) {
        return page.addInitScript(() => {
            (window as any).Razorpay = class {
                private options: any;

                constructor(options: any) {
                    this.options = options;
                }

                open() {
                    setTimeout(() => {
                        this.options.handler({
                            razorpay_payment_id: 'pay_success_123',
                            razorpay_order_id: 'order_123',
                            razorpay_signature: 'valid_signature'
                        });
                    }, 1000);
                }
            };
        });
    }

    /**
     * Mock failed Razorpay payment
     */
    static mockFailure(page: Page, errorCode: string = 'payment_failed') {
        return page.addInitScript((code) => {
            (window as any).Razorpay = class {
                private options: any;

                constructor(options: any) {
                    this.options = options;
                }

                open() {
                    setTimeout(() => {
                        this.options.handler({
                            error: {
                                code: 'BAD_REQUEST_ERROR',
                                description: 'Payment failed',
                                source: 'customer',
                                reason: code
                            }
                        });
                    }, 1000);
                }
            };
        }, errorCode);
    }

    /**
     * Mock user closing Razorpay modal (no callback)
     */
    static mockDismiss(page: Page) {
        return page.addInitScript(() => {
            (window as any).Razorpay = class {
                open() {
                    // User closes modal, no callback fired
                }
            };
        });
    }
}
