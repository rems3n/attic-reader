/* Attic Reader service worker (hand-written, no build step).
 *
 * What works offline once it has been seen with signal:
 *   - page shells: Home, Learn, Library, Practice, Words, Grammar, Help precached on install (with
 *     the /_next/static chunks their HTML references); every other page the
 *     learner opens is cached on the way (network-first, cache fallback,
 *     /offline.html for pages never opened);
 *   - /_next/static/* (content-hashed, immutable) and Google Fonts: cache-first;
 *   - course/vocab/grammar/library JSON from the API: stale-while-revalidate;
 *   - word/phrase audio (POST /api/speak) and story audio
 *     (POST /api/synthesize/stream, the NDJSON path the story reader plays
 *     from): cache-first under a synthetic GET key derived from the request
 *     body, since Cache Storage cannot key on a POST;
 *   - course pictures under /course/pics/: cache-first.
 * Never cached: /api/progress/*, /api/ocr, /api/synthesize, /api/synthesize/batch,
 * /api/course/check and every other POST. When the network is down those
 * get a JSON 503 whose `detail` the app shows as its error text.
 *
 * Bump VERSION to refresh page shells. Audio, API, and image caches keep
 * their independent version so a navigation update preserves downloads.
 */
"use strict";

const VERSION = "v2";
const PREFIX = "attic-";
const CACHES = {
  shell: `${PREFIX}shell-${VERSION}`,
  pages: `${PREFIX}pages-${VERSION}`,
  static: `${PREFIX}static-${VERSION}`,
  api: `${PREFIX}api-v1`,
  audio: `${PREFIX}audio-v1`,
  stream: `${PREFIX}stream-v1`,
  images: `${PREFIX}images-v1`,
};
const LIMITS = { pages: 80, static: 500, api: 400, audio: 400, stream: 40, images: 600 };
const MAX_STREAM_CHARS = 16 * 1024 * 1024; // one very long pasted passage at most
const NAV_TIMEOUT_MS = 5000; // flaky signal: fall back to the cached page after this

const SHELL_PAGES = ["/", "/learn", "/library", "/practice", "/words", "/grammar", "/help"];
const SHELL_FILES = [
  "/offline.html",
  "/manifest.webmanifest",
  "/icon-192.png",
  "/icon-512.png",
  "/apple-touch-icon.png",
  "/favicon-32.png",
];

// The API origin is passed by the page when it registers (/sw.js?api=…);
// NEXT_PUBLIC_API_BASE_URL is baked into the client bundle, not into this file.
const API_ORIGIN = (() => {
  try {
    const api = new URL(self.location.href).searchParams.get("api");
    return api ? new URL(api).origin : self.location.origin;
  } catch {
    return self.location.origin;
  }
})();

// <sw-key> — keep identical to swCacheKey() in lib/offline.ts (tested there).
function swCacheKey(apiBase, kind, text, speed) {
  const base = String(apiBase || "").replace(/\/+$/, "");
  const s = Number(speed);
  const sp = Number.isFinite(s) ? String(s) : "1";
  return `${base}/__sw_${kind}?speed=${encodeURIComponent(sp)}&text=${encodeURIComponent(String(text == null ? "" : text).trim())}`;
}
// </sw-key>

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const shell = await caches.open(CACHES.shell);
      // offline.html is the one file the worker cannot do without.
      await shell.add(new Request("/offline.html", { cache: "reload" }));
      await Promise.all(
        SHELL_FILES.slice(1).map((f) => shell.add(new Request(f, { cache: "reload" })).catch(() => undefined)),
      );
      await Promise.all(SHELL_PAGES.map((path) => cachePage(path, true).catch(() => undefined)));
      await self.skipWaiting();
    })(),
  );
});

/**
 * Store a page's HTML and the /_next/static files it references, so it can
 * render offline. Used for the shell on install and, via a message from the
 * page, for pages reached by client-side navigation (those never pass
 * through the navigation handler) and the first page, loaded before this
 * worker was in control. Skips pages cached in the last hour unless `force`.
 */
