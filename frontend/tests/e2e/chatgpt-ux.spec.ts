import { test, expect, type Page } from '@playwright/test';

declare global {
    interface Window {
        __mockStreamMode?: 'success' | 'slow' | 'error';
    }
}

const mockUser = {
    _id: 'user-e2e',
    firebase_id: 'user-e2e',
    email: 'e2e@example.com',
    name: 'E2E User',
    preferences: {
        travel_style: 'balanced',
        budget_range: 'mid_range',
        travel_vibe: ['relaxed'],
    },
    onboarding_completed: true,
    subscription_tier: 'adventure',
};

const itineraryPayload = {
    title: 'Goa Escape',
    cities: ['Goa'],
    num_days: 5,
    num_travelers: 2,
    budget_total: 65000,
    days: [
        {
            day_number: 1,
            city: 'Goa',
            theme: 'Arrival & North Goa Beaches',
            stay: 'Candolim beach area',
            stops: [
                { time: '09:00', name: 'Candolim Promenade Walk', estimated_cost: 400 },
                { time: '14:00', name: 'Fort Aguada Visit', estimated_cost: 600 },
                { time: '19:30', name: 'Sunset Dinner at Baga', estimated_cost: 1400 },
            ],
        },
        {
            day_number: 2,
            city: 'Goa',
            theme: 'Old Goa & Panjim',
            stay: 'Fontainhas heritage quarter',
            stops: [
                { time: '10:00', name: 'Basilica of Bom Jesus', estimated_cost: 300 },
                { time: '14:30', name: 'Fontainhas Walk', estimated_cost: 700 },
                { time: '20:00', name: 'River Cruise', estimated_cost: 1500 },
            ],
        },
    ],
};

const itineraryMarkdown =
    '# ✈️ 5-Day Goa Itinerary\n\n' +
    '## Day 1 - Arrival & North Goa Beaches\n' +
    '- Morning: Candolim promenade walk\n' +
    '- Afternoon: Fort Aguada and beach cafe lunch\n' +
    '- Evening: Sunset dinner at Baga\n' +
    '- Budget estimate: INR 2,400\n' +
    '- Stay suggestion: Candolim beach area\n\n' +
    '## Day 2 - Old Goa & Panjim\n' +
    '- Morning: Basilica of Bom Jesus\n' +
    '- Afternoon: Fontainhas heritage quarter\n' +
    '- Evening: Mandovi river cruise\n' +
    '- Budget estimate: INR 2,500\n' +
    '- Stay suggestion: Fontainhas heritage quarter\n\n' +
    'If you want, I can now rebalance this for tighter budget, slower pace, or nightlife focus.';

const captureRuntimeErrors = (page: Page) => {
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];

    page.on('pageerror', (err) => pageErrors.push(err.message));
    page.on('console', (msg) => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    return { pageErrors, consoleErrors };
};

async function sendMessage(page: Page, value: string) {
    const input = page.getByPlaceholder('Tell me about your dream trip...');
    await input.fill(value);
    await input.press('Enter');
}

