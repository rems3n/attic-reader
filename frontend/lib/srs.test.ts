import { describe, expect, it } from "vitest";
import { cardKey, grade, mergeCards, newCard, pickSession, shuffleSession, type CardState } from "./srs";

const DAY = 86_400_000;
const now = 1_700_000_000_000;

describe("grade", () => {
  it("schedules 1 day then 3 days then ef-multiplied intervals", () => {
    let c = grade(undefined, 2, now);
    expect(c.interval).toBe(1);
    expect(c.due).toBe(now + DAY);
    c = grade(c, 2, now + DAY);
    expect(c.interval).toBe(3);
    c = grade(c, 2, now + 4 * DAY);
    expect(c.interval).toBeCloseTo(7.5, 1);
    expect(c.reps).toBe(3);
  });
  it("again resets reps, lowers ease and relearns in 10 minutes", () => {
    let c = grade(undefined, 2, now);
    c = grade(c, 0, now + DAY);
    expect(c.reps).toBe(0);
    expect(c.lapses).toBe(1);
    expect(c.ef).toBeCloseTo(2.3);
    expect(c.due - (now + DAY)).toBe(10 * 60 * 1000);
  });
  it("easy grows faster than good and ease never drops below 1.3", () => {
    const good = grade(grade(undefined, 2, now), 2, now + DAY);
    const easy = grade(grade(undefined, 3, now), 3, now + DAY);
    expect(easy.interval).toBeGreaterThan(good.interval);
    let c: CardState = newCard(now);
    for (let i = 0; i < 20; i += 1) c = grade(c, 0, now + i);
    expect(c.ef).toBe(1.3);
  });
});

describe("pickSession", () => {
  const cards: Record<string, CardState> = {
    a: { ...newCard(now), updated: 1, due: now - DAY },
    b: { ...newCard(now), updated: 1, due: now - 2 * DAY },
    c: { ...newCard(now), updated: 1, due: now + DAY },
  };
  it("returns due cards oldest first and fills the session with new cards", () => {
    const s = pickSession(["a", "b", "c", "d", "e", "f"], cards, now, 4);
    expect(s.due).toEqual(["b", "a"]);
    expect(s.fresh).toEqual(["d", "e"]);
  });
  it("never drops a due card for a new one, and caps due cards at the size", () => {
    expect(pickSession(["a", "b", "c", "d"], cards, now, 2)).toEqual({ due: ["b", "a"], fresh: [] });
    expect(pickSession(["a", "b", "c", "d"], cards, now, 1)).toEqual({ due: ["b"], fresh: [] });
  });
});

describe("shuffleSession", () => {
  // deterministic LCG so the test is repeatable
  function lcg(seed: number) {
    let x = seed;
    return () => {
      x = (x * 1664525 + 1013904223) % 4294967296;
      return x / 4294967296;
    };
  }
  const words = ["α", "β", "γ", "δ", "ε", "ζ", "η", "θ"];
  const both = words.flatMap((id) => [{ id, type: "recognition" }, { id, type: "production" }]);
  it("is a permutation that changes the order", () => {
    const out = shuffleSession(both, lcg(7));
    expect(out).toHaveLength(both.length);
    expect([...out].sort((x, y) => (x.id + x.type).localeCompare(y.id + y.type))).toEqual([...both].sort((x, y) => (x.id + x.type).localeCompare(y.id + y.type)));
    expect(out.map((x) => x.id + x.type)).not.toEqual(both.map((x) => x.id + x.type));
  });
  it("never puts the two directions of one word back to back", () => {
    for (let seed = 1; seed < 40; seed += 1) {
      const out = shuffleSession(both, lcg(seed));
      for (let i = 1; i < out.length; i += 1) expect(out[i].id).not.toBe(out[i - 1].id);
    }
  });
});

describe("mergeCards", () => {
  it("keeps the newer state per card", () => {
    const a = { x: { ...newCard(now), updated: 5, reps: 1 }, y: { ...newCard(now), updated: 9, reps: 3 } };
    const b = { x: { ...newCard(now), updated: 7, reps: 2 }, z: { ...newCard(now), updated: 1 } };
    const m = mergeCards(a, b);
    expect(m.x.reps).toBe(2);
    expect(m.y.reps).toBe(3);
    expect(m.z).toBeDefined();
  });
  it("builds keys", () => {
    expect(cardKey("λογος", "forms")).toBe("λογος:forms");
  });
});
