/**
 * Flash-card progress in the browser (localStorage) with an optional sync code
 * that backs the same document up on the server (see /api/progress).
 */

import { pullProgress, pushProgress } from "./api";
import { mergeCards, type CardState, type CardType } from "./srs";

export type Settings = {
  newPerDay: number;
  cardTypes: CardType[];
  syncCode: string;
};

export type Progress = {
  version: 1;
  cards: Record<string, CardState>;
  settings: Settings;
  log: { day: string; reviews: number; newCards: number }[];
  lastSync?: number;
};

const KEY = "attic.srs.v1";

export const DEFAULT_SETTINGS: Settings = { newPerDay: 12, cardTypes: ["recognition", "production"], syncCode: "" };

export function emptyProgress(): Progress {
  return { version: 1, cards: {}, settings: { ...DEFAULT_SETTINGS }, log: [] };
}

export function loadProgress(): Progress {
  try {
    const raw = typeof window !== "undefined" ? window.localStorage.getItem(KEY) : null;
    if (!raw) return emptyProgress();
    const parsed = JSON.parse(raw) as Progress;
    return { ...emptyProgress(), ...parsed, settings: { ...DEFAULT_SETTINGS, ...(parsed.settings ?? {}) } };
  } catch {
    return emptyProgress();
  }
}

export function saveProgress(p: Progress): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(p));
  } catch {
    /* storage unavailable (private mode): keep going in memory */
  }
}

export function today(now = Date.now()): string {
  return new Date(now).toISOString().slice(0, 10);
}

export function bumpLog(p: Progress, isNewCard: boolean, now = Date.now()): Progress {
  const day = today(now);
  const log = [...p.log];
  const last = log[log.length - 1];
  if (last && last.day === day) {
    log[log.length - 1] = { ...last, reviews: last.reviews + 1, newCards: last.newCards + (isNewCard ? 1 : 0) };
  } else {
    log.push({ day, reviews: 1, newCards: isNewCard ? 1 : 0 });
  }
  return { ...p, log: log.slice(-90) };
}

export function newCardsToday(p: Progress, now = Date.now()): number {
  const last = p.log[p.log.length - 1];
  return last && last.day === today(now) ? last.newCards : 0;
}

/** Push the local document to the server under the sync code. */
export async function syncPush(p: Progress): Promise<Progress> {
  const code = p.settings.syncCode.trim();
  if (!code) throw new Error("Set a sync code first.");
  const { saved_at } = await pushProgress(code, { cards: p.cards, settings: { ...p.settings, syncCode: "" }, log: p.log });
  const next = { ...p, lastSync: saved_at * 1000 };
  saveProgress(next);
  return next;
}

/** Merge the server copy into local state (newer card wins) and save. */
export async function syncPull(p: Progress): Promise<{ progress: Progress; found: boolean }> {
  const code = p.settings.syncCode.trim();
  if (!code) throw new Error("Set a sync code first.");
  const remote = await pullProgress<{ cards: Record<string, CardState>; log?: Progress["log"] }>(code);
  if (!remote) return { progress: p, found: false };
  const cards = mergeCards(p.cards, remote.document.cards ?? {});
  const log = remote.document.log && remote.document.log.length > p.log.length ? remote.document.log : p.log;
  const next = { ...p, cards, log, lastSync: remote.saved_at * 1000 };
  saveProgress(next);
  return { progress: next, found: true };
}

export function exportProgress(p: Progress): string {
  return JSON.stringify(p, null, 1);
}

export function importProgress(text: string, current: Progress): Progress {
  const parsed = JSON.parse(text) as Progress;
  const next = { ...current, cards: mergeCards(current.cards, parsed.cards ?? {}) };
  saveProgress(next);
  return next;
}
