/**
 * Bharat Voyager - Service Worker
 * Handles offline caching and background sync
 */

const CACHE_NAME = 'bharat-voyager-v1';
const RUNTIME_CACHE = 'bharat-voyager-runtime-v1';

// Assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/offline.html',
    '/manifest.json',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - network first, fall back to cache
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-HTTP requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API requests - network only with offline fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    return new Response(
                        JSON.stringify({
                            error: 'offline',
                            message: 'You are currently offline. This feature requires internet connection.'
                        }),
                        {
                            status: 503,
                            headers: { 'Content-Type': 'application/json' }
                        }
                    );
                })
        );
        return;
    }

    // Static assets - cache first, network fallback
    if (url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|gif|webp|ico)$/)) {
        event.respondWith(
            caches.match(request)
                .then((cached) => {
                    if (cached) {
                        return cached;
                    }
                    return fetch(request).then((response) => {
                        return caches.open(RUNTIME_CACHE).then((cache) => {
                            cache.put(request, response.clone());
                            return response;
                        });
                    });
                })
        );
        return;
    }

    // HTML pages - network first, cache fallback, offline page as last resort
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Cache successful responses
                if (response.ok) {
                    const responseClone = response.clone();
                    caches.open(RUNTIME_CACHE).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                return caches.match(request)
                    .then((cached) => {
                        if (cached) {
                            return cached;
                        }
                        // Show offline page for navigation requests
                        if (request.mode === 'navigate') {
                            return caches.match('/offline.html');
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Background sync for trip saves (when back online)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-trips') {
        event.waitUntil(syncTrips());
    }
});

async function syncTrips() {
    // Check IndexedDB for pending trip saves
    // Send them to backend when online
    console.log('[SW] Syncing pending trips...');
    // Implementation would go here
}

// Push notifications (for trip reminders, etc.)
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};

    const title = data.title || 'Bharat Voyager';
    const options = {
        body: data.body || 'You have a new notification',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: data.url || '/',
        actions: [
            { action: 'open', title: 'Open App' },
            { action: 'close', title: 'Dismiss' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    }
});

console.log('[SW] Service worker loaded');