test.beforeEach(async ({ page }) => {
    await page.addInitScript(
        ({ user, md, itinerary }) => {
            localStorage.setItem('watchout_dev_bypass', 'true');
            window.__mockStreamMode = 'success';

            const encoder = new TextEncoder();
            const originalFetch = window.fetch.bind(window);

            const json = (payload: unknown, status = 200) =>
                new Response(JSON.stringify(payload), {
                    status,
                    headers: { 'Content-Type': 'application/json' },
                });

            const streamResponse = (events: unknown[], delayMs: number) => {
                const stream = new ReadableStream({
                    start(controller) {
                        let i = 0;
                        const push = () => {
                            if (i >= events.length) {
                                controller.close();
                                return;
                            }
                            controller.enqueue(encoder.encode(`data: ${JSON.stringify(events[i])}\n\n`));
                            i += 1;
                            setTimeout(push, delayMs);
                        };
                        push();
                    },
                });
                return new Response(stream, {
                    status: 200,
                    headers: { 'Content-Type': 'text/event-stream' },
                });
            };

            const clarifyEvents = [
                { type: 'status', agent: 'Travel Buddy', status: 'Understanding your trip...' },
                {
                    type: 'token',
                    content:
                        'To personalize this properly, I need one quick detail.\n' +
                        'What travel duration are you targeting?\n' +
                        '1. 2-3 days\n' +
                        '2. 4-6 days\n' +
                        '3. 7+ days\n' +
                        'Reply with the option number and I will build your plan.',
                },
                { type: 'done', trip_id: 'trip-e2e-clarify' },
            ];

            const itineraryEvents = [
                { type: 'status', agent: 'Itinerary Architect', status: 'Crafting day plans...' },
                { type: 'token', content: md.slice(0, 130) },
                { type: 'token', content: md.slice(130, 340) },
                { type: 'token', content: md.slice(340, 620) },
                { type: 'token', content: md.slice(620) },
                { type: 'data', data_type: 'itinerary', data: itinerary },
                { type: 'done', trip_id: 'trip-e2e-itinerary' },
            ];

            const followUpEvents = [
                { type: 'status', agent: 'Travel Buddy', status: 'Refining your plan...' },
                {
                    type: 'token',
                    content:
                        'Great refinement request. I kept your Goa plan and made Day 2 more relaxed.\n\n' +
                        '## Day 2 - Old Goa & Panjim (Relaxed)\n' +
                        '- Morning: Late start and heritage brunch\n' +
                        '- Afternoon: One major site plus cafe break\n' +
                        '- Evening: Easy riverside walk before dinner',
                },
                { type: 'done', trip_id: 'trip-e2e-itinerary' },
            ];

            const errorEvents = [
                { type: 'status', agent: 'System', status: 'Checking route...' },
                { type: 'error', error: 'Sorry, I hit a temporary issue while planning your trip. Please try again.' },
            ];

            window.fetch = async (input, init) => {
                const url = typeof input === 'string' ? input : input.url;

                if (url.includes('/api/v1/auth/me')) return json(user);
                if (url.includes('/api/v1/chat/conversations') && !url.includes('/messages')) return json([]);
                if (url.includes('/api/v1/chat/conversations/') && url.includes('/messages')) return json([]);

                if (url.includes('/api/v1/chat/stream')) {
                    const body = typeof init?.body === 'string' ? init.body : '{}';
                    let message = '';
                    try {
                        message = (JSON.parse(body).message || '').toLowerCase();
                    } catch {
                        message = '';
                    }

                    if (window.__mockStreamMode === 'error' || message.includes('error')) {
                        return streamResponse(errorEvents, 90);
                    }

                    if (window.__mockStreamMode === 'slow' || message.includes('slow')) {
                        return streamResponse(itineraryEvents, 280);
                    }

                    if (message.includes('ambiguous') || message.includes('not sure')) {
                        return streamResponse(clarifyEvents, 80);
                    }

                    if (message.includes('day 2') || message.includes('relaxed')) {
                        return streamResponse(followUpEvents, 90);
                    }

                    return streamResponse(itineraryEvents, 80);
                }

                return originalFetch(input, init);
            };
        },
        { user: mockUser, md: itineraryMarkdown, itinerary: itineraryPayload }
    );

    await page.goto('/chat?new=true');
    for (let attempt = 0; attempt < 3 && !page.url().includes('/chat'); attempt += 1) {
        await page.goto('/chat?new=true');
        await page.waitForTimeout(300);
    }
    await expect(page.getByText('Plan Your Trip')).toBeVisible();

    const backdrop = page.locator('div.fixed.inset-0.z-30');
    if (await backdrop.count()) {
        await backdrop.first().click({ force: true });
    }
});

test('A. basic conversation renders markdown cleanly without JSON leaks or runtime errors', async ({ page }) => {
    const { pageErrors, consoleErrors } = captureRuntimeErrors(page);

    await sendMessage(page, 'Plan me a Goa itinerary');

    await expect(page.getByRole('heading', { name: /5-Day Goa Itinerary/i })).toBeVisible();
    await expect(page.getByText('Budget estimate: INR 2,400')).toBeVisible();
    await expect(page.locator('text=assistant_message')).toHaveCount(0);
    await expect(page.locator('text={"')).toHaveCount(0);
    await expect(page.locator('.prose h2')).toHaveCount(2);

    expect(pageErrors).toEqual([]);
    expect(consoleErrors.filter((e) => /TypeError|ReferenceError|UnhandledPromiseRejection/i.test(e))).toEqual([]);
});

