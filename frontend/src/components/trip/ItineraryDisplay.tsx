'use client';

import { motion } from 'framer-motion';
import { MapPin, Clock, DollarSign, Sun, Utensils } from 'lucide-react';

interface ItineraryProps {
    itinerary: {
        title?: string;
        days: DayPlan[];
        total_estimated_budget?: number;
        highlights?: string[];
    };
}

interface DayPlan {
    day_number: number;
    city: string;
    theme?: string;
    stops: ActivityStop[];
    notes?: string;
}

interface ActivityStop {
    time?: string;
    name: string;
    description?: string;
    duration_minutes?: number;
    category?: string;
    estimated_cost?: number;
    tips?: string;
}

export function ItineraryDisplay({ itinerary }: ItineraryProps) {
    if (!itinerary?.days?.length) return null;

    return (
        <div className="space-y-6 p-4">
            {/* Header */}
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">
                    {itinerary.title || 'Your Adventure Awaits'}
                </h2>
                {itinerary.total_estimated_budget && (
                    <p className="text-purple-300">
                        Estimated Budget: ₹{itinerary.total_estimated_budget.toLocaleString()}
                    </p>
                )}
            </div>

            {/* Highlights */}
            {itinerary.highlights && itinerary.highlights.length > 0 && (
                <div className="bg-white/5 rounded-xl p-4 mb-6">
                    <h3 className="text-lg font-semibold text-white mb-3">✨ Highlights</h3>
                    <ul className="space-y-2">
                        {itinerary.highlights.map((h, i) => (
                            <li key={i} className="text-purple-200 flex items-start gap-2">
                                <span className="text-purple-400">•</span> {h}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Days */}
            {itinerary.days.map((day, dayIndex) => (
                <motion.div
                    key={day.day_number}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: dayIndex * 0.1 }}
                    className="bg-white/5 rounded-xl overflow-hidden border border-white/10"
                >
                    {/* Day Header */}
                    <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 px-4 py-3 border-b border-white/10">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-white">
                                    Day {day.day_number}
                                </h3>
                                <p className="text-purple-300 text-sm flex items-center gap-1">
                                    <MapPin className="w-4 h-4" />
                                    {day.city}
                                </p>
                            </div>
                            {day.theme && (
                                <span className="px-3 py-1 bg-purple-500/30 rounded-full text-purple-200 text-sm">
                                    {day.theme}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Activities */}
                    <div className="p-4 space-y-4">
                        {day.stops.map((activity, i) => (
                            <div key={i} className="flex gap-4">
                                {/* Time */}
                                <div className="w-16 flex-shrink-0 text-right">
                                    <span className="text-purple-400 text-sm font-medium">
                                        {activity.time || '—'}
                                    </span>
                                </div>

                                {/* Content */}
                                <div className="flex-1 bg-white/5 rounded-lg p-3">
                                    <div className="flex items-start justify-between mb-2">
                                        <h4 className="font-medium text-white">{activity.name}</h4>
                                        <CategoryIcon category={activity.category} />
                                    </div>

                                    {activity.description && (
                                        <p className="text-white/70 text-sm mb-2">
                                            {activity.description}
                                        </p>
                                    )}

                                    <div className="flex flex-wrap gap-3 text-xs text-white/50">
                                        {activity.duration_minutes && (
                                            <span className="flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {activity.duration_minutes} min
                                            </span>
                                        )}
                                        {activity.estimated_cost && (
                                            <span className="flex items-center gap-1">
                                                <DollarSign className="w-3 h-3" />
                                                ₹{activity.estimated_cost}
                                            </span>
                                        )}
                                    </div>

                                    {activity.tips && (
                                        <p className="mt-2 text-xs text-purple-300 italic">
                                            💡 {activity.tips}
                                        </p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Day Notes */}
                    {day.notes && (
                        <div className="px-4 pb-4">
                            <p className="text-white/60 text-sm italic">📝 {day.notes}</p>
                        </div>
                    )}
                </motion.div>
            ))}
        </div>
    );
}

function CategoryIcon({ category }: { category?: string }) {
    const className = "w-4 h-4 text-purple-400";

    switch (category?.toLowerCase()) {
        case 'food':
        case 'restaurant':
            return <Utensils className={className} />;
        case 'attraction':
        case 'sightseeing':
            return <MapPin className={className} />;
        case 'morning':
            return <Sun className={className} />;
        default:
            return null;
    }
}

export default ItineraryDisplay;
