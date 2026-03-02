'use client';

import { Star, MapPin, Clock, DollarSign } from 'lucide-react';
import { Place } from '@/lib/api';
import Image from 'next/image';

interface PlaceCardProps {
    place: Place;
    onClick?: () => void;
}

export function PlaceCard({ place, onClick }: PlaceCardProps) {
    const { name, address, rating, user_ratings_total, price_level, types, opening_hours, photo_reference } = place;

    // Use photo proxy endpoint if photo_reference exists, else use placeholder
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const placeholderImage = "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=400&h=300&fit=crop";
    const imageUrl = photo_reference
        ? `${API_BASE_URL}/places/photo/${encodeURIComponent(photo_reference)}?max_width=400`
        : placeholderImage;

    // Format price level
    const priceIndicator = price_level ? '₹'.repeat(price_level) : null;

    // Format place types
    const category = types && types.length > 0
        ? types[0].replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        : 'Place';

    return (
        <div
            onClick={onClick}
            className="group bg-white dark:bg-slate-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer border border-gray-100 dark:border-slate-700"
        >
            {/* Image */}
            <div className="relative h-48 w-full bg-gradient-to-br from-accent/10 to-accent/5 overflow-hidden">
                <Image
                    src={imageUrl}
                    alt={name}
                    fill
                    sizes="(max-width: 768px) 100vw, 400px"
                    unoptimized
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                    onError={(e) => { (e.target as HTMLImageElement).src = placeholderImage; }}
                />
                {opening_hours !== undefined && (
                    <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-medium ${opening_hours
                        ? 'bg-green-500 text-white'
                        : 'bg-red-500 text-white'
                        }`}>
                        {opening_hours ? 'Open Now' : 'Closed'}
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="p-5">
                {/* Title */}
                <h3 className="font-semibold text-lg mb-2 line-clamp-1 group-hover:text-accent transition-colors" style={{ color: 'var(--text-primary)' }}>
                    {name}
                </h3>

                {/* Address */}
                {address && (
                    <p className="text-sm flex items-start gap-2 mb-3 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                        <MapPin className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>{address}</span>
                    </p>
                )}

                {/* Meta Info */}
                <div className="flex items-center gap-4 flex-wrap">
                    {/* Rating */}
                    {rating && (
                        <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                            <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                                {rating.toFixed(1)}
                            </span>
                            {user_ratings_total && (
                                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                                    ({user_ratings_total.toLocaleString()})
                                </span>
                            )}
                        </div>
                    )}

                    {/* Price Level */}
                    {priceIndicator && (
                        <div className="flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
                            <DollarSign className="w-4 h-4" />
                            <span className="text-sm font-medium">{priceIndicator}</span>
                        </div>
                    )}

                    {/* Category Badge */}
                    <div className="ml-auto">
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent">
                            {category}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
