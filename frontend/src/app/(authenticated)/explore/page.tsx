'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, Compass, MapPin, SlidersHorizontal, Check } from 'lucide-react';
import { api, Trip, Place, PlacePrediction } from '@/lib/api';
import { MediaPlaceCard } from '@/components/places/MediaPlaceCard';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

const placeCategories = [
    { label: 'All Tourist Places', type: null },
    { label: 'Cultural Heritage', type: 'tourist_attraction historical_landmark' },
    { label: 'Pilgrimage & Spiritual', type: 'place_of_worship hindu_temple church mosque' },
    { label: 'Nature & Scenic', type: 'park national_park hiking_area' },
    { label: 'Adventure & Theme Parks', type: 'amusement_park' },
    { label: 'Museums & Arts', type: 'museum art_gallery' },
    { label: 'Culinary & Dining', type: 'restaurant cafe' },
];

export default function ExplorePage() {
    const searchParams = useSearchParams();
    const cityFromUrl = searchParams.get('city');

    const [places, setPlaces] = useState<Place[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState(cityFromUrl || '');
    const [selectedPlaceType, setSelectedPlaceType] = useState<string | null>(null);
    const [showFilters, setShowFilters] = useState(false);
    const filterRef = useRef<HTMLDivElement>(null);
    const searchRef = useRef<HTMLDivElement>(null);

    const [autocompleteResults, setAutocompleteResults] = useState<PlacePrediction[]>([]);
    const [showAutocomplete, setShowAutocomplete] = useState(false);

    // Close dropdowns if clicked outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
                setShowFilters(false);
            }
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowAutocomplete(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [filterRef, searchRef]);

    const fetchPlacesByLocation = async (lat: number, lng: number, type: string | null) => {
        setIsLoading(true);
        try {
            const data = await api.getNearbyPlaces(lat, lng, 5000, type || 'tourist_attraction');
            setPlaces(data.results);
        } catch (error) {
            console.error('Failed to fetch nearby places:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchPlacesByQuery = async (query: string, type: string | null) => {
        setIsLoading(true);
        try {
            let fullQuery = query.trim();
            // Force strict tourist categorization by default unless it's a specific dining/shopping request
            if (type) {
                fullQuery = `${query} ${type}`;
            } else if (!query.toLowerCase().includes('tourist')) {
                // If they just typed a city or generic word, force it to look for attractions
                fullQuery = `tourist attractions in ${query}`;
            }
            const data = await api.searchPlaces(fullQuery);
            setPlaces(data.results);
        } catch (error) {
            console.error('Failed to search places:', error);
            setPlaces([]);
        } finally {
            setIsLoading(false);
        }
    };

    // Autocomplete fetch effect (debounced)
    useEffect(() => {
        const fetchAutocomplete = async () => {
            if (searchQuery.trim().length > 2) {
                try {
                    const data = await api.autocomplete(searchQuery);
                    setAutocompleteResults(data.predictions || []);
                    setShowAutocomplete(true);
                } catch (error) {
                    console.error('Autocomplete failed:', error);
                }
            } else {
                setAutocompleteResults([]);
                setShowAutocomplete(false);
            }
        };

        const timeoutId = setTimeout(fetchAutocomplete, 300);
        return () => clearTimeout(timeoutId);
    }, [searchQuery]);

    // Handle selecting a prediction
    const handlePredictionSelect = async (prediction: PlacePrediction) => {
        setSearchQuery(prediction.description);
        setShowAutocomplete(false);
        setAutocompleteResults([]);

        // Determine if city vs place
        const isCity = prediction.types?.includes('locality') ||
            prediction.types?.includes('administrative_area_level_3') ||
            prediction.types?.includes('postal_code');

        if (isCity) {
            // It's a city -> Search for Places inside this city
            await fetchPlacesByQuery(`tourist attractions in ${prediction.description}`, selectedPlaceType);
        } else {
            // It's a specific place -> Just get that place
            await fetchPlacesByQuery(prediction.description, null);
        }
    };

    // Initial location fetch (Only runs on mount, not on every search change now)
    useEffect(() => {
        const loadInitialPlaces = async () => {
            if (!cityFromUrl) {
                // If no url query, try to get user location or fallback to Hyderabad
                const getFallback = () => fetchPlacesByLocation(17.3850, 78.4867, selectedPlaceType);

                if (navigator.geolocation) {
                    // Try to get cached location first
                    const storedLocation = localStorage.getItem('user_location');
                    const locationTimestamp = localStorage.getItem('user_location_timestamp');
                    const LOCATION_EXPIRY = 2 * 24 * 60 * 60 * 1000;

                    if (storedLocation && locationTimestamp && (Date.now() - parseInt(locationTimestamp) < LOCATION_EXPIRY)) {
                        try {
                            const coords = JSON.parse(storedLocation);
                            await fetchPlacesByLocation(coords.lat, coords.lng, selectedPlaceType);
                            return;
                        } catch (e) { }
                    }

                    navigator.geolocation.getCurrentPosition(
                        (pos) => {
                            const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                            localStorage.setItem('user_location', JSON.stringify(coords));
                            localStorage.setItem('user_location_timestamp', Date.now().toString());
                            fetchPlacesByLocation(coords.lat, coords.lng, selectedPlaceType);
                        },
                        () => getFallback(),
                        { timeout: 10000 }
                    );
                } else {
                    getFallback();
                }
            } else {
                await fetchPlacesByQuery(`tourist attractions in ${cityFromUrl}`, selectedPlaceType);
            }
        };

        loadInitialPlaces();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedPlaceType]);


    return (
        <div className="min-h-screen pb-24">
            {/* Header Area (Z-Index increased to 50 so dropdowns sit above masonry grid) */}
            <header className="px-4 py-8 md:py-12 relative overflow-visible z-50" style={{ background: 'linear-gradient(180deg, var(--bg-tertiary) 0%, var(--bg-primary) 100%)' }}>
                <div className="max-w-7xl mx-auto">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-white" style={{ background: 'linear-gradient(135deg, var(--accent) 0%, #4F46E5 100%)', boxShadow: '0 0 20px rgba(8, 145, 178, 0.4)' }}>
                            <Compass className="w-6 h-6" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                            Explore
                        </h1>
                    </div>

                    {/* Search & Filter Bar */}
                    <div className="flex items-center gap-3 relative max-w-2xl">
                        <div className="relative group flex-1" ref={searchRef}>
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-[var(--accent)] transition-colors" />
                            <input
                                type="text"
                                placeholder="Search for cities or specific places..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onFocus={() => searchQuery.length > 2 && setShowAutocomplete(true)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && searchQuery.trim()) {
                                        setShowAutocomplete(false);
                                        fetchPlacesByQuery(searchQuery, selectedPlaceType);
                                    }
                                }}
                                className="w-full pl-12 pr-4 py-4 rounded-2xl transition-all font-medium"
                                style={{
                                    background: 'var(--bg-secondary)',
                                    color: 'var(--text-primary)',
                                    border: '1px solid var(--border-subtle)'
                                }}
                            />

                            {/* Autocomplete Dropdown */}
                            <AnimatePresence>
                                {showAutocomplete && autocompleteResults.length > 0 && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className="absolute left-0 right-0 top-[calc(100%+8px)] rounded-2xl p-2 z-50 glass shadow-2xl overflow-hidden"
                                        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}
                                    >
                                        <div className="max-h-80 overflow-y-auto hide-scrollbar">
                                            {autocompleteResults.map((pred) => {
                                                const isCity = pred.types?.includes('locality') || pred.types?.includes('administrative_area_level_3');
                                                return (
                                                    <button
                                                        key={pred.place_id}
                                                        onClick={() => handlePredictionSelect(pred)}
                                                        className="w-full flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-black/5 dark:hover:bg-white/5 transition-colors text-left"
                                                    >
                                                        <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--bg-tertiary)' }}>
                                                            {isCity ? <MapPin className="w-5 h-5" style={{ color: 'var(--accent)' }} /> : <Compass className="w-5 h-5 text-gray-400" />}
                                                        </div>
                                                        <div className="flex-1 overflow-hidden">
                                                            <div className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>{pred.main_text || pred.description}</div>
                                                            <div className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>{pred.description}</div>
                                                        </div>
                                                        <div className="px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase border" style={{ background: 'var(--bg-primary)', color: 'var(--text-tertiary)', borderColor: 'var(--border-subtle)' }}>
                                                            {isCity ? 'City' : 'Place'}
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Three Dots More Options Menu */}
                        <div className="relative" ref={filterRef}>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setShowFilters(!showFilters)}
                                className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg"
                                style={{
                                    background: showFilters ? 'var(--accent)' : 'var(--bg-secondary)',
                                    border: '1px solid var(--border-subtle)',
                                    color: showFilters ? '#fff' : 'var(--text-secondary)'
                                }}
                            >
                                <SlidersHorizontal className="w-6 h-6" />
                            </motion.button>

                            <AnimatePresence>
                                {showFilters && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                        className="absolute right-0 top-[calc(100%+12px)] w-56 rounded-2xl p-2 z-50 glass"
                                        style={{
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border-subtle)',
                                            boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
                                        }}
                                    >
                                        <div className="px-3 py-2 text-xs font-semibold mb-1" style={{ color: 'var(--text-tertiary)' }}>
                                            FILTER PLACES
                                        </div>
                                        {placeCategories.map(cat => (
                                            <button
                                                key={cat.label}
                                                onClick={() => {
                                                    setSelectedPlaceType(cat.type);
                                                    setShowFilters(false);
                                                }}
                                                className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-colors text-sm font-medium"
                                                style={{
                                                    background: selectedPlaceType === cat.type ? 'var(--accent-10)' : 'transparent',
                                                    color: selectedPlaceType === cat.type ? 'var(--accent)' : 'var(--text-secondary)'
                                                }}
                                            >
                                                {cat.label}
                                                {selectedPlaceType === cat.type && <Check className="w-4 h-4" />}
                                            </button>
                                        ))}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Media Grid Gallery */}
            <main className="px-4 md:px-8 max-w-7xl mx-auto mt-4">
                {isLoading ? (
                    <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className={`rounded-2xl animate-pulse bg-gray-200 dark:bg-slate-800 break-inside-avoid shadow-sm ${i % 2 === 0 ? 'h-64' : 'h-80'}`} />
                        ))}
                    </div>
                ) : places.length > 0 ? (
                    <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4 pb-12">
                        {places.map((place) => (
                            <MediaPlaceCard key={place.place_id} place={place} />
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-32 opacity-60">
                        <div className="w-24 h-24 mb-6 rounded-full glass flex items-center justify-center" style={{ border: '1px solid var(--border-subtle)' }}>
                            <MapPin className="w-10 h-10" style={{ color: 'var(--text-tertiary)' }} />
                        </div>
                        <h3 className="text-xl font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                            No places discovered
                        </h3>
                        <p className="text-sm text-center max-w-sm" style={{ color: 'var(--text-secondary)' }}>
                            Try adjusting your filters or searching for a different area.
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
}
