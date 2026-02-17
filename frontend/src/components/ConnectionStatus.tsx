/**
 * Connection Status Indicator
 * Shows online/offline status
 */
'use client';

import { useState, useEffect } from 'react';

export default function ConnectionStatus() {
    const [isOnline, setIsOnline] = useState(true);
    const [showNotification, setShowNotification] = useState(false);

    useEffect(() => {
        // Check initial status
        setIsOnline(navigator.onLine);

        const handleOnline = () => {
            setIsOnline(true);
            setShowNotification(true);
            setTimeout(() => setShowNotification(false), 3000);
        };

        const handleOffline = () => {
            setIsOnline(false);
            setShowNotification(true);
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    if (!showNotification) return null;

    return (
        <div
            className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-full shadow-lg flex items-center gap-3 animate-slide-down ${isOnline
                    ? 'bg-green-500 text-white'
                    : 'bg-yellow-500 text-gray-900'
                }`}
        >
            <div
                className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-200' : 'bg-yellow-200'
                    }`}
            />
            <span className="font-medium">
                {isOnline ? 'Back Online' : 'You are Offline'}
            </span>
        </div>
    );
}
