import { describe, expect, it } from "vitest";
import { emptyProgress } from "./progress";
import { newCard } from "./srs";
import {
  hasLearningProgress,
  weeklyMinutes,
  weeklyWords,
  wordCounts,
} from "./dashboard";
describe("dashboard metrics", () => {
  it("counts words once and requires an established review interval, not a first review", () => {
    const p = emptyProgress();
    p.cards = {
      "a:recognition": { ...newCard(0), updated: 1, interval: 28, reps: 3 },
      "a:production": { ...newCard(0), updated: 1, interval: 28, reps: 3 },
      "b:recognition": { ...newCard(0), updated: 1, interval: 1, reps: 1 },
      "c:production": { ...newCard(0), updated: 1, interval: 20, reps: 4 },
      "d:recognition": newCard(0),
    };
    expect(wordCounts(p)).toEqual({ known: 1, learning: 2 });
  });
  it("shows a dashboard for returning guests, including vocabulary-only learners", () => {
    const p = emptyProgress();
    expect(hasLearningProgress(p)).toBe(false);
    p.cards["word:recognition"] = { ...newCard(0), updated: 1 };
    expect(hasLearningProgress(p)).toBe(true);
  });
  it("counts only this UTC week through today, including a month boundary", () => {
    const p = emptyProgress();
    p.course.activity = [
      "2026-08-30",
      "2026-08-31",
      "2026-09-01",
      "2026-09-03",
    ].map((day) => ({ day, minutes: 15, items: 10 }));
    expect(weeklyMinutes(p, Date.parse("2026-09-02T12:00:00Z"))).toBe(30);
  });
});

it("counts unique words reviewed this week without double-counting directions", () => {
  const p = emptyProgress();
  const now = Date.parse("2026-09-02T12:00:00Z");
  p.cards = {
    "a:recognition": { ...newCard(now), updated: now },
    "a:production": { ...newCard(now), updated: now },
    "b:recognition": {
      ...newCard(now),
      updated: Date.parse("2026-08-30T12:00:00Z"),
    },
  };
  expect(weeklyWords(p, now)).toBe(1);
});
