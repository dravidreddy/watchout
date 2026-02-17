/**
 * ActivityCard Component
 * Displays activities, attractions, and experiences with pricing and duration
 */
'use client';

import { Ticket, Clock, Users, IndianRupee, MapPin, Star, Calendar } from 'lucide-react';

export interface ActivityDetails {
    name: string;
    description: string;
    location: string;
    duration: string;
    price: number;
    priceType: 'per person' | 'per group' | 'free';
    category: 'Sightseeing' | 'Adventure' | 'Cultural' | 'Food' | 'Shopping' | 'Nature';
    rating?: number;
    reviews?: number;
    groupSize?: {
        min: number;
        max: number;
    };
    bestTime?: string;
    included?: string[];
    images?: string[];
}

interface ActivityCardProps {
    activity: ActivityDetails;
    onBook?: () => void;
}

export default function ActivityCard({ activity, onBook }: ActivityCardProps) {
    const getCategoryColor = (category: string) => {
        switch (category) {
            case 'Adventure':
                return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
            case 'Cultural':
                return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
            case 'Nature':
                return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            case 'Food':
                return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            case 'Shopping':
                return 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200';
            default:
                return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
        }
    };

    const getCategoryIcon = (category: string) => {
        // Return appropriate emoji or icon
        const icons: Record<string, string> = {
            Sightseeing: '🏛️',
            Adventure: '🏔️',
            Cultural: '🎭',
            Food: '🍽️',
            Shopping: '🛍️',
            Nature: '🌿',
        };
        return icons[category] || '🎫';
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-gray-700">
            {/* Image Section */}
            <div className="relative h-40 bg-gradient-to-br from-indigo-400 to-cyan-500">
                {activity.images && activity.images.length > 0 ? (
                    <img
                        src={activity.images[0]}
                        alt={activity.name}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-6xl">
                        {getCategoryIcon(activity.category)}
                    </div>
                )}

                {/* Category Badge */}
                <div className="absolute top-3 right-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getCategoryColor(activity.category)}`}>
                        {activity.category}
                    </span>
                </div>

                {/* Best Time Badge */}
                {activity.bestTime && (
                    <div className="absolute bottom-3 left-3">
                        <div className="flex items-center gap-1 bg-white/90 dark:bg-gray-900/90 px-2 py-1 rounded-lg text-xs">
                            <Calendar className="w-3 h-3" />
                            <span className="font-medium">{activity.bestTime}</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="p-5">
                {/* Activity Name & Rating */}
                <div className="mb-3">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-2">
                        {activity.name}
                    </h3>

                    {activity.rating && (
                        <div className="flex items-center gap-2 mb-2">
                            <div className="flex items-center gap-1">
                                <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    {activity.rating.toFixed(1)}
                                </span>
                            </div>
                            {activity.reviews && (
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                    ({activity.reviews} reviews)
                                </span>
                            )}
                        </div>
                    )}

                    <div className="flex items-start gap-2 text-gray-600 dark:text-gray-400 mb-2">
                        <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <p className="text-sm">{activity.location}</p>
                    </div>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-4">
                    {activity.description}
                </p>

                {/* Details Grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-blue-500" />
                        <span className="text-gray-700 dark:text-gray-300">{activity.duration}</span>
                    </div>
                    {activity.groupSize && (
                        <div className="flex items-center gap-2 text-sm">
                            <Users className="w-4 h-4 text-green-500" />
                            <span className="text-gray-700 dark:text-gray-300">
                                {activity.groupSize.min}-{activity.groupSize.max} people
                            </span>
                        </div>
                    )}
                </div>

                {/* Included Items */}
                {activity.included && activity.included.length > 0 && (
                    <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Included:</p>
                        <ul className="space-y-1">
                            {activity.included.slice(0, 3).map((item, index) => (
                                <li key={index} className="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-2">
                                    <span className="text-green-500">✓</span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                        {activity.included.length > 3 && (
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                                +{activity.included.length - 3} more
                            </p>
                        )}
                    </div>
                )}

                {/* Pricing & Booking */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                        <div>
                            {activity.priceType === 'free' ? (
                                <span className="text-2xl font-bold text-green-600 dark:text-green-400">FREE</span>
                            ) : (
                                <div className="flex items-baseline gap-1">
                                    <IndianRupee className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                                    <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                        {activity.price.toLocaleString('en-IN')}
                                    </span>
                                    <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                                        {activity.priceType}
                                    </span>
                                </div>
                            )}
                        </div>

                        {onBook && (
                            <button
                                onClick={onBook}
                                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors duration-200 flex items-center gap-2 text-sm"
                            >
                                Book Now
                                <Ticket className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

/**
 * ActivityCardSkeleton - Loading state
 */
export function ActivityCardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden border border-gray-100 dark:border-gray-700 animate-pulse">
            <div className="h-40 bg-gray-300 dark:bg-gray-700"></div>
            <div className="p-5 space-y-4">
                <div className="h-5 w-3/4 bg-gray-300 dark:bg-gray-700 rounded"></div>
                <div className="h-4 w-1/2 bg-gray-200 dark:bg-gray-600 rounded"></div>
                <div className="space-y-2">
                    <div className="h-3 w-full bg-gray-200 dark:bg-gray-600 rounded"></div>
                    <div className="h-3 w-5/6 bg-gray-200 dark:bg-gray-600 rounded"></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded"></div>
                </div>
                <div className="h-px bg-gray-300 dark:bg-gray-600"></div>
                <div className="flex justify-between items-center">
                    <div className="h-8 w-24 bg-gray-300 dark:bg-gray-700 rounded"></div>
                    <div className="h-10 w-28 bg-gray-300 dark:bg-gray-700 rounded-xl"></div>
                </div>
            </div>
        </div>
    );
}
