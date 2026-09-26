/**
 * Derived course state: which lessons are open, which test is unlocked,
 * what to suggest today. Pure functions over the course index and progress.
 */

import type { CourseIndex, LessonSummary, Track, Unit } from "./course";
import type { CourseProgress, LessonStatus } from "./progress";

const HOUR = 3600 * 1000;
const DAY = 24 * HOUR;
export const REREAD_DAYS = [1, 3, 7, 21];

export function lessonStatus(course: CourseIndex, progress: CourseProgress, id: string): LessonStatus {
  const stored = progress.lessons[id];
  if (stored && stored.status !== "locked") return stored.status;
  const track = trackOf(course, id);
  if (track) return trackLessonStatus(progress, track, id);
  const order = course.lesson_order;
  const idx = order.indexOf(id);
  if (idx <= 0) return "open";
  // open when the previous authored lesson is done or skipped
  for (let i = idx - 1; i >= 0; i -= 1) {
    const prev = progress.lessons[order[i]];
    const summary = findLesson(course, order[i]);
    if (summary && !summary.available) continue; // planned, not authored: skip over it
    return prev && (prev.status === "done" || prev.status === "skipped") ? "open" : "locked";
  }
  return "open";
}

export function findLesson(course: CourseIndex, id: string): LessonSummary | null {
  for (const s of course.stages) for (const u of s.units) for (const l of u.lessons) if (l.id === id) return l;
  for (const t of course.tracks ?? []) for (const l of t.lessons) if (l.id === id) return l;
  return null;
}

export function unitOf(course: CourseIndex, lessonId: string): Unit | null {
  for (const s of course.stages) for (const u of s.units) if (u.lessons.some((l) => l.id === lessonId)) return u;
  return null;
}

export type TestGate = { state: "locked" | "waiting" | "open" | "passed"; availableAt?: number; lastDone?: number };

/** A unit test opens when every authored lesson of the unit is done and
 * `unlockHours` have passed since the last one was finished. */
export function testGate(course: CourseIndex, progress: CourseProgress, unit: Unit, now: number, unlockHours = 24): TestGate {
  const lessons = unit.lessons.filter((l) => l.available);
  if (!unit.test || !unit.test_available || !lessons.length) return { state: "locked" };
  const passed = progress.tests[unit.test]?.passedAt;
  if (passed) return { state: "passed", lastDone: passed };
  const done = lessons.map((l) => progress.lessons[l.id]).filter((p) => p && (p.status === "done" || p.status === "skipped"));
  if (done.length < lessons.length) return { state: "locked" };
  const last = Math.max(...done.map((p) => p!.lastDone ?? p!.updated));
  const availableAt = last + unlockHours * HOUR;
  return availableAt <= now ? { state: "open", lastDone: last } : { state: "waiting", availableAt, lastDone: last };
}

/** The lesson to continue: an in-progress one, else the first open lesson
 * after the last one completed, else the first open lesson overall. */
export function nextLesson(course: CourseIndex, progress: CourseProgress): string | null {
  const order = course.lesson_order.filter((id) => findLesson(course, id)?.available);
  const inProgress = order.find((id) => progress.lessons[id]?.status === "in-progress");
  if (inProgress) return inProgress;
  const lastDone = order.reduce((acc, id, i) => (progress.lessons[id]?.status === "done" ? i : acc), -1);
  const after = order.slice(lastDone + 1).find((id) => lessonStatus(course, progress, id) === "open");
  return after ?? order.find((id) => lessonStatus(course, progress, id) === "open") ?? null;
}

export function lastDoneLesson(course: CourseIndex, progress: CourseProgress): string | null {
  const order = course.lesson_order;
  let best: string | null = null;
  for (const id of order) if (progress.lessons[id]?.status === "done") best = id;
  return best;
}

/** A finished story worth rereading today: done 1, 3, 7 or 21 days ago and
 * not reread since that milestone. Returns the most overdue candidate. */
