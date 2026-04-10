const CACHE_NAME = 'rls-gnn-v1';
const ASSETS_TO_CACHE = [
  '/dashboard',
  '/drivers',
  '/handlers',
  '/static/icon-512x512.png',
  '/static/manifest.json'
];

// Install Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Interceptor
self.addEventListener('fetch', (event) => {
  // Only handle GET requests for caching
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        // Fallback for offline if page not in cache
        if (event.request.mode === 'navigate') {
          return caches.match('/drivers'); // Provide drivers portal as default offline page
        }
      });
    })
  );
});

// Background Sync for Offline Job Completion
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-job-updates') {
    event.waitUntil(syncJobUpdates());
  }
});

async function syncJobUpdates() {
  const db = await openDB();
  const pendingUpdates = await db.getAll('pending-updates');
  
  for (const update of pendingUpdates) {
    try {
      await fetch('/api/drivers/job/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update.data)
      });
      await db.delete('pending-updates', update.id);
      console.log('Successfully synced offline job update:', update.id);
    } catch (err) {
      console.error('Failed to sync offline update:', err);
    }
  }
}

// Push Notification Listener
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : { title: 'RLS GNN Update', body: 'New system update available.' };
  
  const options = {
    body: data.body,
    icon: '/static/icon-512x512.png',
    badge: '/static/icon-512x512.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/dashboard'
    },
    actions: [
      { action: 'open', title: 'Open App' },
      { action: 'close', title: 'Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'close') return;

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === event.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url);
      }
    })
  );
});

// Helper for IndexedDB (Simplified for SW)
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('RLS_PWA_DB', 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore('pending-updates', { keyPath: 'id', autoIncrement: true });
    };
    request.onsuccess = () => resolve({
      getAll: (store) => new Promise((res) => {
        const tx = request.result.transaction(store, 'readonly');
        tx.objectStore(store).getAll().onsuccess = (e) => res(e.target.result);
      }),
      delete: (store, id) => new Promise((res) => {
        const tx = request.result.transaction(store, 'readwrite');
        tx.objectStore(store).delete(id).onsuccess = () => res();
      })
    });
    request.onerror = () => reject(request.error);
  });
}
