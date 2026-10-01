"use client";
import { wordCounts, weeklyWords } from "../../lib/dashboard";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { getCourse, getCourseSkill, type SkillDetail } from "../../lib/api";
import { isMastered, skillLevel, type CourseIndex, type Skill, type SkillLevel, type SkillState } from "../../lib/course";
import { loadProgress, type Progress } from "../../lib/progress";
import { filterGroups, groupSkills, lastPractised, levelCounts, LEVEL_LABEL, matchesFilter, mistakeCount, type SkillFilter } from "../../lib/skills";
import styles from "./skills.module.css";

const LESSONS_SHOWN = 8;

const FILTERS: { id: SkillFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "met", label: "Practised" },
  { id: "weak", label: "Needs practice" },
];

/** Topic progress summaries with optional, explicitly named skill details. */
export default function SkillsPage() {
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [progress] = useState<Progress>(() => loadProgress());
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<SkillFilter>("all");
  const [selected, setSelected] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, SkillDetail | "error">>({});
  const [now] = useState(() => Date.now());
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getCourse().then(setCourse).catch((e) => setError(e instanceof Error ? e.message : "Could not load the course"));
    try {
      const want = new URLSearchParams(window.location.search).get("skill");
      if (want) setSelected(want);
    } catch {
      /* no location (prerender) */
    }
  }, []);

  useEffect(() => {
    if (!selected || details[selected]) return;
    getCourseSkill(selected)
      .then((d) => setDetails((x) => ({ ...x, [selected]: d })))
      .catch(() => setDetails((x) => ({ ...x, [selected]: "error" })));
  }, [selected, details]);

  useEffect(() => {
    if (selected) panelRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selected]);

  const states = progress.course.skills;
  const groups = useMemo(() => (course ? groupSkills(course.skills, course.families) : []), [course]);
  const visible = useMemo(() => filterGroups(groups, states, filter), [groups, states, filter]);
  const all = useMemo(() => groups.flatMap((g) => g.skills), [groups]);
  const counts = useMemo(() => levelCounts(all, states), [all, states]);
  const filterCount = (f: SkillFilter) => all.filter((s) => matchesFilter(states[s.id], f)).length;
  const mistakes = mistakeCount(progress.course.errors);

  if (error) return <main className="shell"><p className="error">{error}</p></main>;
  if (!course) return <main className="shell"><p className="muted">Loading your skills…</p></main>;

  return (
    <main className="shell">
      <p className="crumbs"><Link href="/learn">← Course</Link></p>
      <section className="hero">
        <p className="eyebrow">ΤΕΧΝΑΙ · SKILLS</p>
        <h1>Your progress</h1>
        <p className="lede">Track completed lessons and grammar skills. Expand a topic to see what you have practised and what to work on next.</p>
      </section>

      <section className={`card ${styles.overview}`} aria-label="Learning progress">
        <ProgressBar label="Lessons completed" value={course.lesson_order.filter(id => progress.course.lessons[id]?.status === "done").length} total={course.lesson_order.length} note="Lessons marked complete in the course." />
        <ProgressBar label="Grammar skills practised" value={all.length - counts.unseen} total={all.length} note="Skills you have answered at least one exercise on; this measures coverage, not mastery." />
        <ProgressBar label="Grammar skills mastered" value={counts.mastered} total={all.length} note="At least 85% recent accuracy across 8 answers, with practice on days at least two days apart." />
      </section>
      {all.length === counts.unseen && <p className={styles.filterNote}>No grammar practice recorded yet. Complete lesson exercises to start tracking your skills. <Link href="/learn">Go to the course →</Link></p>}

      <section className="card"><h2>Words</h2><p>{wordCounts(progress).known} known · {wordCounts(progress).learning} learning</p><p>Weekly word goal: {weeklyWords(progress)} / {progress.course.goal.wordsPerWeek ?? 25} different words reviewed.</p><Link href="/words">Review vocabulary →</Link></section>

      <div className={styles.toolbar}>
        <div className="chips" role="group" aria-label="Show">
          {FILTERS.map((f) => (
            <button key={f.id} type="button" className={`chip ${filter === f.id ? "on" : ""}`} aria-pressed={filter === f.id} onClick={() => setFilter(f.id)}>
              {f.label} <span className={styles.chipCount}>{filterCount(f.id)}</span>
            </button>
          ))}
        </div>
        <Link href="/practice/review?mode=mistakes" className={styles.mistakesLink}>Mistakes deck <strong>{mistakes}</strong></Link>
      </div>
      {filter === "weak" && <p className={styles.filterNote}>Needs practice shows skills with recent accuracy below 75%.</p>}

      {visible.length === 0 && (
        <p className={`card ${styles.empty}`}>{filter === "all" ? "No skills in the course yet." : "Nothing here yet: skills appear once you answer an exercise that tests them."}</p>
      )}

      {visible.map((g) => {
        const fullGroup = groups.find(group => group.id === g.id)!;
        const met = fullGroup.skills.filter((s) => (states[s.id]?.total ?? 0) > 0).length;
        const mastered = fullGroup.skills.filter(s => isMastered(states[s.id])).length;
        const open = selected && g.skills.some((s) => s.id === selected) ? selected : null;
        return (
          <section key={g.id} className={styles.family} aria-labelledby={`fam-${g.id}`}>
            <div className={styles.familyHead}>
              <h2 id={`fam-${g.id}`}>{g.label}</h2>
              <span className={styles.familyCount}>{mastered} mastered</span>
            </div>
            <ProgressBar label={`${g.label} skills practised`} value={met} total={fullGroup.skills.length} />
            <details className={styles.skillDisclosure} open={open ? true : undefined}>
              <summary>View {g.skills.length} {filter === "all" ? "" : "matching "}skills</summary>
            <div className={styles.skillList}>
              {g.skills.map((s) => {
                const lv = skillLevel(states[s.id]);
                const on = selected === s.id;
                return (
                  <button
                    key={s.id}
                    type="button"
                    className={`${styles.skillRow} ${on ? styles.selected : ""}`}
                    aria-label={`${s.label}: ${LEVEL_LABEL[lv]}`}
                    aria-expanded={on}
                    aria-controls={on ? "skill-detail" : undefined}
                    title={`${s.label} · ${LEVEL_LABEL[lv]}`}
                    data-skill={s.id}
                    onClick={() => setSelected(on ? null : s.id)}
                  >
                    <span>{s.label}</span>
                    <span className={styles.skillStatus}>{LEVEL_LABEL[lv]}{states[s.id]?.total ? ` · ${Math.round(states[s.id].ewma * 100)}% accuracy` : ""}</span>
                  </button>
                );
              })}
            </div>
            </details>
            {open && (
              <div ref={panelRef}>
                <SkillPanel key={open} skill={g.skills.find((s) => s.id === open)!} state={states[open]} detail={details[open]} now={now} onClose={() => setSelected(null)} />
              </div>
            )}
          </section>
        );
      })}

      {selected && !all.some((s) => s.id === selected) && <p className="muted">No skill {selected} in the course.</p>}
    </main>
  );
}

