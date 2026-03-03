'use client';

import React, { useState } from 'react';
import { X, Share2, Download, Loader2, MapPin, Calendar, Users, Wallet, Clock, Crown } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter } from 'next/navigation';
import { normalizeItinerary } from '@/lib/itinerary';

interface ItineraryModalProps {
    isOpen: boolean;
    onClose: () => void;
    itinerary: any;
    weatherData?: any;
    tripId: string;
}

export const ItineraryModal: React.FC<ItineraryModalProps> = ({
    isOpen,
    onClose,
    itinerary,
    weatherData,
    tripId
}) => {
    const [isExporting, setIsExporting] = useState(false);
    const { user } = useAuth();
    const router = useRouter();
    const normalizedItinerary = normalizeItinerary(itinerary);

    if (!isOpen || !normalizedItinerary) return null;

    const canExport = user?.subscription_tier === 'adventure' || user?.subscription_tier === 'ultimate';

    const handleDownload = async () => {
        if (!canExport) {
            toast.error('PDF Export is a premium feature. Redirecting ...');
            setTimeout(() => router.push('/plans'), 2000);
            return;
        }

        setIsExporting(true);
        try {
            await api.downloadItineraryPdf(tripId);
            toast.success('Itinerary PDF downloaded!');
        } catch (error) {
            toast.error('Failed to generate PDF');
        } finally {
            setIsExporting(false);
        }
    };

    const handleShare = async () => {
        try {
            const res = await api.updateTrip(tripId, { is_public: true });
            let shareId = res.sharing_id || (normalizedItinerary as any).sharing_id;

            if (!shareId) {
                const updated = await api.getTrip(tripId);
                shareId = updated.sharing_id;
            }

            if (!shareId) {
                toast.error('Failed to generate sharing link.');
                return;
            }

            const shareUrl = `${window.location.origin}/shared/${shareId}`;
            navigator.clipboard.writeText(shareUrl);
            toast.success('Share link copied to clipboard!');
        } catch (e) {
            toast.error('Failed to share trip');
        }
    };

    const { title, cities, num_days, num_travelers, budget_total, days } = normalizedItinerary;
    const dayBudgets = (days || []).map((day: any) =>
        (day.stops || []).reduce((sum: number, stop: any) => sum + (Number(stop.estimated_cost) || 0), 0)
    );
    const hasPerDayBudget = dayBudgets.some((n: number) => n > 0);

    // Helper functions for weather
    const getWeatherIcon = (description: string) => {
        const desc = description.toLowerCase();
        if (desc.includes('rain') || desc.includes('shower')) return '🌧️';
        if (desc.includes('cloud')) return '☁️';
        if (desc.includes('clear') || desc.includes('sun')) return '☀️';
        if (desc.includes('snow')) return '❄️';
        if (desc.includes('thunder')) return '⛈️';
        return '⛅';
    };

    return (
        <div
            className="fixed inset-0 z-50 overflow-auto"
            style={{ background: 'rgba(0, 0, 0, 0.5)' }}
            onClick={onClose}
        >
            <div className="min-h-screen px-4 py-8 flex items-center justify-center">
                <div
                    className="relative w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden"
                    style={{ background: 'var(--bg-primary)' }}
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div
                        className="flex items-center justify-between px-6 py-4 border-b"
                        style={{
                            background: 'var(--bg-secondary)',
                            borderColor: 'rgba(0,0,0,0.05)'
                        }}
                    >
                        <div>
                            <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                                {title || 'Your Trip Plan'}
                            </h2>
                            <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                                Trip saved successfully!
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-black/5 transition-colors"
                        >
                            <X className="w-6 h-6" style={{ color: 'var(--text-secondary)' }} />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="max-h-[70vh] overflow-y-auto">
                        {/* Summary */}
                        <div className="p-6 border-b" style={{ borderColor: 'rgba(0,0,0,0.05)' }}>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    <MapPin className="w-4 h-4 text-accent" />
                                    <span className="truncate">{cities?.join(', ') || 'Destination'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    <Calendar className="w-4 h-4 text-accent" />
                                    <span>{num_days ? `${num_days} Days` : 'Duration'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    <Users className="w-4 h-4 text-accent" />
                                    <span>{num_travelers || 1} Travelers</span>
                                </div>
                                {budget_total && (
                                    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                                        <Wallet className="w-4 h-4 text-accent" />
                                        <span>₹{budget_total.toLocaleString()}</span>
                                    </div>
                                )}
                            </div>
                            {hasPerDayBudget && (
                                <div className="mt-4 rounded-xl p-3 text-sm" style={{ background: 'var(--bg-tertiary)' }}>
                                    <div className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Budget Breakdown</div>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                        {dayBudgets.map((value: number, index: number) => (
                                            <div key={`budget-${index}`} style={{ color: 'var(--text-secondary)' }}>
                                                Day {index + 1}: <span style={{ color: 'var(--text-primary)' }}>{`INR ${value.toLocaleString()}`}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Weather Summary (if available) */}
                        {weatherData && weatherData.weather && weatherData.weather.length > 0 && (
                            <div className="p-6 border-b" style={{ borderColor: 'rgba(0,0,0,0.05)', backgroundColor: 'var(--bg-tertiary)' }}>
                                <h3 className="font-semibold text-sm uppercase tracking-wide mb-3" style={{ color: 'var(--text-tertiary)' }}>
                                    Weather Forecast
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {weatherData.weather.map((w: any, i: number) => {
                                        // Pick the first day forecast
                                        const forecast = w.forecast.daily?.[0];
                                        return (
                                            <div key={i} className="flex items-center gap-3 bg-white dark:bg-slate-800 p-3 rounded-xl shadow-sm border border-black/5 dark:border-white/5">
                                                <div className="text-3xl">
                                                    {getWeatherIcon(forecast?.description || 'clear')}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                                                        {w.city}
                                                    </div>
                                                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                                                        {forecast?.description || 'Clear skies'} • {w.forecast.current?.temp_c ? `${w.forecast.current.temp_c}°C` : ''}
                                                    </div>
                                                </div>
                                                <div className="text-right text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                                    <div>H: {forecast?.max_temp_c}°C</div>
                                                    <div>L: {forecast?.min_temp_c}°C</div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                                {weatherData.alerts && weatherData.alerts.length > 0 && (
                                    <div className="mt-3 p-3 rounded-lg text-sm bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 border border-red-100 dark:border-red-800/30 flex items-start gap-2">
                                        <span>⚠️</span>
                                        <div>
                                            <div className="font-semibold">Weather Alert</div>
                                            <div>{weatherData.alerts[0].headline}</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Day by Day Plan */}
                        <div className="p-6 space-y-6">
                            {days && days.map((day: any, idx: number) => (
                                <div key={day.day_number || idx}>
                                    <div className="flex items-center gap-3 mb-4">
                                        <div
                                            className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white"
                                            style={{ background: 'var(--accent)' }}
                                        >
                                            {day.day_number}
                                        </div>
                                        <h4 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>
                                            {day.city || 'Destination'}
                                        </h4>
                                    </div>

                                    <div className="space-y-3 ml-4 border-l-2 pl-6" style={{ borderColor: 'var(--accent-50)' }}>
                                        {day.stops && day.stops.map((activity: any, actIdx: number) => (
                                            <div key={actIdx} className="relative">
                                                {/* Dot on line */}
                                                <div
                                                    className="absolute -left-[31px] top-1.5 w-2 h-2 rounded-full border-2 border-white"
                                                    style={{ background: 'var(--accent)' }}
                                                />

                                                <div className="flex flex-col gap-1">
                                                    <div className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--accent)' }}>
                                                        <Clock className="w-3 h-3" />
                                                        <span>{activity.time || 'Flexible timing'}</span>
                                                    </div>
                                                    <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                                                        {activity.name}
                                                    </div>
                                                    {activity.description && (
                                                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                                            {activity.description}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div
                        className="flex items-center justify-end gap-3 px-6 py-4 border-t"
                        style={{
                            background: 'var(--bg-secondary)',
                            borderColor: 'rgba(0,0,0,0.05)'
                        }}
                    >
                        <button
                            onClick={handleShare}
                            className="btn btn-secondary flex items-center gap-2"
                        >
                            <Share2 className="w-4 h-4" />
                            Share
                        </button>
                        <button
                            onClick={handleDownload}
                            disabled={isExporting}
                            className="btn btn-primary flex items-center gap-2"
                        >
                            {isExporting ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Download className="w-4 h-4" />
                            )}
                            Download
                            {!canExport && <Crown className="w-3.5 h-3.5 ml-1 text-yellow-300" />}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
