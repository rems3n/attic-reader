import type { Progress } from "./progress";
import { today } from "./progress";

/** Count lemmas, not card directions. Known means an interval of at least 21 days. */
export function wordCounts(p: Progress) {
  const studied = new Set<string>();
  const known = new Set<string>();
  for (const [key, c] of Object.entries(p.cards)) {
    if (!c.updated) continue;
    const [id] = key.split(":");
    studied.add(id);
    if (c.interval >= 21 && c.reps > 0) known.add(id);
  }
  return { known: known.size, learning: studied.size - known.size };
}
export function hasLearningProgress(p: Progress) {
  return (
    Object.keys(p.course.lessons).length > 0 ||
    Object.keys(p.cards).length > 0 ||
    p.course.activity.length > 0 ||
    !!p.course.placement
  );
}
/** Match the existing progress log's UTC day convention; include Monday through today only. */
export function weeklyMinutes(p: Progress, now = Date.now()) {
  const d = new Date(now);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  const start = today(d.getTime());
  const end = today(now);
  return Math.round(
    p.course.activity
      .filter((a) => a.day >= start && a.day <= end)
      .reduce((sum, a) => sum + a.minutes, 0),
  );
}

/** Unique words reviewed this week, across all card directions. */
export function weeklyWords(p: Progress, now = Date.now()) {
  const d = new Date(now);
  d.setUTCHours(0, 0, 0, 0);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  const ids = new Set<string>();
  for (const [key, card] of Object.entries(p.cards)) {
    if (card.updated >= d.getTime() && card.updated <= now)
      ids.add(key.split(":")[0]);
  }
  return ids.size;
}
