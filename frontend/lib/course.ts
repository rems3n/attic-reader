/**
 * Course types, local grading (mirrors backend/app/course/grade.py) and the
 * per-skill mastery model. Pure functions; tested in course.test.ts.
 */

import { answersMatch, tokens } from "./normalize";

// ----------------------------------------------------------------- content

export type Gloss = { word: string; kind: "pic" | "=" | "↔" | "<" | "|" | "en" | "note"; value: string };
export type StorySentence = { text: string; glosses?: Gloss[]; orig?: number[] };
export type OriginalText = { id: string; title: string | null; author: string | null; work: string | null; ref: string | null; blurb?: string | null; note?: string | null; source?: { edition?: string; license?: string; url?: string } | null; sentences: string[] };
export type ImageRecord = {
  id: string;
  kind: string;
  file: string | null;
  alt_grc: string;
  alt_en: string;
  credit: string;
  license: string;
  source_url: string | null;
  /** our own diagram, rendered from components/course/diagrams */
  svg?: boolean;
};
export type StoryParagraph = { image?: string | null; image_record?: ImageRecord | null; sentences: StorySentence[] };
export type LessonVocab = {
  id: string;
  lemma: string;
  headword: string;
  short: string;
  definition: string;
  kind: string;
  pos: string;
  ipa: string;
  pic: string | null;
  gloss_grc: string | null;
  source: string;
  cognates: { derivatives?: string[]; cognates?: string[] } | null;
};
export type Option = { id: string; text?: string; image?: string; audio?: string };
export type ParseGroup = { id: string; label: string; options: { id: string; label: string }[] };
export type Item = {
  id: string;
  type: string;
  prompt?: string;
  prompt_grc?: string | null;
  skills: string[];
  explain?: string;
  audio?: string | null;
  image?: string | null;
  generated?: boolean;
  // choice
  options?: Option[];
  answer?: unknown;
  // typed
  template?: string;
  gaps?: { answers: string[]; hint?: string }[];
  strict_accents?: boolean;
  lemma?: string;
  cell?: string;
  // parse
  form?: string;
  groups?: ParseGroup[];
  // locate
  sentence?: string;
  tokens?: string[];
  // reorder
  answers?: string[];
  // match
  pairs?: { left: string; right: string }[];
  // self-graded
  model?: string;
  bank?: string[];
};
export type Skill = { id: string; label: string; paradigm?: string | null };
export type Lesson = {
  id: string;
  title_grc: string;
  title_en: string;
  summary_grc?: string;
  summary_en?: string;
  cover?: string | null;
  cover_image: ImageRecord | null;
  caption_grc?: string;
  story: StoryParagraph[];
  story_text: string;
  original_text?: OriginalText | null;
  vocab: LessonVocab[];
  notice: string[];
  grammar: { md: string; paradigms: string[]; diagram?: string | null };
  exercises: Item[];
  questions: Item[];
  culture: { title: string; md: string; image?: string | null; image_record?: ImageRecord | null } | null;
  quiz: Item[];
  skills: Skill[];
  unit: { id: string; n: number; title_grc: string; title_en: string; test: string | null };
  stage: { id: string; title_grc: string; title_en: string };
  position: { index: number; prev: string | null; next: string | null; in_unit: number; unit_size: number };
};
export type LessonSummary = { id: string; title_grc: string; title_en: string; available: boolean; skills?: string[]; word_count?: number; exercise_count?: number; quiz_count?: number };
export type Unit = { id: string; n: number; title_grc: string; title_en: string; lessons: LessonSummary[]; test: string | null; test_available: boolean };
export type Stage = { id: string; title_grc: string; title_en: string; blurb: string; units: Unit[] };
export type Track = { id: string; title_grc: string; title_en: string; blurb: string; unlock_after_unit: number; lessons: string[] };
export type CourseIndex = { stages: Stage[]; tracks: Track[]; skills: Skill[]; families: { id: string; label: string }[]; lesson_order: string[] };
export type TestSection = { id: string; title: string; passage_title?: string; passage?: string; passage_source?: { author?: string; work?: string; ref?: string } | null; passage_note?: string; glosses?: Record<string, string>; items: Item[] };
export type CourseTest = { id: string; title_grc: string; title_en: string; scope: string; pass_score: number; unlock_after_hours?: number; retake_after_days?: number; blurb?: string; sections: TestSection[]; item_count: number };
export type PlacementBlock = { unit: number; title_grc: string; title_en: string; test: string; scope: string; lessons: string[]; next_lesson: string | null; items: Item[] };
export type Placement = { blocks: PlacementBlock[]; per_unit: number; stop_after_misses: number; pass_score: number; seed: number };

