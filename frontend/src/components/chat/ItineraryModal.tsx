'use client';

import React, { useState } from 'react';
import { X, Share2, Download, Loader2, MapPin, Calendar, Users, Wallet, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface ItineraryModalProps {
    isOpen: boolean;
    onClose: () => void;
    itinerary: any;
    tripId: string;
}

export const ItineraryModal: React.FC<ItineraryModalProps> = ({
    isOpen,
    onClose,
    itinerary,
    tripId
}) => {
    const [isExporting, setIsExporting] = useState(false);

    if (!isOpen || !itinerary) return null;

    const handleDownload = async () => {
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

    const handleShare = () => {
        const shareUrl = `${window.location.origin}/shared/${tripId}`;
        navigator.clipboard.writeText(shareUrl);
        toast.success('Share link copied to clipboard!');
    };

    const { title, cities, start_date, num_days, num_travelers, budget_total, days } = itinerary;

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
                        </div>

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
                                        {day.activities && day.activities.map((activity: any, actIdx: number) => (
                                            <div key={actIdx} className="relative">
                                                {/* Dot on line */}
                                                <div
                                                    className="absolute -left-[31px] top-1.5 w-2 h-2 rounded-full border-2 border-white"
                                                    style={{ background: 'var(--accent)' }}
                                                />

                                                <div className="flex flex-col gap-1">
                                                    <div className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--accent)' }}>
                                                        <Clock className="w-3 h-3" />
                                                        <span>{activity.time}</span>
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
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
