/**
 * HotelCard Component
 * Displays hotel information with amenities, ratings, pricing
 */
'use client';

import { Hotel, Star, MapPin, Wifi, Coffee, Car, Utensils, IndianRupee, Check } from 'lucide-react';

export interface HotelDetails {
    name: string;
    address: string;
    city: string;
    rating: number;
    reviews: number;
    pricePerNight: number;
    totalPrice: number;
    nights: number;
    roomType: string;
    amenities: string[];
    images?: string[];
    category: '3-Star' | '4-Star' | '5-Star' | 'Budget' | 'Luxury';
}

interface HotelCardProps {
    hotel: HotelDetails;
    onBook?: () => void;
}

export default function HotelCard({ hotel, onBook }: HotelCardProps) {
    const getAmenityIcon = (amenity: string) => {
        const lowerAmenity = amenity.toLowerCase();
        if (lowerAmenity.includes('wifi')) return <Wifi className="w-4 h-4" />;
        if (lowerAmenity.includes('breakfast')) return <Coffee className="w-4 h-4" />;
        if (lowerAmenity.includes('parking')) return <Car className="w-4 h-4" />;
        if (lowerAmenity.includes('restaurant')) return <Utensils className="w-4 h-4" />;
        return <Check className="w-4 h-4" />;
    };

    const getCategoryColor = (category: string) => {
        switch (category) {
            case 'Luxury':
            case '5-Star':
                return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
            case '4-Star':
                return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
            case '3-Star':
                return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            default:
                return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
        }
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-gray-700">
            {/* Image Section */}
            <div className="relative h-48 bg-gradient-to-br from-blue-400 to-purple-500">
                {hotel.images && hotel.images.length > 0 ? (
                    <img
                        src={hotel.images[0]}
                        alt={hotel.name}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <Hotel className="w-16 h-16 text-white opacity-50" />
                    </div>
                )}

                {/* Category Badge */}
                <div className="absolute top-4 right-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getCategoryColor(hotel.category)}`}>
                        {hotel.category}
                    </span>
                </div>
            </div>

            {/* Content */}
            <div className="p-6">
                {/* Hotel Name & Rating */}
                <div className="mb-4">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{hotel.name}</h3>

                    <div className="flex items-center gap-4 mb-2">
                        <div className="flex items-center gap-1">
                            {[...Array(5)].map((_, i) => (
                                <Star
                                    key={i}
                                    className={`w-4 h-4 ${i < Math.floor(hotel.rating)
                                        ? 'text-yellow-400 fill-yellow-400'
                                        : 'text-gray-300 dark:text-gray-600'
                                        }`}
                                />
                            ))}
                            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 ml-1">
                                {hotel.rating.toFixed(1)}
                            </span>
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                            ({hotel.reviews.toLocaleString()} reviews)
                        </span>
                    </div>

                    <div className="flex items-start gap-2 text-gray-600 dark:text-gray-400">
                        <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <p className="text-sm">{hotel.address}, {hotel.city}</p>
                    </div>
                </div>

                {/* Room Type */}
                <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                        {hotel.roomType}
                    </p>
                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                        {hotel.nights} night{hotel.nights > 1 ? 's' : ''}
                    </p>
                </div>

                {/* Amenities */}
                <div className="mb-4">
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Amenities</p>
                    <div className="grid grid-cols-2 gap-2">
                        {hotel.amenities.slice(0, 6).map((amenity, index) => (
                            <div key={index} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                {getAmenityIcon(amenity)}
                                <span className="truncate">{amenity}</span>
                            </div>
                        ))}
                    </div>
                    {hotel.amenities.length > 6 && (
                        <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                            +{hotel.amenities.length - 6} more amenities
                        </p>
                    )}
                </div>

                {/* Pricing */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-end justify-between mb-3">
                        <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Price per night</p>
                            <div className="flex items-baseline gap-1">
                                <IndianRupee className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                                <span className="text-lg font-semibold text-gray-900 dark:text-white">
                                    {hotel.pricePerNight.toLocaleString('en-IN')}
                                </span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Total ({hotel.nights} nights)</p>
                            <div className="flex items-baseline gap-1 justify-end">
                                <IndianRupee className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {hotel.totalPrice.toLocaleString('en-IN')}
                                </span>
                            </div>
                        </div>
                    </div>

                    {onBook && (
                        <button
                            onClick={onBook}
                            className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
                        >
                            Book Hotel
                            <Hotel className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * HotelCardSkeleton - Loading state
 */
export function HotelCardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden border border-gray-100 dark:border-gray-700 animate-pulse">
            <div className="h-48 bg-gray-300 dark:bg-gray-700"></div>
            <div className="p-6 space-y-4">
                <div className="h-6 w-3/4 bg-gray-300 dark:bg-gray-700 rounded"></div>
                <div className="h-4 w-1/2 bg-gray-200 dark:bg-gray-600 rounded"></div>
                <div className="space-y-2">
                    <div className="h-4 w-full bg-gray-200 dark:bg-gray-600 rounded"></div>
                    <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-600 rounded"></div>
                </div>
                <div className="h-px bg-gray-300 dark:bg-gray-600"></div>
                <div className="flex justify-between">
                    <div className="h-8 w-24 bg-gray-300 dark:bg-gray-700 rounded"></div>
                    <div className="h-8 w-32 bg-gray-300 dark:bg-gray-700 rounded"></div>
                </div>
                <div className="h-12 w-full bg-gray-300 dark:bg-gray-700 rounded-xl"></div>
            </div>
        </div>
    );
}
