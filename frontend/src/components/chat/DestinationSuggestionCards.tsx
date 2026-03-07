'use client';

import React from 'react';
import { MapPin } from 'lucide-react';

export interface DestinationSuggestion {
    city: string;
    emoji: string;
    pitch: string;
    best_for?: string;
}

interface DestinationSuggestionCardsProps {
    suggestions: DestinationSuggestion[];
    onPick: (city: string) => void;
}

export function DestinationSuggestionCards({ suggestions, onPick }: DestinationSuggestionCardsProps) {
    if (!suggestions || suggestions.length === 0) return null;

    return (
        <div className="flex flex-col gap-2.5 mt-3 animate-in fade-in slide-in-from-bottom-3 duration-400">
            {suggestions.map((dest, i) => (
                <button
                    key={`${dest.city}-${i}`}
                    onClick={() => onPick(dest.city)}
                    className="group relative flex items-start gap-3 text-left px-4 py-3.5 rounded-2xl
                               bg-white/5 hover:bg-purple-500/15 border border-white/8
                               hover:border-purple-400/40 transition-all duration-200
                               hover:shadow-lg hover:shadow-purple-500/10 hover:-translate-y-0.5
                               active:translate-y-0 active:scale-[0.99]"
                    aria-label={`Pick ${dest.city} as your destination`}
                >
                    {/* Emoji blob */}
                    <div className="text-2xl leading-none flex-shrink-0 mt-0.5 transition-transform duration-200 group-hover:scale-110">
                        {dest.emoji}
                    </div>

                    {/* Text */}
                    <div className="flex flex-col min-w-0">
                        <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-semibold text-white text-sm">{dest.city}</span>
                            {dest.best_for && (
                                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/20">
                                    {dest.best_for}
                                </span>
                            )}
                        </div>
                        <p className="text-white/55 text-xs mt-0.5 leading-snug">{dest.pitch}</p>
                    </div>

                    {/* Hover arrow */}
                    <div className="ml-auto flex-shrink-0 self-center opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                        <MapPin className="w-3.5 h-3.5 text-purple-400" />
                    </div>
                </button>
            ))}
        </div>
    );
}