async function cachePage(path, force = false) {
  const url = new URL(path, self.location.origin);
  if (url.origin !== self.location.origin) return;
  url.hash = "";
  const pages = await caches.open(CACHES.pages);
  if (!force) {
    const hit = await pages.match(url.href, { ignoreVary: true });
    const date = hit && Date.parse(hit.headers.get("Date") || "");
    if (hit && (!date || Date.now() - date < 3600 * 1000)) return;
  }
  const res = await fetch(new Request(url.href, { cache: "no-cache", credentials: "same-origin" }));
  if (!res.ok || res.redirected || !(res.headers.get("Content-Type") || "").includes("text/html")) return;
  const html = await res.clone().text();
  await pages.put(url.href, res);
  await trim(CACHES.pages, LIMITS.pages);
  const assets = new Set();
  for (const m of html.matchAll(/["'(](\/_next\/static\/[^"'()\s\\]+)/g)) assets.add(m[1]);
  const statics = await caches.open(CACHES.static);
  await Promise.all(
    [...assets].map(async (a) => {
      if (await statics.match(a)) return;
      try {
        const r = await fetch(a);
        if (r.ok) await statics.put(a, r);
      } catch {
        /* best effort */
      }
    }),
  );
}

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keep = new Set(Object.values(CACHES));
      for (const name of await caches.keys()) {
        if (name.startsWith(PREFIX) && !keep.has(name)) await caches.delete(name);
      }
      if (self.registration.navigationPreload) {
        try {
          await self.registration.navigationPreload.disable();
        } catch {
          /* not supported */
        }
      }
      await self.clients.claim();
    })(),
  );
});

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

self.addEventListener("fetch", (event) => {
  const req = event.request;
  let url;
  try {
    url = new URL(req.url);
  } catch {
    return;
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return;

  const isApi = url.pathname.startsWith("/api/") && (url.origin === API_ORIGIN || url.origin === self.location.origin);
  if (isApi) {
    event.respondWith(handleApi(event, url));
    return;
  }
  if (req.method !== "GET") return;

  if (url.origin === self.location.origin) {
    if (req.mode === "navigate") {
      event.respondWith(handleNavigation(event, url));
      return;
    }
    // App Router flight requests: let them fail offline so Next falls back to
    // a full navigation, which the navigation handler serves from the cache.
    if (url.searchParams.has("_rsc") || req.headers.get("RSC")) return;
    if (url.pathname.startsWith("/_next/static/")) {
      event.respondWith(cacheFirst(event, req, CACHES.static, LIMITS.static));
      return;
    }
    if (url.pathname.startsWith("/course/pics/")) {
      event.respondWith(cacheFirst(event, req, CACHES.images, LIMITS.images));
      return;
    }
    if (SHELL_FILES.includes(url.pathname)) {
      event.respondWith(staleWhileRevalidate(event, req, CACHES.shell, 0));
    }
    return;
  }

  if (url.hostname === "fonts.googleapis.com") {
    event.respondWith(staleWhileRevalidate(event, req, CACHES.static, LIMITS.static));
    return;
  }
  if (url.hostname === "fonts.gstatic.com") {
    event.respondWith(cacheFirst(event, req, CACHES.static, LIMITS.static));
  }
});

const CACHEABLE_API_GET = [/^\/api\/course(\/|$)/, /^\/api\/vocab(\/|$)/, /^\/api\/grammar(\/|$)/, /^\/api\/library(\/|$)/, /^\/api\/analyze\/library$/];

function handleApi(event, url) {
  const req = event.request;
  const path = url.pathname;
  if (req.method === "GET" && CACHEABLE_API_GET.some((re) => re.test(path))) {
    return staleWhileRevalidate(event, req, CACHES.api, LIMITS.api, true);
  }
  if (req.method === "POST" && path === "/api/speak") {
    return handleClip(event, url, "speak", CACHES.audio, LIMITS.audio);
  }
  if (req.method === "POST" && path === "/api/synthesize/stream") {
    return handleClip(event, url, "stream", CACHES.stream, LIMITS.stream);
  }
  // Everything else goes to the network untouched; only the failure changes.
  return fetch(req).catch(() => offlineJson(path));
}

// ---------------------------------------------------------------------------
// Strategies
// ---------------------------------------------------------------------------

async function handleNavigation(event, url) {
  const req = event.request;
  const network = fetch(req);
  event.waitUntil(
    network
      .then(async (res) => {
        if (!res.ok || res.type !== "basic" || res.redirected) return;
        const copy = res.clone(); // before the page starts reading the body
        const cache = await caches.open(CACHES.pages);
        await cache.put(url.href, copy);
        await trim(CACHES.pages, LIMITS.pages);
      })
      .catch(() => undefined),
  );

  const timeout = new Promise((resolve) => setTimeout(() => resolve(null), NAV_TIMEOUT_MS));
  try {
    const first = await Promise.race([network, timeout]);
    if (first) return first;
    const cached = await cachedPage(url);
    if (cached) return cached;
    return await network;
  } catch {
    const cached = await cachedPage(url);
    if (cached) return cached;
    const offline = await caches.match("/offline.html", { cacheName: CACHES.shell });
    return offline || new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
}

async function cachedPage(url) {
  const pages = await caches.open(CACHES.pages);
  return (
    (await pages.match(url.href, { ignoreVary: true })) ||
    (await pages.match(url.href, { ignoreVary: true, ignoreSearch: true })) ||
    (url.pathname.endsWith("/") && url.pathname.length > 1
      ? await pages.match(url.origin + url.pathname.replace(/\/+$/, ""), { ignoreVary: true, ignoreSearch: true })
      : undefined)
  );
}

async function cacheFirst(event, req, cacheName, limit) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreVary: true });
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok || res.type === "opaque") {
    event.waitUntil(cache.put(req, res.clone()).then(() => trim(cacheName, limit)).catch(() => undefined));
  }
  return res;
}

