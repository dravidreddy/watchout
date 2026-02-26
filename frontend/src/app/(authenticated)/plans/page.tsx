'use client';

import { useState } from 'react';

import { Check, ArrowLeft, Sparkles, Zap, Crown } from 'lucide-react';
import Link from 'next/link';

const plans = [
    {
        id: 'free',
        name: 'Explorer',
        icon: Sparkles,
        price: 'Free',
        period: '',
        description: 'Perfect for occasional travelers',
        image: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=600&h=400&fit=crop',
        features: [
            '3 trips per month',
            'Basic itinerary planning',
            'Email support',
        ],
        cta: 'Current Plan',
        color: '#6B7280',
    },
    {
        id: 'adventure',
        name: 'Adventure',
        icon: Zap,
        price: '₹299',
        period: '/month',
        description: 'For the passionate explorer',
        image: 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=600&h=400&fit=crop',
        features: [
            'Unlimited trips',
            'AI-powered recommendations',
            'Offline access',
            'Priority support',
            'Export to PDF',
        ],
        cta: 'Start Free Trial',
        popular: true,
        color: '#0891B2',
    },
    {
        id: 'ultimate',
        name: 'Ultimate',
        icon: Crown,
        price: '₹799',
        period: '/month',
        description: 'The complete travel experience',
        image: 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600&h=400&fit=crop',
        features: [
            'Everything in Adventure',
            'Real-time flight & hotel deals',
            'Concierge support',
            'Group trip planning',
            'Travel insurance discounts',
            'Early access to features',
        ],
        cta: 'Go Ultimate',
        color: '#7C3AED',
    },
];

import { useAuth } from '@/components/auth/AuthProvider';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { openCheckout } from '@/lib/razorpay';
import { toast } from 'sonner';

export default function PlansPage() {
    const { user } = useAuth();
    const setUser = useAuthStore((state) => state.setUser);
    const [updatingPlan, setUpdatingPlan] = useState<string | null>(null);

    const handlePlanSelect = async (planId: string) => {
        if (!user || updatingPlan) return;

        const plan = plans.find(p => p.id === planId);
        if (!plan) return;

        if (planId === 'free') {
            setUpdatingPlan(planId);
            try {
                await api.updateProfile({ subscription_tier: planId });
                setUser({ ...user, subscription_tier: planId });
                toast.success('Plan updated to Explorer');
            } catch (error) {
                console.error('Failed to update plan:', error);
                toast.error('Failed to update plan');
            } finally {
                setUpdatingPlan(null);
            }
            return;
        }

        // For paid plans, open Razorpay checkout
        const amount = parseInt(plan.price.replace('₹', ''));
        setUpdatingPlan(planId);

        openCheckout({
            planId,
            amount,
            email: user.email || '',
            name: user.name || 'Traveler',
            onSuccess: (tier) => {
                setUser({ ...user, subscription_tier: tier });
                toast.success(`Successfully upgraded to ${plan.name}!`);
                setUpdatingPlan(null);
            },
            onError: (error) => {
                toast.error(error.message);
                setUpdatingPlan(null);
            }
        });
    };

    return (
        <div className="min-h-screen pb-8">
            {/* Header */}
            <header className="px-4 md:px-8 py-6">
                <div className="flex items-center gap-3 mb-4">
                    <Link href="/profile" className="p-2 -ml-2 rounded-lg hover:bg-black/5">
                        <ArrowLeft className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                    </Link>
                    <h1 className="text-title" style={{ color: 'var(--text-primary)' }}>
                        Choose Your Plan
                    </h1>
                </div>
                <p className="max-w-lg" style={{ color: 'var(--text-secondary)' }}>
                    Unlock the full potential of AI-powered travel planning
                </p>
            </header>

            <div className="px-4 md:px-8 max-w-5xl mx-auto">
                {/* Plans Grid */}
                <div className="grid md:grid-cols-3 gap-6">
                    {plans.map((plan, index) => {
                        const isCurrent = user?.subscription_tier === plan.id || (!user?.subscription_tier && plan.id === 'free');
                        const isUpdating = updatingPlan === plan.id;

                        return (
                            <div
                                key={plan.id}
                                className={`animate-page-mount relative card overflow-hidden ${plan.popular ? 'ring-2 ring-[var(--accent)]' : ''}`}
                            >
                                {/* Popular Badge */}
                                {plan.popular && (
                                    <div
                                        className="absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-semibold text-white"
                                        style={{ background: 'var(--accent)' }}
                                    >
                                        Most Popular
                                    </div>
                                )}

                                {/* Hero Image */}
                                <div
                                    className="h-32 bg-cover bg-center"
                                    style={{
                                        backgroundImage: `url(${plan.image})`,
                                        backgroundColor: 'var(--bg-tertiary)'
                                    }}
                                >
                                    <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-black/40 to-transparent" />
                                </div>

                                {/* Content */}
                                <div className="p-6">
                                    {/* Icon & Name */}
                                    <div className="flex items-center gap-3 mb-2">
                                        <div
                                            className="w-10 h-10 rounded-xl flex items-center justify-center"
                                            style={{ background: `${plan.color}20` }}
                                        >
                                            <plan.icon className="w-5 h-5" style={{ color: plan.color }} />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                                {plan.name}
                                            </h3>
                                        </div>
                                    </div>

                                    {/* Price */}
                                    <div className="mb-4">
                                        <span className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
                                            {plan.price}
                                        </span>
                                        {plan.period && (
                                            <span style={{ color: 'var(--text-tertiary)' }}>{plan.period}</span>
                                        )}
                                    </div>

                                    <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                                        {plan.description}
                                    </p>

                                    {/* Features */}
                                    <ul className="space-y-2 mb-6">
                                        {plan.features.map((feature, i) => (
                                            <li key={i} className="flex items-start gap-2 text-sm">
                                                <Check
                                                    className="w-4 h-4 mt-0.5 flex-shrink-0"
                                                    style={{ color: plan.color }}
                                                />
                                                <span style={{ color: 'var(--text-primary)' }}>{feature}</span>
                                            </li>
                                        ))}
                                    </ul>

                                    {/* CTA */}
                                    <button
                                        onClick={() => handlePlanSelect(plan.id)}
                                        disabled={isCurrent || isUpdating}
                                        className="w-full py-3 rounded-xl font-medium transition-all flex justify-center items-center gap-2"
                                        style={{
                                            background: isCurrent ? 'var(--bg-tertiary)' : plan.color,
                                            color: isCurrent ? 'var(--text-secondary)' : 'white',
                                            cursor: (isCurrent || isUpdating) ? 'default' : 'pointer',
                                            opacity: isUpdating ? 0.7 : 1
                                        }}
                                    >
                                        {isUpdating ? 'Updating...' : (isCurrent ? 'Current Plan' : plan.cta)}
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* FAQ or Trust indicators */}
                <div className="mt-12 text-center">
                    <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                        ✓ Cancel anytime &nbsp;•&nbsp; ✓ 7-day free trial &nbsp;•&nbsp; ✓ Secure payment
                    </p>
                    <div className="flex justify-center gap-4 mt-4">
                        <img src="/visa.svg" alt="Visa" className="h-6 opacity-50" />
                        <img src="/mastercard.svg" alt="Mastercard" className="h-6 opacity-50" />
                    </div>
                </div>
            </div>
        </div>
    );
}
