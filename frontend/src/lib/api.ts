import { getIdToken } from './firebase';
import { getFriendlyErrorMessage } from './apiErrorHandler';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';


async function getAuthHeaders(): Promise<HeadersInit> {
    const token = await getIdToken();

    // Dev Bypass Check - ONLY allowed in development
    const isDevBypass = process.env.NODE_ENV !== 'production' && process.env.NEXT_PUBLIC_DEV_BYPASS;

    if (isDevBypass) {
        console.warn('⚠️ USING DEV BYPASS TOKEN - THIS SHOULD NOT HAPPEN IN PRODUCTION ⚠️');
    }

    const timezoneOffset = new Date().getTimezoneOffset().toString();
    const timezoneId = Intl.DateTimeFormat().resolvedOptions().timeZone;

    return {
        'Content-Type': 'application/json',
        'X-Timezone-Offset': timezoneOffset,
        'X-Timezone-Id': timezoneId,
        ...(isDevBypass ? { 'X-Test-Bypass-Token': process.env.NEXT_PUBLIC_DEV_BYPASS as string } : {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
}

interface RequestOptions extends RequestInit {
    retries?: number;
    timeout?: number;
}

export class ApiError extends Error {
    public friendlyMessage: string;
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
        this.friendlyMessage = getFriendlyErrorMessage({ status, message });
    }
}

export async function apiRequest<T>(
    endpoint: string,
    options: RequestOptions = {}
): Promise<T> {
    const { retries = 2, timeout = 30000, ...fetchOptions } = options;
    const headers = await getAuthHeaders();

    let lastError: any = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...fetchOptions,
                headers: {
                    ...headers,
                    ...fetchOptions.headers
                },
                signal: controller.signal
            });

            clearTimeout(id);

            if (!response.ok) {
                console.error(`API Error for ${API_BASE_URL}${endpoint}:`, response.status, response.statusText);
                if (response.status === 401) {
                    console.error("Unauthorized access - token might be invalid");
                }
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                console.error('Error details:', errorData);
                throw new ApiError(
                    response.status,
                    errorData.detail || errorData.message || 'Request failed'
                );
            }

            return response.json();
        } catch (error: any) {
            lastError = error;

            // Don't retry on 4xx errors (except 408 or 429)
            if (error instanceof ApiError && error.status >= 400 && error.status < 500 && error.status !== 408 && error.status !== 429) {
                throw error;
            }

            // If it's the last attempt, throw
            if (attempt === retries) {
                if (!(error instanceof ApiError)) {
                    error.friendlyMessage = getFriendlyErrorMessage(error);
                }
                throw error;
            }

            // Wait before retry (exponential backoff)
            const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    throw lastError || new Error('Request failed after retries');
}

