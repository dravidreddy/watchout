'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Wallet, Sparkles, Check, ChevronRight, Compass } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { toast } from 'sonner';

interface OnboardModalProps {
    onComplete: () => void;
}

const steps = [
    {
        id: 'location',
        title: 'Where do you live?',
        description: 'Help us find travel deals and routes from your home city.',
        icon: MapPin,
    },
    {
        id: 'style',
        title: 'Travel Style',
        description: 'What kind of trips do you usually enjoy?',
        icon: Compass,
    },
    {
        id: 'budget',
        title: 'Budget Preference',
        description: 'How do you like to spend?',
        icon: Wallet,
    }
];

export const OnboardModal: React.FC<OnboardModalProps> = ({ onComplete }) => {
    const [step, setStep] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const user = useAuthStore((state) => state.user);
    const setUser = useAuthStore((state) => state.setUser);

    const [form, setForm] = useState({
        home_city: '',
        travel_style: 'balanced',
        budget_range: 'mid-range'
    });

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
                    budget_range: form.budget_range
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
                        budget_range: form.budget_range
                    }
                });
            }

            // Mark onboarding as dismissed in localStorage
            localStorage.setItem('onboarding_dismissed', 'true');

            toast.success('Preferences saved!');
            onComplete();
        } catch (error) {
            toast.error('Failed to save preferences');
        } finally {
            setIsSubmitting(false);
        }
    };

    const currentStep = steps[step];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-md">
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="w-full max-w-lg bg-white rounded-3xl overflow-hidden shadow-2xl border border-slate-200"
            >
                <div className="p-8">
                    {/* Header */}
                    <div className="flex items-center gap-5 mb-8">
                        <div className="w-14 h-14 rounded-2xl bg-accent flex items-center justify-center shadow-lg shadow-accent/20">
                            <currentStep.icon className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-slate-900">{currentStep.title}</h2>
                            <p className="text-slate-600 font-medium">{currentStep.description}</p>
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
                                            className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:border-accent focus:bg-white focus:ring-4 focus:ring-accent/10 transition-all outline-none text-lg font-medium"
                                        />
                                        <MapPin className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    </div>
                                    <p className="text-sm text-slate-500 font-medium ml-1">We'll use this to optimize travel recommendations from your home.</p>
                                </div>
                            )}

                            {step === 1 && (
                                <div className="grid grid-cols-2 gap-4">
                                    {[
                                        { name: 'Relaxing', sub: 'Slow & peaceful' },
                                        { name: 'Adventure', sub: 'Thrill & action' },
                                        { name: 'Cultural', sub: 'Heritage & arts' },
                                        { name: 'Balanced', sub: 'Best of both' }
                                    ].map((style) => (
                                        <button
                                            key={style.name}
                                            onClick={() => setForm({ ...form, travel_style: style.name.toLowerCase() })}
                                            className={`p-5 rounded-2xl border-2 text-left transition-all duration-300 ${form.travel_style === style.name.toLowerCase()
                                                ? 'border-accent bg-accent/5 shadow-md ring-2 ring-accent/20'
                                                : 'border-slate-100 bg-slate-50 hover:bg-white hover:border-slate-200 text-slate-600'
                                                }`}
                                        >
                                            <div className={`font-bold mb-0.5 text-lg ${form.travel_style === style.name.toLowerCase() ? 'text-accent' : 'text-slate-900'}`}>
                                                {style.name}
                                            </div>
                                            <div className={`text-xs ${form.travel_style === style.name.toLowerCase() ? 'text-accent/80' : 'text-slate-500'}`}>
                                                {style.sub}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}

                            {step === 2 && (
                                <div className="space-y-4">
                                    {[
                                        { name: 'Budget', sub: 'Cost-effective, local stays' },
                                        { name: 'Mid-range', sub: 'Comfortable & valuable' },
                                        { name: 'Luxury', sub: 'Premium & high-end' }
                                    ].map((b) => (
                                        <button
                                            key={b.name}
                                            onClick={() => setForm({ ...form, budget_range: b.name.toLowerCase() })}
                                            className={`w-full p-5 rounded-2xl border-2 text-left flex items-center justify-between transition-all duration-300 ${form.budget_range === b.name.toLowerCase()
                                                ? 'border-accent bg-accent/5 shadow-md ring-2 ring-accent/20'
                                                : 'border-slate-100 bg-slate-50 hover:bg-white hover:border-slate-200'
                                                }`}
                                        >
                                            <div>
                                                <div className={`font-bold mb-0.5 text-lg ${form.budget_range === b.name.toLowerCase() ? 'text-accent' : 'text-slate-900'}`}>
                                                    {b.name}
                                                </div>
                                                <div className={`text-xs ${form.budget_range === b.name.toLowerCase() ? 'text-accent/80' : 'text-slate-500'}`}>
                                                    {b.sub}
                                                </div>
                                            </div>
                                            {form.budget_range === b.name.toLowerCase() && (
                                                <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center shadow-lg shadow-accent/20">
                                                    <Check className="w-5 h-5 text-white" />
                                                </div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>

                    {/* Footer */}
                    <div className="mt-12 flex items-center justify-between border-t border-slate-200/50 pt-8">
                        <div className="flex gap-2">
                            {steps.map((_, i) => (
                                <div
                                    key={i}
                                    className={`h-2 rounded-full transition-all duration-300 ${i === step ? 'w-10 bg-accent' : 'w-2 bg-slate-200'}`}
                                />
                            ))}
                        </div>

                        <button
                            onClick={handleNext}
                            disabled={isSubmitting || (step === 0 && !form.home_city)}
                            className="bg-accent text-white px-10 py-4 rounded-2xl font-bold flex items-center gap-3 hover:opacity-90 disabled:opacity-50 transition-all shadow-lg shadow-accent/25"
                        >
                            {isSubmitting ? 'Saving...' : (step === steps.length - 1 ? 'Get Started' : 'Next')}
                            {!isSubmitting && <ChevronRight className="w-5 h-5" />}
                        </button>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};
