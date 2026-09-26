import { describe, expect, it } from "vitest";
import { familyMastery, gradeItem, isMastered, keyText, modality, placementDecision, seededShuffle, skillLevel, updateSkill, weakSkills, type Item } from "./course";

const base = { id: "x", skills: [] as string[] };

describe("gradeItem mirrors the backend", () => {
  it("choice", () => {
    const item: Item = { ...base, type: "cloze-choice", options: [{ id: "a", text: "ὁ" }, { id: "b", text: "ἡ" }], answer: "b" };
    expect(gradeItem(item, "b").correct).toBe(true);
    expect(gradeItem(item, "a").correct).toBe(false);
    expect(modality({ ...base, type: "true-false-grc", answer: "false" })).toBe("choice");
    expect(gradeItem({ ...base, type: "true-false-grc", answer: "false" }, "true").correct).toBe(false);
  });
  it("typed with gaps, movable nu, strictness", () => {
    const item: Item = { ...base, type: "cloze-type", gaps: [{ answers: ["γυνή"] }, { answers: ["ἐστί(ν)"] }] };
    const r = gradeItem(item, ["γυνη", "εστι"]);
    expect(r.correct).toBe(true);
    expect(r.gaps).toEqual([true, true]);
    expect(gradeItem({ ...item, strict_accents: true }, ["γυνη", "εστι"]).correct).toBe(false);
    expect(gradeItem(item, "γυνή").correct).toBe(false); // second gap missing
  });
  it("parse, locate, reorder, match, self", () => {
    expect(gradeItem({ ...base, type: "parse", answer: { case: "dat", number: "sg" } }, { case: "dat", number: "sg" }).correct).toBe(true);
    const loc = gradeItem({ ...base, type: "locate", answer: [0, 4] }, [4]);
    expect(loc.correct).toBe(false);
    expect(loc.missing).toEqual([0]);
    expect(gradeItem({ ...base, type: "reorder", tokens: [], answers: ["ὁ Ἀρίστων κεραμεύς ἐστιν"] }, ["ὁ", "Ἀρίστων", "κεραμεύς", "ἐστιν"]).correct).toBe(true);
    expect(gradeItem({ ...base, type: "match", pairs: [{ left: "ὁ", right: "κεραμεύς" }, { left: "ἡ", right: "γυνή" }] }, { ὁ: "κεραμεύς", ἡ: "γυνή" }).correct).toBe(true);
    expect(gradeItem({ ...base, type: "translate-en", model: "x" }, true)).toEqual({ correct: true, self: true });
  });
  it("keyText", () => {
    expect(keyText({ ...base, type: "cloze-choice", options: [{ id: "a", text: "ὁ" }], answer: "a" })).toBe("ὁ");
    expect(keyText({ ...base, type: "locate", sentence: "ἡ Χρυσὶς γυνή ἐστιν", answer: [0] })).toBe("ἡ");
    expect(keyText({ ...base, type: "parse", groups: [{ id: "case", label: "Case", options: [{ id: "dat", label: "dative" }] }], answer: { case: "dat" } })).toBe("dative");
  });
});

describe("mastery", () => {
  const day = 24 * 3600 * 1000;
  it("updates and masters over spaced days", () => {
    let s = updateSkill(undefined, true, 0);
    expect(s).toMatchObject({ correct: 1, total: 1, streak: 1, ewma: 1 });
    for (let i = 0; i < 6; i += 1) s = updateSkill(s, true, i * 3600 * 1000);
    expect(isMastered(s)).toBe(false); // one day only
    s = updateSkill(s, true, 3 * day);
    expect(s.total).toBe(8);
    expect(isMastered(s)).toBe(true);
    expect(skillLevel(s)).toBe("mastered");
    const miss = updateSkill(s, false, 3 * day + 1);
    expect(miss.streak).toBe(0);
    expect(miss.ewma).toBeLessThan(s.ewma);
  });
  it("levels, weak skills and family roll-up", () => {
    expect(skillLevel(undefined)).toBe("unseen");
    const skills = {
      "noun.decl2.dat.sg": updateSkill(undefined, false, 0),
      "verb.pres.act.ind.3sg": updateSkill(updateSkill(undefined, true, 0), true, 1),
      "art.nom.sg": updateSkill(undefined, true, 0),
    };
    expect(weakSkills(skills, 2)).toEqual(["noun.decl2.dat.sg", "art.nom.sg"]);
    const fam = familyMastery(skills);
    expect(fam.noun.total).toBe(1);
    expect(fam.verb.ewma).toBe(1);
  });
  it("seeded shuffle is stable", () => {
    expect(seededShuffle([1, 2, 3, 4, 5], 7)).toEqual(seededShuffle([1, 2, 3, 4, 5], 7));
    expect(seededShuffle([1, 2, 3, 4, 5], 7)).not.toEqual([1, 2, 3, 4, 5]);
  });
});

describe("placementDecision", () => {
  const blocks = [1, 2, 3].map((n) => ({ unit: n, title_grc: "", title_en: "", test: `unit-${n}`, scope: `${n}.4`, lessons: [], next_lesson: `${n + 1}.1`, items: [] }));
  it("asks for the next block while every block so far passed", () => {
    expect(placementDecision(blocks, [], 0.6, 3)).toEqual({ passed: null, next: 0 });
    const d = placementDecision(blocks, [[true, true, false, true]], 0.6, 3);
    expect(d.passed?.unit).toBe(1);
    expect(d.next).toBe(1);
  });
  it("stops on three misses in a row even with a passing score", () => {
    const d = placementDecision(blocks, [[true, true, true, true, true, false, false, false, true]], 0.6, 3);
    expect(d.passed).toBeNull();
    expect(d.next).toBeNull();
  });
  it("stops on a block under the pass score and keeps the last passed unit", () => {
    const d = placementDecision(blocks, [[true, true, true, true], [true, false, true, false]], 0.6, 3);
    expect(d.passed?.unit).toBe(1);
    expect(d.next).toBeNull();
  });
  it("ends after the last block", () => {
    const d = placementDecision(blocks, [[true], [true], [true]], 0.6, 3);
    expect(d.passed?.unit).toBe(3);
    expect(d.next).toBeNull();
  });
});
