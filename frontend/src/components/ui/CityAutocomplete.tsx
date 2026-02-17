'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Loader2, X, Search } from 'lucide-react';
import { api, PlacePrediction } from '@/lib/api';

interface CityAutocompleteProps {
    value: string;
    onChange: (city: string, placeId?: string) => void;
    placeholder?: string;
    className?: string;
    types?: string; // e.g. "(cities)"
}

export const CityAutocomplete: React.FC<CityAutocompleteProps> = ({
    value,
    onChange,
    placeholder = 'Search for a city...',
    className = '',
    types = '(cities)'
}) => {
    const [input, setInput] = useState(value);
    const [suggestions, setSuggestions] = useState<PlacePrediction[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setInput(value);
    }, [value]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        if (!input || input.length < 3 || !isOpen) {
            setSuggestions([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsLoading(true);
            try {
                const response = await api.autocomplete(input);
                setSuggestions(response.predictions);
            } catch (error) {
                console.error('Autocomplete error:', error);
            } finally {
                setIsLoading(false);
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [input, isOpen]);

    const handleSelect = (prediction: PlacePrediction) => {
        const cityName = prediction.description.split(',')[0];
        setInput(cityName);
        onChange(cityName, prediction.place_id);
        setIsOpen(false);
        setSuggestions([]);
    };

    const clearInput = () => {
        setInput('');
        onChange('');
        setSuggestions([]);
        setIsOpen(false);
    };

    return (
        <div ref={containerRef} className={`relative ${className}`}>
            <div className="relative">
                <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${isLoading ? 'text-accent' : 'text-gray-400'}`} />
                <input
                    type="text"
                    value={input}
                    onChange={(e) => {
                        setInput(e.target.value);
                        setIsOpen(true);
                    }}
                    onFocus={() => setIsOpen(true)}
                    placeholder={placeholder}
                    className="w-full pl-10 pr-10 py-3 rounded-xl text-sm border-transparent bg-gray-50 focus:bg-white focus:ring-2 focus:ring-accent/20 transition-all outline-none"
                    style={{ border: '1px solid rgba(0,0,0,0.05)' }}
                />
                {input && (
                    <button
                        onClick={clearInput}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                    >
                        <X className="w-3.5 h-3.5 text-gray-500" />
                    </button>
                )}
            </div>

            {isOpen && (suggestions.length > 0 || isLoading) && (
                <div
                    className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden"
                    style={{ maxHeight: '300px', overflowY: 'auto' }}
                >
                    {isLoading && suggestions.length === 0 && (
                        <div className="flex items-center justify-center p-4">
                            <Loader2 className="w-5 h-5 animate-spin text-accent" />
                        </div>
                    )}

                    {suggestions.map((suggestion) => (
                        <button
                            key={suggestion.place_id}
                            onClick={() => handleSelect(suggestion)}
                            className="w-full h-full flex items-start gap-3 p-3 text-left hover:bg-gray-50 transition-colors border-b last:border-0 border-gray-50"
                        >
                            <MapPin className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
                            <div>
                                <div className="text-sm font-medium text-gray-900">{suggestion.main_text || suggestion.description.split(',')[0]}</div>
                                <div className="text-xs text-gray-500 line-clamp-1">{suggestion.description}</div>
                            </div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};
