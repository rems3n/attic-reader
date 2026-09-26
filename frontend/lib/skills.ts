/**
 * Skills grid (/course/skills) and mistakes deck (/course/review?mode=mistakes):
 * pure helpers, tested in skills.test.ts.
 */

import { modality, skillLevel, type Item, type Skill, type SkillLevel, type SkillState } from "./course";
import type { ErrorEntry } from "./progress";

// ------------------------------------------------------------------- grid

export const LEVELS: SkillLevel[] = ["unseen", "weak", "learning", "strong", "mastered"];

export const LEVEL_LABEL: Record<SkillLevel, string> = {
  unseen: "Not met yet",
  weak: "Weak",
  learning: "Learning",
  strong: "Strong",
  mastered: "Mastered",
};

/** Families the taxonomy file does not list (skills from track files, adverbs, numerals). */
const EXTRA_FAMILY_LABEL: Record<string, string> = { adv: "Adverbs", num: "Numerals" };

export type SkillFilter = "all" | "met" | "weak";

export type SkillGroup = { id: string; label: string; skills: Skill[] };

export function familyOf(skillId: string): string {
  return skillId.split(".")[0];
}

/** Skills grouped by family, in the taxonomy's family order; unknown
 * prefixes become their own groups at the end. */
export function groupSkills(skills: Skill[], families: { id: string; label: string }[]): SkillGroup[] {
  const groups = new Map<string, SkillGroup>(families.map((f) => [f.id, { id: f.id, label: f.label, skills: [] }]));
  for (const s of skills) {
    const fam = familyOf(s.id);
    if (!groups.has(fam)) groups.set(fam, { id: fam, label: EXTRA_FAMILY_LABEL[fam] ?? fam.charAt(0).toUpperCase() + fam.slice(1), skills: [] });
    const g = groups.get(fam)!;
    if (!g.skills.some((x) => x.id === s.id)) g.skills.push(s);
  }
  return [...groups.values()].filter((g) => g.skills.length > 0);
}

/** "met" = practised at least once; "weak" = met but below strong (weak or learning). */
export function matchesFilter(state: SkillState | undefined, filter: SkillFilter): boolean {
  if (filter === "all") return true;
  if (!state || state.total === 0) return false;
  if (filter === "met") return true;
  const level = skillLevel(state);
  return level === "weak" || level === "learning";
}

export function filterGroups(groups: SkillGroup[], states: Record<string, SkillState>, filter: SkillFilter): SkillGroup[] {
  return groups.map((g) => ({ ...g, skills: g.skills.filter((s) => matchesFilter(states[s.id], filter)) })).filter((g) => g.skills.length > 0);
}

export function levelCounts(skills: Skill[], states: Record<string, SkillState>): Record<SkillLevel, number> {
  const out: Record<SkillLevel, number> = { unseen: 0, weak: 0, learning: 0, strong: 0, mastered: 0 };
  for (const s of skills) out[skillLevel(states[s.id])] += 1;
  return out;
}

/** "today", "yesterday", "3 days ago", else a short date. */
export function lastPractised(ts: number | undefined, now: number): string {
  if (!ts) return "never";
  const day = (t: number) => Math.floor(t / 86400000);
  const d = day(now) - day(ts);
  if (d <= 0) return "today";
  if (d === 1) return "yesterday";
  if (d < 30) return `${d} days ago`;
  return new Date(ts).toISOString().slice(0, 10);
}

// ---------------------------------------------------------- mistakes deck

/** An item rebuilt by POST /api/course/items. */
export type DeckItem = Item & {
  source?: string;
  origin?: { kind: "lesson" | "test" | "drill"; id: string; block: string | null; scope: string; generated: boolean };
  context?: { kind: "story" | "passage"; title?: string | null; text: string; glosses?: Record<string, string> | null } | null;
};

export type DeckCard = {
  /** `${lesson}|${item}`: the same generated id (drill3) can come from different lessons */
  key: string;
  item: string;
  lesson: string;
  answer: string;
  /** latest miss */
  at: number;
  misses: number;
  /** correct answers in a row since the latest miss */
  right: number;
  skills?: string[];
};

export const CLEAR_AFTER = 2;

export function deckKey(e: Pick<ErrorEntry, "item" | "lesson">): string {
  return `${e.lesson}|${e.item}`;
}

/** Uncleared mistakes, one card per item, most recent miss first. */
export function mistakeDeck(errors: ErrorEntry[]): DeckCard[] {
  const cards = new Map<string, DeckCard>();
  for (const e of errors) {
    if (e.cleared != null) continue;
    const key = deckKey(e);
    const cur = cards.get(key);
    if (!cur) {
      cards.set(key, { key, item: e.item, lesson: e.lesson, answer: e.answer, at: e.at, misses: 1, right: e.right ?? 0, skills: e.skills });
    } else {
      cur.misses += 1;
      if (e.at >= cur.at) Object.assign(cur, { answer: e.answer, at: e.at, right: e.right ?? 0, skills: e.skills ?? cur.skills });
    }
  }
  return [...cards.values()].sort((a, b) => b.at - a.at);
}

