'use client';

import { useState, useEffect, useCallback } from 'react';
import { Calendar, MapPin, ChevronRight, Filter, Search, Clock, Users, Compass, CheckSquare, Trash2 } from 'lucide-react';
import Link from 'next/link';

const statusColors: Record<string, { bg: string; text: string }> = {
    upcoming: { bg: '#D1FAE5', text: '#065F46' },
    completed: { bg: '#E5E7EB', text: '#6B7280' },
    planning: { bg: '#DBEAFE', text: '#1E40AF' },
};

import { api, Trip } from '@/lib/api';
import { FilterDrawer, FilterState } from '@/components/trips/FilterDrawer';
import { TripCard } from '@/components/trips/TripCard';
import { TripDetailPanel } from '@/components/trips/TripDetailPanel';
import { DeleteConfirmDialog } from '@/components/trips/DeleteConfirmDialog';
import { toast } from 'sonner';

export default function TripsPage() {
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [filters, setFilters] = useState<FilterState>({
        sort_by: 'created_at',
        sort_order: -1
    });
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [trips, setTrips] = useState<Trip[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSearching, setIsSearching] = useState(false);
    const [selectionMode, setSelectionMode] = useState(false);
    const [selectedTrips, setSelectedTrips] = useState<Set<string>>(new Set());
    const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
    const [isLoadingDetail, setIsLoadingDetail] = useState(false);

    // Debounce search query
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(searchQuery);
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const fetchTrips = useCallback(async () => {
        setIsSearching(true);
        try {
            let data;
            if (debouncedSearch.trim()) {
                data = await api.searchTrips(debouncedSearch);
            } else {
                data = await api.listTrips(filters);
            }
            setTrips(data);
        } catch (error) {
            console.error('Failed to fetch trips:', error);
        } finally {
            setIsLoading(false);
            setIsSearching(false);
        }
    }, [debouncedSearch, filters]);

    useEffect(() => {
        fetchTrips();
    }, [fetchTrips]);

    const handleFilterApply = (newFilters: FilterState) => {
        setFilters(newFilters);
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return 'Date TBD';
        return new Date(dateStr).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short'
        });
    };

    const handleTripDelete = (tripId: string) => {
        setTrips(prev => prev.filter(t => t._id !== tripId));
        setSelectedTrips(prev => {
            const newSet = new Set(prev);
            newSet.delete(tripId);
            return newSet;
        });
    };

    const handleToggleSelect = (tripId: string) => {
        setSelectedTrips(prev => {
            const newSet = new Set(prev);
            if (newSet.has(tripId)) {
                newSet.delete(tripId);
            } else {
                newSet.add(tripId);
            }
            return newSet;
        });
    };

    const handleBulkDelete = async () => {
        setIsDeleting(true);
        try {
            await Promise.all(
                Array.from(selectedTrips).map(tripId => api.deleteTrip(tripId))
            );
            toast.success(`${selectedTrips.size} trip(s) deleted successfully`);
            setTrips(prev => prev.filter(t => !selectedTrips.has(t._id)));
            setSelectedTrips(new Set());
            setSelectionMode(false);
        } catch (error) {
            console.error('Failed to bulk delete:', error);
            toast.error('Failed to delete some trips');
        } finally {
            setIsDeleting(false);
            setShowBulkDeleteConfirm(false);
        }
    };

    const handleSelectAll = () => {
        if (selectedTrips.size === trips.length) {
            setSelectedTrips(new Set());
        } else {
            setSelectedTrips(new Set(trips.map(t => t._id)));
        }
    };

    // Open trip detail panel by fetching the full trip (with itinerary)
    const handleOpenTrip = async (trip: Trip) => {
        if (selectionMode) return;
        setIsLoadingDetail(true);
        setSelectedTrip(trip); // show panel immediately with list data
        try {
            const tripId = trip.trip_id || trip._id;
            const full = await api.getTrip(tripId);
            setSelectedTrip({ ...trip, ...full });
        } catch {
            // keep the shallow trip data if full fetch fails
        } finally {
            setIsLoadingDetail(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--accent)]" />
            </div>
        );
    }

    return (
        <div className="min-h-screen flex">
            {/* Left: Trip list — compresses when detail panel is open */}
            <div className={`flex flex-col flex-shrink-0 transition-all duration-300 ${selectedTrip ? 'hidden md:flex md:w-[40%] md:border-r' : 'flex w-full'
                }`} style={{ borderColor: 'rgba(0,0,0,0.07)' }}>
                {/* Header */}
                <header className="px-4 md:px-8 py-6">
                    <div className="flex items-center justify-between mb-2">
                        <h1 className="text-title" style={{ color: 'var(--text-primary)' }}>
                            Your Trips
                        </h1>
                        <div className="flex items-center gap-2">
                            {selectionMode && selectedTrips.size > 0 && (
                                <button
                                    onClick={() => setShowBulkDeleteConfirm(true)}
                                    className="text-sm font-medium flex items-center gap-1.5 bg-red-600 text-white px-3 py-1.5 rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    <Trash2 className="w-4 h-4" />
                                    Delete Selected ({selectedTrips.size})
                                </button>
                            )}
                            <button
                                onClick={() => {
                                    setSelectionMode(!selectionMode);
                                    setSelectedTrips(new Set());
                                }}
                                className={`text-sm font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${selectionMode
                                    ? 'bg-accent text-white hover:bg-accent/90'
                                    : 'border border-accent/20 text-accent hover:bg-accent/5'
                                    }`}
                            >
                                <CheckSquare className="w-4 h-4" />
                                {selectionMode ? 'Cancel' : 'Select'}
                            </button>
                            <Link href="/explore" className="text-sm font-medium flex items-center gap-1 text-accent border border-accent/20 px-3 py-1.5 rounded-lg hover:bg-accent/5 transition-colors">
                                <Compass className="w-4 h-4" />
                                Explore More
                            </Link>
                        </div>
                    </div>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        {trips.length} trips planned
                    </p>
                </header>

                <div className="px-4 md:px-8 max-w-4xl">
                    {/* Search & Filters */}
                    <div className="flex gap-3 mb-6">
                        <div className="relative flex-1">
                            <Search
                                className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors ${isSearching ? 'text-accent' : 'text-gray-400'
                                    }`}
                            />
                            <input
                                type="text"
                                placeholder="Search by destination or title..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-4 py-3 rounded-xl text-sm transition-all shadow-sm"
                                style={{
                                    background: 'var(--bg-secondary)',
                                    border: '1px solid rgba(0,0,0,0.05)',
                                    color: 'var(--text-primary)'
                                }}
                            />
                            {isSearching && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-accent" />
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => setIsFilterOpen(true)}
                            className={`p-3 rounded-xl transition-all border shadow-sm flex items-center gap-2 ${(filters.status || filters.city || filters.start_date || filters.end_date)
                                ? 'bg-accent/5 border-accent text-accent'
                                : 'bg-white border-gray-100 text-gray-600'
                                }`}
                        >
                            <Filter className="w-5 h-5" />
                            <span className="hidden md:block text-sm font-medium">Filters</span>
                            {(filters.status || filters.city || filters.start_date || filters.end_date) && (
                                <span className="flex h-2 w-2 rounded-full bg-accent" />
                            )}
                        </button>
                    </div>

                    {/* Filter Chips - Fast toggle for common statuses */}
                    <div className="flex gap-2 mb-6 overflow-x-auto hide-scrollbar pb-2">
                        {['all', 'planning', 'upcoming', 'completed'].map((status) => (
                            <button
                                key={status}
                                onClick={() => setFilters({ ...filters, status: status === 'all' ? undefined : status })}
                                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${(filters.status === status || (status === 'all' && !filters.status))
                                    ? 'bg-accent text-white shadow-md'
                                    : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'
                                    }`}
                            >
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                            </button>
                        ))}
                    </div>

                    {/* Select All */}
                    {selectionMode && trips.length > 0 && (
                        <div className="mb-4">
                            <button
                                onClick={handleSelectAll}
                                className="text-sm font-medium text-accent hover:text-accent/80 transition-colors"
                            >
                                {selectedTrips.size === trips.length ? 'Deselect All' : 'Select All'}
                            </button>
                        </div>
                    )}

                    <FilterDrawer
                        isOpen={isFilterOpen}
                        onClose={() => setIsFilterOpen(false)}
                        initialFilters={filters}
                        onApply={handleFilterApply}
                    />

                    {/* Trips List */}
                    {isLoading ? (
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="card h-32 animate-pulse bg-gray-50/50" />
                            ))}
                        </div>
                    ) : trips.length === 0 ? (
                        <div className="card p-8 text-center">
                            <MapPin className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--text-tertiary)' }} />
                            <p className="text-body" style={{ color: 'var(--text-secondary)' }}>
                                No trips found
                            </p>
                            <Link href="/chat?new=true">
                                <button className="btn btn-primary mt-4">
                                    Plan a new trip
                                </button>
                            </Link>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {trips.map((trip) => (
                                <div
                                    className={`animate-page-mount cursor-pointer rounded-xl transition-all ${selectedTrip?._id === trip._id
                                        ? 'ring-2 ring-accent ring-offset-1'
                                        : ''
                                        }`}
                                    key={trip._id}
                                    onClick={() => handleOpenTrip(trip)}
                                >
                                    <TripCard
                                        trip={trip}
                                        showVisibility
                                        onDelete={handleTripDelete}
                                        selectionMode={selectionMode}
                                        isSelected={selectedTrips.has(trip._id)}
                                        onToggleSelect={handleToggleSelect}
                                    />
                                </div>
                            ))}
                        </div>
                    )}
                </div>{/* end inner content div */}
            </div>{/* end left column */}

            {/* Right: Trip detail panel */}
            {selectedTrip && (
                <div className="flex-1 flex flex-col border-l overflow-hidden relative" style={{ borderColor: 'rgba(0,0,0,0.07)' }}>
                    {isLoadingDetail && (
                        <div className="absolute inset-0 bg-white/50 dark:bg-black/20 z-10 flex items-center justify-center pointer-events-none">
                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent" />
                        </div>
                    )}
                    <TripDetailPanel
                        trip={selectedTrip}
                        onClose={() => setSelectedTrip(null)}
                    />
                </div>
            )}

            <DeleteConfirmDialog
                isOpen={showBulkDeleteConfirm}
                onClose={() => setShowBulkDeleteConfirm(false)}
                onConfirm={handleBulkDelete}
                tripCount={selectedTrips.size}
                isDeleting={isDeleting}
            />
        </div>
    );
}
