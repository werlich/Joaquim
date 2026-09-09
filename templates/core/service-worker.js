/* Joaquim PWA — service worker nativo (sem Workbox). Cache {{ cache_version }}. */
const CACHE_VERSION = '{{ cache_version }}';
const STATIC_CACHE = 'joaquim-static-' + CACHE_VERSION;
const HTML_CACHE = 'joaquim-html-' + CACHE_VERSION;
const IMAGE_CACHE = 'joaquim-img-' + CACHE_VERSION;
const IMAGE_CACHE_MAX = 80;
const PRECACHE_URLS = {{ precache_urls|safe }};
const OFFLINE_URL = '/offline/';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(
      names
        .filter((name) => name.startsWith('joaquim-') && name !== STATIC_CACHE && name !== HTML_CACHE && name !== IMAGE_CACHE)
        .map((name) => caches.delete(name))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING' || (event.data && event.data.type === 'SKIP_WAITING')) {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Never intercept POST/PUT/PATCH/DELETE or non-GET.
  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  if (shouldBypass(url, request)) {
    return;
  }

  if (isStaticAsset(url) && !isImageRequest(request, url)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  if (isNavigation(request) || isPublicHtml(url.pathname)) {
    event.respondWith(networkFirstHtml(request, url));
    return;
  }

  if (isImageRequest(request, url) || url.pathname.startsWith('/media/')) {
    event.respondWith(staleWhileRevalidate(request, IMAGE_CACHE, IMAGE_CACHE_MAX));
  }
});

function shouldBypass(url, request) {
  const path = url.pathname;
  if (path.startsWith('/admin/')) return true;
  if (path.startsWith('/cha/acesso')) return true;
  if (path.indexOf('/reservar/') !== -1) return true;
  if (isVideoRequest(request, url)) return true;
  return false;
}

function isStaticAsset(url) {
  return url.pathname.startsWith('/static/');
}

function isPublicHtml(pathname) {
  return (
    pathname === '/' ||
    pathname.startsWith('/timeline') ||
    pathname.startsWith('/cha') ||
    pathname.startsWith('/recadinhos') ||
    pathname === OFFLINE_URL
  );
}

function isNavigation(request) {
  if (request.mode === 'navigate') return true;
  const accept = request.headers.get('accept') || '';
  return accept.indexOf('text/html') !== -1;
}

function isImageRequest(request, url) {
  if (request.destination === 'image') return true;
  return /\.(png|jpe?g|gif|webp|svg|ico|avif)$/i.test(url.pathname);
}

function isVideoRequest(request, url) {
  if (request.headers.has('Range') || request.headers.has('range')) return true;
  if (request.destination === 'video' || request.destination === 'audio') return true;
  return /\.(mp4|webm|ogg|m4v|mov)$/i.test(url.pathname);
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  const fresh = await fetch(request);
  if (fresh.ok) {
    cache.put(request, fresh.clone());
  }
  return fresh;
}

async function networkFirstHtml(request, url) {
  const cache = await caches.open(HTML_CACHE);
  try {
    const fresh = await fetch(request);
    if (fresh.ok) {
      cache.put(request, fresh.clone());
    }
    return fresh;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    if (url.pathname === OFFLINE_URL) {
      return new Response('Você está offline.', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      });
    }
    const offline = await caches.match(OFFLINE_URL);
    if (offline) return offline;
    return new Response('Você está offline.', {
      status: 503,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}

async function staleWhileRevalidate(request, cacheName, maxEntries) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then((fresh) => {
      if (fresh.ok) {
        cache.put(request, fresh.clone());
        trimCache(cache, maxEntries);
      }
      return fresh;
    })
    .catch(() => cached);
  return cached || network;
}

async function trimCache(cache, maxEntries) {
  const keys = await cache.keys();
  if (keys.length <= maxEntries) return;
  await Promise.all(keys.slice(0, keys.length - maxEntries).map((key) => cache.delete(key)));
}
