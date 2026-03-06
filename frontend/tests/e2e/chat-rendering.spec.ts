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
    },
    onboarding_completed: true,
    subscription_tier: 'adventure',
};

const captureRuntimeErrors = (page: Page) => {
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];

    page.on('pageerror', (err) => pageErrors.push(err.message));
    page.on('console', (msg) => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    return { pageErrors, consoleErrors };
};

test.beforeEach(async ({ page }) => {
    await page.addInitScript((user) => {
        localStorage.setItem('watchout_dev_bypass', 'true');

        const encoder = new TextEncoder();
        const originalFetch = window.fetch.bind(window);
        window.__mockStreamMode = 'success';

        const json = (payload: unknown, status = 200) =>
            new Response(JSON.stringify(payload), {
                status,
                headers: { 'Content-Type': 'application/json' },
            });

        const streamResponse = (events: unknown[], delayMs: number) => {
            const stream = new ReadableStream({
                start(controller) {
                    let index = 0;
                    const push = () => {
                        if (index >= events.length) {
                            controller.close();
                            return;
                        }
                        controller.enqueue(
                            encoder.encode(`data: ${JSON.stringify(events[index])}\n\n`)
                        );
                        index += 1;
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

        const successEvents = [
            { type: 'status', agent: 'Travel Buddy', status: 'Understanding your trip...' },
            { type: 'token', content: '## Trip Plan\n' },
            { type: 'token', content: '- **Destination:** Goa\n- **Duration:** 3 days\n' },
            { type: 'token', content: '\n| Day | Focus |\n| --- | --- |\n| 1 | Beaches |\n| 2 | Cafes |\n' },
            {
                type: 'data',
                data_type: 'confirmation_required',
                data: {
                    destinations_or_region: 'Goa',
                    duration_days: 3,
                    num_travelers: 2,
                    budget_range: 'mid_range',
                },
            },
            {
                type: 'data',
                data_type: 'itinerary',
                data: {
                    title: 'Goa Escape',
                    cities: ['Goa'],
                    num_days: 3,
                    num_travelers: 2,
                    budget_total: 30000,
                    days: [
                        {
                            day_number: 1,
                            city: 'Goa',
                            stops: [
                                { arrival_time: '09:00', name: 'Calangute Beach', description: 'Relax by the coast', estimated_cost: 1200 },
                            ],
                        },
                        {
                            day_number: 1,
                            city: 'Goa',
                            stops: [
                                { time: '11:00', name: 'Cafe Breakfast', estimated_cost: 500 },
                            ],
                        },
                        {
                            day_number: 2,
                            city: 'Goa',
                            stops: [
                                { time: '10:30', name: 'Old Goa Churches' },
                            ],
                        },
                    ],
                },
            },
            { type: 'token', content: '\nWould you like me to optimize this for nightlife or budget?' },
            { type: 'done', trip_id: 'trip-e2e-1' },
        ];

        const errorEvents = [
            { type: 'token', content: 'Working on it...' },
            { type: 'error', error: 'Mock upstream timeout' },
        ];

        window.fetch = async (input, init) => {
            const url = typeof input === 'string' ? input : input.url;

            if (url.includes('/api/v1/auth/me')) return json(user);
            if (url.includes('/api/v1/chat/conversations') && !url.includes('/messages')) return json([]);
            if (url.includes('/api/v1/chat/conversations/') && url.includes('/messages')) return json([]);

            if (url.includes('/api/v1/chat/stream')) {
                const body = typeof init?.body === 'string' ? init.body : '';
                let message = '';
                try {
                    message = JSON.parse(body).message || '';
                } catch {
                    message = '';
                }

                const mode = message.toLowerCase().includes('error')
                    ? 'error'
                    : message.toLowerCase().includes('slow')
                        ? 'slow'
                        : window.__mockStreamMode;

                if (mode === 'error') return streamResponse(errorEvents, 80);
                if (mode === 'slow') return streamResponse(successEvents, 250);
                return streamResponse(successEvents, 80);
            }

            return originalFetch(input, init);
        };
    }, mockUser);

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

    const closeButton = page.getByRole('button', { name: 'Close' });
    if (await closeButton.isVisible()) {
        await closeButton.click({ force: true });
    }
});

test('renders streamed markdown, table, follow-up, and itinerary without JSON leaks', async ({ page }) => {
    const { pageErrors, consoleErrors } = captureRuntimeErrors(page);
    await page.getByPlaceholder('Tell me about your dream trip...').fill('Plan me a Goa itinerary');
    await page.getByPlaceholder('Tell me about your dream trip...').press('Enter');

    await expect(page.getByRole('heading', { name: 'Trip Plan' })).toBeVisible();
    await expect(page.locator('table')).toHaveCount(1);
    await expect(page.getByText('Would you like me to optimize this for nightlife or budget?')).toBeVisible();
    await expect(page.getByText('Confirm & Generate', { exact: false })).toBeVisible();

    await expect(page.getByText('Goa Escape')).toBeVisible();
    await expect(page.getByText('Calangute Beach')).toBeVisible();
    await expect(page.getByText('Budget Breakdown')).toBeVisible();

    // Day numbers should be resequenced and deduplicated by UI normalization.
    await expect(page.getByText('Day 1: INR', { exact: false })).toBeVisible();

    await expect(page.locator('text=assistant_message')).toHaveCount(0);
    await expect(page.locator('text={"')).toHaveCount(0);

    expect(pageErrors).toEqual([]);
    expect(consoleErrors.filter((e) => /UnhandledPromiseRejection|TypeError|ReferenceError/i.test(e))).toEqual([]);
});

test('keeps loading state visible during slow streaming and final layout intact', async ({ page }) => {
    await page.getByPlaceholder('Tell me about your dream trip...').fill('Plan a slow streamed trip');
    await page.getByPlaceholder('Tell me about your dream trip...').press('Enter');

    await expect(page.getByText('Thinking...')).toBeVisible();
    await expect(page.getByText('Would you like me to optimize this for nightlife or budget?')).toBeVisible();
    await expect(page.locator('table')).toHaveCount(1);
});

test('shows stream errors in-chat without collapsing the message layout', async ({ page }) => {
    await page.getByPlaceholder('Tell me about your dream trip...').fill('Trigger an error');
    await page.getByPlaceholder('Tell me about your dream trip...').press('Enter');

    await expect(page.getByText(/Mock upstream timeout/).first()).toBeVisible();
    await expect(page.locator('[class*="animate-slide-in-up"]').first()).toBeVisible();
});
