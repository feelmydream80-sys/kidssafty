// sw.js - Service Worker for Kids Safety PWA
const CACHE_NAME = 'kids-safety-v1';

const PRECACHE_URLS = [
    '/',
    '/index.html',
    '/combined.html',
    '/manifest.json',
    '/css/style.css',
    '/js/app_main.js',
    '/js/config.js',
    '/js/dataLoader.js',
    '/js/dataUploader.js',
    '/js/eventHandlers.js',
    '/js/mapInit.js',
    '/js/missionSystem.js',
    '/js/settingsPanel.js',
    '/js/userLocation.js',
    '/js/zoneManager.js',
    '/js/alertSystem.js',
    '/data/locations.json',
    '/data/analysis/school_safety_grades.json',
    '/data/analysis/accessibility_score.json',
    '/data/analysis/risk_density_grid.json',
    '/data/analysis/safety_index.json',
    '/data/analysis/signal_priority.json',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    if (event.request.url.startsWith('chrome-extension://')) return;
    if (event.request.url.includes('/api/')) {
        event.respondWith(fetch(event.request).catch(() => new Response(JSON.stringify({offline: true}), {status: 503})));
        return;
    }
    event.respondWith(
        caches.match(event.request).then(cached => {
            const fetchPromise = fetch(event.request).then(response => {
                if (response && response.ok && event.request.url.startsWith(self.location.origin)) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => cached || new Response('Offline', {status: 503}));
            return cached || fetchPromise;
        })
    );
});
