'use client';

import { Calendar, MapPin, ChevronRight, Users, Globe, Lock, Share2, Trash2 } from 'lucide-react';
import { Trip, api } from '@/lib/api';
import { toast } from 'sonner';
import { useState } from 'react';
import Image from 'next/image';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';

interface TripCardProps {
    trip: Trip;
    showVisibility?: boolean;
    onClick?: () => void;
    onUpdate?: () => void;
    onDelete?: (tripId: string) => void;
    selectionMode?: boolean;
    isSelected?: boolean;
    onToggleSelect?: (tripId: string) => void;
}

const statusColors: Record<string, { bg: string; text: string }> = {
    upcoming: { bg: '#D1FAE5', text: '#065F46' },
    completed: { bg: '#E5E7EB', text: '#6B7280' },
    planning: { bg: '#DBEAFE', text: '#1E40AF' },
};

export function TripCard({
    trip: initialTrip,
    showVisibility = false,
    onClick,
    onUpdate,
    onDelete,
    selectionMode = false,
    isSelected = false,
    onToggleSelect
}: TripCardProps) {
    const [trip, setTrip] = useState(initialTrip);
    const [isUpdating, setIsUpdating] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return 'Date TBD';
        return new Date(dateStr).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short'
        });
    };

    const handleToggleVisibility = async (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsUpdating(true);
        try {
            const newIsPublic = !trip.is_public;
            await api.updateTrip(trip._id, { is_public: newIsPublic });

            // Re-fetch trip to get sharing_id if it was just made public
            const updated = await api.getTrip(trip._id);
            setTrip(updated);
            onUpdate?.();
            toast.success(newIsPublic ? 'Trip is now public' : 'Trip is now private');
        } catch (error) {
            console.error('Failed to update visibility:', error);
            toast.error('Failed to update visibility');
        } finally {
            setIsUpdating(false);
        }
    };

    const handleCopyLink = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!trip.sharing_id) return;

        const url = `${window.location.origin}/shared/${trip.sharing_id}`;
        navigator.clipboard.writeText(url);
        toast.success('Link copied to clipboard!');
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setShowDeleteConfirm(true);
    };

    const confirmDelete = async () => {
        setIsDeleting(true);
        try {
            await api.deleteTrip(trip._id);
            toast.success('Trip deleted successfully');
            onDelete?.(trip._id);
        } catch (error) {
            console.error('Failed to delete trip:', error);
            toast.error('Failed to delete trip');
        } finally {
            setIsDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const handleCheckboxClick = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        onToggleSelect?.(trip._id);
    };

    return (
        <>
            <div
                onClick={onClick}
                className="card card-hover-scale flex flex-col md:flex-row overflow-hidden cursor-pointer"
                style={{ height: 'auto', minHeight: '140px' }}
            >
                {/* Image */}
                <div className="w-full md:w-32 lg:w-40 h-32 md:h-auto flex-shrink-0 relative bg-gray-100">
                    {selectionMode && (
                        <div
                            className="absolute top-2 left-2 z-10"
                            onClick={handleCheckboxClick}
                        >
                            <div className={`w-6 h-6 rounded-md border-2 flex items-center justify-center cursor-pointer transition-all ${isSelected
                                ? 'bg-accent border-accent'
                                : 'bg-white border-gray-300 hover:border-accent'
                                }`}>
                                {isSelected && (
                                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                )}
                            </div>
                        </div>
                    )}
                    <Image
                        src="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600&h=400&fit=crop"
                        alt={`Trip to ${trip.cities?.join(', ') || trip.title}`}
                        fill
                        sizes="(max-width: 768px) 100vw, 160px"
                        className="object-cover"
                    />
                </div>

                {/* Content */}
                <div className="flex-1 p-4 flex flex-col justify-between">
                    <div>
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex flex-col">
                                <h3 className="font-semibold line-clamp-1" style={{ color: 'var(--text-primary)' }}>
                                    {trip.title}
                                </h3>
                                {showVisibility && (
                                    <button
                                        onClick={handleToggleVisibility}
                                        disabled={isUpdating}
                                        className={`flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider mt-1 px-2 py-0.5 rounded-full transition-colors ${trip.is_public ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                            }`}
                                    >
                                        {trip.is_public ? <Globe className="w-2.5 h-2.5" /> : <Lock className="w-2.5 h-2.5" />}
                                        {trip.is_public ? 'Public' : 'Private'}
                                    </button>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                {trip.is_public && trip.sharing_id && (
                                    <button
                                        onClick={handleCopyLink}
                                        className="p-1.5 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                                        title="Copy Link"
                                    >
                                        <Share2 className="w-4 h-4" />
                                    </button>
                                )}
                                {!selectionMode && (
                                    <button
                                        onClick={handleDelete}
                                        className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                                        title="Delete Trip"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                )}
                                <span
                                    className="text-xs font-medium px-2 py-1 rounded-full flex-shrink-0"
                                    style={{
                                        background: statusColors[trip.status]?.bg || statusColors['planning'].bg,
                                        color: statusColors[trip.status]?.text || statusColors['planning'].text
                                    }}
                                >
                                    {trip.status}
                                </span>
                            </div>
                        </div>
                        <p className="text-sm mt-2 flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
                            <MapPin className="w-3.5 h-3.5" />
                            {trip.cities?.join(', ') || 'No cities specified'}
                        </p>

                        {/* Category & Tags */}
                        <div className="flex flex-wrap gap-1.5 mt-2">
                            {trip.category && (
                                <span className="text-[10px] font-bold bg-blue-50 text-blue-600 px-2 py-0.5 rounded-md uppercase tracking-wide">
                                    {trip.category}
                                </span>
                            )}
                            {trip.tags?.slice(0, 3).map(tag => (
                                <span key={tag} className="text-[10px] bg-gray-50 text-gray-500 px-2 py-0.5 rounded-md border border-gray-100">
                                    #{tag}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-tertiary)' }}>
                            <span className="flex items-center gap-1">
                                <Calendar className="w-3.5 h-3.5" />
                                {formatDate(trip.start_date)}
                            </span>
                            <span className="flex items-center gap-1">
                                <Users className="w-3.5 h-3.5" />
                                {trip.num_travelers}
                            </span>
                        </div>
                        <ChevronRight className="w-5 h-5" style={{ color: 'var(--text-tertiary)' }} />
                    </div>
                </div>
            </div>

            {/* Delete confirmation dialog - outside card for proper z-index */}
            <DeleteConfirmDialog
                isOpen={showDeleteConfirm}
                onClose={() => setShowDeleteConfirm(false)}
                onConfirm={confirmDelete}
                tripCount={1}
                isDeleting={isDeleting}
            />
        </>
    );
}

export default TripCard;
