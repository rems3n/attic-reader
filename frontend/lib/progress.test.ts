import { describe, expect, it } from "vitest";
import { updateSkill } from "./course";
import { emptyCourse, mergeCourse, mergeErrors, migrateProgress, recordTest, setLesson, streakDays, strictAccentsFor, DEFAULT_SETTINGS } from "./progress";

describe("progress v2", () => {
  it("migrates a v1 document", () => {
    const p = migrateProgress({ version: 1, cards: { "x:recognition": { ef: 2.5, interval: 1, reps: 1, lapses: 0, due: 1, updated: 1 } }, settings: { cardTypes: ["recognition"], newPerDay: 10 } as never, log: [] } as never);
    expect(p.version).toBe(2);
    expect(p.course.lessons).toEqual({});
    expect(p.settings.direction).toBe("grc-en");
    expect(p.settings.showEnglish).toBe(true);
    expect(Object.keys(p.cards)).toHaveLength(1);
  });
  it("records lessons and tests", () => {
    let c = setLesson(emptyCourse(), "1.1", { status: "done", best: 0.85 }, 10);
    expect(c.lessons["1.1"]).toMatchObject({ status: "done", best: 0.85, updated: 10 });
    c = recordTest(c, "unit-1", { at: 20, score: 0.7, misses: ["a"] }, 0.8);
    expect(c.tests["unit-1"].passedAt).toBeUndefined();
    c = recordTest(c, "unit-1", { at: 30, score: 0.9, misses: [] }, 0.8, 7);
    expect(c.tests["unit-1"].passedAt).toBe(30);
    expect(c.tests["unit-1"].retakeDue).toBe(30 + 7 * 86400000);
  });
  it("merges newest-wins and unions errors", () => {
    const a = setLesson(emptyCourse(), "1.1", { status: "in-progress", step: 3 }, 10);
    const b = setLesson(emptyCourse(), "1.1", { status: "done", best: 1 }, 20);
    a.skills["s"] = updateSkill(undefined, true, 0);
    b.skills["s"] = updateSkill(updateSkill(undefined, true, 0), false, 1);
    a.errors = [{ item: "i", lesson: "1.1", answer: "x", at: 1 }];
    b.errors = [{ item: "i", lesson: "1.1", answer: "x", at: 1 }, { item: "j", lesson: "1.1", answer: "y", at: 2 }];
    const m = mergeCourse(a, b);
    expect(m.lessons["1.1"].status).toBe("done");
    expect(m.skills["s"].total).toBe(2);
    expect(m.errors).toHaveLength(2);
    expect(mergeCourse(b, a).lessons["1.1"].status).toBe("done");
  });
  it("keeps old error entries through migration and merges mistakes-deck marks", () => {
    const old = migrateProgress({ version: 2, cards: {}, log: [], course: { errors: [{ item: "1.1:e1", lesson: "1.1", answer: '"a"', at: 5 }] } } as never);
    expect(old.course.errors).toEqual([{ item: "1.1:e1", lesson: "1.1", answer: '"a"', at: 5 }]);
    expect(old.course.errors[0].cleared).toBeUndefined();
    const base = { item: "1.1:e1", lesson: "1.1", answer: '"a"', at: 5 };
    const a = { ...emptyCourse(), errors: [{ ...base, right: 1 }] };
    const b = { ...emptyCourse(), errors: [{ ...base, right: 2, cleared: 40 }, { item: "2.1:e3", lesson: "2.1", answer: "[]", at: 7 }] };
    for (const m of [mergeCourse(a, b), mergeCourse(b, a)]) {
      expect(m.errors).toHaveLength(2);
      expect(m.errors[0]).toMatchObject({ item: "1.1:e1", right: 2, cleared: 40 });
      expect(m.errors[1].cleared).toBeUndefined();
    }
    // the earlier clearing wins when both sides cleared the entry
    const c = { ...emptyCourse(), errors: [{ ...base, right: 2, cleared: 30 }] };
    expect(mergeCourse(b, c).errors[0].cleared).toBe(30);
    // plain entries with no marks stay plain
    expect(mergeErrors([base], [base])).toEqual([base]);
  });
  it("streak and accent policy", () => {
    const day = 86400000;
    const now = Date.parse("2026-09-25T12:00:00Z");
    const c = { ...emptyCourse(), activity: [{ day: "2026-09-23", minutes: 1, items: 1 }, { day: "2026-09-24", minutes: 1, items: 1 }] };
    expect(streakDays(c, now)).toBe(2); // yesterday and the day before, nothing yet today
    expect(streakDays({ ...c, activity: [...c.activity, { day: "2026-09-25", minutes: 1, items: 1 }] }, now)).toBe(3);
    expect(streakDays(c, now + 2 * day)).toBe(0);
    expect(strictAccentsFor(DEFAULT_SETTINGS, "1.3")).toBe(false);
    expect(strictAccentsFor(DEFAULT_SETTINGS, "4.1")).toBe(true);
    expect(strictAccentsFor({ ...DEFAULT_SETTINGS, accents: "strict" }, "0.1")).toBe(true);
    expect(strictAccentsFor(DEFAULT_SETTINGS, "myth.1")).toBe(true);
  });
});
