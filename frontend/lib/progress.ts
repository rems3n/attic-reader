/**
 * Learner progress in the browser (localStorage) with an optional sync code
 * that backs the same document up on the server (see /api/progress).
 *
 * Version 2 adds the course: lesson status, test attempts, skill mastery,
 * an error log, reread timestamps, a daily goal and activity.
 */

import { pullProgress, pushProgress } from "./api";
import { type SkillState } from "./course";
import { mergeCards, type CardState, type CardType } from "./srs";

export type Direction = "grc-en" | "en-grc" | "both";

export type Settings = {
  /** Which way the basic cards face: Greek → English, English → Greek, or both (shuffled). */
  direction: Direction;
  /** Extra card types added on top of the direction: forms drill, principal parts. */
  cardTypes: CardType[];
  /** Cards per study session (due cards first, new cards fill the rest). */
  sessionSize: number;
  syncCode: string;
  /** Speak the Greek automatically when a card appears and when it is revealed. */
  autoSpeak: boolean;
  /** Show the English toggles (glosses, grammar terms) in lessons by default. */
  showEnglish: boolean;
  /** Typed answers must carry the right accents (auto: strict from Unit 4). */
  accents: "auto" | "lenient" | "strict";
};

export type LessonStatus = "locked" | "open" | "in-progress" | "done" | "skipped";
export type LessonProgress = { status: LessonStatus; best: number; attempts: number; step?: number; firstDone?: number; lastDone?: number; updated: number };
export type TestAttempt = { at: number; score: number; misses: string[] };
export type TestProgress = { attempts: TestAttempt[]; passedAt?: number; retakeDue?: number; updated: number };
export type ErrorEntry = {
  item: string;
  lesson: string;
  answer: string;
  at: number;
  /** skills of the missed item (recorded by review drills, whose ids are not rebuildable) */
  skills?: string[];
  /** mistakes deck: correct answers in a row since the miss */
  right?: number;
  /** mistakes deck: when the item left the deck (answered right twice in a row) */
  cleared?: number;
};

export type CourseProgress = {
  track?: string;
  placement?: { unit: number; at: number };
  lessons: Record<string, LessonProgress>;
  tests: Record<string, TestProgress>;
  skills: Record<string, SkillState>;
  errors: ErrorEntry[];
  rereads: Record<string, number[]>;
  goal: { minutesPerDay: number; wordsPerWeek?: number };
  activity: { day: string; minutes: number; items: number }[];
};

export type Progress = {
  version: 2;
  cards: Record<string, CardState>;
  settings: Settings;
  log: { day: string; reviews: number; newCards: number }[];
  lastSync?: number;
  course: CourseProgress;
};

const KEY = "attic.srs.v1"; // kept for continuity; the document carries its own version
const MAX_ERRORS = 500;

export const DEFAULT_SETTINGS: Settings = { direction: "both", cardTypes: [], sessionSize: 20, syncCode: "", autoSpeak: false, showEnglish: true, accents: "auto" };

export function emptyCourse(): CourseProgress {
  return { lessons: {}, tests: {}, skills: {}, errors: [], rereads: {}, goal: { minutesPerDay: 15 }, activity: [] };
}

export function emptyProgress(): Progress {
  return { version: 2, cards: {}, settings: { ...DEFAULT_SETTINGS }, log: [], course: emptyCourse() };
}

/** Bring a stored document (v1 or partial v2) up to the current shape. */
export function migrateProgress(raw: Partial<Progress> & { version?: number; course?: Partial<CourseProgress> }): Progress {
  const course = { ...emptyCourse(), ...(raw.course ?? {}) };
  return {
    ...emptyProgress(),
    ...raw,
    version: 2,
    cards: raw.cards ?? {},
    log: raw.log ?? [],
    settings: migrateSettings(raw.settings),
    course,
  };
}