export async function streamRequest(
    endpoint: string,
    body: object,
    onEvent: (event: StreamEvent) => void,
    signal?: AbortSignal,       // FE1: support external AbortController
    maxRetries: number = 3,     // FE1: max reconnect attempts on network/5xx errors
): Promise<void> {
    let attempt = 0;

    while (true) {
        // FE1: exponential back-off — 0ms for first attempt, then 1s → 2s → 4s … max 30s
        if (attempt > 0) {
            const delayMs = Math.min(1000 * Math.pow(2, attempt - 1), 30_000);
            await new Promise<void>((resolve, reject) => {
                const onAbort = () => {
                    clearTimeout(id);
                    signal?.removeEventListener('abort', onAbort);
                    reject(new DOMException('Aborted', 'AbortError'));
                };
                const id = setTimeout(() => {
                    signal?.removeEventListener('abort', onAbort);
                    resolve();
                }, delayMs);
                signal?.addEventListener('abort', onAbort, { once: true });
            });
        }

        // Bail immediately if the caller aborted
        if (signal?.aborted) return;

        // Sentence buffer to reduce layout shifts (CLS optimization)
        let sentenceBuffer = '';

        try {
            const headers = await getAuthHeaders();

            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers,
                body: JSON.stringify(body),
                signal,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                // FE3: Preserve 422 field-level error details so forms can surface them
                const message = response.status === 422
                    ? JSON.stringify(errorData.detail ?? errorData)
                    : (errorData.detail || errorData.message || 'Stream request failed');
                throw new ApiError(response.status, message);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) return;

            // Buffer for partial SSE lines split across TCP chunks
            let lineBuffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    // Flush remaining buffer on stream end
                    if (sentenceBuffer.trim()) {
                        onEvent({ type: 'token', content: sentenceBuffer });
                        sentenceBuffer = '';
                    }
                    return;  // success — exits the retry loop
                }

                const chunk = decoder.decode(value, { stream: true });
                // Prepend any leftover partial line from previous read
                const combined = lineBuffer + chunk;
                const lines = combined.split('\n');
                // Last element may be an incomplete line — save for next iteration
                lineBuffer = lines.pop() || '';

                for (const line of lines) {
                    const normalizedLine = line.trimEnd();
                    // Skip heartbeat comments (AR6 backend keepalive pings)
                    if (normalizedLine.startsWith(':')) {
                        continue;
                    }

                    if (normalizedLine.startsWith('data:')) {
                        const data = normalizedLine.slice(5).trimStart();
                        if (data === '[DONE]') {
                            // Flush buffer before completing
                            if (sentenceBuffer.trim()) {
                                onEvent({ type: 'token', content: sentenceBuffer });
                                sentenceBuffer = '';
                            }
                            return;
                        }

                        try {
                            const event = JSON.parse(data) as StreamEvent;

                            // Apply sentence buffering ONLY to token events
                            if (event.type === 'token' && event.content) {
                                sentenceBuffer += event.content;

                                // Flush on sentence boundaries OR if buffer gets too long
                                const hasSentenceEnd = /[.!?]\s/.test(sentenceBuffer);
                                const bufferTooLong = sentenceBuffer.length > 200;

                                if (hasSentenceEnd || bufferTooLong) {
                                    onEvent({ type: 'token', content: sentenceBuffer });
                                    sentenceBuffer = '';
                                }
                            } else {
                                // For non-token events, flush buffer first, then pass event
                                if (sentenceBuffer.trim()) {
                                    onEvent({ type: 'token', content: sentenceBuffer });
                                    sentenceBuffer = '';
                                }
                                onEvent(event);
                            }
                        } catch {
                            // Ignore parse errors for individual SSE lines
                        }
                    }
                }
            }

        } catch (error: any) {
            // Flush buffer on error
            if (sentenceBuffer.trim()) {
                onEvent({ type: 'token', content: sentenceBuffer });
            }

            // User aborted intentionally — stop immediately, no retry
            if (error?.name === 'AbortError') return;

            // 4xx errors are non-retriable (bad request / auth / validation)
            if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                throw error;
            }

            // FE1: Network/5xx error — retry if we have attempts left
            attempt++;
            if (attempt > maxRetries) {
                if (!(error instanceof ApiError)) {
                    error.friendlyMessage = getFriendlyErrorMessage(error);
                }
                throw error;
            }
            // else: loop back for retry with back-off
        }
    }
}

export interface StreamEvent {
    type: 'token' | 'status' | 'data' | 'tool_start' | 'tool_end' | 'error' | 'done' | 'itinerary' | 'cancelled';
    content?: string;
    status?: string;
    agent?: string;
    data_type?: string;
    data?: unknown;
    itinerary?: any;
    error?: string;
    trip_id?: string;
    is_complete?: boolean;
    message?: string;
    friendlyMessage?: string;
}

