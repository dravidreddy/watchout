'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Wallet, Sparkles, Check, ChevronRight, Compass, MessageSquare } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore, useMoodStore } from '@/lib/store';
import { MOODS } from '@/components/home/MoodSelector';
import { toast } from 'sonner';

interface OnboardModalProps {
    onComplete: () => void;
}

const steps = [
    {
        id: 'location',
        title: 'Where do you live?',
        description: 'Help us find deals and routes from your home city.',
        icon: MapPin,
    },
    {
        id: 'style',
        title: 'Your Travel Style',
        description: 'What kind of trips do you usually enjoy?',
        icon: Compass,
    },
    {
        id: 'vibe',
        title: 'Your Travel Vibe',
        description: 'What best describes your travel mood?',
        icon: Sparkles,
    },
    {
        id: 'budget',
        title: 'Budget Preference',
        description: 'How do you like to spend on trips?',
        icon: Wallet,
    },
    {
        id: 'language',
        title: 'AI Language',
        description: 'What language should we speak?',
        icon: MessageSquare,
    }
];

export const OnboardModal: React.FC<OnboardModalProps> = ({ onComplete }) => {
    const [step, setStep] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const user = useAuthStore((state) => state.user);
    const setUser = useAuthStore((state) => state.setUser);
    const { setMood } = useMoodStore();

    const [form, setForm] = useState({
        home_city: '',
        travel_style: 'balanced',
        travel_vibe: [] as string[],
        budget_range: 'mid-range',
        language: 'English'
    });

    const toggleVibe = (id: string) => {
        setForm(f => ({
            ...f,
            travel_vibe: f.travel_vibe.includes(id)
                ? f.travel_vibe.filter(v => v !== id)
                : [...f.travel_vibe, id]
        }));
    };

    const handleNext = () => {
        if (step < steps.length - 1) {
            setStep(step + 1);
        } else {
            handleSubmit();
        }
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        try {
            await api.updateProfile({
                home_city: form.home_city,
                preferences: {
                    travel_style: form.travel_style,
                    travel_vibe: form.travel_vibe,
                    budget_range: form.budget_range,
                    language: form.language
                },
                onboarding_completed: true
            });

            if (user) {
                setUser({
                    ...user,
                    home_city: form.home_city,
                    onboarding_completed: true,
                    preferences: {
                        ...user.preferences,
                        travel_style: form.travel_style,
                        travel_vibe: form.travel_vibe,
                        budget_range: form.budget_range,
                        language: form.language
                    }
                });
            }

            // Set the first vibe as initial mood if selected
            if (form.travel_vibe.length > 0) {
                setMood(form.travel_vibe[0]);
            }

            localStorage.setItem('onboarding_dismissed', 'true');
            toast.success('Preferences saved! Welcome to Watchout 🎉');
            onComplete();
        } catch (error) {
            toast.error('Failed to save preferences');
        } finally {
            setIsSubmitting(false);
        }
    };

    const currentStep = steps[step];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(13,17,23,0.9)', backdropFilter: 'blur(16px)' }}>
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="w-full max-w-lg rounded-3xl overflow-hidden shadow-2xl"
                style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-default)' }}
            >
                <div className="p-8">
                    {/* Header */}
                    <div className="flex items-center gap-5 mb-8">
                        <div className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg" style={{ background: 'var(--accent-50)', border: '1px solid var(--border-default)' }}>
                            <currentStep.icon className="w-7 h-7" style={{ color: 'var(--accent)' }} />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{currentStep.title}</h2>
                            <p className="font-medium" style={{ color: 'var(--text-secondary)' }}>{currentStep.description}</p>
                        </div>
                    </div>

                    {/* Form Content */}
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={step}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="min-h-[220px]"
                        >
                            {step === 0 && (
                                <div className="space-y-4">
                                    <div className="relative">
                                        <input
                                            type="text"
                                            placeholder="e.g. Mumbai, India"
                                            value={form.home_city}
                                            onChange={(e) => setForm({ ...form, home_city: e.target.value })}
                                            className="w-full px-5 py-4 rounded-2xl text-lg font-medium outline-none transition-all"
                                            style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}
                                        />
                                        <MapPin className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-tertiary)' }} />
                                    </div>
                                    <p className="text-sm ml-1" style={{ color: 'var(--text-tertiary)' }}>We'll use this to optimize travel recommendations from your home.</p>
                                </div>
                            )}

                            {step === 1 && (
                                <div className="grid grid-cols-2 gap-3">
                                    {[
                                        { name: 'Relaxing', sub: 'Slow & peaceful' },
                                        { name: 'Adventure', sub: 'Thrill & action' },
                                        { name: 'Cultural', sub: 'Heritage & arts' },
                                        { name: 'Balanced', sub: 'Best of both' }
                                    ].map((style) => (
                                        <button
                                            key={style.name}
                                            onClick={() => setForm({ ...form, travel_style: style.name.toLowerCase() })}
                                            className={`p-4 rounded-2xl text-left transition-all duration-300`}
                                            style={{
                                                border: `1px solid ${form.travel_style === style.name.toLowerCase() ? 'var(--accent)' : 'var(--border-subtle)'}`,
                                                background: form.travel_style === style.name.toLowerCase() ? 'var(--accent-50)' : 'var(--bg-tertiary)',
                                            }}
                                        >
                                            <div className="font-bold mb-0.5 text-lg" style={{ color: form.travel_style === style.name.toLowerCase() ? 'var(--accent)' : 'var(--text-primary)' }}>
                                                {style.name}
                                            </div>
                                            <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                                {style.sub}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}

                            {/* NEW: Step 2 — Travel Vibe */}
                            {step === 2 && (
                                <div>
                                    <p className="text-sm mb-3" style={{ color: 'var(--text-tertiary)' }}>Pick one or more that describe you</p>
                                    <div className="flex flex-wrap gap-2">
                                        {MOODS.map((m) => (
                                            <button
                                                key={m.id}
                                                onClick={() => toggleVibe(m.id)}
                                                className={`mood-pill ${form.travel_vibe.includes(m.id) ? 'active' : ''}`}
                                            >
                                                <span className="text-base leading-none">{m.emoji}</span>
                                                <span>{m.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {step === 3 && (
                                <div className="space-y-3">
                                    {[
                                        { name: 'Budget', sub: 'Cost-effective, local stays' },
                                        { name: 'Mid-range', sub: 'Comfortable & valuable' },
                                        { name: 'Luxury', sub: 'Premium & high-end' }
                                    ].map((b) => (
                                        <button
                                            key={b.name}
                                            onClick={() => setForm({ ...form, budget_range: b.name.toLowerCase() })}
                                            className="w-full p-4 rounded-2xl text-left flex items-center justify-between transition-all duration-300"
                                            style={{
                                                border: `1px solid ${form.budget_range === b.name.toLowerCase() ? 'var(--accent)' : 'var(--border-subtle)'}`,
                                                background: form.budget_range === b.name.toLowerCase() ? 'var(--accent-50)' : 'var(--bg-tertiary)',
                                            }}
                                        >
                                            <div>
                                                <div className="font-bold mb-0.5" style={{ color: form.budget_range === b.name.toLowerCase() ? 'var(--accent)' : 'var(--text-primary)' }}>{b.name}</div>
                                                <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{b.sub}</div>
                                            </div>
                                            {form.budget_range === b.name.toLowerCase() && (
                                                <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: 'var(--accent)' }}>
                                                    <Check className="w-4 h-4 text-white" />
                                                </div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}

                            {step === 4 && (
                                <div className="space-y-3">
                                    {['English', 'Hindi', 'Spanish', 'French', 'German'].map((lang) => (
                                        <button
                                            key={lang}
                                            onClick={() => setForm({ ...form, language: lang })}
                                            className="w-full p-4 rounded-2xl text-left flex items-center justify-between transition-all duration-300"
                                            style={{
                                                border: `1px solid ${form.language === lang ? 'var(--accent)' : 'var(--border-subtle)'}`,
                                                background: form.language === lang ? 'var(--accent-50)' : 'var(--bg-tertiary)',
                                            }}
                                        >
                                            <div className="font-bold" style={{ color: form.language === lang ? 'var(--accent)' : 'var(--text-primary)' }}>{lang}</div>
                                            {form.language === lang && (
                                                <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: 'var(--accent)' }}>
                                                    <Check className="w-4 h-4 text-white" />
                                                </div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>

                    {/* Footer */}
                    <div className="mt-10 flex items-center justify-between pt-6" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                        <div className="flex gap-2">
                            {steps.map((_, i) => (
                                <div
                                    key={i}
                                    className="h-2 rounded-full transition-all duration-300"
                                    style={{
                                        width: i === step ? '2.5rem' : '0.5rem',
                                        background: i === step ? 'var(--accent)' : 'var(--border-subtle)'
                                    }}
                                />
                            ))}
                        </div>

                        <button
                            onClick={handleNext}
                            disabled={isSubmitting || (step === 0 && !form.home_city)}
                            className="btn btn-primary px-8 py-3 font-bold flex items-center gap-2 disabled:opacity-50"
                        >
                            {isSubmitting ? 'Saving...' : (step === steps.length - 1 ? 'Get Started 🚀' : 'Next')}
                            {!isSubmitting && <ChevronRight className="w-5 h-5" />}
                        </button>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};