function ProgressBar({ label, value, total, note }: { label: string; value: number; total: number; note?: string }) {
  const percent = total ? Math.round(value / total * 100) : 0;
  return <div className={styles.progressMetric}>
    <div className={styles.metricLabel}><span>{label}</span><strong>{percent}%</strong></div>
    <progress className={styles.progressBar} value={value} max={total || 1} aria-label={label} />
    <p className={styles.metricNote}>{value} of {total}{note ? ` · ${note}` : ""}</p>
  </div>;
}

function SkillPanel({ skill, state, detail, now, onClose }: { skill: Skill; state: SkillState | undefined; detail: SkillDetail | "error" | undefined; now: number; onClose: () => void }) {
  const lv: SkillLevel = skillLevel(state);
  const d = detail && detail !== "error" ? detail : null;
  const paradigm = d?.paradigm ?? skill.paradigm ?? null;
  const [allLessons, setAllLessons] = useState(false);
  const lessons = d ? (allLessons ? d.lessons : d.lessons.slice(0, LESSONS_SHOWN)) : [];
  return (
    <div id="skill-detail" className={styles.detail} role="region" aria-label={skill.label}>
      <div className={styles.detailTop}>
        <span className={styles.levelBadge}><span className={`${styles.swatch} ${styles[lv]}`} aria-hidden="true">{lv === "mastered" ? "✓" : ""}</span>{LEVEL_LABEL[lv]}</span>
        <button type="button" className={styles.close} onClick={onClose} aria-label="Close">×</button>
      </div>
      <h3 className={styles.detailTitle}>{skill.label}</h3>
      <p className={styles.skillId}>{skill.id}</p>

      <dl className={styles.stats}>
        <div><dt>Answers right</dt><dd>{state ? `${state.correct} / ${state.total}` : "0 / 0"}</dd></div>
        <div><dt>Recent accuracy</dt><dd>{state?.total ? `${Math.round(state.ewma * 100)} %` : "—"}</dd></div>
        <div><dt>Last practised</dt><dd>{lastPractised(state?.last, now)}</dd></div>
        <div><dt>Days practised</dt><dd>{state?.days.length ?? 0}</dd></div>
      </dl>
      {state && state.total > 0 && !isMastered(state) && (
        <p className={styles.hint}>
          {state.total < 8 ? `${8 - state.total} more ${8 - state.total === 1 ? "answer" : "answers"} before it can count as mastered.` : state.ewma < 0.85 ? "Keep practising: mastery needs 85 % recent accuracy." : "Come back on another day: mastery needs practice on days at least two days apart."}
        </p>
      )}

      <h4 className={styles.subhead}>Taught in</h4>
      {detail === undefined && <p className="muted">Loading…</p>}
      {detail === "error" && <p className="muted">Could not load the lessons for this skill.</p>}
      {d && d.lessons.length === 0 && <p className="muted">No authored lesson lists this skill yet.</p>}
      {d && d.lessons.length > 0 && (
        <ul className={styles.lessons}>
          {lessons.map((l) => (
            <li key={l.id}>
              <Link href={`/learn/lesson/${encodeURIComponent(l.id)}`}>
                <span className={styles.lessonId}>{l.id}</span>
                <span className={styles.lessonTitle}><span lang="grc">{l.title_grc}</span><span className={styles.lessonEn}>{l.title_en}</span></span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {d && d.lessons.length > LESSONS_SHOWN && (
        <button type="button" className={styles.more} aria-expanded={allLessons} onClick={() => setAllLessons(!allLessons)}>
          {allLessons ? "Show fewer" : `Show all ${d.lessons.length} lessons`}
        </button>
      )}

      <div className={styles.actions}>
        {d?.drillable && <Link href={`/practice/review?skills=${encodeURIComponent(skill.id)}`} className="primary buttonLike">Practise</Link>}
        {paradigm && <Link href={`/grammar/${encodeURIComponent(paradigm)}`} className="secondary buttonLike">See the paradigm</Link>}
      </div>
      {d && !d.drillable && <p className={styles.hint}>This skill is practised inside lessons and tests; there is no generated drill for it.</p>}
    </div>
  );
}
