import { describe, expect, it } from "vitest";
import { familyMastery, gradeItem, isMastered, keyText, modality, seededShuffle, skillLevel, updateSkill, weakSkills, type Item } from "./course";

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
