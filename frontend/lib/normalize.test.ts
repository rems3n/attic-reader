import { describe, expect, it } from "vitest";
import fixtures from "./normalize.fixtures.json";
import { answersMatch, expandMovable, normalizeAnswer, tokens } from "./normalize";

describe("normalizeAnswer matches the Python reference", () => {
  for (const c of fixtures.normalize) {
    it(`${JSON.stringify(c.text)} accents=${c.accents}`, () => {
      expect(normalizeAnswer(c.text, c.accents)).toBe(c.want);
    });
  }
});

describe("answersMatch matches the Python reference", () => {
  for (const c of fixtures.match) {
    it(`${JSON.stringify(c.given)} vs ${JSON.stringify(c.accepted)} accents=${c.accents}`, () => {
      expect(answersMatch(c.given, c.accepted, c.accents)).toBe(c.want);
    });
  }
});

it("expands movable nu and tokenizes", () => {
  expect(expandMovable("ἐστί(ν)")).toEqual(["ἐστίν", "ἐστί"]);
  expect(tokens("ἡ Χρυσὶς γυνή ἐστιν· ὁ Λύσις.")).toEqual(["ἡ", "Χρυσὶς", "γυνή", "ἐστιν", "ὁ", "Λύσις"]);
});
