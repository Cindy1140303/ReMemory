const CACHE_NAME = "life-map-v1";
const urlsToCache = [
  "./",
  "./index.html",
  "./manifest.json",
  "./assets/",
  "./static/",
  "./uploads/"
];

// 安裝時快取必要檔案
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// 攔截請求：離線時讀快取
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