/** Walk the placement blocks in order with the outcomes so far: a block is
 * passed when its score reaches `passScore` and it never had `stopAfter`
 * misses in a row. Returns the highest passed block (or null) and whether
 * the walk should continue to the next block. */
export function placementDecision(blocks: PlacementBlock[], results: boolean[][], passScore: number, stopAfter: number): { passed: PlacementBlock | null; next: number | null } {
  let passed: PlacementBlock | null = null;
  for (let i = 0; i < blocks.length; i += 1) {
    const r = results[i];
    if (!r) return { passed, next: i };
    let run = 0;
    let broke = false;
    for (const ok of r) {
      run = ok ? 0 : run + 1;
      if (run >= stopAfter) broke = true;
    }
    const score = r.length ? r.filter(Boolean).length / r.length : 0;
    if (broke || score < passScore) return { passed, next: null };
    passed = blocks[i];
  }
  return { passed, next: null };
}

// ----------------------------------------------------------------- grading

export const CHOICE_TYPES = new Set(["pick-picture", "listen-pick", "cloze-choice", "true-false-grc", "bank-cloze", "label"]);
export const TYPED_TYPES = new Set(["cloze-type", "produce-form", "transform", "compose-grc", "dictation", "endings-cloze", "answer-grc"]);
export const SELF_TYPES = new Set(["translate-en", "describe-picture", "retell", "read-aloud", "continue-story"]);

export type Modality = "choice" | "typed" | "parse" | "locate" | "reorder" | "match" | "self";

export function modality(item: Item): Modality {
  const t = item.type;
  if (CHOICE_TYPES.has(t) || (t === "answer-grc" && item.options)) return "choice";
  if (TYPED_TYPES.has(t)) return "typed";
  if (t === "parse") return "parse";
  if (t === "locate") return "locate";
  if (t === "reorder") return "reorder";
  if (t === "match" || t === "word-family") return "match";
  return "self";
}

export type Response = string | string[] | number[] | Record<string, string> | boolean | null;
export type GradeResult = { correct: boolean; gaps?: boolean[]; groups?: Record<string, boolean>; missing?: number[]; extra?: number[]; pairs?: Record<string, boolean>; self?: boolean };

export function itemOptions(item: Item): Option[] {
  if (item.type === "true-false-grc" && !item.options) return [{ id: "true", text: "ἀληθές" }, { id: "false", text: "ψευδές" }];
  return item.options ?? [];
}

export function itemTokens(item: Item): string[] {
  return item.tokens ?? tokens(item.sentence ?? "");
}

export function gradeItem(item: Item, response: Response, accents = false): GradeResult {
  const m = modality(item);
  if (m === "choice") return { correct: response === item.answer };
  if (m === "typed") {
    const given = typeof response === "string" ? [response] : ((response as string[] | null) ?? []);
    const gaps = item.gaps ?? (item.answers ? [{ answers: item.answers }] : []);
    const strict = item.strict_accents ?? accents;
    const results = gaps.map((g, i) => answersMatch(given[i] ?? "", g.answers, strict));
    return { correct: results.every(Boolean), gaps: results };
  }
  if (m === "parse") {
    const answer = (item.answer ?? {}) as Record<string, string>;
    const given = (response && typeof response === "object" && !Array.isArray(response) ? response : {}) as Record<string, string>;
    const groups: Record<string, boolean> = {};
    for (const [g, v] of Object.entries(answer)) groups[g] = given[g] === v;
    return { correct: Object.values(groups).every(Boolean), groups };
  }
  if (m === "locate") {
    const want = new Set((item.answer as number[]) ?? []);
    const got = new Set(((response as number[] | null) ?? []).map(Number));
    const missing = [...want].filter((i) => !got.has(i)).sort((a, b) => a - b);
    const extra = [...got].filter((i) => !want.has(i)).sort((a, b) => a - b);
    return { correct: missing.length === 0 && extra.length === 0, missing, extra };
  }
  if (m === "reorder") {
    const given = Array.isArray(response) ? (response as string[]).join(" ") : String(response ?? "");
    return { correct: answersMatch(given, item.answers ?? [], accents) };
  }
  if (m === "match") {
    const given = (response && typeof response === "object" && !Array.isArray(response) ? response : {}) as Record<string, string>;
    const pairs: Record<string, boolean> = {};
    for (const p of item.pairs ?? []) pairs[p.left] = given[p.left] === p.right;
    return { correct: Object.values(pairs).every(Boolean), pairs };
  }
  return { correct: Boolean(response), self: true };
}

