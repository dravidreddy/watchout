'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api, Trip } from '@/lib/api';
import { ItineraryPreview } from '@/components/chat/ItineraryPreview';
import { Compass, Share2 } from 'lucide-react';
import Link from 'next/link';

export default function SharedTripPage() {
    const params = useParams();
    const sharingId = params.sharingId as string;
    const [trip, setTrip] = useState<Trip | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSharedTrip = async () => {
            if (!sharingId) return;
            try {
                const data = await api.getSharedTrip(sharingId);
                setTrip(data);
            } catch (err) {
                console.error('Failed to fetch shared trip:', err);
                setError('This trip might be private or no longer exists.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchSharedTrip();
    }, [sharingId]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" style={{ borderColor: 'var(--accent)' }} />
            </div>
        );
    }

    if (error || !trip) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50 text-center">
                <Compass className="w-16 h-16 text-gray-300 mb-6" />
                <h1 className="text-2xl font-bold mb-2">Trip Not Found</h1>
                <p className="text-gray-600 mb-8 max-w-sm">{error}</p>
                <Link href="/">
                    <button className="btn btn-primary">Go Home</button>
                </Link>
            </div>
        );
    }

    // Prepare data for ItineraryPreview
    const itineraryData = trip.itinerary ? {
        title: trip.title,
        cities: trip.cities,
        start_date: trip.start_date,
        num_days: trip.num_days,
        num_travelers: trip.num_travelers,
        budget_total: trip.budget_total,
        days: trip.itinerary.days
    } : {
        title: trip.title,
        cities: trip.cities,
        start_date: trip.start_date,
        num_days: trip.num_days,
        num_travelers: trip.num_travelers,
        budget_total: trip.budget_total,
        days: []
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Minimal Header */}
            <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-white text-xs font-bold" style={{ background: 'var(--accent)' }}>
                        B
                    </div>
                    <span className="font-semibold text-sm">Shared Itinerary</span>
                </div>
                <Link href="/">
                    <button className="text-xs font-medium hover:underline flex items-center gap-1" style={{ color: 'var(--accent)' }}>
                        Plan a similar trip <Share2 className="w-3 h-3" />
                    </button>
                </Link>
            </header>

            <main className="max-w-4xl mx-auto md:py-8">
                <div className="bg-white md:rounded-2xl shadow-sm border overflow-hidden">
                    <ItineraryPreview itinerary={itineraryData} />
                </div>

                {/* CTA for viewers */}
                <div className="mt-8 p-8 text-center">
                    <h3 className="text-xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Want to plan your own trip?</h3>
                    <p className="text-gray-600 mb-6" style={{ color: 'var(--text-secondary)' }}>Bharat Voyager uses AI to build perfectly customized itineraries in seconds.</p>
                    <Link href="/">
                        <button className="btn btn-primary px-8">Get Started</button>
                    </Link>
                </div>
            </main>
        </div>
    );
}
