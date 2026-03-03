'use client';

import { useEffect } from 'react';

export function ServiceWorkerRegistration() {
    useEffect(() => {
        if (!('serviceWorker' in navigator)) return;

        const register = () => {
            navigator.serviceWorker.register('/service-worker.js').catch(() => {
                // Silent failure in production UX to avoid noisy console errors for users.
            });
        };

        window.addEventListener('load', register);
        return () => {
            window.removeEventListener('load', register);
        };
    }, []);

    return null;
}
