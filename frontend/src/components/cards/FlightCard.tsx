/**
 * FlightCard Component
 * Displays flight information with airline, timings, pricing
 */
'use client';

import { Plane, Clock, IndianRupee, Users, Briefcase } from 'lucide-react';

export interface FlightDetails {
    airline: string;
    flightNumber: string;
    departure: {
        airport: string;
        city: string;
        time: string;
        date: string;
    };
    arrival: {
        airport: string;
        city: string;
        time: string;
        date: string;
    };
    duration: string;
    price: number;
    cabinClass: 'Economy' | 'Premium Economy' | 'Business' | 'First';
    stops: number;
    layover?: string;
}

interface FlightCardProps {
    flight: FlightDetails;
    onBook?: () => void;
}

export default function FlightCard({ flight, onBook }: FlightCardProps) {
    const getCabinIcon = (cabin: string) => {
        return cabin === 'Business' || cabin === 'First' ? <Briefcase className="w-4 h-4" /> : <Users className="w-4 h-4" />;
    };

    const getStopsText = (stops: number) => {
        if (stops === 0) return 'Non-stop';
        if (stops === 1) return '1 stop';
        return `${stops} stops`;
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-gray-700">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Plane className="w-5 h-5 text-white" />
                    <div>
                        <h3 className="text-white font-semibold">{flight.airline}</h3>
                        <p className="text-blue-100 text-sm">{flight.flightNumber}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 text-white">
                    {getCabinIcon(flight.cabinClass)}
                    <span className="text-sm">{flight.cabinClass}</span>
                </div>
            </div>

            {/* Flight Route */}
            <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                    {/* Departure */}
                    <div className="flex-1">
                        <p className="text-3xl font-bold text-gray-900 dark:text-white">{flight.departure.time}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{flight.departure.date}</p>
                        <p className="text-lg font-semibold text-gray-800 dark:text-gray-200 mt-2">{flight.departure.city}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{flight.departure.airport}</p>
                    </div>

                    {/* Duration & Stops */}
                    <div className="flex-1 px-6">
                        <div className="flex flex-col items-center">
                            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
                                <Clock className="w-4 h-4" />
                                <span className="text-sm">{flight.duration}</span>
                            </div>
                            <div className="w-full h-px bg-gray-300 dark:bg-gray-600 relative">
                                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                                    <Plane className="w-4 h-4 text-blue-500 rotate-90" />
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                {getStopsText(flight.stops)}
                            </p>
                            {flight.layover && (
                                <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                                    via {flight.layover}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Arrival */}
                    <div className="flex-1 text-right">
                        <p className="text-3xl font-bold text-gray-900 dark:text-white">{flight.arrival.time}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{flight.arrival.date}</p>
                        <p className="text-lg font-semibold text-gray-800 dark:text-gray-200 mt-2">{flight.arrival.city}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{flight.arrival.airport}</p>
                    </div>
                </div>

                {/* Price & Booking */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-baseline gap-1">
                        <IndianRupee className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                        <span className="text-2xl font-bold text-gray-900 dark:text-white">
                            {flight.price.toLocaleString('en-IN')}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">per person</span>
                    </div>

                    {onBook && (
                        <button
                            onClick={onBook}
                            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors duration-200 flex items-center gap-2"
                        >
                            Book Now
                            <Plane className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * FlightCardSkeleton - Loading state
 */
export function FlightCardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden border border-gray-100 dark:border-gray-700 animate-pulse">
            <div className="bg-gray-300 dark:bg-gray-700 h-16"></div>
            <div className="p-6 space-y-4">
                <div className="flex justify-between">
                    <div className="space-y-2">
                        <div className="h-8 w-20 bg-gray-300 dark:bg-gray-700 rounded"></div>
                        <div className="h-4 w-24 bg-gray-200 dark:bg-gray-600 rounded"></div>
                    </div>
                    <div className="h-8 w-8 bg-gray-300 dark:bg-gray-700 rounded-full"></div>
                    <div className="space-y-2">
                        <div className="h-8 w-20 bg-gray-300 dark:bg-gray-700 rounded"></div>
                        <div className="h-4 w-24 bg-gray-200 dark:bg-gray-600 rounded"></div>
                    </div>
                </div>
                <div className="h-px bg-gray-300 dark:bg-gray-600"></div>
                <div className="flex justify-between">
                    <div className="h-8 w-32 bg-gray-300 dark:bg-gray-700 rounded"></div>
                    <div className="h-10 w-28 bg-gray-300 dark:bg-gray-700 rounded-xl"></div>
                </div>
            </div>
        </div>
    );
}