export function rereadSuggestion(course: CourseIndex, progress: CourseProgress, now: number): { id: string; daysAgo: number } | null {
  let pick: { id: string; daysAgo: number } | null = null;
  for (const id of course.lesson_order) {
    const p = progress.lessons[id];
    if (!p || p.status !== "done" || !p.firstDone) continue;
    if (!id.match(/^\d+\.\d+$/) || id.startsWith("0.")) continue; // alphabet lessons have no story
    const daysAgo = Math.floor((now - p.firstDone) / DAY);
    const milestone = [...REREAD_DAYS].reverse().find((d) => d <= daysAgo);
    if (!milestone) continue;
    const rereads = progress.rereads[id] ?? [];
    const sinceMilestone = rereads.some((t) => t >= p.firstDone! + milestone * DAY);
    if (sinceMilestone) continue;
    if (!pick || daysAgo > pick.daysAgo) pick = { id, daysAgo };
  }
  return pick;
}

export function completedCount(course: CourseIndex, progress: CourseProgress): { done: number; total: number } {
  const ids = course.lesson_order.filter((id) => findLesson(course, id)?.available);
  return { done: ids.filter((id) => progress.lessons[id]?.status === "done").length, total: ids.length };
}

export function formatWait(ms: number): string {
  const h = Math.ceil(ms / HOUR);
  if (h < 1) return "a few minutes";
  if (h < 24) return `${h} h`;
  return `${Math.ceil(h / 24)} d`;
}

// ------------------------------------------------------------------ tracks

function finished(progress: CourseProgress, id: string): boolean {
  const s = progress.lessons[id]?.status;
  return s === "done" || s === "skipped";
}

export function trackOf(course: CourseIndex, lessonId: string): Track | null {
  return (course.tracks ?? []).find((t) => t.lessons.some((l) => l.id === lessonId)) ?? null;
}

/** A track lesson opens when the main-course lesson it builds on is finished
 * (9.4 for the side readings 1–3, 12.4 for the rest) and the track's
 * previous authored lesson is done. Tracks never wait on each other. */
export function trackLessonStatus(progress: CourseProgress, track: Track, id: string): LessonStatus {
  const stored = progress.lessons[id];
  if (stored && stored.status !== "locked") return stored.status;
  const idx = track.lessons.findIndex((l) => l.id === id);
  const summary = track.lessons[idx];
  if (!summary?.available) return "locked";
  if (!finished(progress, summary.requires ?? track.full_after)) return "locked";
  for (let i = idx - 1; i >= 0; i -= 1) {
    if (!track.lessons[i].available) continue;
    return finished(progress, track.lessons[i].id) ? "open" : "locked";
  }
  return "open";
}

/** The track as a unit, so the gate follows the unit-test rules (all lessons
 * done, then a day's wait). */
export function trackAsUnit(track: Track): Unit {
  return { id: track.id, n: 0, title_grc: track.title_grc, title_en: track.title_en, lessons: track.lessons, test: track.gate, test_available: track.gate_available };
}

export function trackGate(course: CourseIndex, progress: CourseProgress, track: Track, now: number): TestGate {
  return testGate(course, progress, trackAsUnit(track), now);
}

export type TrackState = {
  /** locked: before 9.4 · side: lessons 1–3 open · open: all open · done: every authored lesson done */
  state: "locked" | "side" | "open" | "done";
  done: number;
  total: number;
  next: string | null;
};

export function trackState(progress: CourseProgress, track: Track): TrackState {
  const authored = track.lessons.filter((l) => l.available);
  const done = authored.filter((l) => progress.lessons[l.id]?.status === "done").length;
  const inProgress = authored.find((l) => progress.lessons[l.id]?.status === "in-progress");
  const next = inProgress?.id ?? authored.find((l) => trackLessonStatus(progress, track, l.id) === "open")?.id ?? null;
  const state = authored.length > 0 && done === authored.length ? "done" : finished(progress, track.full_after) ? "open" : finished(progress, track.side_after) ? "side" : "locked";
  return { state, done, total: authored.length, next };
}
