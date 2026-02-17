'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Briefcase, Compass, User, Plus } from 'lucide-react';
import { useState, useEffect } from 'react';

const tabs = [
    { name: 'Home', href: '/home', icon: Home },
    { name: 'Trips', href: '/trips', icon: Briefcase },
    { name: 'Explore', href: '/explore', icon: Compass },
    { name: 'Profile', href: '/profile', icon: User },
];

export function BottomNav() {
    const pathname = usePathname();
    const [indicatorLeft, setIndicatorLeft] = useState(0);

    // Pages where we show the floating New Trip button
    const showNewTripButton = pathname === '/home' || pathname === '/trips';

    // Calculate active tab indicator position
    useEffect(() => {
        const activeIndex = tabs.findIndex(tab =>
            pathname === tab.href || pathname.startsWith(tab.href + '/')
        );
        if (activeIndex !== -1) {
            // Each tab is 25% wide (4 tabs), center the 3rem indicator
            const tabWidth = 25; // percentage
            const indicatorWidth = 3; // rem, converted to percentage later
            setIndicatorLeft(activeIndex * tabWidth + (tabWidth / 2));
        }
    }, [pathname]);

    return (
        <>
            {/* Floating New Trip Button */}
            {showNewTripButton && (
                <Link href="/chat">
                    <button
                        className="floating-btn btn-scale fixed bottom-20 right-4 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-lg"
                        style={{
                            background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)',
                            boxShadow: '0 4px 20px rgba(8, 145, 178, 0.4)'
                        }}
                    >
                        <Plus className="w-6 h-6 text-white" />
                    </button>
                </Link>
            )}

            {/* Bottom Navigation Bar */}
            <nav className="fixed bottom-0 left-0 right-0 z-40 glass safe-area-inset-bottom md:hidden"
                style={{
                    borderTop: '1px solid rgba(0,0,0,0.05)',
                    background: 'rgba(255, 255, 255, 0.95)'
                }}>
                <div className="relative flex justify-around items-center h-16 max-w-md mx-auto px-2">
                    {/* Active indicator */}
                    <div
                        className="absolute top-0 w-12 h-1 rounded-full transition-all duration-300 ease-out"
                        style={{
                            background: 'var(--accent)',
                            left: `calc(${indicatorLeft}% - 1.5rem)`
                        }}
                    />

                    {tabs.map((tab) => {
                        const isActive = pathname === tab.href || pathname.startsWith(tab.href + '/');

                        return (
                            <Link
                                key={tab.name}
                                href={tab.href}
                                className="relative flex flex-col items-center justify-center flex-1 h-full py-2"
                            >
                                <tab.icon
                                    className="w-5 h-5 transition-colors duration-200"
                                    style={{
                                        color: isActive ? 'var(--accent)' : 'var(--text-tertiary)'
                                    }}
                                />
                                <span
                                    className="text-xs mt-1 font-medium transition-colors duration-200"
                                    style={{
                                        color: isActive ? 'var(--accent)' : 'var(--text-tertiary)'
                                    }}
                                >
                                    {tab.name}
                                </span>
                            </Link>
                        );
                    })}
                </div>
            </nav>
        </>
    );
}

export default BottomNav;
