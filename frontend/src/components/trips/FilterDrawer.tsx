'use client';

import React, { useState } from 'react';
import { X, Calendar, MapPin, CheckCircle2, SlidersHorizontal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FilterDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    onApply: (filters: FilterState) => void;
    initialFilters: FilterState;
}

export interface FilterState {
    status?: string;
    city?: string;
    start_date?: string;
    end_date?: string;
    sort_by: string;
    sort_order: number;
}

export const FilterDrawer: React.FC<FilterDrawerProps> = ({
    isOpen,
    onClose,
    onApply,
    initialFilters
}) => {
    const [filters, setFilters] = useState<FilterState>(initialFilters);

    const handleApply = () => {
        onApply(filters);
        onClose();
    };

    const resetFilters = () => {
        setFilters({
            sort_by: 'created_at',
            sort_order: -1
        });
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/40 z-[100] backdrop-blur-sm"
                    />

                    {/* Drawer */}
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed right-0 top-0 h-full w-full max-w-md bg-white z-[101] shadow-2xl flex flex-col"
                    >
                        {/* Header */}
                        <div className="p-6 border-b flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <SlidersHorizontal className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                                <h3 className="text-lg font-bold">Filter Trips</h3>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-black/5 rounded-full transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-8">
                            {/* Sort Section */}
                            <div>
                                <h4 className="text-sm font-semibold uppercase tracking-wider mb-4 text-gray-500">Sort By</h4>
                                <div className="grid grid-cols-2 gap-3">
                                    {[
                                        { label: 'Newest First', val: 'created_at', order: -1 },
                                        { label: 'Oldest First', val: 'created_at', order: 1 },
                                        { label: 'Name (A-Z)', val: 'title', order: 1 },
                                        { label: 'Name (Z-A)', val: 'title', order: -1 }
                                    ].map((opt) => (
                                        <button
                                            key={opt.label}
                                            onClick={() => setFilters({ ...filters, sort_by: opt.val, sort_order: opt.order })}
                                            className={`px-4 py-3 rounded-xl text-sm transition-all border ${filters.sort_by === opt.val && filters.sort_order === opt.order
                                                    ? 'border-accent bg-accent/5 text-accent font-medium'
                                                    : 'border-transparent bg-gray-50 text-gray-600 hover:bg-gray-100'
                                                }`}
                                        >
                                            {opt.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Status Section */}
                            <div>
                                <h4 className="text-sm font-semibold uppercase tracking-wider mb-4 text-gray-500">Status</h4>
                                <div className="flex flex-wrap gap-2">
                                    {['all', 'planning', 'upcoming', 'completed', 'cancelled'].map((s) => (
                                        <button
                                            key={s}
                                            onClick={() => setFilters({ ...filters, status: s === 'all' ? undefined : s })}
                                            className={`px-4 py-2 rounded-full text-sm transition-all border ${(filters.status === s || (s === 'all' && !filters.status))
                                                    ? 'border-accent bg-accent text-white font-medium'
                                                    : 'border-transparent bg-gray-50 text-gray-600 hover:bg-gray-100'
                                                }`}
                                        >
                                            {s.charAt(0).toUpperCase() + s.slice(1)}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* City Filter */}
                            <div>
                                <h4 className="text-sm font-semibold uppercase tracking-wider mb-4 text-gray-500">Destination</h4>
                                <div className="relative">
                                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Filter by city..."
                                        value={filters.city || ''}
                                        onChange={(e) => setFilters({ ...filters, city: e.target.value || undefined })}
                                        className="w-full pl-10 pr-4 py-3 rounded-xl text-sm border-transparent bg-gray-50 focus:bg-white focus:ring-2 focus:ring-accent/20 transition-all"
                                    />
                                </div>
                            </div>

                            {/* Date Filter (Simplified) */}
                            <div>
                                <h4 className="text-sm font-semibold uppercase tracking-wider mb-4 text-gray-500">Trip Dates</h4>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="space-y-1">
                                        <label className="text-xs text-gray-400 ml-2">After</label>
                                        <input
                                            type="date"
                                            value={filters.start_date || ''}
                                            onChange={(e) => setFilters({ ...filters, start_date: e.target.value || undefined })}
                                            className="w-full px-4 py-3 rounded-xl text-sm border-transparent bg-gray-50 focus:bg-white transition-all"
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-gray-400 ml-2">Before</label>
                                        <input
                                            type="date"
                                            value={filters.end_date || ''}
                                            onChange={(e) => setFilters({ ...filters, end_date: e.target.value || undefined })}
                                            className="w-full px-4 py-3 rounded-xl text-sm border-transparent bg-gray-50 focus:bg-white transition-all"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-6 border-t bg-gray-50 grid grid-cols-2 gap-4">
                            <button
                                onClick={resetFilters}
                                className="px-6 py-3 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-200 transition-colors"
                            >
                                Reset All
                            </button>
                            <button
                                onClick={handleApply}
                                className="px-6 py-3 rounded-xl text-sm font-medium text-white bg-accent hover:opacity-90 transition-all shadow-lg shadow-accent/20"
                            >
                                Apply Filters
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};
