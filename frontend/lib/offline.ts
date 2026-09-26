/**
 * Offline support, page side. The service worker (public/sw.js) does the
 * caching; this module warms its caches for a lesson so it opens again
 * without signal, and holds the pure helpers shared with the worker.
 */
import type { ImageRecord, Lesson } from "./course";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Pace the course pre-renders and the lesson page starts at. */
export const OFFLINE_SPEED = 0.75;

/**
 * Cache key for a POST audio request (Cache Storage cannot key on a POST
 * body). `kind` is "speak" (POST /api/speak) or "stream"
 * (POST /api/synthesize/stream). public/sw.js carries a verbatim copy
 * between its `<sw-key>` markers; offline.test.ts checks the two agree.
 */
export function swCacheKey(apiBase: string, kind: string, text: unknown, speed: unknown): string {
  const base = String(apiBase || "").replace(/\/+$/, "");
  const s = Number(speed);
  const sp = Number.isFinite(s) ? String(s) : "1";
  return `${base}/__sw_${kind}?speed=${encodeURIComponent(sp)}&text=${encodeURIComponent(String(text == null ? "" : text).trim())}`;
}

/** The text useSpeaker() actually sends for a ▶ button (components/Speak.tsx). */
export function cleanSpeakText(text: string): string {
  return text.replace(/\(ν\)$/, "ν").replace(/[()]/g, "").split(" / ")[0].trim();
}

/** Same-origin picture URLs a lesson shows (cover, story, words, culture, diagram). */
export function lessonImageUrls(lesson: Lesson, images: ImageRecord[]): string[] {
  const byId = new Map(images.map((i) => [i.id, i]));
  const records: (ImageRecord | null | undefined)[] = [lesson.cover_image, lesson.culture?.image_record];
  const ids: (string | null | undefined)[] = [lesson.cover, lesson.culture?.image, lesson.grammar?.diagram];
  for (const p of lesson.story ?? []) {
    records.push(p.image_record);
    ids.push(p.image);
    for (const s of p.sentences) for (const g of s.glosses ?? []) if (g.kind === "pic") ids.push(g.value);
  }
  for (const v of lesson.vocab ?? []) ids.push(v.pic);
  for (const id of ids) if (id) records.push(byId.get(id));
  const urls = new Set<string>();
  for (const r of records) {
    if (!r || !r.file || r.license === "placeholder") continue;
    urls.add(r.file.startsWith("/") ? r.file : `/${r.file}`);
  }
  return [...urls];
}

/** Word clips worth having offline: the lesson's words as their ▶ plays them. */
export function lessonWordTexts(lesson: Lesson): string[] {
  const out = new Set<string>();
  for (const v of lesson.vocab ?? []) {
    const t = cleanSpeakText(v.lemma);
    if (t) out.add(t);
  }
  return [...out];
}

type NetInfo = { saveData?: boolean; type?: string; effectiveType?: string };

/** Warm only with signal, a controlling worker and no data-saver. */
export function shouldPrefetch(nav: { onLine?: boolean; connection?: NetInfo; serviceWorker?: unknown } | undefined): boolean {
  if (!nav || nav.onLine === false || !nav.serviceWorker) return false;
  const c = nav.connection;
  if (c?.saveData) return false;
  if (c?.effectiveType === "slow-2g" || c?.effectiveType === "2g") return false;
  return true;
}

/** Resolve once a service worker controls the page, or null after `ms`. */
function controller(ms: number): Promise<ServiceWorker | null> {
  const sw = navigator.serviceWorker;
  if (sw.controller) return Promise.resolve(sw.controller);
  return new Promise((resolve) => {
    const done = () => {
      clearTimeout(timer);
      sw.removeEventListener("controllerchange", done);
      resolve(sw.controller);
    };
    const timer = setTimeout(done, ms);
    sw.addEventListener("controllerchange", done);
  });
}

async function drain(res: Response): Promise<void> {
  // Reading the body to the end lets the worker finish storing it.
  if (res.ok) await res.arrayBuffer();
}

async function postJson(path: string, body: unknown): Promise<Response> {
  return fetch(`${API_BASE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

const warmed = new Set<string>();

/**
 * Fire-and-forget: fetch a lesson's JSON, the course index and image list,
 * its pictures, the story audio at 0.75× (the same POST the story reader
 * sends, so the worker's key matches) and its word clips, all through the
 * service worker so they land in its caches. Returns what it warmed.
 */
export async function prefetchLesson(id: string, lesson?: Lesson | null): Promise<{ images: number; words: number; story: boolean } | null> {
  if (typeof window === "undefined" || typeof navigator === "undefined") return null;
  if (!shouldPrefetch(navigator as unknown as Parameters<typeof shouldPrefetch>[0])) return null;
  if (warmed.has(id)) return null;
  warmed.add(id);
  try {
    if (!(await controller(15000))) {
      warmed.delete(id);
      return null;
    }
    const enc = encodeURIComponent(id);
    const [lessonRes, imagesRes] = await Promise.all([
      fetch(`${API_BASE}/api/course/lesson/${enc}`),
      fetch(`${API_BASE}/api/course/images`),
      fetch(`${API_BASE}/api/course`).then(drain),
    ]);
    const data: Lesson = lesson ?? (await lessonRes.json());
    if (lesson) await drain(lessonRes);
    const images: ImageRecord[] = imagesRes.ok ? ((await imagesRes.json()).images ?? []) : [];

    const pics = lessonImageUrls(data, images);
    await Promise.all(pics.map((u) => fetch(u).then(drain).catch(() => undefined)));

    let story = false;
    const text = data.story_text?.trim();
    if (text) {
      try {
        const res = await postJson("/api/synthesize/stream", { text: data.story_text, speed: OFFLINE_SPEED });
        await drain(res);
        story = res.ok;
      } catch {
        story = false;
      }
    }

    const words = lessonWordTexts(data);
    for (const w of words) {
      if (!navigator.onLine) break;
      await postJson("/api/speak", { text: w, speed: OFFLINE_SPEED }).then(drain).catch(() => undefined);
    }
    return { images: pics.length, words: words.length, story };
  } catch {
    warmed.delete(id);
    return null;
  }
}