async function staleWhileRevalidate(event, req, cacheName, limit, api = false) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreVary: true });
  const network = fetch(req);
  event.waitUntil(
    network
      .then(async (res) => {
        if (!(res.ok || (!api && res.type === "opaque"))) return;
        await cache.put(req, res.clone()); // synchronous clone: `cache` is already open
        await trim(cacheName, limit);
      })
      .catch(() => undefined),
  );
  if (hit) return hit;
  try {
    return await network;
  } catch {
    if (api) return offlineJson(new URL(req.url).pathname);
    throw new Error("offline");
  }
}

/** POST audio: cache-first under a GET key built from {text, speed}. */
async function handleClip(event, url, kind, cacheName, limit) {
  const req = event.request;
  let key = null;
  try {
    const body = await req.clone().json();
    if (body && typeof body.text === "string") key = swCacheKey(url.origin, kind, body.text, body.speed == null ? 1 : body.speed);
  } catch {
    key = null;
  }
  const cache = await caches.open(cacheName);
  if (key) {
    const hit = await cache.match(key);
    if (hit) {
      // LRU-ish: re-inserting moves the entry to the end of keys().
      event.waitUntil(cache.put(key, hit.clone()).catch(() => undefined));
      return hit;
    }
  }
  let res;
  try {
    res = await fetch(req);
  } catch {
    return offlineJson(url.pathname);
  }
  if (!key || !res.ok) return res;

  if (kind === "speak") {
    event.waitUntil(cache.put(key, res.clone()).then(() => trim(cacheName, limit)).catch(() => undefined));
    return res;
  }
  // NDJSON stream: hand one branch to the page as it arrives, keep the other
  // and store it only if the stream finished cleanly with every clip present.
  if (!res.body) return res;
  const [toPage, toCache] = res.body.tee();
  event.waitUntil(
    (async () => {
      try {
        const text = await new Response(toCache).text();
        if (text.length > MAX_STREAM_CHARS) return;
        if (!/"type":\s*"done"/.test(text) || /"type":\s*"error"/.test(text) || /"audio_base64":\s*null/.test(text)) return;
        await cache.put(key, new Response(text, { headers: { "Content-Type": "application/x-ndjson; charset=utf-8" } }));
        await trim(cacheName, limit);
      } catch {
        /* aborted mid-stream: nothing cached */
      }
    })(),
  );
  return new Response(toPage, { status: res.status, statusText: res.statusText, headers: res.headers });
}

async function trim(cacheName, limit) {
  if (!limit) return;
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - limit; i += 1) await cache.delete(keys[i]);
}

function offlineJson(path) {
  let detail = "You are offline. This needs a connection.";
  if (path === "/api/ocr") detail = "You are offline. Reading a photo (OCR) needs a connection.";
  else if (path.startsWith("/api/synthesize") || path === "/api/speak") detail = "You are offline. New audio needs a connection; audio you already played still works.";
  else if (path.startsWith("/api/progress")) detail = "You are offline. Sync needs a connection; your progress stays saved on this device.";
  else if (CACHEABLE_API_GET.some((re) => re.test(path))) detail = "You are offline, and this has not been saved on this device yet. Open it once with a connection to keep it for offline use.";
  return new Response(JSON.stringify({ detail, offline: true }), {
    status: 503,
    statusText: "Offline",
    headers: { "Content-Type": "application/json" },
  });
}

self.addEventListener("message", (event) => {
  const data = event.data;
  if (data === "skipWaiting") {
    self.skipWaiting();
  } else if (data && data.type === "cache-page" && typeof data.url === "string") {
    event.waitUntil(cachePage(data.url).catch(() => undefined));
  }
});