// API endpoints
export const api = {
    // Auth
    login: (data: { firebase_id: string; email: string; name?: string; photo_url?: string }) =>
        apiRequest<UserProfile>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    getProfile: () => apiRequest<UserProfile>('/auth/me'),

    updateProfile: (data: Partial<UserProfile>) =>
        apiRequest<{ status: string }>('/auth/me', {
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    // Trips
    listTrips: (params?: {
        status?: string;
        city?: string;
        start_date?: string;
        end_date?: string;
        sort_by?: string;
        sort_order?: number
    }) => {
        const query = params ? `?${new URLSearchParams(Object.entries(params).filter(([_, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))}` : '';
        return apiRequest<Trip[]>(`/trips/${query}`);
    },

    searchTrips: (q: string) => apiRequest<Trip[]>(`/trips/search?q=${encodeURIComponent(q)}`),

    createTrip: (data: TripCreate) =>
        apiRequest<{ trip_id: string; status: string }>('/trips/', {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    getTrip: (tripId: string) => apiRequest<Trip>(`/trips/${tripId}`),

    updateTrip: (tripId: string, data: Partial<Trip>) =>
        apiRequest<{ status: string; sharing_id?: string }>(`/trips/${tripId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    deleteTrip: (tripId: string) =>
        apiRequest<{ status: string }>(`/trips/${tripId}`, { method: 'DELETE' }),

    // Places
    searchPlaces: (query: string) =>
        apiRequest<{ results: Place[] }>(`/places/search?query=${encodeURIComponent(query)}`),

    getNearbyPlaces: (lat: number, lng: number, radius: number = 5000, placeType: string = 'tourist_attraction') =>
        apiRequest<{ results: Place[] }>(`/places/nearby?latitude=${lat}&longitude=${lng}&radius=${radius}&place_type=${placeType}`),

    getPlaceDetails: (placeId: string) =>
        apiRequest<Place>(`/places/details/${placeId}`),

    autocomplete: (input: string) =>
        apiRequest<{ predictions: PlacePrediction[] }>(`/places/autocomplete?input=${encodeURIComponent(input)}`),

    // Destinations
    getTrendingDestinations: () =>
        apiRequest<Destination[]>('/destinations/trending'),

    getNearbyDestinations: (lat: number, lng: number, radiusKm: number = 1000) =>
        apiRequest<Destination[]>(`/destinations/nearby?lat=${lat}&lng=${lng}&radius_km=${radiusKm}`),

    getAISuggestions: () =>
        apiRequest<string[]>('/destinations/suggestions'),

    exploreTrips: (params?: { city?: string; category?: string; tag?: string }) => {
        const query = new URLSearchParams();
        if (params?.city) query.append('city', params.city);
        if (params?.category) query.append('category', params.category);
        if (params?.tag) query.append('tag', params.tag);
        return apiRequest<Trip[]>(`/trips/explore${query.toString() ? `?${query.toString()}` : ''}`);
    },

    getSharedTrip: (sharingId: string) =>
        apiRequest<Trip>(`/trips/shared/${sharingId}`),

    // Conversations (Chat History)
    listConversations: () =>
        apiRequest<any[]>('/chat/conversations'),

    getTripMessages: (tripId: string) =>
        apiRequest<any[]>(`/chat/conversations/${tripId}/messages`),

    saveConversationAsTrip: (tripId: string) =>
        apiRequest<{ status: string; trip_id: string }>(`/chat/conversations/${tripId}/save-as-trip`, {
            method: 'POST'
        }),

    deleteConversation: (tripId: string) =>
        apiRequest<{ status: string }>(`/chat/conversations/${tripId}`, { method: 'DELETE' }),

    shareConversation: (tripId: string) =>
        apiRequest<{ sharing_url: string; sharing_id: string }>(`/chat/conversations/${tripId}/share`, {
            method: 'POST'
        }),

    deleteMessage: (tripId: string, messageId: string) =>
        apiRequest<{ status: string }>(`/chat/conversations/${tripId}/messages/${messageId}`, {
            method: 'DELETE'
        }),

    editMessage: (tripId: string, messageId: string, content: string) =>
        apiRequest<{ status: string; content: string }>(`/chat/conversations/${tripId}/messages/${messageId}`, {
            method: 'PATCH',
            body: JSON.stringify({ content }),
        }),


    // Payments
    createOrder: (tier: string = 'adventure') =>
        apiRequest<any>('/payments/create-order?tier=' + encodeURIComponent(tier), { method: 'POST' }),

    verifyPayment: (data: any) =>
        apiRequest<{ status: string; tier: string }>('/payments/verify', {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    downloadItineraryPdf: async (tripId: string) => {
        const headers = await getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/export/pdf/${tripId}`, {
            headers
        });
        if (!response.ok) throw new Error('Failed to download PDF');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Itinerary_${tripId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    },
};

// Types
export interface UserProfile {
    _id: string;
    firebase_id: string;
    email: string;
    name?: string;
    photo_url?: string;
    home_city?: string;
    preferences: UserPreferences;
    onboarding_completed: boolean;
    subscription_tier: string;
}

export interface UserPreferences {
    travel_style?: string;
    budget_range?: string;
    food_preferences?: string[];
    interests?: string[];
    language?: string;
    current_mood?: string;
    travel_vibe?: string[];
    notifications_email?: boolean;
    notifications_push?: boolean;
    notifications_trip_updates?: boolean;
}

export interface Trip {
    _id: string;
    trip_id?: string;      // UUID used by the chat system (may differ from _id)
    user_id: string;
    title: string;
    cities: string[];
    city?: string;         // single-city alias
    start_date?: string;
    end_date?: string;
    num_days?: number;
    duration_days?: number; // alias
    num_travelers: number;
    budget_total?: number;
    status: string;
    itinerary?: any;       // full assembled itinerary object from orchestrator
    category?: string;
    tags: string[];
    is_public: boolean;
    sharing_id?: string;
    created_at: string;
    updated_at: string;
}


export interface TripCreate {
    title?: string;
    cities: string[];
    origin_city?: string;
    start_date?: string;
    end_date?: string;
    num_days?: number;
    num_travelers: number;
    budget_total?: number;
    category?: string;
    tags?: string[];
    is_public?: boolean;
    itinerary?: Itinerary;
}

export interface JourneyStop {
    city_name: string;
    nights: number;
    reason?: string;
}

export interface JourneyRoute {
    origin: string;
    destination: string;
    stops: JourneyStop[];
}

export interface Itinerary {
    journey_route?: JourneyRoute;
    days: DayPlan[];
    total_estimated_cost?: number;
    highlights?: string[];
}

export interface DayPlan {
    day_number: number;
    city: string;
    stops: ActivityStop[];
    notes?: string;
}

export interface ActivityStop {
    time?: string;
    name: string;
    description?: string;
    duration_minutes?: number;
    category?: string;
    estimated_cost?: number;
    address?: string;
    latitude?: number;
    longitude?: number;
    arrival_time?: string;
    departure_time?: string;
    rating?: number;
    photo_url?: string;
}

export interface Place {
    place_id: string;
    name: string;
    address?: string;
    latitude?: number;
    longitude?: number;
    rating?: number;
    user_ratings_total?: number;
    price_level?: number;
    types?: string[];
    opening_hours?: boolean | string[]; // boolean from search, array of strings from details
    photo_reference?: string;
    photos?: string[];
    reviews?: { author: string; rating: number; text: string }[];
    phone?: string;
    website?: string;
}

export interface Destination {
    _id: string;
    name: string;
    description: string;
    image_url: string;
    category: string[];
    rating: number;
    location: {
        type: string;
        coordinates: [number, number];
    };
    tags: string[];
}

export interface PlacePrediction {
    place_id: string;
    description: string;
    main_text?: string;
    types?: string[];
}

export interface ScreenshotAnalyzeResponse {
    status: string;
    detected_location?: string;
    context?: string;
    error?: string;
}

export const analyzeScreenshot = async (imageBase64: string): Promise<ScreenshotAnalyzeResponse> => {
    return apiRequest<ScreenshotAnalyzeResponse>('/tools/analyze-screenshot', {
        method: 'POST',
        body: JSON.stringify({ image_base64: imageBase64 }),
    });
};
