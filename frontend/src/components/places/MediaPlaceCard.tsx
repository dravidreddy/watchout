import { useState } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Star, X, Navigation, ChevronLeft, ChevronRight, Quote } from 'lucide-react';
import { Place, api } from '@/lib/api';

interface MediaPlaceCardProps {
    place: Place;
}

export function MediaPlaceCard({ place }: MediaPlaceCardProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [detailedPlace, setDetailedPlace] = useState<Place | null>(null);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);
    const [activePhotoIndex, setActivePhotoIndex] = useState(0);

    const { name, address, rating, user_ratings_total, types, opening_hours, photo_reference } = detailedPlace || place;

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const placeholderImage = "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=600&h=800&fit=crop";

    // Arrays of photos to swipe through
    const photos = detailedPlace?.photos?.length ? detailedPlace.photos : (photo_reference ? [photo_reference] : []);

    const getImageUrl = (ref: string) => ref ? `${API_BASE_URL}/places/photo/${encodeURIComponent(ref)}?max_width=800` : placeholderImage;
    const coverImageUrl = getImageUrl(photos[0] || '');

    const category = types && types.length > 0
        ? types[0].replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        : 'Tourist Attraction';

    const openDetailsModal = async () => {
        setIsOpen(true);
        if (detailedPlace) return;

        setIsLoadingDetails(true);
        try {
            const data = await api.getPlaceDetails(place.place_id);
            setDetailedPlace(data);
        } catch (err) {
            console.error("Failed to fetch place details:", err);
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const nextPhoto = (e: React.MouseEvent) => {
        e.stopPropagation();
        setActivePhotoIndex((prev) => (prev + 1) % photos.length);
    };

    const prevPhoto = (e: React.MouseEvent) => {
        e.stopPropagation();
        setActivePhotoIndex((prev) => (prev - 1 + photos.length) % photos.length);
    };

    return (
        <>
            {/* The Grid Item - Image Only */}
            <motion.div
                whileHover={{ scale: 1.02, y: -4 }}
                whileTap={{ scale: 0.98 }}
                onClick={openDetailsModal}
                className="relative cursor-pointer rounded-2xl overflow-hidden group shadow-md break-inside-avoid mb-4 bg-gray-900"
                style={{
                    // Randomize height slightly for masonry effect if desired, or let image dictate
                    minHeight: '200px',
                    border: '1px solid var(--border-subtle)'
                }}
            >
                <div className="relative w-full aspect-[4/5]">
                    <Image
                        src={coverImageUrl}
                        alt={name}
                        fill
                        unoptimized
                        sizes="(max-width: 768px) 50vw, 33vw"
                        className="object-cover transition-transform duration-700 group-hover:scale-110"
                        onError={(e) => { (e.target as HTMLImageElement).src = placeholderImage; }}
                    />
                    {/* Subtle gradient overlay to make things pop if we ever add text, but for now just a dark bottom vignette */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                </div>
            </motion.div>

            {/* The Detail Modal */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsOpen(false)}
                            className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ opacity: 0, y: 100, scale: 0.9 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 20, scale: 0.95 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className="fixed inset-x-4 bottom-24 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 z-[70] md:max-w-md w-full glass rounded-3xl overflow-hidden shadow-2xl"
                            style={{
                                background: 'var(--bg-primary)',
                                border: '1px solid var(--border-subtle)'
                            }}
                        >
                            {/* Modal Image Header */}
                            <div className="relative w-full h-64 md:h-72 bg-black group/slider">
                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={activePhotoIndex}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.3 }}
                                        className="absolute inset-0"
                                    >
                                        <Image
                                            src={getImageUrl(photos[activePhotoIndex])}
                                            alt={name}
                                            fill
                                            unoptimized
                                            className="object-cover"
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60" />
                                    </motion.div>
                                </AnimatePresence>

                                {/* Swiper Controls */}
                                {photos.length > 1 && (
                                    <>
                                        <button onClick={prevPhoto} className="absolute left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/40 text-white flex items-center justify-center backdrop-blur-md opacity-0 group-hover/slider:opacity-100 transition-opacity hover:bg-black/60">
                                            <ChevronLeft className="w-5 h-5" />
                                        </button>
                                        <button onClick={nextPhoto} className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/40 text-white flex items-center justify-center backdrop-blur-md opacity-0 group-hover/slider:opacity-100 transition-opacity hover:bg-black/60">
                                            <ChevronRight className="w-5 h-5" />
                                        </button>
                                        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                                            {photos.map((_, i) => (
                                                <div key={i} className={`w-1.5 h-1.5 rounded-full transition-all ${i === activePhotoIndex ? 'bg-white w-3.5' : 'bg-white/50'}`} />
                                            ))}
                                        </div>
                                    </>
                                )}

                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="absolute top-4 right-4 p-2 rounded-full bg-black/40 text-white backdrop-blur-md hover:bg-black/70 transition-colors border border-white/10"
                                >
                                    <X className="w-5 h-5" />
                                </button>

                                {opening_hours !== undefined && (
                                    <div className="absolute top-4 left-4">
                                        {Array.isArray(opening_hours) ? (
                                            <div className="px-3 py-1.5 rounded-full text-xs font-semibold backdrop-blur-md shadow-lg bg-black/50 text-white border border-white/10">
                                                More info below
                                            </div>
                                        ) : (
                                            <div className={`px-3 py-1.5 rounded-full text-xs font-semibold backdrop-blur-md shadow-lg ${opening_hours ? 'bg-green-500/90 text-white' : 'bg-red-500/90 text-white'}`}>
                                                {opening_hours ? 'Open Now' : 'Closed'}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Modal Content */}
                            <div className="p-6">
                                <div className="flex items-start justify-between gap-4 mb-2">
                                    <h2 className="text-2xl font-bold line-clamp-2" style={{ color: 'var(--text-primary)' }}>
                                        {name}
                                    </h2>
                                </div>

                                <div className="flex items-center gap-2 mb-4">
                                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-accent/20 text-accent border border-accent/20">
                                        {category}
                                    </span>
                                    {rating && (
                                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
                                            <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />
                                            <span>{rating.toFixed(1)}</span>
                                            {user_ratings_total && <span style={{ color: 'var(--text-tertiary)' }}>({user_ratings_total})</span>}
                                        </div>
                                    )}
                                </div>

                                {address && (
                                    <p className="flex items-start gap-2.5 text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                                        <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0 text-accent" />
                                        <span className="leading-relaxed">{address}</span>
                                    </p>
                                )}

                                {/* Descriptions & Reviews excerpt */}
                                {isLoadingDetails ? (
                                    <div className="animate-pulse flex flex-col gap-2 mb-6">
                                        <div className="h-3 bg-white/5 rounded w-full"></div>
                                        <div className="h-3 bg-white/5 rounded w-5/6"></div>
                                        <div className="h-3 bg-white/5 rounded w-4/6"></div>
                                    </div>
                                ) : detailedPlace?.reviews && detailedPlace.reviews.length > 0 && (
                                    <div className="mb-6 p-4 rounded-xl relative overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                                        <Quote className="absolute -top-2 -left-2 w-12 h-12 opacity-5" style={{ color: 'var(--text-primary)' }} />
                                        <p className="text-sm italic leading-relaxed relative z-10" style={{ color: 'var(--text-secondary)' }}>
                                            <span aria-hidden="true">&ldquo;</span>
                                            {detailedPlace.reviews[0].text}
                                            <span aria-hidden="true">&rdquo;</span>
                                        </p>
                                        <span className="block mt-2 text-xs font-medium" style={{ color: 'var(--text-tertiary)' }}>
                                            — {detailedPlace.reviews[0].author}
                                        </span>
                                    </div>
                                )}

                                <a
                                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(name + ' ' + (address || ''))}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-full py-3.5 rounded-xl flex items-center justify-center gap-2 font-medium text-white shadow-lg transition-transform hover:scale-[1.02] active:scale-[0.98]"
                                    style={{
                                        background: 'linear-gradient(135deg, var(--accent) 0%, #4F46E5 100%)'
                                    }}
                                >
                                    <Navigation className="w-5 h-5" />
                                    Get Directions
                                </a>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
