import React, { useState } from 'react';
import { MapPin, Calendar, Users, Wallet, Clock, Download, Share2, Loader2, Crown } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter } from 'next/navigation';
import { normalizeItinerary } from '@/lib/itinerary';

interface ItineraryPreviewProps {
    itinerary: any;
    isSaving?: boolean;
    onSave?: () => void;
    tripId?: string;
}

export const ItineraryPreview: React.FC<ItineraryPreviewProps> = ({
    itinerary,
    tripId
}) => {
    // ...
    const [isExporting, setIsExporting] = useState(false);
    const { user } = useAuth();
    const router = useRouter();
    const normalizedItinerary = normalizeItinerary(itinerary);

    const canExport = user?.subscription_tier === 'adventure' || user?.subscription_tier === 'ultimate';

    const handleDownload = async () => {
        if (!tripId) {
            toast.error('Please save your trip first to export it as PDF');
            return;
        }
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
        if (!tripId) {
            toast.error('Please save your trip first to share it');
            return;
        }

        try {
            const res = await api.updateTrip(tripId, { is_public: true });
            let shareId = res.sharing_id || (normalizedItinerary as any)?.sharing_id;

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
    if (!normalizedItinerary) {
        return (
            <div className="flex-1 flex items-center justify-center p-8 h-full">
                <div className="text-center max-w-sm">
                    <div
                        className="w-20 h-20 rounded-2xl mx-auto mb-6 flex items-center justify-center"
                        style={{ background: 'var(--accent-50)' }}
                    >
                        <MapPin className="w-10 h-10" style={{ color: 'var(--accent)' }} />
                    </div>
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                        Start Planning
                    </h3>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Tell me where you'd like to go and I'll create a detailed day-by-day itinerary for you.
                    </p>
                </div>
            </div>
        );
    }

    const { title, cities, num_days, num_travelers, budget_total, days } = normalizedItinerary;

    return (
        <div className="flex flex-col h-full overflow-hidden">
            {/* Summary Header */}
            <div className="p-6 bg-white border-b" style={{ borderColor: 'rgba(0,0,0,0.05)' }}>
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
                        {title || 'Your Trip Plan'}
                    </h3>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleShare}
                            className="p-2 rounded-lg hover:bg-black/5 transition-colors"
                            title="Share Trip"
                        >
                            <Share2 className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                        </button>
                        <button
                            onClick={handleDownload}
                            disabled={isExporting}
                            className="p-2 rounded-lg hover:bg-black/5 transition-colors flex items-center gap-1"
                            title="Export to PDF"
                        >
                            {isExporting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />}
                            {!canExport && <Crown className="w-3.5 h-3.5 text-yellow-500" />}
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <MapPin className="w-4 h-4 text-accent" />
                        <span className="truncate">{cities?.join(', ') || 'Picking destinations...'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <Calendar className="w-4 h-4 text-accent" />
                        <span>{num_days ? `${num_days} Days` : 'Duration TBD'}</span>
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
            </div>

            {/* Day by Day Plan */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
                {days && days.map((day: any, idx: number) => (
                    <div
                        key={day.day_number || idx}
                        className="stagger-item"
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <div
                                className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm text-white"
                                style={{ background: 'var(--accent)' }}
                            >
                                {day.day_number}
                            </div>
                            <h4 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>
                                {day.city || 'Destination'}
                            </h4>
                        </div>

                        <div className="space-y-4 ml-4 border-l-2 pl-6 pb-2" style={{ borderColor: 'var(--accent-50)' }}>
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
                                            <p className="text-sm line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                                                {activity.description}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {(!day.stops || day.stops.length === 0) && (
                                <p className="text-sm italic" style={{ color: 'var(--text-tertiary)' }}>
                                    No activities planned yet...
                                </p>
                            )}
                        </div>
                    </div>
                ))}

                {(!days || days.length === 0) && (
                    <div className="py-20 text-center">
                        <p style={{ color: 'var(--text-tertiary)' }}>
                            Day-by-day activities will appear here as we refine your trip.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};
