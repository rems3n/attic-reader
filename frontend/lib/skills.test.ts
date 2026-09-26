import { describe, expect, it } from "vitest";
import { updateSkill, type Item, type SkillState } from "./course";
import type { ErrorEntry } from "./progress";
import { answerFits, deckRefs, dismissCards, filterGroups, groupSkills, lastPractised, levelCounts, markDeckAnswer, mistakeCount, mistakeDeck, pickDeckItems, type DeckItem } from "./skills";

const families = [{ id: "noun", label: "Nouns" }, { id: "verb", label: "Verbs" }, { id: "read", label: "Reading" }];
const skills = [
  { id: "noun.decl1.gen.sg", label: "1st gen sg" },
  { id: "verb.pres.act.ind.3sg", label: "3sg" },
  { id: "noun.decl2.dat.sg", label: "2nd dat sg" },
  { id: "adv.formation", label: "adverbs" },
  { id: "read.comprehension", label: "reading" },
];

function state(results: boolean[], start = 0): SkillState {
  let s: SkillState | undefined;
  results.forEach((r, i) => (s = updateSkill(s, r, start + i)));
  return s!;
}

describe("skills grid", () => {
  it("groups by family in taxonomy order, unknown prefixes last", () => {
    const g = groupSkills(skills, families);
    expect(g.map((x) => x.id)).toEqual(["noun", "verb", "read", "adv"]);
    expect(g[0].skills.map((s) => s.id)).toEqual(["noun.decl1.gen.sg", "noun.decl2.dat.sg"]);
    expect(g[3].label).toBe("Adverbs");
  });
  it("filters met and weak skills and counts levels", () => {
    const states: Record<string, SkillState> = {
      "noun.decl1.gen.sg": state([false, false, true]), // ewma well under 0.5
      "verb.pres.act.ind.3sg": state([true, true, true]),
    };
    const g = groupSkills(skills, families);
    expect(filterGroups(g, states, "all").flatMap((x) => x.skills)).toHaveLength(5);
    expect(filterGroups(g, states, "met").flatMap((x) => x.skills.map((s) => s.id))).toEqual(["noun.decl1.gen.sg", "verb.pres.act.ind.3sg"]);
    expect(filterGroups(g, states, "weak").flatMap((x) => x.skills.map((s) => s.id))).toEqual(["noun.decl1.gen.sg"]);
    expect(levelCounts(skills, states)).toEqual({ unseen: 3, weak: 1, learning: 0, strong: 1, mastered: 0 });
  });
  it("formats the last practice", () => {
    const now = Date.parse("2026-09-26T12:00:00Z");
    expect(lastPractised(undefined, now)).toBe("never");
    expect(lastPractised(now - 3600e3, now)).toBe("today");
    expect(lastPractised(now - 86400e3, now)).toBe("yesterday");
    expect(lastPractised(now - 5 * 86400e3, now)).toBe("5 days ago");
    expect(lastPractised(Date.parse("2026-07-01T10:00:00Z"), now)).toBe("2026-07-01");
  });
});

describe("mistakes deck", () => {
  const errors: ErrorEntry[] = [
    { item: "1.1:e2", lesson: "1.1", answer: '["x"]', at: 10 },
    { item: "drill3", lesson: "2.1", answer: '"a"', at: 20 },
    { item: "1.1:e2", lesson: "1.1", answer: '["y"]', at: 30 },
    { item: "drill3", lesson: "3.2", answer: '"b"', at: 40 },
    { item: "1.2:q1", lesson: "1.2", answer: '"b"', at: 5, cleared: 50 },
  ];

  it("groups uncleared misses per lesson + item, newest first", () => {
    const deck = mistakeDeck(errors);
    expect(deck.map((c) => c.key)).toEqual(["3.2|drill3", "1.1|1.1:e2", "2.1|drill3"]);
    expect(deck[1]).toMatchObject({ misses: 2, answer: '["y"]', at: 30, right: 0 });
    expect(mistakeCount(errors)).toBe(3);
    expect(deckRefs(deck)[1]).toEqual({ id: "1.1:e2", key: "1.1|1.1:e2", lesson: "1.1" });
  });

  it("clears a card after two right answers in a row, a miss resets the run", () => {
    let e = markDeckAnswer(errors, "1.1|1.1:e2", true, 100);
    expect(mistakeDeck(e).find((c) => c.key === "1.1|1.1:e2")?.right).toBe(1);
    e = markDeckAnswer(e, "1.1|1.1:e2", false, 110);
    expect(mistakeDeck(e).find((c) => c.key === "1.1|1.1:e2")?.right).toBe(0);
    e = markDeckAnswer(e, "1.1|1.1:e2", true, 120);
    e = markDeckAnswer(e, "1.1|1.1:e2", true, 130);
    expect(mistakeDeck(e).map((c) => c.key)).toEqual(["3.2|drill3", "2.1|drill3"]);
    expect(e.filter((x) => x.item === "1.1:e2").every((x) => x.cleared === 130)).toBe(true);
    // the already-cleared entry is untouched
    expect(e[4].cleared).toBe(50);
  });

  it("a new miss after clearing brings the item back", () => {
    let e = markDeckAnswer(markDeckAnswer(errors, "2.1|drill3", true, 1), "2.1|drill3", true, 2);
    expect(mistakeCount(e)).toBe(2);
    e = [...e, { item: "drill3", lesson: "2.1", answer: '"c"', at: 3 }];
    expect(mistakeDeck(e).find((c) => c.key === "2.1|drill3")).toMatchObject({ misses: 1, right: 0 });
  });

  it("dismisses cards", () => {
    expect(mistakeCount(dismissCards(errors, ["2.1|drill3", "3.2|drill3"], 9))).toBe(1);
  });

  it("picks the candidate whose shape fits the recorded answer", () => {
    const question: Item = { id: "1.1:q1", type: "answer-grc", skills: [], options: [{ id: "a", text: "x" }, { id: "b", text: "y" }], answer: "a" };
    const quiz: Item = { id: "1.1:q1", type: "cloze-type", skills: [], gaps: [{ answers: ["x"] }] };
    expect(answerFits(question, '"b"')).toBe(true);
    expect(answerFits(quiz, '"b"')).toBe(false);
    expect(answerFits(quiz, '["λόγος"]')).toBe(true);
    expect(answerFits({ id: "t", type: "true-false-grc", skills: [], answer: "true" }, '"false"')).toBe(true);
    expect(answerFits({ id: "p", type: "parse", skills: [], groups: [{ id: "case", label: "", options: [] }] }, '{"case":"gen"}')).toBe(true);
    expect(answerFits(quiz, "not json")).toBe(false);

    const cards = mistakeDeck([
      { item: "1.1:q1", lesson: "1.1", answer: '["λόγος"]', at: 2 },
      { item: "1.1:q1", lesson: "1.1-other", answer: '"b"', at: 1 },
    ]);
    const items: DeckItem[] = [
      { ...question, source: "1.1|1.1:q1" },
      { ...quiz, source: "1.1|1.1:q1" },
      { ...question, source: "1.1-other|1.1:q1" },
    ];
    const { items: picked, keyOf } = pickDeckItems(cards, items);
    expect(picked.map((i) => i.type)).toEqual(["cloze-type", "answer-grc"]);
    // ids stay unique within a session
    expect(picked.map((i) => i.id)).toEqual(["1.1:q1", "1.1:q1#2"]);
    expect(keyOf.get("1.1:q1#2")).toBe("1.1-other|1.1:q1");
  });
});
