/**
 * MediaHub Mobile Service Worker
 * Provides offline functionality and caching for PWA
 */

const CACHE_NAME = 'mediahub-mobile-v1.1.0';
const STATIC_CACHE_URLS = [
    '/m/',
    '/m/index.html',
    '/m/assets/css/mobile.css',
    '/m/assets/js/mobile-app.js',
    '/m/assets/icons/icon-192.png',
    '/m/assets/icons/icon-512.png',
    '/m/assets/icons/placeholder.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching static assets...');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Error caching static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Handle different types of requests
    if (request.method === 'GET') {
        if (isStaticAsset(url.pathname)) {
            // Static assets - cache first
            event.respondWith(cacheFirst(request));
        } else if (isAPIRequest(url.pathname)) {
            // API requests - network first with cache fallback
            event.respondWith(networkFirst(request));
        } else if (isStreamingRequest(url.pathname)) {
            // Streaming requests - network only (don't cache)
            event.respondWith(networkOnly(request));
        } else {
            // Other requests - network first
            event.respondWith(networkFirst(request));
        }
    }
});

// Cache first strategy for static assets
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Cache first strategy failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

// Network first strategy for API requests
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok && isCacheable(request)) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return new Response(JSON.stringify({
            success: false,
            error: 'Offline - no cached data available',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Network only strategy for streaming
async function networkOnly(request) {
    try {
        return await fetch(request);
    } catch (error) {
        return new Response('Streaming unavailable offline', { status: 503 });
    }
}

// Helper functions
function isStaticAsset(pathname) {
    return pathname.startsWith('/m/assets/') || 
           pathname.endsWith('.css') || 
           pathname.endsWith('.js') || 
           pathname.endsWith('.png') || 
           pathname.endsWith('.jpg') || 
           pathname.endsWith('.svg') ||
           pathname === '/m/' ||
           pathname === '/m/index.html';
}

function isAPIRequest(pathname) {
    return pathname.startsWith('/api/');
}

function isStreamingRequest(pathname) {
    return pathname.includes('/stream/') || 
           pathname.includes('/cast/') ||
           pathname.endsWith('.m3u8') ||
           pathname.endsWith('.ts');
}

function isCacheable(request) {
    const url = new URL(request.url);
    
    // Don't cache streaming or real-time data
    if (isStreamingRequest(url.pathname)) {
        return false;
    }
    
    // Don't cache POST requests
    if (request.method !== 'GET') {
        return false;
    }
    
    // Cache library and metadata requests
    if (url.pathname.includes('/library') || 
        url.pathname.includes('/metadata') ||
        url.pathname.includes('/smart_rails')) {
        return true;
    }
    
    return false;
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'download-queue') {
        event.waitUntil(syncDownloadQueue());
    } else if (event.tag === 'settings-sync') {
        event.waitUntil(syncSettings());
    }
});

async function syncDownloadQueue() {
    try {
        // Get queued downloads from IndexedDB
        const queuedDownloads = await getQueuedDownloads();
        
        for (const download of queuedDownloads) {
            try {
                const response = await fetch('/api/downloads/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(download)
                });
                
                if (response.ok) {
                    await removeFromQueue(download.id);
                }
            } catch (error) {
                console.error('Failed to sync download:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

async function syncSettings() {
    try {
        // Sync settings when back online
        const settings = await getOfflineSettings();
        
        if (settings) {
            const response = await fetch('/api/settings/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                await clearOfflineSettings();
            }
        }
    } catch (error) {
        console.error('Settings sync failed:', error);
    }
}

// IndexedDB helpers (simplified)
async function getQueuedDownloads() {
    // Implementation would use IndexedDB
    return [];
}

async function removeFromQueue(id) {
    // Implementation would use IndexedDB
}

async function getOfflineSettings() {
    // Implementation would use IndexedDB
    return null;
}

async function clearOfflineSettings() {
    // Implementation would use IndexedDB
}

// Push notification handling
self.addEventListener('push', (event) => {
    console.log('Push notification received:', event);
    
    const options = {
        body: 'MediaHub notification',
        icon: '/m/assets/icons/icon-192.png',
        badge: '/m/assets/icons/icon-192.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/m/'
        }
    };
    
    if (event.data) {
        const data = event.data.json();
        options.body = data.message || options.body;
        options.data = data;
    }
    
    event.waitUntil(
        self.registration.showNotification('MediaHub', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    const url = event.notification.data?.url || '/m/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes('/m/') && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window if app not open
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

console.log('MediaHub Mobile Service Worker loaded');
