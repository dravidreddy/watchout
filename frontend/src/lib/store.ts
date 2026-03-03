'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserProfile, UserPreferences, Trip } from '@/lib/api';

interface AuthState {
    user: UserProfile | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    setUser: (user: UserProfile | null) => void;
    setLoading: (loading: boolean) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            isLoading: true,
            isAuthenticated: false,
            setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
            setLoading: (isLoading) => set({ isLoading }),
            logout: () => set({ user: null, isAuthenticated: false })
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({ user: state.user })
        }
    )
);

interface ChatState {
    messages: ChatMessage[];
    isStreaming: boolean;
    currentAgent: string;
    currentStatus: string;
    extractedItinerary: any | null;
    weatherData: any | null;
    activeTripId: string | null;
    isUploadingImage: boolean;
    extractedLocation: string | null;
    isVerifyingLocation: boolean;
    addMessage: (message: ChatMessage) => void;
    appendToLastMessage: (content: string) => void;
    setStreaming: (streaming: boolean) => void;
    setAgentStatus: (agent: string, status: string) => void;
    setExtractedItinerary: (itinerary: any) => void;
    setWeatherData: (data: any) => void;
    setActiveTripId: (tripId: string | null) => void;
    setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
    updateLastMessageData: (data: unknown) => void;
    clearMessages: () => void;
    setUploadingImage: (isUploading: boolean) => void;
    setExtractedLocation: (location: string | null) => void;
    setVerifyingLocation: (isVerifying: boolean) => void;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    agent?: string;
    data?: unknown;
    status?: 'pending' | 'complete' | 'error';
}

export const useChatStore = create<ChatState>((set, get) => ({
    messages: [],
    isStreaming: false,
    currentAgent: '',
    currentStatus: '',
    extractedItinerary: null,
    weatherData: null,
    activeTripId: null,
    isUploadingImage: false,
    extractedLocation: null,
    isVerifyingLocation: false,

    setActiveTripId: (activeTripId) => set({ activeTripId }),

    addMessage: (message) => set((state) => {
        if (state.messages.some(m => m.id === message.id)) {
            return state;
        }
        return { messages: [...state.messages, message] };
    }),

    appendToLastMessage: (content) => set((state) => {
        const messages = [...state.messages];
        if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
            messages[messages.length - 1] = {
                ...messages[messages.length - 1],
                content: messages[messages.length - 1].content + content
            };
        }
        return { messages };
    }),

    setStreaming: (isStreaming) => set({ isStreaming }),

    setAgentStatus: (currentAgent, currentStatus) => set({ currentAgent, currentStatus }),

    setExtractedItinerary: (extractedItinerary) => set({ extractedItinerary }),
    setWeatherData: (weatherData) => set({ weatherData }),

    setMessages: (messagesOrUpdater) => set((state) => ({
        messages: typeof messagesOrUpdater === 'function'
            ? (messagesOrUpdater as (prev: ChatMessage[]) => ChatMessage[])(state.messages)
            : messagesOrUpdater
    })),

    updateLastMessageData: (data) => set((state) => {
        const messages = [...state.messages];
        if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
            const lastMsg = messages[messages.length - 1];
            messages[messages.length - 1] = {
                ...lastMsg,
                data: {
                    ...(typeof lastMsg.data === 'object' && lastMsg.data !== null ? lastMsg.data : {}),
                    ...(typeof data === 'object' && data !== null ? data : {})
                }
            };
        }
        return { messages };
    }),

    clearMessages: () => set({ messages: [], currentAgent: '', currentStatus: '', extractedItinerary: null, weatherData: null }),

    setUploadingImage: (isUploadingImage) => set({ isUploadingImage }),

    setExtractedLocation: (extractedLocation) => set({ extractedLocation }),

    setVerifyingLocation: (isVerifyingLocation) => set({ isVerifyingLocation })
}));

interface TripState {
    currentTrip: Trip | null;
    trips: Trip[];
    preferences: UserPreferences;
    setCurrentTrip: (trip: Trip | null) => void;
    setTrips: (trips: Trip[]) => void;
    updatePreferences: (prefs: Partial<UserPreferences>) => void;
}

export const useTripStore = create<TripState>((set, get) => ({
    currentTrip: null,
    trips: [],
    preferences: {},

    setCurrentTrip: (currentTrip) => set({ currentTrip }),
    setTrips: (trips) => set({ trips }),
    updatePreferences: (prefs) => set((state) => ({
        preferences: { ...state.preferences, ...prefs }
    }))
}));

// ── Mood store (persisted across sessions) ──────────────────────────────────

interface MoodState {
    currentMood: string | null;
    setMood: (mood: string | null) => void;
}

export const useMoodStore = create<MoodState>()(
    persist(
        (set) => ({
            currentMood: null,
            setMood: (currentMood) => set({ currentMood }),
        }),
        { name: 'watchout-mood' }
    )
);
