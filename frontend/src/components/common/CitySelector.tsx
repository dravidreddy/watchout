'use client';

import { useState } from 'react';
import { MapPin, Search, X } from 'lucide-react';

const POPULAR_CITIES = [
    'Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata',
    'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Goa',
    'Agra', 'Varanasi', 'Udaipur', 'Kochi', 'Manali'
];

interface CitySelectorProps {
    onSelect: (city: string) => void;
    onCancel?: () => void;
}

export function CitySelector({ onSelect, onCancel }: CitySelectorProps) {
    const [searchQuery, setSearchQuery] = useState('');
    const [customCity, setCustomCity] = useState('');

    const filteredCities = POPULAR_CITIES.filter(city =>
        city.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (customCity.trim()) {
            onSelect(customCity.trim());
        }
    };

    const handleCityClick = (city: string) => {
        onSelect(city);
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                        Select Your City
                    </h3>
                    {onCancel && (
                        <button
                            onClick={onCancel}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                            aria-label="Close"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    Choose a city to help us plan your perfect trip
                </p>

                {/* Search */}
                <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search for a city..."
                        className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    />
                </div>

                {/* Popular Cities */}
                <div className="max-h-60 overflow-y-auto mb-4 space-y-2 scrollbar-thin">
                    {filteredCities.length > 0 ? (
                        filteredCities.map((city) => (
                            <button
                                key={city}
                                onClick={() => handleCityClick(city)}
                                className="w-full text-left px-4 py-3 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 text-gray-700 dark:text-gray-300 transition-all group"
                            >
                                <MapPin className="inline w-4 h-4 mr-2 text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform" />
                                {city}
                            </button>
                        ))
                    ) : (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-4">
                            No cities found. Try a different search or enter a custom city below.
                        </p>
                    )}
                </div>

                {/* Custom City Input */}
                <form onSubmit={handleSubmit} className="space-y-3">
                    <div className="relative">
                        <input
                            type="text"
                            value={customCity}
                            onChange={(e) => setCustomCity(e.target.value)}
                            placeholder="Or enter your city name..."
                            className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                        />
                    </div>
                    <div className="flex gap-3">
                        {onCancel && (
                            <button
                                type="button"
                                onClick={onCancel}
                                className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50 font-medium transition-all"
                            >
                                Cancel
                            </button>
                        )}
                        <button
                            type="submit"
                            disabled={!customCity.trim()}
                            className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all shadow-lg shadow-purple-500/30"
                        >
                            Continue
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
