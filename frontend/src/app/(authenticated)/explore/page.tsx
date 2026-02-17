'use client';

import { useState, useEffect } from 'react';
import { Search, Compass, MapPin } from 'lucide-react';
import { api, Trip, Place } from '@/lib/api';
import { TripCard } from '@/components/trips/TripCard';
import { PlaceCard } from '@/components/places/PlaceCard';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

// Place categories for filtering
const placeCategories = [
    { label: 'All', type: null },
    { label: 'Tourist Attractions', type: 'tourist_attraction' },
    { label: 'Recreational', type: 'park' },
    { label: 'Pilgrimage', type: 'place_of_worship' },
    { label: 'Restaurants', type: 'restaurant' },
    { label: 'Museums', type: 'museum' },
    { label: 'Shopping', type: 'shopping_mall' },
];

export default function ExplorePage() {
    const searchParams = useSearchParams();
    const cityFromUrl = searchParams.get('city');

    const [trips, setTrips] = useState<Trip[]>([]);
    const [places, setPlaces] = useState<Place[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [selectedPlaceType, setSelectedPlaceType] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'trips' | 'places'>('trips');

    // Auto-fill search and switch to places mode if city parameter is in URL
    useEffect(() => {
        if (cityFromUrl && !searchQuery) {
            setSearchQuery(cityFromUrl);
            setViewMode('places');
        }
    }, [cityFromUrl]);

    // Fetch trips
    useEffect(() => {
        if (viewMode === 'trips') {
            const fetchPublicTrips = async () => {
                setIsLoading(true);
                try {
                    const data = await api.exploreTrips({
                        category: selectedCategory || undefined
                    });
                    setTrips(data);
                } catch (error) {
                    console.error('Failed to fetch explore trips:', error);
                } finally {
                    setIsLoading(false);
                }
            };
            fetchPublicTrips();
        }
    }, [selectedCategory, viewMode]);

    // Fetch places when search query changes
    useEffect(() => {
        if (viewMode === 'places' && searchQuery.trim()) {
            const fetchPlaces = async () => {
                setIsLoading(true);
                try {
                    // Build enhanced query for pilgrimage sites
                    let fullQuery = searchQuery.trim();

                    if (selectedPlaceType === 'place_of_worship') {
                        // For pilgrimage, add specific keywords to get diverse religious sites
                        fullQuery = `${searchQuery} temples mosques churches gurudwaras pilgrimage religious sites`;
                    } else if (selectedPlaceType) {
                        fullQuery = `${searchQuery} ${selectedPlaceType}`;
                    }

                    const data = await api.searchPlaces(fullQuery);
                    setPlaces(data.results);
                } catch (error) {
                    console.error('Failed to fetch places:', error);
                    setPlaces([]);
                } finally {
                    setIsLoading(false);
                }
            };

            // Debounce search
            const timeoutId = setTimeout(fetchPlaces, 500);
            return () => clearTimeout(timeoutId);
        } else if (viewMode === 'places' && !searchQuery.trim()) {
            setPlaces([]);
            setIsLoading(false);
        }
    }, [searchQuery, selectedPlaceType, viewMode]);

    // Switch to places mode when user types in search
    const handleSearchChange = (value: string) => {
        setSearchQuery(value);
        if (value.trim()) {
            setViewMode('places');
        }
    };

    // Filter trips for trips mode
    const filteredTrips = trips.filter(trip =>
        trip.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        trip.cities?.some(city => city.toLowerCase().includes(searchQuery.toLowerCase())) ||
        trip.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const categories = ['Adventure', 'Relaxation', 'Cultural', 'Family', 'Solo'];

    return (
        <div className="min-h-screen pb-20">
            {/* Header */}
            <header className="px-4 md:px-8 py-8 md:py-12" style={{ background: 'linear-gradient(to bottom, rgba(8, 145, 178, 0.05), transparent)' }}>
                <div className="max-w-5xl mx-auto">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-2xl bg-accent flex items-center justify-center text-white" style={{ background: 'var(--accent)' }}>
                            <Compass className="w-7 h-7" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                            Explore {viewMode === 'places' ? 'Places' : 'Trips'}
                        </h1>
                    </div>
                    <p className="text-lg mb-8" style={{ color: 'var(--text-secondary)' }}>
                        {viewMode === 'places'
                            ? 'Search for cities and discover amazing places to visit.'
                            : 'Discover itineraries created by the community and get inspired for your next journey.'}
                    </p>

                    {/* View Mode Toggle */}
                    <div className="flex gap-2 mb-6">
                        <button
                            onClick={() => { setViewMode('trips'); setSearchQuery(''); }}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${viewMode === 'trips'
                                ? 'bg-accent text-white shadow-md'
                                : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'}`}
                        >
                            Browse Trips
                        </button>
                        <button
                            onClick={() => setViewMode('places')}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${viewMode === 'places'
                                ? 'bg-accent text-white shadow-md'
                                : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'}`}
                        >
                            Search Places
                        </button>
                    </div>

                    {/* Search Bar */}
                    <div className="relative group mb-6">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-accent transition-colors" />
                        <input
                            type="text"
                            placeholder={viewMode === 'places' ? "Search for a city (e.g., Mumbai, Delhi)..." : "Search by city, theme, or title..."}
                            value={searchQuery}
                            onChange={(e) => handleSearchChange(e.target.value)}
                            className="w-full pl-12 pr-4 py-4 rounded-2xl shadow-sm border border-gray-100 focus:border-accent focus:ring-4 focus:ring-accent/10 transition-all text-lg"
                            style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                        />
                    </div>

                    {/* Category Filters */}
                    <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
                        {viewMode === 'places' ? (
                            // Place categories
                            <>
                                {placeCategories.map(cat => (
                                    <button
                                        key={cat.label}
                                        onClick={() => setSelectedPlaceType(cat.type)}
                                        className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${selectedPlaceType === cat.type
                                            ? 'bg-accent text-white shadow-md'
                                            : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'}`}
                                    >
                                        {cat.label}
                                    </button>
                                ))}
                            </>
                        ) : (
                            // Trip categories
                            <>
                                <button
                                    onClick={() => setSelectedCategory(null)}
                                    className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${!selectedCategory
                                        ? 'bg-accent text-white shadow-md'
                                        : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'}`}
                                >
                                    All
                                </button>
                                {categories.map(cat => (
                                    <button
                                        key={cat}
                                        onClick={() => setSelectedCategory(cat)}
                                        className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${selectedCategory === cat
                                            ? 'bg-accent text-white shadow-md'
                                            : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'}`}
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </>
                        )}
                    </div>
                </div>
            </header>

            <main className="px-4 md:px-8 max-w-5xl mx-auto">
                {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-36 rounded-2xl animate-pulse bg-gray-100 dark:bg-slate-800" />
                        ))}
                    </div>
                ) : viewMode === 'places' ? (
                    // Places Grid
                    places.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {places.map((place) => (
                                <div
                                    key={place.place_id}
                                    className="animate-page-mount"
                                >
                                    <PlaceCard place={place} />
                                </div>
                            ))}
                        </div>
                    ) : searchQuery.trim() ? (
                        <div className="text-center py-20">
                            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <MapPin className="w-10 h-10 text-gray-300" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                No places found
                            </h3>
                            <p style={{ color: 'var(--text-secondary)' }}>
                                Try searching for a different city or changing the category filter.
                            </p>
                        </div>
                    ) : (
                        <div className="text-center py-20">
                            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Search className="w-10 h-10 text-gray-300" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                Search for a city
                            </h3>
                            <p style={{ color: 'var(--text-secondary)' }}>
                                Enter a city name to discover tourist attractions, restaurants, and more.
                            </p>
                        </div>
                    )
                ) : (
                    // Trips Grid
                    filteredTrips.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {filteredTrips.map((trip, index) => (
                                <div className="animate-page-mount"
                                    key={trip._id}
                                >
                                    <Link href={`/trips/shared/${trip.sharing_id}`}>
                                        <TripCard trip={trip} />
                                    </Link>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20">
                            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <MapPin className="w-10 h-10 text-gray-300" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                No trips found
                            </h3>
                            <p style={{ color: 'var(--text-secondary)' }}>
                                Try searching for a different city or destination.
                            </p>
                        </div>
                    )
                )}
            </main>
        </div>
    );
}
