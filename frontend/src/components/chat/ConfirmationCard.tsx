'use client';

import React from 'react';
import { MapPin, Calendar, Users, DollarSign, Smile, Utensils, Heart, CheckCircle2, Edit2 } from 'lucide-react';
import { MOODS } from '@/components/home/MoodSelector';

interface ConfirmationCardProps {
    data: Record<string, any>;
    onConfirm: () => void;
    onEdit: () => void;
}

const fieldConfig: { key: string; label: string; icon: React.ReactNode; format?: (v: any) => string }[] = [
    {
        key: 'destinations_or_region',
        label: 'Destination',
        icon: <MapPin className="w-4 h-4" style={{ color: 'var(--accent)' }} />,
    },
    {
        key: 'origin_city',
        label: 'Flying From',
        icon: <MapPin className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />,
    },
    {
        key: 'duration_days',
        label: 'Duration',
        icon: <Calendar className="w-4 h-4" style={{ color: 'var(--accent)' }} />,
        format: (v) => `${v} days`,
    },
    {
        key: 'num_travelers',
        label: 'Travelers',
        icon: <Users className="w-4 h-4" style={{ color: 'var(--accent)' }} />,
        format: (v) => `${v} ${Number(v) === 1 ? 'person' : 'people'}`,
    },
    {
        key: 'budget_range',
        label: 'Budget',
        icon: <DollarSign className="w-4 h-4" style={{ color: '#3FB950' }} />,
    },
    {
        key: 'travel_vibe',
        label: 'Vibe',
        icon: <Heart className="w-4 h-4" style={{ color: '#F85149' }} />,
        format: (v) => Array.isArray(v) ? v.join(', ') : String(v),
    },
    {
        key: 'current_mood',
        label: 'Mood',
        icon: <Smile className="w-4 h-4" style={{ color: 'var(--accent)' }} />,
        format: (v) => {
            const mood = MOODS.find(m => m.id === v);
            return mood ? `${mood.emoji} ${mood.label}` : String(v);
        },
    },
    {
        key: 'food_preferences',
        label: 'Food',
        icon: <Utensils className="w-4 h-4" style={{ color: 'var(--warning)' }} />,
        format: (v) => Array.isArray(v) ? v.join(', ') : String(v),
    },
    {
        key: 'travel_style',
        label: 'Style',
        icon: <Heart className="w-4 h-4" style={{ color: 'var(--accent)' }} />,
    },
    {
        key: 'interests',
        label: 'Interests',
        icon: <Heart className="w-4 h-4" style={{ color: 'var(--accent)' }} />,
        format: (v) => Array.isArray(v) ? v.join(', ') : String(v),
    },
];

export function ConfirmationCard({ data, onConfirm, onEdit }: ConfirmationCardProps) {
    const relevantFields = fieldConfig.filter(f => data[f.key] != null && data[f.key] !== '');

    return (
        <div className="confirm-card my-2 animate-slide-in-up" style={{ maxWidth: 460 }}>
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                    Here's what I've gathered — does everything look right?
                </span>
            </div>

            {/* Field rows */}
            <div className="mb-4">
                {relevantFields.length === 0 && (
                    <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                        No preferences captured yet.
                    </p>
                )}
                {relevantFields.map((field) => {
                    const raw = data[field.key];
                    const display = field.format ? field.format(raw) : String(raw);
                    return (
                        <div key={field.key} className="confirm-row">
                            <span className="flex items-center gap-1.5 confirm-label">
                                {field.icon} {field.label}
                            </span>
                            <span className="confirm-value">{display}</span>
                        </div>
                    );
                })}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 mt-2">
                <button
                    onClick={onConfirm}
                    className="btn btn-primary flex-1 text-sm py-2"
                >
                    ✅ Confirm & Generate
                </button>
                <button
                    onClick={onEdit}
                    className="btn btn-secondary text-sm py-2 px-4 flex items-center gap-1.5"
                >
                    <Edit2 className="w-3.5 h-3.5" />
                    Edit
                </button>
            </div>
        </div>
    );
}
