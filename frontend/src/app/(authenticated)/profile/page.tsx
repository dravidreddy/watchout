'use client';

import { useState } from 'react';
import { CityAutocomplete } from '@/components/ui/CityAutocomplete';
import { AnimatePresence, motion } from 'framer-motion';
import { X, User, MapPin, Bell, Palette, Shield, LogOut, ChevronRight, Camera, CreditCard, Plane, Mountain, Wallet, Moon, Sun, Monitor, MessageSquare } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import Link from 'next/link';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useTheme } from 'next-themes';

// Travel style options
const travelStyles = ['Adventure', 'Relaxation', 'Cultural', 'Family', 'Budget', 'Luxury'];

// Budget ranges
const budgetRanges = ['Budget', 'Mid-range', 'Luxury'];

// Languages
const languages = ['English', 'Hindi', 'Spanish', 'French', 'German'];

export default function ProfilePage() {
    const { user, setUser, logout, isLoading } = useAuth();
    const [selectedStyle, setSelectedStyle] = useState(user?.preferences?.travel_style || 'Adventure');
    const [selectedBudget, setSelectedBudget] = useState(user?.preferences?.budget_range || 'Mid-range');
    const [selectedLanguage, setSelectedLanguage] = useState(user?.preferences?.language || 'English');
    const { theme, setTheme } = useTheme();
    const [isSaving, setIsSaving] = useState(false);
    const [isHomeCityModalOpen, setIsHomeCityModalOpen] = useState(false);
    const [isThemeModalOpen, setIsThemeModalOpen] = useState(false);
    const [isNotificationsModalOpen, setIsNotificationsModalOpen] = useState(false);
    const [notifications, setNotifications] = useState({
        email: true,
        push: true,
        tripUpdates: true
    });
    const [homeCity, setHomeCity] = useState(user?.home_city || '');

    const updatePreference = async (key: string, value: string) => {
        if (!user) return;

        // Optimistic update
        if (key === 'travel_style') setSelectedStyle(value);
        if (key === 'budget_range') setSelectedBudget(value);
        if (key === 'language') setSelectedLanguage(value);

        try {
            setIsSaving(true);
            const updatedProfile = await api.updateProfile({
                preferences: {
                    ...user.preferences,
                    [key]: value
                }
            });
            setUser({
                ...user,
                preferences: {
                    ...user.preferences,
                    [key]: value
                }
            });
        } catch (error) {
            console.error('Failed to update profile:', error);
            toast.error('Failed to update preference');
        } finally {
            setIsSaving(false);
        }
    };

    const handleHomeCityUpdate = async () => {
        if (!user) return;
        try {
            setIsSaving(true);
            await api.updateProfile({ home_city: homeCity });
            setUser({ ...user, home_city: homeCity });
            toast.success(`Home city updated to ${homeCity}`);
            setIsHomeCityModalOpen(false);
        } catch (error) {
            toast.error('Failed to update home city');
        } finally {
            setIsSaving(false);
        }
    };

    const menuItems = [
        { icon: MapPin, label: 'Home City', value: user?.home_city || 'Not set', href: '#' },
        { icon: Bell, label: 'Notifications', value: 'Enabled', href: '#' },
        { icon: Palette, label: 'Theme', value: theme ? theme.charAt(0).toUpperCase() + theme.slice(1) : 'System', href: '#' },
        { icon: Shield, label: 'Privacy', value: '', href: '#' },
    ];

    const handleLogout = async () => {
        await logout();
    };

    if (isLoading) {
        return (
            <div className="min-h-screen pb-8 px-4 md:px-8 animate-pulse">
                <div className="h-8 w-32 bg-gray-200 rounded-lg mb-8 mt-6" />
                <div className="max-w-2xl mx-auto">
                    <div className="card h-32 bg-gray-50/50 mb-6" />
                    <div className="h-4 w-40 bg-gray-100 rounded mb-3" />
                    <div className="card h-48 bg-gray-50/50 mb-6" />
                    <div className="h-4 w-40 bg-gray-100 rounded mb-3" />
                    <div className="card h-64 bg-gray-50/50" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pb-8">
            {/* Header */}
            <header className="px-4 md:px-8 py-6">
                <h1 className="text-title" style={{ color: 'var(--text-primary)' }}>
                    Profile
                </h1>
            </header>

            <div className="px-4 md:px-8 max-w-2xl mx-auto">
                {/* Profile Card */}
                <div className="card p-6 mb-6">
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            {user?.photo_url ? (
                                <img
                                    src={user.photo_url}
                                    alt={user?.name || 'Profile'}
                                    className="w-20 h-20 rounded-2xl object-cover"
                                    style={{ boxShadow: 'var(--shadow-md)' }}
                                />
                            ) : (
                                <div
                                    className="w-20 h-20 rounded-2xl flex items-center justify-center text-2xl font-bold text-white"
                                    style={{
                                        background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)',
                                        boxShadow: 'var(--shadow-md)'
                                    }}
                                >
                                    {user?.name?.[0] || user?.email?.[0] || '?'}
                                </div>
                            )}
                        </div>
                        <div className="flex-1">
                            <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                                {user?.name || 'Traveler'}
                            </h2>
                            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                {user?.email}
                            </p>
                            <span
                                className="inline-flex items-center gap-1 mt-2 px-3 py-1 rounded-full text-xs font-medium"
                                style={{
                                    background: 'var(--accent-50)',
                                    color: 'var(--accent-dark)'
                                }}
                            >
                                {user?.subscription_tier === 'premium' ? '⭐ Premium' : '🌱 Free Plan'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Travel Preferences */}
                <section className="mb-6">
                    <h3 className="text-sm font-semibold uppercase tracking-wide mb-3 px-1" style={{ color: 'var(--text-tertiary)' }}>
                        Travel Preferences
                    </h3>
                    <div className="card p-6">
                        {/* Travel Style */}
                        <div className="mb-6">
                            <label className="flex items-center gap-2 text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
                                <Plane className="w-4 h-4" />
                                Travel Style
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {travelStyles.map((style) => (
                                    <button
                                        key={style}
                                        onClick={() => updatePreference('travel_style', style)}
                                        className="px-4 py-2 rounded-full text-sm font-medium transition-all"
                                        style={{
                                            background: selectedStyle === style ? 'var(--accent)' : 'var(--bg-tertiary)',
                                            color: selectedStyle === style ? 'white' : 'var(--text-secondary)'
                                        }}
                                    >
                                        {style}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* AI Language */}
                        <div className="mb-6">
                            <label className="flex items-center gap-2 text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
                                <MessageSquare className="w-4 h-4" />
                                AI Language
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {languages.map((lang) => (
                                    <button
                                        key={lang}
                                        onClick={() => updatePreference('language', lang)}
                                        className="px-4 py-2 rounded-full text-sm font-medium transition-all"
                                        style={{
                                            background: selectedLanguage === lang ? 'var(--accent)' : 'var(--bg-tertiary)',
                                            color: selectedLanguage === lang ? 'white' : 'var(--text-secondary)'
                                        }}
                                    >
                                        {lang}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Budget Range */}
                        <div>
                            <label className="flex items-center gap-2 text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
                                <Wallet className="w-4 h-4" />
                                Budget Range
                            </label>
                            <div className="flex gap-2">
                                {budgetRanges.map((budget) => (
                                    <button
                                        key={budget}
                                        onClick={() => updatePreference('budget_range', budget)}
                                        className="flex-1 py-3 rounded-xl text-sm font-medium transition-all"
                                        style={{
                                            background: selectedBudget === budget ? 'var(--accent)' : 'var(--bg-tertiary)',
                                            color: selectedBudget === budget ? 'white' : 'var(--text-secondary)'
                                        }}
                                    >
                                        {budget}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Settings */}
                <section className="mb-6">
                    <h3 className="text-sm font-semibold uppercase tracking-wide mb-3 px-1" style={{ color: 'var(--text-tertiary)' }}>
                        Settings
                    </h3>
                    <div className="card overflow-hidden">
                        {menuItems.map((item, index) => (
                            <button
                                key={item.label}
                                onClick={() => {
                                    if (item.label === 'Home City') setIsHomeCityModalOpen(true);
                                    else if (item.label === 'Theme') setIsThemeModalOpen(true);
                                    else if (item.label === 'Notifications') setIsNotificationsModalOpen(true);
                                    else toast.info(`${item.label} coming soon!`);
                                }}
                                className="w-full p-4 flex items-center justify-between transition-colors hover:bg-black/[0.02]"
                                style={{
                                    borderBottom: index < menuItems.length - 1 ? '1px solid rgba(0,0,0,0.05)' : 'none'
                                }}
                            >
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-9 h-9 rounded-xl flex items-center justify-center"
                                        style={{ background: 'var(--accent-50)' }}
                                    >
                                        <item.icon className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                                    </div>
                                    <span style={{ color: 'var(--text-primary)' }}>{item.label}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    {item.value && (
                                        <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                                            {item.value}
                                        </span>
                                    )}
                                    <ChevronRight className="w-5 h-5" style={{ color: 'var(--text-tertiary)' }} />
                                </div>
                            </button>
                        ))}
                    </div>
                </section>

                {/* Subscription */}
                <section className="mb-6">
                    <h3 className="text-sm font-semibold uppercase tracking-wide mb-3 px-1" style={{ color: 'var(--text-tertiary)' }}>
                        Subscription
                    </h3>
                    <Link href="/plans">
                        <div
                            className="card p-6 cursor-pointer transition-all hover:shadow-lg"
                            style={{
                                background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%)',
                            }}
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-semibold text-white mb-1">Upgrade to Premium</h4>
                                    <p className="text-white/80 text-sm">Unlimited trips, offline access & more</p>
                                </div>
                                <ChevronRight className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </Link>
                </section>

                {/* Logout */}
                <motion.button
                    whileTap={{ scale: 0.98 }}
                    onClick={handleLogout}
                    className="w-full p-4 rounded-xl flex items-center justify-center gap-2 transition-colors"
                    style={{
                        background: '#FEE2E2',
                        color: '#DC2626'
                    }}
                >
                    <LogOut className="w-5 h-5" />
                    Sign Out
                </motion.button>

                {/* Version */}
                <p className="text-center text-sm mt-8" style={{ color: 'var(--text-tertiary)' }}>
                    Watchout v1.0.0
                </p>
            </div>

            {/* Home City Modal */}

            {isHomeCityModalOpen && (
                <>
                    <div
                        onClick={() => setIsHomeCityModalOpen(false)}
                        className="animate-page-mount fixed inset-0 bg-black/40 z-[100] backdrop-blur-sm"
                    />
                    <div
                        className="animate-page-mount fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-white z-[101] rounded-2xl shadow-2xl p-6"
                    >
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold">Update Home City</h3>
                            <button
                                onClick={() => setIsHomeCityModalOpen(false)}
                                className="p-1 hover:bg-gray-100 rounded-full"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <p className="text-sm text-gray-500 mb-6">
                            Setting your home city helps us provide better travel recommendations from your location.
                        </p>

                        <div className="space-y-6">
                            <CityAutocomplete
                                value={homeCity}
                                onChange={(city) => setHomeCity(city)}
                                placeholder="Enter your home city..."
                            />

                            <div className="flex gap-3">
                                <button
                                    onClick={() => setIsHomeCityModalOpen(false)}
                                    className="flex-1 py-3 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleHomeCityUpdate}
                                    disabled={isSaving || !homeCity}
                                    className="flex-1 py-3 rounded-xl text-sm font-medium text-white bg-accent hover:opacity-90 transition-all disabled:opacity-50"
                                >
                                    {isSaving ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}


            {/* Theme Modal */}

            {isThemeModalOpen && (
                <>
                    <div
                        onClick={() => setIsThemeModalOpen(false)}
                        className="animate-page-mount fixed inset-0 bg-black/40 z-[100] backdrop-blur-sm"
                    />
                    <div
                        className="animate-page-mount fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-white dark:bg-slate-900 z-[101] rounded-2xl shadow-2xl p-6"
                    >
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold">Select Theme</h3>
                            <button
                                onClick={() => setIsThemeModalOpen(false)}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="grid grid-cols-1 gap-3">
                            {[
                                { id: 'light', label: 'Light', icon: Sun },
                                { id: 'dark', label: 'Dark', icon: Moon },
                                { id: 'system', label: 'System', icon: Monitor }
                            ].map((option) => (
                                <button
                                    key={option.id}
                                    onClick={() => {
                                        setTheme(option.id);
                                        setIsThemeModalOpen(false);
                                        toast.success(`Theme set to ${option.label}`);
                                    }}
                                    className={`flex items-center gap-3 p-4 rounded-xl border transition-all ${theme === option.id
                                        ? 'border-accent bg-accent/5 text-accent font-medium'
                                        : 'border-transparent bg-gray-50 dark:bg-slate-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700'
                                        }`}
                                >
                                    <option.icon className="w-5 h-5" />
                                    <span>{option.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </>
            )}


            {/* Notifications Modal */}

            {isNotificationsModalOpen && (
                <>
                    <div
                        onClick={() => setIsNotificationsModalOpen(false)}
                        className="animate-page-mount fixed inset-0 bg-black/40 z-[100] backdrop-blur-sm"
                    />
                    <div
                        className="animate-page-mount fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-white dark:bg-slate-900 z-[101] rounded-2xl shadow-2xl p-6"
                    >
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold">Notifications</h3>
                            <button
                                onClick={() => setIsNotificationsModalOpen(false)}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {[
                                { id: 'email', label: 'Email Notifications', desc: 'Get trip updates via email' },
                                { id: 'push', label: 'Push Notifications', desc: 'Real-time alerts on your device' },
                                { id: 'tripUpdates', label: 'Trip Updates', desc: 'AI suggestions and itinerary changes' }
                            ].map((opt) => (
                                <div key={opt.id} className="flex items-center justify-between p-2">
                                    <div>
                                        <div className="text-sm font-medium">{opt.label}</div>
                                        <div className="text-xs text-gray-500">{opt.desc}</div>
                                    </div>
                                    <button
                                        onClick={() => setNotifications({ ...notifications, [opt.id as keyof typeof notifications]: !notifications[opt.id as keyof typeof notifications] })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${notifications[opt.id as keyof typeof notifications] ? 'bg-accent' : 'bg-gray-200 dark:bg-slate-700'
                                            }`}
                                    >
                                        <span
                                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${notifications[opt.id as keyof typeof notifications] ? 'translate-x-6' : 'translate-x-1'
                                                }`}
                                        />
                                    </button>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => {
                                toast.success('Notification preferences saved');
                                setIsNotificationsModalOpen(false);
                            }}
                            className="w-full mt-8 py-3 rounded-xl text-sm font-medium text-white bg-accent hover:opacity-90 transition-all shadow-lg shadow-accent/20"
                        >
                            Done
                        </button>
                    </div>
                </>
            )}

        </div>
    );
}
