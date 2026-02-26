import React from 'react';
import { MapPin, Star, DollarSign, Clock, ExternalLink } from 'lucide-react';

// --- Types ---
export interface Restaurant {
    name: string;
    rating?: string | number;
    address?: string;
    price_level?: string;
    cuisine?: string;
    url?: string;
}

export interface Attraction {
    name: string;
    description?: string;
    time?: string;
    duration?: string;
}

// --- Components ---

export const RestaurantCard: React.FC<{ restaurant: Restaurant }> = ({ restaurant }) => {
    return (
        <div className="bg-white/10 border border-white/20 rounded-xl p-3 my-2 max-w-sm backdrop-blur-sm hover:bg-white/15 hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500/50 transition-all duration-200" tabIndex={0}>
            <div className="flex justify-between items-start mb-1">
                <h4 className="font-semibold text-white text-base">{restaurant.name}</h4>
                {restaurant.rating && (
                    <div className="flex items-center bg-yellow-500/20 px-1.5 py-0.5 rounded text-yellow-300 text-xs font-bold">
                        <Star className="w-3 h-3 mr-1 fill-yellow-300" />
                        {restaurant.rating}
                    </div>
                )}
            </div>

            <div className="space-y-1">
                {restaurant.cuisine && (
                    <div className="text-xs text-purple-200 bg-purple-500/20 inline-block px-2 py-0.5 rounded-full mb-1">
                        {restaurant.cuisine}
                    </div>
                )}

                {restaurant.address && (
                    <div className="flex items-start text-xs text-slate-300">
                        <MapPin className="w-3 h-3 mr-1 mt-0.5 flex-shrink-0 opacity-70" />
                        <span className="line-clamp-2">{restaurant.address}</span>
                    </div>
                )}

                {restaurant.price_level && (
                    <div className="flex items-center text-xs text-slate-300">
                        <DollarSign className="w-3 h-3 mr-1 opacity-70" />
                        <span>{restaurant.price_level}</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export const AttractionCard: React.FC<{ activity: Attraction }> = ({ activity }) => {
    return (
        <div className="bg-white/5 border-l-2 border-purple-500 pl-3 py-1 my-2 hover:bg-white/10 hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500/50 transition-all duration-200 rounded-r-md" tabIndex={0}>
            <div className="flex items-center justify-between">
                <h4 className="font-medium text-white">{activity.name}</h4>
                {activity.time && (
                    <div className="text-xs text-purple-300 flex items-center bg-purple-900/40 px-2 py-0.5 rounded">
                        <Clock className="w-3 h-3 mr-1" />
                        {activity.time}
                    </div>
                )}
            </div>
            {activity.description && (
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{activity.description}</p>
            )}
        </div>
    );
};
