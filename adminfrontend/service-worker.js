const CACHE_NAME = 'rememory-cache-v3';
const PRECACHE_URLS = [
	'/', // 視需要加入要快取的靜態檔案路徑
	'/index.html',
	'/static/css/main.css',
	'/static/js/main.js'
];

// 後端 API 主機（開發時使用本機後端）
const BACKEND_ORIGIN = 'http://127.0.0.1:8020';

// 安裝階段：預快取
self.addEventListener('install', event => {
	console.log('[SW] install');
	event.waitUntil(
		caches.open(CACHE_NAME)
			.then(cache => cache.addAll(PRECACHE_URLS).catch(() => {
				console.warn('[SW] some precache resources failed to cache');
			}))
			.then(() => self.skipWaiting())
	);
});

// 啟用階段：清理舊快取並通知 clients 有新版
self.addEventListener('activate', event => {
	console.log('[SW] activate');
	event.waitUntil(
		caches.keys().then(keys => Promise.all(
			keys.map(k => {
				if (k !== CACHE_NAME) {
					console.log('[SW] deleting cache', k);
					return caches.delete(k);
				}
			})
		)).then(() => {
			// 讓新的 SW 立即接管所有頁面
			self.clients.claim();
			// 通知所有 clients 可更新（頁面可根據此訊息自行 reload）
			self.clients.matchAll().then(clients => {
				clients.forEach(client => {
					client.postMessage({ type: 'SW_UPDATED', message: 'New service worker activated. Please reload to use the latest version.' });
				});
			});
		})
	);
});

// 處理來自頁面的訊息，例如要求立即 skipWaiting
self.addEventListener('message', event => {
	if (!event.data) return;
	if (event.data.type === 'SKIP_WAITING') {
		self.skipWaiting();
	}
});

// fetch 處理：API 使用 network-first，其他靜態使用 cache-first
self.addEventListener('fetch', event => {
	const req = event.request;
	const url = new URL(req.url);

	// 忽略瀏覽器 擴充/第三方 內部資源請求
	if (url.protocol.startsWith('chrome-extension') || url.hostname === 'localhost' && url.port === '0') {
		return;
	}

	// 對 API 請求採用 network-first 策略
	if (url.pathname.startsWith('/api/')) {
		event.respondWith((async () => {
			const backendUrl = BACKEND_ORIGIN + url.pathname + url.search;
			try {
				// 建立 fetch 選項，複製 headers
				const fetchOptions = {
					method: req.method,
					headers: {},
					credentials: 'include',
					mode: 'cors'
				};
				req.headers.forEach((v, k) => { fetchOptions.headers[k] = v; });
				
				// 若有 body（非 GET/HEAD），嘗試複製
				if (req.method !== 'GET' && req.method !== 'HEAD') {
					try {
						const bodyBuf = await req.clone().arrayBuffer();
						fetchOptions.body = bodyBuf;
					} catch (e) {
						// 無法讀取 body，仍嘗試不帶 body 的請求
						console.warn('[SW] could not clone request body for forwarding', e);
					}
				}

				const networkResponse = await fetch(backendUrl, fetchOptions);
				return networkResponse;
			} catch (err) {
				console.warn('[SW] API fetch failed, trying cache or returning offline error', err);
				try {
					const cached = await caches.match(req);
					if (cached) return cached;
				} catch (e) {
					// ignore
				}
				return new Response(JSON.stringify({
					error: 'network_error',
					message: 'Unable to reach API. You appear to be offline or the server is unreachable.'
				}), {
					status: 503,
					headers: { 'Content-Type': 'application/json' }
				});
			}
		})());
		return;
	}

	// 靜態資源採 cache-first 策略
	event.respondWith(
		caches.match(req).then(cached => {
			if (cached) return cached;
			return fetch(req).then(networkResponse => {
				// 可選：把靜態資源加入快取
				if (req.method === 'GET' && networkResponse && networkResponse.status === 200 && req.destination !== 'document') {
					const respClone = networkResponse.clone();
					caches.open(CACHE_NAME).then(cache => {
						cache.put(req, respClone).catch(() => {/* ignore cache put errors */});
					});
				}
				return networkResponse;
			}).catch(err => {
				console.warn('[SW] Fetch failed for', req.url, err);
				// 若是文件請求，回傳離線 fallback 頁面（若有）
				if (req.mode === 'navigate' || req.destination === 'document') {
					// 嘗試從快取回傳 index.html
					return caches.match('/index.html').then(fallback => fallback || new Response('Offline', { status: 503 }));
				}
				// 其他資源直接回傳一個簡單的 503 回應
				return new Response('Service Unavailable', { status: 503 });
			});
		})
	);
});
