import { describe, expect, it } from "vitest";
import type { CourseIndex, Track } from "./course";
import { lessonStatus, trackGate, trackLessonStatus, trackState } from "./courseState";
import { emptyCourse, type CourseProgress, type LessonStatus } from "./progress";

const lesson = (id: string, requires?: string, available = true) => ({ id, title_grc: id, title_en: id, available, requires, side: requires === "9.4" });
const track: Track = {
  id: "mythology",
  title_grc: "Μυθολογία",
  title_en: "Mythology",
  blurb: "",
  lessons: [lesson("myth.1", "9.4"), lesson("myth.2", "9.4"), lesson("myth.3", "9.4"), lesson("myth.4", "12.4"), lesson("myth.5", "12.4", false)],
  gate: "gate-myth",
  gate_available: true,
  side_after: "9.4",
  full_after: "12.4",
  side_lessons: 3,
};
const course: CourseIndex = {
  stages: [{ id: "2", title_grc: "", title_en: "", blurb: "", units: [{ id: "9", n: 9, title_grc: "", title_en: "", test: null, test_available: false, lessons: [lesson("9.4"), lesson("12.4")] }] }],
  tracks: [track],
  skills: [],
  families: [],
  lesson_order: ["9.4", "12.4"],
};
const DAY = 24 * 3600 * 1000;

function withDone(ids: string[], at = 0, status: LessonStatus = "done"): CourseProgress {
  const c = emptyCourse();
  for (const id of ids) c.lessons[id] = { status, best: 1, attempts: 1, lastDone: at, updated: at };
  return c;
}

describe("track gating", () => {
  it("locks every track lesson before 9.4", () => {
    const p = emptyCourse();
    expect(trackLessonStatus(p, track, "myth.1")).toBe("locked");
    expect(trackState(p, track).state).toBe("locked");
  });
  it("opens the side readings after 9.4, one after another", () => {
    const p = withDone(["9.4"]);
    expect(trackLessonStatus(p, track, "myth.1")).toBe("open");
    expect(trackLessonStatus(p, track, "myth.2")).toBe("locked");
    expect(lessonStatus(course, p, "myth.1")).toBe("open"); // routed through the track, not the main order
    expect(trackState(p, track)).toMatchObject({ state: "side", next: "myth.1" });
    const q = withDone(["9.4", "myth.1", "myth.2", "myth.3"]);
    expect(trackLessonStatus(q, track, "myth.4")).toBe("locked"); // needs 12.4
  });
  it("opens lesson 4 after 12.4 (or a placement skip) and counts done lessons", () => {
    const p = withDone(["9.4", "myth.1", "myth.2", "myth.3"]);
    p.lessons["12.4"] = { status: "skipped", best: 0, attempts: 0, updated: 0 };
    expect(trackLessonStatus(p, track, "myth.4")).toBe("open");
    expect(trackLessonStatus(p, track, "myth.5")).toBe("locked"); // not authored
    expect(trackState(p, track)).toMatchObject({ state: "open", done: 3, total: 4, next: "myth.4" });
  });
  it("gate follows the unit-test rule: all lessons done, then a day", () => {
    const now = 10 * DAY;
    const p = withDone(["9.4", "12.4", "myth.1", "myth.2", "myth.3", "myth.4"], now - DAY / 2);
    expect(trackGate(course, p, track, now).state).toBe("waiting");
    expect(trackGate(course, p, track, now + DAY).state).toBe("open");
    expect(trackGate(course, withDone(["myth.1"]), track, now).state).toBe("locked");
    expect(trackState(p, track).state).toBe("done");
  });
});
