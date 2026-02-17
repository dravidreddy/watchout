/**
 * PWA Install Banner Component
 * Prompts users to install the app
 */
'use client';

import { useState, useEffect } from 'react';

export default function PWAInstallBanner() {
    const [showBanner, setShowBanner] = useState(false);
    const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

    useEffect(() => {
        const handler = (e: Event) => {
            e.preventDefault();
            setDeferredPrompt(e);
            setShowBanner(true);
        };

        window.addEventListener('beforeinstallprompt', handler);

        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            setShowBanner(false);
        }

        return () => {
            window.removeEventListener('beforeinstallprompt', handler);
        };
    }, []);

    const handleInstall = async () => {
        if (!deferredPrompt) return;

        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;

        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        }

        setDeferredPrompt(null);
        setShowBanner(false);
    };

    const handleDismiss = () => {
        setShowBanner(false);
        // Remember dismissal for 7 days
        localStorage.setItem('pwa-banner-dismissed', Date.now().toString());
    };

    // Don't show if dismissed recently
    useEffect(() => {
        const dismissed = localStorage.getItem('pwa-banner-dismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed);
            const sevenDays = 7 * 24 * 60 * 60 * 1000;
            if (Date.now() - dismissedTime < sevenDays) {
                setShowBanner(false);
            }
        }
    }, []);

    if (!showBanner) return null;

    return (
        <div className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl shadow-2xl p-5 z-50 animate-slide-up">
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-2xl">
                        ✈️
                    </div>
                    <div>
                        <h3 className="font-bold text-lg">Install Bharat Voyager</h3>
                        <p className="text-sm text-blue-100">Quick access & offline support</p>
                    </div>
                </div>
                <button
                    onClick={handleDismiss}
                    className="text-white/80 hover:text-white text-xl"
                    aria-label="Dismiss"
                >
                    ×
                </button>
            </div>

            <div className="space-y-2 mb-4 text-sm">
                <div className="flex items-center gap-2">
                    <span className="text-blue-200">✓</span>
                    <span>Launch from home screen</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-blue-200">✓</span>
                    <span>Works offline</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-blue-200">✓</span>
                    <span>Faster loading</span>
                </div>
            </div>

            <button
                onClick={handleInstall}
                className="w-full bg-white text-blue-600 font-semibold py-3 rounded-xl hover:bg-blue-50 transition-colors"
            >
                Install App
            </button>
        </div>
    );
}
