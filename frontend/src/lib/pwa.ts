/**
 * PWA Service Worker Registration Utility
 */

export function registerServiceWorker() {
    if (typeof window === 'undefined') {
        return; // Skip on server-side
    }

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker
                .register('/service-worker.js')
                .then((registration) => {
                    console.log('✅ Service Worker registered successfully:', registration.scope);

                    // Check for updates periodically
                    setInterval(() => {
                        registration.update();
                    }, 60000); // Check every minute

                    // Listen for updates
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        if (newWorker) {
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    // New service worker available
                                    showUpdateNotification();
                                }
                            });
                        }
                    });
                })
                .catch((error) => {
                    console.error('❌ Service Worker registration failed:', error);
                });
        });
    } else {
        console.warn('⚠️  Service Workers are not supported in this browser');
    }
}

function showUpdateNotification() {
    if (confirm('A new version is available! Reload to update?')) {
        window.location.reload();
    }
}

/**
 * Check if app can be installed (PWA install prompt)
 */
export function setupInstallPrompt() {
    if (typeof window === 'undefined') return;

    let deferredPrompt: any = null;

    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent the mini-infobar from appearing
        e.preventDefault();

        // Stash the event for later use
        deferredPrompt = e;

        // Show custom install button
        const installButton = document.getElementById('pwa-install-btn');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log(`User ${outcome} the install prompt`);
                    deferredPrompt = null;
                    installButton.style.display = 'none';
                }
            });
        }
    });

    // Log if app is already installed
    window.addEventListener('appinstalled', () => {
        console.log('✅ PWA installed successfully');
        deferredPrompt = null;
    });
}

/**
 * Check if user is online/offline
 */
export function setupConnectionMonitor() {
    if (typeof window === 'undefined') return;

    const updateOnlineStatus = () => {
        const isOnline = navigator.onLine;
        const statusEl = document.getElementById('connection-status');

        if (statusEl) {
            statusEl.textContent = isOnline ? 'Online' : 'Offline';
            statusEl.className = isOnline ? 'status-online' : 'status-offline';
        }

        // Show toast notification
        if (!isOnline) {
            console.warn('⚠️  You are offline. Some features may be unavailable.');
        } else {
            console.log('✅ Connection restored');
        }
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Initial check
    updateOnlineStatus();
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission() {
    if (typeof window === 'undefined' || !('Notification' in window)) {
        return false;
    }

    if (Notification.permission === 'granted') {
        return true;
    }

    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    return false;
}

/**
 * Subscribe to push notifications
 */
export async function subscribeToPush() {
    if (typeof window === 'undefined') return;

    try {
        const registration = await navigator.serviceWorker.ready;

        // Check if already subscribed
        let subscription = await registration.pushManager.getSubscription();

        if (!subscription) {
            // Subscribe to push notifications
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(
                    process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ''
                )
            });

            console.log('✅ Subscribed to push notifications');

            // Send subscription to backend
            await fetch('/api/v1/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(subscription)
            });
        }

        return subscription;
    } catch (error) {
        console.error('❌ Push subscription failed:', error);
        return null;
    }
}

// Helper: Convert VAPID key
function urlBase64ToUint8Array(base64String: string) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

/**
 * Initialize all PWA features
 */
export function initPWA() {
    registerServiceWorker();
    setupInstallPrompt();
    setupConnectionMonitor();
}