export function mistakeCount(errors: ErrorEntry[]): number {
  return mistakeDeck(errors).length;
}

/** Record a mistakes-deck answer on the uncleared entries of one card: a
 * right answer extends the run (and clears the card at CLEAR_AFTER), a wrong
 * one resets it. The caller adds a new error entry for the miss itself. */
export function markDeckAnswer(errors: ErrorEntry[], key: string, correct: boolean, now: number): ErrorEntry[] {
  const mine = errors.filter((e) => e.cleared == null && deckKey(e) === key);
  if (!mine.length) return errors;
  const latest = mine.reduce((a, b) => (b.at >= a.at ? b : a));
  const right = correct ? (latest.right ?? 0) + 1 : 0;
  const cleared = correct && right >= CLEAR_AFTER ? now : undefined;
  return errors.map((e) => {
    if (e.cleared != null || deckKey(e) !== key) return e;
    const next: ErrorEntry = { ...e, right };
    if (cleared != null) next.cleared = cleared;
    return next;
  });
}

/** Take cards out of the deck without practice (items that can no longer be rebuilt). */
export function dismissCards(errors: ErrorEntry[], keys: string[], now: number): ErrorEntry[] {
  const drop = new Set(keys);
  return errors.map((e) => (e.cleared == null && drop.has(deckKey(e)) ? { ...e, cleared: now } : e));
}

/** Refs for POST /api/course/items. */
export function deckRefs(cards: DeckCard[]): { id: string; key: string; lesson: string; skills?: string[] }[] {
  return cards.map((c) => ({ id: c.item, key: c.key, lesson: c.lesson, ...(c.skills?.length ? { skills: c.skills } : {}) }));
}

/** Whether a stored answer (JSON of the response) has the shape this item expects. */
export function answerFits(item: Item, answer: string): boolean {
  let r: unknown;
  try {
    r = JSON.parse(answer);
  } catch {
    return false;
  }
  const m = modality(item);
  const isObj = !!r && typeof r === "object" && !Array.isArray(r);
  if (m === "choice") return typeof r === "string" && (item.type === "true-false-grc" && !item.options ? r === "true" || r === "false" : (item.options ?? []).some((o) => o.id === r));
  if (m === "typed") return Array.isArray(r) && r.every((x) => typeof x === "string") && r.length === (item.gaps?.length ?? 1);
  if (m === "parse") return isObj && Object.keys(r as object).every((k) => (item.groups ?? []).some((g) => g.id === k));
  if (m === "locate") return Array.isArray(r) && r.every((x) => typeof x === "number");
  if (m === "reorder") return Array.isArray(r) && r.every((x) => typeof x === "string");
  if (m === "match") return isObj && Object.keys(r as object).every((k) => (item.pairs ?? []).some((p) => p.left === k));
  return typeof r === "boolean";
}

/** One item per card: a lesson's questions and quiz share ids (1.1:q1), so an
 * id can come back twice; the recorded answer's shape picks the right one. */
export function pickDeckItems(cards: DeckCard[], items: DeckItem[]): { items: DeckItem[]; keyOf: Map<string, string> } {
  const bySource = new Map<string, DeckItem[]>();
  for (const it of items) {
    const k = it.source ?? it.id;
    bySource.set(k, [...(bySource.get(k) ?? []), it]);
  }
  const out: DeckItem[] = [];
  const keyOf = new Map<string, string>();
  const used = new Set<string>();
  for (const card of cards) {
    const cands = bySource.get(card.key);
    if (!cands?.length) continue;
    const pick = cands.find((c) => answerFits(c, card.answer)) ?? cands[0];
    let id = pick.id;
    for (let n = 2; used.has(id); n += 1) id = `${pick.id}#${n}`;
    used.add(id);
    keyOf.set(id, card.key);
    out.push(id === pick.id ? pick : { ...pick, id });
  }
  return { items: out, keyOf };
}

/** Where an item came from, for the line above it. */
export function originLabel(item: DeckItem): string {
  const o = item.origin;
  if (!o) return "";
  if (o.generated) return `Fresh drill · words up to lesson ${o.scope}`;
  const block = o.block === "exercises" ? "exercises" : o.block === "questions" ? "questions" : o.block === "quiz" ? "quiz" : o.block ? `${o.block} section` : "";
  return o.kind === "test" ? `From ${o.id} · ${block}` : `From lesson ${o.id} · ${block}`;
}
