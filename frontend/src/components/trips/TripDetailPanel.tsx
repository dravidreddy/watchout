'use client';

import React, { useState } from 'react';
import {
    X, MapPin, Calendar, Users, Wallet, Clock, Share2, Download,
    MessageSquare, ChevronDown, ChevronUp, Utensils, Hotel, ArrowRight, Loader2, Crown
} from 'lucide-react';
import { api, Trip } from '@/lib/api';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';

interface TripDetailPanelProps {
    trip: Trip;
    onClose: () => void;
}

export function TripDetailPanel({ trip, onClose }: TripDetailPanelProps) {
    const router = useRouter();
    const { user } = useAuth();
    const [expandedDay, setExpandedDay] = useState<number | null>(0);
    const [isExporting, setIsExporting] = useState(false);
    const [isSharing, setIsSharing] = useState(false);

    const itinerary = (trip as any).itinerary;
    const canExport = user?.subscription_tier === 'adventure' || user?.subscription_tier === 'ultimate';

    const handleEditInChat = () => {
        router.push(`/chat?trip=${trip.trip_id || trip._id}`);
    };

    const handleShare = async () => {
        setIsSharing(true);
        try {
            const tripId = trip.trip_id || trip._id;
            const res = await api.updateTrip(tripId, { is_public: true });
            let shareId = res.sharing_id;
            if (!shareId) {
                const updated = await api.getTrip(tripId);
                shareId = updated.sharing_id;
            }
            if (!shareId) { toast.error('Failed to generate sharing link.'); return; }
            const url = `${window.location.origin}/shared/${shareId}`;
            await navigator.clipboard.writeText(url);
            toast.success('Share link copied!');
        } catch { toast.error('Failed to share trip'); }
        finally { setIsSharing(false); }
    };

    const handleDownload = async () => {
        if (!canExport) {
            toast.error('PDF Export is a premium feature. Upgrade your plan!');
            router.push('/plans');
            return;
        }
        setIsExporting(true);
        try {
            await api.downloadItineraryPdf(trip.trip_id || trip._id);
            toast.success('Itinerary PDF downloaded!');
        } catch { toast.error('Failed to generate PDF'); }
        finally { setIsExporting(false); }
    };

    const days = itinerary?.days || [];
    const cities = itinerary?.cities || (trip.city ? [trip.city] : []);
    const numDays = itinerary?.num_days || trip.duration_days;
    const numTravelers = itinerary?.num_travelers || trip.num_travelers || 1;
    const budgetTotal = itinerary?.budget_total;

    return (
        <div className="flex flex-col h-full overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
            {/* Header */}
            <div
                className="flex-shrink-0 px-5 py-4 border-b flex items-start justify-between gap-3"
                style={{ background: 'var(--bg-secondary)', borderColor: 'rgba(0,0,0,0.07)' }}
            >
                <div className="min-w-0">
                    <h2 className="font-bold text-lg leading-tight truncate" style={{ color: 'var(--text-primary)' }}>
                        {trip.title || 'Trip Itinerary'}
                    </h2>
                    <div className="flex flex-wrap items-center gap-3 mt-1.5">
                        {cities.length > 0 && (
                            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                                <MapPin className="w-3 h-3 text-accent" />
                                {cities.join(' → ')}
                            </span>
                        )}
                        {numDays && (
                            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                                <Calendar className="w-3 h-3 text-accent" />
                                {numDays} Days
                            </span>
                        )}
                        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                            <Users className="w-3 h-3 text-accent" />
                            {numTravelers} Traveler{numTravelers !== 1 ? 's' : ''}
                        </span>
                        {budgetTotal && (
                            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                                <Wallet className="w-3 h-3 text-accent" />
                                ₹{budgetTotal.toLocaleString()}
                            </span>
                        )}
                    </div>
                </div>
                <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg flex-shrink-0 hover:bg-black/5 transition-colors"
                    style={{ color: 'var(--text-secondary)' }}
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Action Bar */}
            <div
                className="flex-shrink-0 flex items-center gap-2 px-5 py-3 border-b"
                style={{ borderColor: 'rgba(0,0,0,0.05)' }}
            >
                <button
                    onClick={handleEditInChat}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90"
                    style={{ background: 'var(--accent)' }}
                >
                    <MessageSquare className="w-4 h-4" />
                    Edit in Chat
                </button>
                <button
                    onClick={handleShare}
                    disabled={isSharing}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium border transition-all hover:bg-black/5"
                    style={{ borderColor: 'rgba(0,0,0,0.1)', color: 'var(--text-secondary)' }}
                >
                    <Share2 className="w-4 h-4" />
                    Share
                </button>
                <button
                    onClick={handleDownload}
                    disabled={isExporting}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium border transition-all hover:bg-black/5 ml-auto"
                    style={{ borderColor: 'rgba(0,0,0,0.1)', color: 'var(--text-secondary)' }}
                >
                    {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    PDF
                    {!canExport && <Crown className="w-3 h-3 ml-0.5 text-yellow-400" />}
                </button>
            </div>

            {/* Day-by-Day Itinerary */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
                {days.length === 0 && !itinerary ? (
                    <div className="text-center py-12">
                        <MessageSquare
                            className="w-10 h-10 mx-auto mb-3"
                            style={{ color: 'var(--text-tertiary)' }}
                        />
                        <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                            No itinerary generated yet
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
                            Open in Chat to continue planning
                        </p>
                        <button
                            onClick={handleEditInChat}
                            className="mt-4 px-4 py-2 rounded-xl text-sm font-semibold text-white"
                            style={{ background: 'var(--accent)' }}
                        >
                            Open in Chat
                        </button>
                    </div>
                ) : (
                    days.map((day: any, idx: number) => {
                        const isOpen = expandedDay === idx;
                        return (
                            <div
                                key={idx}
                                className="rounded-xl overflow-hidden border"
                                style={{ borderColor: 'rgba(0,0,0,0.07)' }}
                            >
                                {/* Day Header */}
                                <button
                                    onClick={() => setExpandedDay(isOpen ? null : idx)}
                                    className="w-full flex items-center justify-between px-4 py-3 text-left transition-colors hover:bg-black/5"
                                    style={{ background: 'var(--bg-secondary)' }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                                            style={{ background: 'var(--accent)' }}
                                        >
                                            {day.day_number ?? idx + 1}
                                        </div>
                                        <div className="text-left">
                                            <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                                                {day.city || day.theme || `Day ${idx + 1}`}
                                            </div>
                                            {day.stops?.length > 0 && (
                                                <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                                    {day.stops.length} stops
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    {isOpen
                                        ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
                                        : <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
                                    }
                                </button>

                                {/* Day Content */}
                                {isOpen && (
                                    <div className="px-4 pb-4 pt-2 space-y-3" style={{ background: 'var(--bg-primary)' }}>
                                        {/* Stops timeline */}
                                        {(day.stops || []).map((stop: any, sIdx: number) => (
                                            <div key={sIdx} className="flex gap-3">
                                                <div className="flex flex-col items-center">
                                                    <div
                                                        className="w-2 h-2 rounded-full flex-shrink-0 mt-1.5"
                                                        style={{ background: 'var(--accent)' }}
                                                    />
                                                    {sIdx < (day.stops.length - 1) && (
                                                        <div className="w-px flex-1 mt-1" style={{ background: 'var(--accent-50)' }} />
                                                    )}
                                                </div>
                                                <div className="pb-3">
                                                    {stop.time && (
                                                        <div className="flex items-center gap-1 text-xs font-medium mb-0.5" style={{ color: 'var(--accent)' }}>
                                                            <Clock className="w-3 h-3" />
                                                            {stop.time}
                                                        </div>
                                                    )}
                                                    <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                                                        {stop.name}
                                                    </div>
                                                    {stop.description && (
                                                        <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                                                            {stop.description}
                                                        </p>
                                                    )}
                                                    {stop.estimated_cost && (
                                                        <span className="inline-flex items-center gap-1 mt-1 text-xs px-1.5 py-0.5 rounded" style={{ background: 'var(--accent-50)', color: 'var(--accent)' }}>
                                                            ₹{stop.estimated_cost}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}

                                        {/* Stay */}
                                        {day.stay && (
                                            <div className="flex items-start gap-2 p-3 rounded-lg border mt-2" style={{ borderColor: 'rgba(0,0,0,0.05)', background: 'var(--bg-secondary)' }}>
                                                <Hotel className="w-4 h-4 mt-0.5 flex-shrink-0 text-blue-500" />
                                                <div>
                                                    <div className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>Where to Stay</div>
                                                    <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                                                        {typeof day.stay === 'string' ? day.stay : day.stay?.name || JSON.stringify(day.stay)}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Food spots */}
                                        {day.food_spots?.length > 0 && (
                                            <div className="flex items-start gap-2 p-3 rounded-lg border mt-2" style={{ borderColor: 'rgba(0,0,0,0.05)', background: 'var(--bg-secondary)' }}>
                                                <Utensils className="w-4 h-4 mt-0.5 flex-shrink-0 text-orange-500" />
                                                <div>
                                                    <div className="text-xs font-semibold mb-1" style={{ color: 'var(--text-secondary)' }}>Local Food</div>
                                                    {day.food_spots.slice(0, 3).map((f: any, fi: number) => (
                                                        <div key={fi} className="text-sm" style={{ color: 'var(--text-primary)' }}>
                                                            {typeof f === 'string' ? f : f?.name || ''}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
