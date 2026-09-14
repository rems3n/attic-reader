/**
 * Spaced repetition (SM-2 style), pure functions so it can be unit-tested.
 *
 * A card is one (word, card type) pair. `interval` is in days; `due` is a
 * millisecond timestamp. Grades: 0 again, 1 hard, 2 good, 3 easy.
 */

export type Grade = 0 | 1 | 2 | 3;

export type CardState = {
  ef: number; // ease factor, ≥ 1.3
  interval: number; // days until the next review after the last grade
  reps: number; // successful reviews in a row
  lapses: number;
  due: number; // ms epoch
  updated: number; // ms epoch of the last grade (used for merging)
};

export const CARD_TYPES = ["recognition", "production", "forms", "parts"] as const;
export type CardType = (typeof CARD_TYPES)[number];

const DAY = 24 * 60 * 60 * 1000;
const RELEARN = 10 * 60 * 1000;

export function newCard(now: number): CardState {
  return { ef: 2.5, interval: 0, reps: 0, lapses: 0, due: now, updated: 0 };
}

export function isNew(card: CardState | undefined): boolean {
  return !card || card.updated === 0;
}

export function grade(card: CardState | undefined, q: Grade, now: number): CardState {
  const c = card ? { ...card } : newCard(now);
  if (q === 0) {
    c.lapses += 1;
    c.reps = 0;
    c.interval = 0;
    c.ef = Math.max(1.3, c.ef - 0.2);
    c.due = now + RELEARN;
  } else {
    let interval: number;
    if (q === 1) {
      interval = c.reps === 0 ? 1 : Math.max(1, c.interval * 1.2);
      c.ef = Math.max(1.3, c.ef - 0.15);
    } else if (q === 2) {
      interval = c.reps === 0 ? 1 : c.reps === 1 ? 3 : c.interval * c.ef;
    } else {
      interval = c.reps === 0 ? 2 : c.reps === 1 ? 5 : c.interval * c.ef * 1.3;
      c.ef += 0.15;
    }
    c.reps += 1;
    c.interval = Math.round(interval * 10) / 10;
    c.due = now + c.interval * DAY;
  }
  c.updated = now;
  return c;
}

/** A session of at most `sessionSize` cards: everything due (oldest first)
 * takes priority, never-seen keys fill the rest in deck order. */
export function pickSession(
  keys: string[],
  cards: Record<string, CardState>,
  now: number,
  sessionSize: number,
): { due: string[]; fresh: string[] } {
  const size = Math.max(0, Math.floor(sessionSize));
  const due = keys
    .filter((k) => cards[k] && cards[k].updated > 0 && cards[k].due <= now)
    .sort((a, b) => cards[a].due - cards[b].due)
    .slice(0, size);
  const fresh = keys.filter((k) => isNew(cards[k])).slice(0, Math.max(0, size - due.length));
  return { due, fresh };
}

/** Fisher–Yates shuffle, then keep the two directions of one word apart:
 * a card whose `id` equals its predecessor's is swapped with the next
 * card of a different word. Pure; `rand` is injectable for tests. */
export function shuffleSession<T extends { id: string }>(items: T[], rand: () => number = Math.random): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  const clash = (k: number) => k > 0 && k < out.length && out[k].id === out[k - 1].id;
  for (let i = 1; i < out.length; i += 1) {
    if (!clash(i)) continue;
    for (let j = 0; j < out.length; j += 1) {
      if (j === i || j === i - 1) continue;
      [out[i], out[j]] = [out[j], out[i]];
      if (!clash(i) && !clash(i + 1) && !clash(j) && !clash(j + 1)) break;
      [out[i], out[j]] = [out[j], out[i]]; // revert and try the next candidate
    }
  }
  return out;
}

/** Merge two progress maps: the state with the newer `updated` wins per card. */
export function mergeCards(a: Record<string, CardState>, b: Record<string, CardState>): Record<string, CardState> {
  const out: Record<string, CardState> = { ...a };
  for (const [k, v] of Object.entries(b)) {
    if (!out[k] || v.updated > out[k].updated) out[k] = v;
  }
  return out;
}

export function cardKey(entryId: string, type: CardType): string {
  return `${entryId}:${type}`;
}

export function describeInterval(card: CardState | undefined, now: number): string {
  if (!card || card.updated === 0) return "new";
  const ms = card.due - now;
  if (ms <= 0) return "due";
  const days = ms / DAY;
  if (days < 1) return `${Math.max(1, Math.round(ms / 60000))} min`;
  if (days < 30) return `${Math.round(days)} d`;
  return `${Math.round(days / 30)} mo`;
}
