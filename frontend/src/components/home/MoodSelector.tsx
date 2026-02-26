'use client';

import React from 'react';
import { useMoodStore } from '@/lib/store';
import { api } from '@/lib/api';
import { useAuth } from '@/components/auth/AuthProvider';
import { useAuthStore } from '@/lib/store';

export const MOODS = [
    { id: 'adventurous', label: 'Adventurous', emoji: '😎' },
    { id: 'chill', label: 'Chill', emoji: '🌿' },
    { id: 'romantic', label: 'Romantic', emoji: '❤️' },
    { id: 'family', label: 'Family Fun', emoji: '👨‍👩‍👧' },
    { id: 'workation', label: 'Workation', emoji: '💼' },
    { id: 'spiritual', label: 'Spiritual', emoji: '🙏' },
    { id: 'foodie', label: 'Foodie Tour', emoji: '🍜' },
    { id: 'party', label: 'Party Mode', emoji: '🎉' },
];

export function MoodSelector() {
    const { currentMood, setMood } = useMoodStore();
    const { user } = useAuth();
    const setUser = useAuthStore((s) => s.setUser);

    const handleSelect = async (moodId: string) => {
        const next = moodId === currentMood ? null : moodId;
        setMood(next);

        // Persist to backend (fire and forget — don't block UI)
        if (user) {
            try {
                const updated = await api.updateProfile({
                    preferences: {
                        ...user.preferences,
                        current_mood: next ?? undefined,
                    }
                });
                // Optimistic update of the auth store so chat picks it up instantly
                setUser({ ...user, preferences: { ...user.preferences, current_mood: next ?? undefined } });
            } catch {
                // silent — mood is still set locally
            }
        }
    };

    return (
        <div className="w-full">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3"
                style={{ color: 'var(--text-tertiary)' }}>
                Today's Vibe
            </p>
            <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-1">
                {MOODS.map((m) => (
                    <button
                        key={m.id}
                        onClick={() => handleSelect(m.id)}
                        className={`mood-pill flex-shrink-0 ${currentMood === m.id ? 'active' : ''}`}
                    >
                        <span className="text-base leading-none">{m.emoji}</span>
                        <span>{m.label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
