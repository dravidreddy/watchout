'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

interface DestinationCardProps {
    name: string;
    image: string;
    tag?: string;
    rating?: number;
    distance?: string;
    onClick?: () => void;
}

export function DestinationCard({
    name,
    image,
    tag,
    rating,
    distance,
    onClick
}: DestinationCardProps) {
    return (
        <motion.div
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className="destination-card cursor-pointer"
            style={{ minWidth: '160px' }}
        >
            {/* Background Image */}
            <div className="absolute inset-0">
                <Image
                    src={image}
                    alt={name}
                    fill
                    sizes="(max-width: 768px) 160px, 200px"
                    className="object-cover"
                    priority={false}
                />
            </div>

            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

            {/* Content */}
            <div className="destination-card-content">
                {tag && (
                    <span
                        className="chip chip-accent text-xs mb-2"
                        style={{
                            background: 'var(--accent)',
                            backdropFilter: 'blur(8px)'
                        }}
                    >
                        {tag}
                    </span>
                )}

                <h3 className="font-semibold text-white text-lg">{name}</h3>

                {(rating || distance) && (
                    <div className="flex items-center gap-3 mt-1 text-white/80 text-sm">
                        {rating && (
                            <span className="flex items-center gap-1">
                                ⭐ {rating}
                            </span>
                        )}
                        {distance && (
                            <span>{distance}</span>
                        )}
                    </div>
                )}
            </div>
        </motion.div>
    );
}

// Wide card variant for seasonal picks
export function SeasonalCard({
    title,
    subtitle,
    image,
    onClick
}: {
    title: string;
    subtitle: string;
    image: string;
    onClick?: () => void;
}) {
    return (
        <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className="relative rounded-2xl overflow-hidden cursor-pointer h-36"
            style={{ boxShadow: 'var(--shadow-card)' }}
        >
            {/* Background */}
            <div className="absolute inset-0">
                <Image
                    src={image}
                    alt={title}
                    fill
                    sizes="(max-width: 768px) 100vw, 800px"
                    className="object-cover"
                    priority={false}
                />
            </div>

            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-black/60 to-transparent" />

            {/* Content */}
            <div className="absolute inset-0 p-4 flex flex-col justify-end">
                <h3 className="font-semibold text-white text-lg">{title}</h3>
                <p className="text-white/80 text-sm">{subtitle}</p>
            </div>
        </motion.div>
    );
}

export default DestinationCard;