export function loadProgress(): Progress {
  try {
    const raw = typeof window !== "undefined" ? window.localStorage.getItem(KEY) : null;
    if (!raw) return emptyProgress();
    return migrateProgress(JSON.parse(raw));
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

// ---------------------------------------------------------------- course ops

export function bumpActivity(course: CourseProgress, items: number, minutes: number, now = Date.now()): CourseProgress {
  const day = today(now);
  const activity = [...course.activity];
  const last = activity[activity.length - 1];
  if (last && last.day === day) activity[activity.length - 1] = { ...last, items: last.items + items, minutes: Math.round((last.minutes + minutes) * 10) / 10 };
  else activity.push({ day, items, minutes: Math.round(minutes * 10) / 10 });
  return { ...course, activity: activity.slice(-90) };
}

export function addError(course: CourseProgress, entry: ErrorEntry): CourseProgress {
  return { ...course, errors: [...course.errors, entry].slice(-MAX_ERRORS) };
}

export function setLesson(course: CourseProgress, id: string, patch: Partial<LessonProgress>, now = Date.now()): CourseProgress {
  const prev = course.lessons[id] ?? { status: "open" as LessonStatus, best: 0, attempts: 0, updated: 0 };
  return { ...course, lessons: { ...course.lessons, [id]: { ...prev, ...patch, updated: now } } };
}

export function recordTest(course: CourseProgress, id: string, attempt: TestAttempt, passScore: number, retakeAfterDays = 7): CourseProgress {
  const prev = course.tests[id] ?? { attempts: [], updated: 0 };
  const passed = attempt.score >= passScore;
  return {
    ...course,
    tests: {
      ...course.tests,
      [id]: {
        ...prev,
        attempts: [...prev.attempts, attempt].slice(-20),
        passedAt: passed ? prev.passedAt ?? attempt.at : prev.passedAt,
        retakeDue: passed && !prev.passedAt ? attempt.at + retakeAfterDays * 24 * 3600 * 1000 : prev.retakeDue,
        updated: attempt.at,
      },
    },
  };
}

/** Streak of consecutive days (ending today or yesterday) with any activity. */
export function streakDays(course: CourseProgress, now = Date.now()): number {
  const days = new Set(course.activity.map((a) => a.day));
  let streak = 0;
  const d = new Date(now);
  if (!days.has(today(now))) d.setDate(d.getDate() - 1);
  for (;;) {
    const key = d.toISOString().slice(0, 10);
    if (!days.has(key)) break;
    streak += 1;
    d.setDate(d.getDate() - 1);
  }
  return streak;
}

/** Merge two course documents (sync): newest wins per lesson/test, the
 * larger history wins per skill, errors are unioned. */
export function mergeCourse(a: CourseProgress, b: CourseProgress): CourseProgress {
  const lessons = { ...a.lessons };
  for (const [k, v] of Object.entries(b.lessons)) if (!lessons[k] || v.updated > lessons[k].updated) lessons[k] = v;
  const tests = { ...a.tests };
  for (const [k, v] of Object.entries(b.tests)) if (!tests[k] || v.updated > tests[k].updated) tests[k] = v;
  const skills = { ...a.skills };
  for (const [k, v] of Object.entries(b.skills)) if (!skills[k] || v.total > skills[k].total || (v.total === skills[k].total && v.last > skills[k].last)) skills[k] = v;
  const errors = mergeErrors(a.errors, b.errors);
  const rereads = { ...a.rereads };
  for (const [k, v] of Object.entries(b.rereads)) rereads[k] = [...new Set([...(rereads[k] ?? []), ...v])].sort();
  const activityByDay = new Map(a.activity.map((x) => [x.day, x]));
  for (const x of b.activity) {
    const cur = activityByDay.get(x.day);
    if (!cur || x.items > cur.items) activityByDay.set(x.day, x);
  }
  const activity = [...activityByDay.values()].sort((x, y) => x.day.localeCompare(y.day)).slice(-90);
  return { ...a, ...b, lessons, tests, skills, errors, rereads, activity, goal: a.goal ?? b.goal, track: a.track ?? b.track };
}

/** Union two error logs by `(item, at)`; the same entry on both sides keeps
 * the longer mistakes-deck run and the earliest `cleared` mark. */
export function mergeErrors(a: ErrorEntry[], b: ErrorEntry[]): ErrorEntry[] {
  const byKey = new Map<string, ErrorEntry>();
  for (const e of [...a, ...b]) {
    const k = `${e.item}|${e.at}`;
    const cur = byKey.get(k);
    if (!cur) {
      byKey.set(k, e);
      continue;
    }
    const right = Math.max(cur.right ?? 0, e.right ?? 0);
    const cleared = cur.cleared != null && e.cleared != null ? Math.min(cur.cleared, e.cleared) : cur.cleared ?? e.cleared;
    const merged: ErrorEntry = { ...cur };
    if (right) merged.right = right;
    if (cleared != null) merged.cleared = cleared;
    byKey.set(k, merged);
  }
  return [...byKey.values()].sort((x, y) => x.at - y.at).slice(-MAX_ERRORS);
}

// --------------------------------------------------------------------- sync

/** Push the local document to the server under the sync code. */
export async function syncPush(p: Progress): Promise<Progress> {
  const code = p.settings.syncCode.trim();
  if (!code) throw new Error("Set a sync code first.");
  const { saved_at } = await pushProgress(code, { version: 2, cards: p.cards, settings: { ...p.settings, syncCode: "" }, log: p.log, course: p.course });
  const next = { ...p, lastSync: saved_at * 1000 };
  saveProgress(next);
  return next;
}

/** Merge the server copy into local state (newer card wins) and save. */
export async function syncPull(p: Progress): Promise<{ progress: Progress; found: boolean }> {
  const code = p.settings.syncCode.trim();
  if (!code) throw new Error("Set a sync code first.");
  const remote = await pullProgress<{ cards: Record<string, CardState>; log?: Progress["log"]; course?: Partial<CourseProgress> }>(code);
  if (!remote) return { progress: p, found: false };
  const cards = mergeCards(p.cards, remote.document.cards ?? {});
  const log = remote.document.log && remote.document.log.length > p.log.length ? remote.document.log : p.log;
  const course = remote.document.course ? mergeCourse(p.course, { ...emptyCourse(), ...remote.document.course }) : p.course;
  const next = { ...p, cards, log, course, lastSync: remote.saved_at * 1000 };
  saveProgress(next);
  return { progress: next, found: true };
}

export function exportProgress(p: Progress): string {
  return JSON.stringify(p, null, 1);
}

export function importProgress(text: string, current: Progress): Progress {
  const parsed = migrateProgress(JSON.parse(text));
  const next = { ...current, cards: mergeCards(current.cards, parsed.cards ?? {}), course: mergeCourse(current.course, parsed.course) };
  saveProgress(next);
  return next;
}

/** Older documents stored recognition/production inside `cardTypes` and a
 * daily new-card limit; map them onto direction + extras + session size. */
export function migrateSettings(raw: (Partial<Settings> & { cardTypes?: string[]; newPerDay?: number }) | undefined): Settings {
  const src = raw ?? {};
  const types = Array.isArray(src.cardTypes) ? src.cardTypes : [];
  let direction: Direction = src.direction ?? DEFAULT_SETTINGS.direction;
  if (!src.direction && types.length) {
    const rec = types.includes("recognition");
    const prod = types.includes("production");
    direction = rec && !prod ? "grc-en" : prod && !rec ? "en-grc" : "both";
  }
  const extras = types.filter((t): t is CardType => t === "forms" || t === "parts");
  return {
    ...DEFAULT_SETTINGS,
    ...src,
    direction,
    cardTypes: extras,
    sessionSize: typeof src.sessionSize === "number" && src.sessionSize > 0 ? src.sessionSize : DEFAULT_SETTINGS.sessionSize,
  };
}

/** Whether typed answers are graded strictly for a given lesson, per settings. */
export function strictAccentsFor(settings: Settings, lessonId: string): boolean {
  if (settings.accents === "strict") return true;
  if (settings.accents === "lenient") return false;
  const unit = Number(lessonId.split(".")[0]);
  if (!Number.isFinite(unit)) return true; // track lessons (myth.1, gate scopes) come after Unit 9
  return unit >= 4;
}
