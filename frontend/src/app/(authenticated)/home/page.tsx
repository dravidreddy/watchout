'use client';

import { useEffect, useState } from 'react';
import { Bell, User, Search, ArrowRight, MapPin, Star, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/components/auth/AuthProvider';
import { DestinationCard, SeasonalCard } from '@/components/home/DestinationCard';
import { api, Destination } from '@/lib/api';
import { OnboardModal } from '@/components/onboarding/OnboardModal';

const aiSuggestions = [
    'Best weekend trip from Hyderabad',
    'Budget-friendly Kerala 5D',
    'Himachal in March',
    'Romantic Udaipur getaway',
];

const seasonalPicks = [
    { id: '1', title: 'Monsoon Escapes', subtitle: 'Coorg, Munnar, Lonavala', image: 'https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=600&h=400&fit=crop' },
    { id: '2', title: 'Winter Road Trips', subtitle: 'Himachal, Uttarakhand', image: 'https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=600&h=400&fit=crop' },
];

export default function HomePage() {
    const { user } = useAuth();
    const [searchQuery, setSearchQuery] = useState('');
    const [trending, setTrending] = useState<Destination[]>([]);
    const [nearby, setNearby] = useState<Destination[]>([]);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showOnboarding, setShowOnboarding] = useState(false);

    useEffect(() => {
        // Check both user state and localStorage to prevent onboarding from showing after completion
        const onboardingDismissed = localStorage.getItem('onboarding_dismissed');
        if (user && !user.onboarding_completed && onboardingDismissed !== 'true') {
            setShowOnboarding(true);
        }
    }, [user]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch trending and suggestions in parallel
                // Fetch trending destinations
                const trendingData = await api.getTrendingDestinations();
                setTrending(trendingData);

                // Fetch suggestions only if user is logged in
                if (user) {
                    try {
                        const suggestionsData = await api.getAISuggestions();
                        setSuggestions(suggestionsData);
                    } catch (e) {
                        console.error('Failed to fetch suggestions:', e);
                        // Don't fail the whole page load
                    }
                }

                // Get nearby based on location or home_city
                const getFallbackLocation = () => {
                    // Default to Hyderabad if nothing else
                    return { lat: 17.3850, lng: 78.4867 };
                };

                // Check for stored location first
                const storedLocation = localStorage.getItem('user_location');
                const locationTimestamp = localStorage.getItem('user_location_timestamp');
                const LOCATION_EXPIRY = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds

                if (storedLocation && locationTimestamp) {
                    const age = Date.now() - parseInt(locationTimestamp);
                    if (age < LOCATION_EXPIRY) {
                        // Use stored location if it's less than 7 days old
                        try {
                            const coords = JSON.parse(storedLocation);
                            const nearbyData = await api.getNearbyDestinations(coords.lat, coords.lng);
                            setNearby(nearbyData);
                            return; // Exit early, we have valid data
                        } catch (e) {
                            console.error('Failed to use stored location', e);
                            // Continue to request new location
                        }
                    }
                }

                // Only request location if we don't have valid stored data
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        async (pos) => {
                            try {
                                const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                                // Store the location for future use
                                localStorage.setItem('user_location', JSON.stringify(coords));
                                localStorage.setItem('user_location_timestamp', Date.now().toString());

                                const nearbyData = await api.getNearbyDestinations(coords.lat, coords.lng);
                                setNearby(nearbyData);
                            } catch (e) {
                                console.error('Nearby fetch failed', e);
                                const fallback = getFallbackLocation();
                                const nearbyData = await api.getNearbyDestinations(fallback.lat, fallback.lng);
                                setNearby(nearbyData);
                            }
                        },
                        async () => {
                            const fallback = getFallbackLocation();
                            const nearbyData = await api.getNearbyDestinations(fallback.lat, fallback.lng);
                            setNearby(nearbyData);
                        }
                    );
                } else {
                    const fallback = getFallbackLocation();
                    const nearbyData = await api.getNearbyDestinations(fallback.lat, fallback.lng);
                    setNearby(nearbyData);
                }
            } catch (error) {
                console.error('Home page data fetch error:', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const LoadingSkeleton = () => (
        <div className="flex gap-4 overflow-hidden pb-2 -mx-4 px-4">
            {[1, 2, 3].map((i) => (
                <div key={i} className="min-w-[160px] h-56 rounded-2xl animate-pulse bg-gray-200 dark:bg-slate-800" />
            ))}
        </div>
    );

    return (
        <div className="min-h-screen">
            {/* Mobile Header */}
            <header className="md:hidden sticky top-0 z-30 glass px-4 py-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold"
                            style={{ background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)' }}
                        >
                            B
                        </div>
                        <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                            Bharat Voyager
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button className="p-2 rounded-lg hover:bg-black/5 transition-colors relative">
                            <Bell className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
                        </button>
                        <Link href="/profile">
                            <div
                                className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-medium"
                                style={{ background: 'var(--accent)' }}
                            >
                                {user?.name?.[0] || user?.email?.[0] || '?'}
                            </div>
                        </Link>
                    </div>
                </div>
            </header>

            <div className="px-4 md:px-8 py-6 max-w-7xl mx-auto">
                {/* Search Bar */}
                <div className="mb-6">
                    <div className="relative">
                        <Search
                            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5"
                            style={{ color: 'var(--text-tertiary)' }}
                        />
                        <input
                            type="text"
                            placeholder="Where do you want to go?"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="input search-input py-4"
                            style={{ paddingLeft: '2.75rem' }}
                        />
                    </div>
                    <p className="mt-2 text-sm" style={{ color: 'var(--text-tertiary)' }}>
                        Trips, places, routes, weather…
                    </p>
                </div>

                {/* Desktop Layout */}
                <div className="flex gap-8">
                    {/* Main Content */}
                    <div className="flex-1">
                        {/* Start Trip CTA */}
                        <Link href="/chat">
                            <div
                                className="card p-6 mb-8 cursor-pointer card-hover-scale"
                                style={{
                                    background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 50%, #0E7490 100%)',
                                    boxShadow: '0 8px 32px rgba(8, 145, 178, 0.3)'
                                }}
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h2 className="text-xl font-semibold text-white mb-1">
                                            Plan a new itinerary
                                        </h2>
                                        <p className="text-white/80">
                                            AI will build a day-by-day plan in minutes.
                                        </p>
                                    </div>
                                    <div
                                        className="w-12 h-12 rounded-xl flex items-center justify-center"
                                        style={{ background: 'rgba(255,255,255,0.2)' }}
                                    >
                                        <ArrowRight className="w-6 h-6 text-white" />
                                    </div>
                                </div>
                            </div>
                        </Link>

                        {/* Trending Section */}
                        <section className="mb-8">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-heading" style={{ color: 'var(--text-primary)' }}>
                                    Trending in India
                                </h2>
                                <Link
                                    href="/explore"
                                    className="text-sm font-medium flex items-center gap-1 hover:underline"
                                    style={{ color: 'var(--accent)' }}
                                >
                                    View all <ChevronRight className="w-4 h-4" />
                                </Link>
                            </div>
                            <div className="flex gap-4 overflow-x-auto hide-scrollbar pb-2 -mx-4 px-4">
                                {isLoading ? (
                                    <LoadingSkeleton />
                                ) : (
                                    trending.map((dest, index) => (
                                        <div
                                            key={dest._id}
                                            className="stagger-item"
                                        >
                                            <Link href={`/explore?city=${encodeURIComponent(dest.name)}`}>
                                                <DestinationCard
                                                    name={dest.name}
                                                    image={dest.image_url}
                                                    tag={dest.category[0]}
                                                    rating={dest.rating}
                                                />
                                            </Link>
                                        </div>
                                    ))
                                )}
                            </div>
                        </section>

                        {/* Seasonal Picks */}
                        <section className="mb-8">
                            <h2 className="text-heading mb-4" style={{ color: 'var(--text-primary)' }}>
                                Seasonal Picks
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {seasonalPicks.map((pick, index) => (
                                    <div
                                        key={pick.id}
                                        className="stagger-item"
                                    >
                                        <SeasonalCard
                                            title={pick.title}
                                            subtitle={pick.subtitle}
                                            image={pick.image}
                                        />
                                    </div>
                                ))}
                            </div>
                        </section>

                        {/* Nearby Favorites */}
                        <section className="mb-8">
                            <div className="flex items-center gap-2 mb-4">
                                <MapPin className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                                <h2 className="text-heading" style={{ color: 'var(--text-primary)' }}>
                                    Nearby Favorites
                                </h2>
                            </div>
                            <div className="flex gap-4 overflow-x-auto hide-scrollbar pb-2 -mx-4 px-4">
                                {isLoading ? (
                                    <LoadingSkeleton />
                                ) : (
                                    nearby.map((place, index) => (
                                        <div
                                            key={place._id}
                                            className="stagger-item"
                                        >
                                            <Link href={`/explore?city=${encodeURIComponent(place.name)}`}>
                                                <DestinationCard
                                                    name={place.name}
                                                    image={place.image_url}
                                                    rating={place.rating}
                                                    tag={place.category[0]}
                                                />
                                            </Link>
                                        </div>
                                    ))
                                )}
                            </div>
                        </section>
                    </div>

                    {/* AI Suggestions Panel (Desktop Only) */}
                    <div className="hidden lg:block w-80">
                        <div className="card p-6 sticky top-24">
                            <h3 className="text-heading mb-4" style={{ color: 'var(--text-primary)' }}>
                                ✨ AI Suggestions
                            </h3>
                            <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                                One-click trip ideas just for you
                            </p>
                            <div className="space-y-3">
                                {suggestions.map((suggestion, index) => (
                                    <Link href={`/chat?q=${encodeURIComponent(suggestion)}`} key={index}>
                                        <div
                                            className="p-3 rounded-xl cursor-pointer transition-all flex items-center justify-between group hover:translate-x-1"
                                            style={{ background: 'var(--bg-tertiary)' }}
                                        >
                                            <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                                                {suggestion}
                                            </span>
                                            <ArrowRight
                                                className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity"
                                                style={{ color: 'var(--accent)' }}
                                            />
                                        </div>
                                    </Link>
                                ))}
                                {suggestions.length === 0 && !isLoading && (
                                    <p className="text-xs text-center text-gray-500 py-4 italic">
                                        Planning your next adventure...
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="mt-12 pt-6 text-center text-sm" style={{ borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                    <div className="flex justify-center gap-6 mb-4">
                        <Link href="/privacy" className="hover:underline" style={{ color: 'var(--text-tertiary)' }}>
                            Privacy & Consent
                        </Link>
                        <Link href="/support" className="hover:underline" style={{ color: 'var(--text-tertiary)' }}>
                            Support
                        </Link>
                        <Link href="/terms" className="hover:underline" style={{ color: 'var(--text-tertiary)' }}>
                            Terms
                        </Link>
                    </div>
                    <p style={{ color: 'var(--text-tertiary)' }}>
                        © 2026 Bharat Voyager. Made with ❤️ in India.
                    </p>
                </footer>
            </div>
            {showOnboarding && (
                <OnboardModal onComplete={() => setShowOnboarding(false)} />
            )}
        </div>
    );
}