test('B. clarification follow-up uses clean structured framing and natural tone', async ({ page }) => {
    await sendMessage(page, 'I am not sure, this is ambiguous');

    await expect(page.getByText('To personalize this properly, I need one quick detail.')).toBeVisible();
    await expect(page.locator('.prose ol li').nth(0)).toContainText('2-3 days');
    await expect(page.locator('.prose ol li').nth(1)).toContainText('4-6 days');
    await expect(page.locator('.prose ol li').nth(2)).toContainText('7+ days');
    await expect(page.getByText(/Reply with the option number/i)).toBeVisible();
});

test('C. itinerary generation is consistently formatted with no duplicated day sections', async ({ page }) => {
    await sendMessage(page, 'Create a premium Goa itinerary');

    await expect(page.getByRole('heading', { name: /5-Day Goa Itinerary/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Day 1 - Arrival & North Goa Beaches/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Day 2 - Old Goa & Panjim/i })).toBeVisible();
    await expect(page.getByText('Budget estimate: INR 2,500')).toBeVisible();
    await expect(page.locator('text=```')).toHaveCount(0);

    const dayHeaders = (await page.locator('h2').allInnerTexts()).filter((t) => /^Day \d+ - /.test(t));
    const unique = new Set(dayHeaders);
    expect(unique.size).toBe(dayHeaders.length);
});

test('D. streaming stays progressive and stable under slow delivery', async ({ page, context, browserName }) => {
    const { pageErrors, consoleErrors } = captureRuntimeErrors(page);

    if (browserName === 'chromium') {
        const cdp = await context.newCDPSession(page);
        await cdp.send('Network.enable');
        await cdp.send('Network.emulateNetworkConditions', {
            offline: false,
            latency: 200,
            downloadThroughput: 64 * 1024,
            uploadThroughput: 64 * 1024,
            connectionType: 'cellular3g',
        });
    }

    await page.evaluate(() => {
        window.__mockStreamMode = 'slow';
    });

    const composer = page.locator('form').last();
    const beforeBox = await composer.boundingBox();

    await sendMessage(page, 'Slow stream this itinerary');

    const prose = page.locator('.prose').last();
    await expect(prose).toBeVisible();
    await page.waitForTimeout(350);
    const len1 = (await prose.innerText()).length;
    await page.waitForTimeout(500);
    const len2 = (await prose.innerText()).length;
    expect(len2).toBeGreaterThan(len1);

    await expect(page.getByRole('heading', { name: /5-Day Goa Itinerary/i })).toBeVisible();
    const bubbleCount = await page.locator('.animate-slide-in-up').count();
    expect(bubbleCount).toBe(2);

    const afterBox = await composer.boundingBox();
    expect(Math.abs((afterBox?.y ?? 0) - (beforeBox?.y ?? 0))).toBeLessThanOrEqual(48);

    expect(pageErrors).toEqual([]);
    expect(consoleErrors.filter((e) => /TypeError|ReferenceError|UnhandledPromiseRejection/i.test(e))).toEqual([]);
});

test('E. backend failure shows user-safe error without stack traces', async ({ page }) => {
    await sendMessage(page, 'Trigger error handling');

    await expect(page.locator('.prose').filter({ hasText: /temporary issue while planning your trip/i }).first()).toBeVisible();
    await expect(page.getByText(/Traceback|Exception:|File "/)).toHaveCount(0);
});

test('F. multi-turn follow-up preserves context continuity', async ({ page }) => {
    await sendMessage(page, 'Plan me a Goa itinerary');
    await expect(page.getByRole('heading', { name: /5-Day Goa Itinerary/i })).toBeVisible();

    await sendMessage(page, 'Can you make day 2 more relaxed but keep Goa?');

    await expect(page.getByText(/kept your Goa plan/i)).toBeVisible();
    await expect(page.getByRole('heading', { name: /Day 2 - Old Goa & Panjim \(Relaxed\)/i })).toBeVisible();
    await expect(page.getByText(/5-Day Goa Itinerary/i)).toBeVisible();
});

test.describe('G. mobile readability', () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test('chat formatting remains readable on mobile viewport', async ({ page }) => {
        await sendMessage(page, 'Plan me a Goa itinerary');
        await expect(page.getByRole('heading', { name: /5-Day Goa Itinerary/i })).toBeVisible();

        const prose = page.locator('.prose').last();
        const box = await prose.boundingBox();
        expect(box).not.toBeNull();
        expect((box?.width ?? 0)).toBeLessThanOrEqual(358);

        const hasHorizontalOverflow = await page.evaluate(() => (
            document.documentElement.scrollWidth > window.innerWidth
        ));
        expect(hasHorizontalOverflow).toBeFalsy();
    });
});