/** The key answer shown after a miss, as text. */
export function keyText(item: Item): string {
  const m = modality(item);
  if (m === "choice") {
    const o = itemOptions(item).find((x) => x.id === item.answer);
    return o?.text ?? o?.image ?? String(item.answer);
  }
  if (m === "typed") return (item.gaps ?? []).map((g) => g.answers[0]).join(" · ");
  if (m === "parse") {
    const a = (item.answer ?? {}) as Record<string, string>;
    return (item.groups ?? []).map((g) => g.options.find((o) => o.id === a[g.id])?.label ?? a[g.id]).join(", ");
  }
  if (m === "locate") {
    const toks = itemTokens(item);
    return ((item.answer as number[]) ?? []).map((i) => toks[i]).join(" · ");
  }
  if (m === "reorder") return item.answers?.[0] ?? "";
  if (m === "match") return (item.pairs ?? []).map((p) => `${p.left} — ${p.right}`).join(" · ");
  return item.model ?? "";
}

// ----------------------------------------------------------------- mastery

export type SkillState = { correct: number; total: number; streak: number; last: number; ewma: number; days: string[] };

export function dayOf(now: number): string {
  return new Date(now).toISOString().slice(0, 10);
}

export function updateSkill(prev: SkillState | undefined, correct: boolean, now: number): SkillState {
  const day = dayOf(now);
  const days = prev ? [...prev.days] : [];
  if (!days.includes(day)) days.push(day);
  const value = correct ? 1 : 0;
  return {
    correct: (prev?.correct ?? 0) + value,
    total: (prev?.total ?? 0) + 1,
    streak: correct ? (prev?.streak ?? 0) + 1 : 0,
    last: now,
    ewma: prev ? prev.ewma * 0.8 + value * 0.2 : value,
    days: days.slice(-30),
  };
}

const DAY = 24 * 60 * 60 * 1000;

/** Mastered = ewma ≥ 0.85 over ≥ 8 items seen on ≥ 2 days ≥ 2 days apart. */
export function isMastered(s: SkillState | undefined): boolean {
  if (!s || s.total < 8 || s.ewma < 0.85 || s.days.length < 2) return false;
  const first = Date.parse(s.days[0]);
  const last = Date.parse(s.days[s.days.length - 1]);
  return last - first >= 2 * DAY;
}

export type SkillLevel = "unseen" | "weak" | "learning" | "strong" | "mastered";

export function skillLevel(s: SkillState | undefined): SkillLevel {
  if (!s || s.total === 0) return "unseen";
  if (isMastered(s)) return "mastered";
  if (s.ewma >= 0.75) return "strong";
  if (s.ewma >= 0.5) return "learning";
  return "weak";
}

/** Skills to review, weakest first, from those the learner has met. */
export function weakSkills(skills: Record<string, SkillState>, limit = 4): string[] {
  return Object.entries(skills)
    .filter(([, s]) => s.total > 0 && !isMastered(s))
    .sort((a, b) => a[1].ewma - b[1].ewma || a[1].last - b[1].last)
    .slice(0, limit)
    .map(([id]) => id);
}

/** Roll skill states up to their family ("noun", "verb", …). */
export function familyMastery(skills: Record<string, SkillState>): Record<string, { total: number; ewma: number; n: number }> {
  const out: Record<string, { total: number; ewma: number; n: number }> = {};
  for (const [id, s] of Object.entries(skills)) {
    const fam = id.split(".")[0];
    const cur = out[fam] ?? { total: 0, ewma: 0, n: 0 };
    cur.total += s.total;
    cur.ewma = (cur.ewma * cur.n + s.ewma) / (cur.n + 1);
    cur.n += 1;
    out[fam] = cur;
  }
  return out;
}

// ----------------------------------------------------------------- scoring

export function scoreOf(results: { correct: boolean }[]): number {
  if (!results.length) return 0;
  return results.filter((r) => r.correct).length / results.length;
}

/** Deterministic shuffle (mulberry32) so a seeded test shows options in a stable order. */
export function seededShuffle<T>(items: T[], seed: number): T[] {
  let a = seed >>> 0;
  const rand = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const out = [...items];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export function hashString(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
