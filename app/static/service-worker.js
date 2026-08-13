const CACHE_NAME='valifood-v1';
const STATIC_ASSETS=['/','/static/css/style.css','/static/js/app.js','/static/js/scanner.js','/static/js/products.js','/static/js/notifications.js','/static/icons/icon-192x192.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(STATIC_ASSETS)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(n=>Promise.all(n.filter(n=>n!==CACHE_NAME).map(n=>caches.delete(n)))));self.clients.claim();});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(caches.match(e.request).then(c=>{if(c)return c;return fetch(e.request).catch(()=>{if(e.request.mode==='navigate')return caches.match('/');});}));});
