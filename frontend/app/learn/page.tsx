"use client";

import Link from "next/link";
import { syllabus } from "../../lib/syllabus";
import { useEffect, useMemo, useState } from "react";
import { getCourse, getCourseImages } from "../../lib/api";
import { familyMastery, weakSkills, type CourseIndex, type ImageRecord } from "../../lib/course";
import { completedCount, findLesson, formatWait, lessonStatus, nextLesson, rereadSuggestion, testGate, trackOf, trackState } from "../../lib/courseState";
import { loadProgress, saveProgress, streakDays, type Progress } from "../../lib/progress";
import { mistakeCount } from "../../lib/skills";
import { isNew } from "../../lib/srs";
import { PageError, PageLoading } from "../../components/PageState";

export default function CourseHome() {
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [error, setError] = useState("");
  const [now] = useState(() => Date.now());

  useEffect(() => {
    getCourse().then(setCourse).catch((e) => setError(e instanceof Error ? e.message : "Could not load the course"));
    getCourseImages().then(setImages).catch(() => setImages([]));
  }, []);
  useEffect(() => saveProgress(progress), [progress]);

  const cp = progress.course;
  // continue: a track lesson in progress, else the main course, else the chosen track
  const chosenTrack = course?.tracks.find((t) => t.id === cp.track) ?? null;
  const trackInProgress = course?.tracks.flatMap((t) => t.lessons).find((l) => cp.lessons[l.id]?.status === "in-progress")?.id ?? null;
  const continueId = course ? trackInProgress ?? nextLesson(course, cp) ?? (chosenTrack ? trackState(cp, chosenTrack).next : null) : null;
  const counts = course ? completedCount(course, cp) : { done: 0, total: 0 };
  const dueCards = useMemo(() => Object.values(progress.cards).filter((c) => !isNew(c) && c.due <= now).length, [progress.cards, now]);
  const reread = course ? rereadSuggestion(course, cp, now) : null;
  const weak = weakSkills(cp.skills, 4);
  const mistakes = mistakeCount(cp.errors);
  const metSkills = Object.values(cp.skills).filter((s) => s.total > 0).length;
  const families = familyMastery(cp.skills);
  const streak = streakDays(cp, now);
  const todayMinutes = cp.activity.find((a) => a.day === new Date(now).toISOString().slice(0, 10))?.minutes ?? 0;

  if (error) return <PageError message={error} back={{ href: "/library", label: "Open the Library instead" }} />;
  if (!course) return <PageLoading label="Loading the course…" />;

  const continueLesson = continueId ? findLesson(course, continueId) : null;
  const continueState = continueId ? cp.lessons[continueId] : undefined;
  const skillLabel = (id: string) => course.skills.find((s) => s.id === id)?.label ?? id;

  return (
    <main className="shell courseHome">
      <section className="hero">
        <p className="eyebrow">ΜΑΘΗΜΑΤΑ · A COURSE IN CLASSICAL ATTIC</p>
        <h1>Course syllabus</h1>
        <p className="lede">Learn Classical Attic Greek from the alphabet to supported reading of original authors. See the grammar, vocabulary and reading skills covered in every unit, including units you have not unlocked yet.</p>
        <nav className="quickLinks" aria-label="Course pages">
          <ul>
            <li><a href="#units">Unit syllabus</a></li>
            <li><a href="#tracks">Reading specialisations</a></li>
            <li><Link href="/progress">Skills</Link></li>
            <li><Link href="/learn/placement">Placement test</Link></li>
            <li><Link href="/learn/credits">Image credits</Link></li>
          </ul>
        </nav>
      </section>

      <section className="todayRow">
        <div className="statTile">
          <span className="statLabel">Today</span>
          <span className="statValue">{todayMinutes} <small>/ {cp.goal.minutesPerDay} min</small></span>
          <div className="meter" aria-hidden="true"><div style={{ width: `${Math.min(100, (todayMinutes / Math.max(1, cp.goal.minutesPerDay)) * 100)}%` }} /></div>
        </div>
        <div className="statTile">
          <span className="statLabel">Streak</span>
          <span className="statValue">{streak} <small>d</small></span>
        </div>
        <div className="statTile">
          <span className="statLabel">Lessons</span>
          <span className="statValue">{counts.done} <small>/ {counts.total}</small></span>
        </div>
      </section>

      {continueLesson && (
        <Link href={`/learn/lesson/${continueLesson.id}`} className="card continueCard">
          <span className="eyebrow">{continueState?.status === "in-progress" ? "CONTINUE" : counts.done === 0 ? "START HERE" : "NEXT"} · {trackOf(course, continueLesson.id) ? `${trackOf(course, continueLesson.id)!.title_grc.toUpperCase()} ${continueLesson.id.split(".")[1]}` : `ΜΑΘΗΜΑ ${continueLesson.id.replace(".", "·")}`}</span>
          <span className="continueTitle" lang="grc">{continueLesson.title_grc}</span>
          <span className="continueSub">{continueLesson.title_en}{continueLesson.word_count ? ` · ${continueLesson.word_count} words` : ""}{continueState?.step != null ? ` · step ${continueState.step + 1} of 10` : ""}</span>
          <span className="primary buttonLike">{continueState?.status === "in-progress" ? "Resume" : "Open"}</span>
        </Link>
      )}

      {counts.done === 0 && !cp.placement && (
        <p className="placementHint">Already know some Greek? <Link href="/learn/placement">Take the placement test</Link> and start where you belong.</p>
      )}

      <section className="card reviewCard">
        <div className="sectionHead"><div><h2>Review</h2><p>Little and often beats a long session.</p></div></div>
        <ul className="reviewList">
          <li><Link href="/words">Words due</Link><strong>{dueCards}</strong></li>
          <li>
            {reread ? <Link href={`/learn/lesson/${reread.id}?step=2&reread=1`}>Reread {reread.id}</Link> : <span className="muted">Reread a story</span>}
            <strong>{reread ? `${reread.daysAgo} d` : "—"}</strong>
          </li>
          <li>
            {weak.length ? <Link href="/practice/review">Review quiz</Link> : <span className="muted">Review quiz</span>}
            <strong>{weak.length ? `${weak.length} skills` : "—"}</strong>
          </li>
          <li>
            {mistakes ? <Link href="/practice/review?mode=mistakes">Mistakes</Link> : <span className="muted">Mistakes</span>}
            <strong>{mistakes || "—"}</strong>
          </li>
          <li>
            <Link href="/progress">Skills</Link>
            <strong>{metSkills ? `${metSkills} met` : "—"}</strong>
          </li>
        </ul>
        {weak.length > 0 && <p className="muted small">Weakest: {weak.map(skillLabel).join(" · ")}</p>}
      </section>

      <section className="card syllabusOverview" aria-labelledby="syllabus-overview">
        <h2 id="syllabus-overview">What you will learn</h2>
        <p><strong>13 units · 52 main-course lessons · 4 optional reading specialisations.</strong> Each specialisation has seven lessons.</p>
        <dl>
          <div><dt>Nouns and cases</dt><dd>Nominative (subject), accusative (object), genitive (possession and other relationships), dative (recipient, means and other uses), and vocative (direct address). Learn the three declensions: the main patterns of noun endings.</dd></div>
          <div><dt>Verbs and sentence structure</dt><dd>Tense and aspect, active/middle/passive voice, commands, subjunctive and optative moods, participles, infinitives and subordinate clauses.</dd></div>
          <div><dt>Vocabulary and reading</dt><dd>Learn words in context, recognise their inflected forms, practise recall and listen to Classical Attic audio. Progress from simple sentences to supported passages by Greek authors.</dd></div>
        </dl>
        <p className="muted small">The Athenian family story supplies reading practice; the syllabus below shows the language taught. Lesson vocabulary counts are entries studied, including review—not a count of unique words across the course.</p>
      </section>
      <span id="units" className="anchorTarget" />
      {course.stages.map((stage) => (
        <section key={stage.id} className="stage" aria-labelledby={`stage-${stage.id}`}>
          <h2 className="stageTitle" id={`stage-${stage.id}`}>{syllabus.stages[stage.id as keyof typeof syllabus.stages]?.title ?? stage.title_en}</h2>
          <p className="muted stageBlurb">{syllabus.stages[stage.id as keyof typeof syllabus.stages]?.description ?? stage.blurb}</p>
          <div className="unitGrid syllabusGrid">
            {stage.units.map((unit) => {
              const outline = syllabus.units[String(unit.n) as keyof typeof syllabus.units];
              const authored = unit.lessons.filter((l) => l.available);
              const gate = testGate(course, cp, unit, now);
              const doneHere = authored.filter((l) => cp.lessons[l.id]?.status === "done").length;
              const state = !authored.length ? "planned" : doneHere === authored.length ? "done" : authored.some((l) => lessonStatus(course, cp, l.id) !== "locked") ? "open" : "locked";
              // The explicit continue link opens the next lesson; the outline stays expandable.
              const target = state === "open" || state === "done" ? (authored.find((l) => !["done", "skipped", "locked"].includes(lessonStatus(course, cp, l.id))) ?? authored[0]) : null;
              return (
                <div key={unit.id} id={`unit-${unit.n}`} className={`unitTile anchorTarget ${state} syllabusUnit`}>
                  <span className="unitLabel">UNIT {unit.n}{state === "done" ? (cp.tests[unit.test ?? ""]?.passedAt ? ` · TEST ${Math.round((cp.tests[unit.test ?? ""].attempts.at(-1)?.score ?? 0) * 100)} %` : " · DONE") : state === "open" ? " · NOW" : state === "planned" ? " · PLANNED" : ""}</span>
                  <h3 className="syllabusUnitTitle">{outline?.title ?? unit.title_en}</h3>
                  <span className="unitSub" id={`unit-sub-${unit.n}`}>Reading theme: {unit.title_en} <span lang="grc">· {unit.title_grc}</span></span>
                  {outline && <div className="syllabusObjectives">
                    <p><strong>Grammar and skills</strong>{outline.grammar}</p>
                    <p><strong>Vocabulary</strong>{outline.vocabulary}</p>
                  </div>}
                  <details className="syllabusLessons">
                    <summary>Lesson outline · {unit.lessons.length} lessons</summary>
                    <ol>
                      {unit.lessons.map((lesson, index) => {
                        const status = lessonStatus(course, cp, lesson.id);
                        return <li key={lesson.id}>
                          <strong>{lesson.id} · {outline?.lessons[index] ?? lesson.title_en}</strong>
                          <span>{lesson.title_en}{lesson.word_count != null ? ` · ${lesson.word_count} vocabulary entries` : ""}</span>
                          {lesson.available && status !== "locked" ? <Link href={`/learn/lesson/${lesson.id}`}>Open lesson →</Link> : <span className="muted small">{lesson.available ? "Unlocks as you progress" : "Planned lesson"}</span>}
                        </li>;
                      })}
                    </ol>
                  </details>
                  {target && <Link className="syllabusContinue" href={`/learn/lesson/${target.id}`}>{state === "done" ? "Review unit" : "Continue unit"} →</Link>}
                  <div className="lessonDots">
                    {unit.lessons.map((l) => {
                      const st = l.available ? lessonStatus(course, cp, l.id) : "locked";
                      const dot = <span className={`dot ${st} ${!l.available ? "planned" : ""}`} title={l.available ? `${l.id} ${l.title_en}` : `${l.id} (planned)`} aria-hidden="true" />;
                      return l.available && st !== "locked" ? <Link key={l.id} href={`/learn/lesson/${l.id}`} aria-label={`Lesson ${l.id}: ${l.title_en} (${st === "in-progress" ? "in progress" : st})`}>{dot}</Link> : <span key={l.id}>{dot}</span>;
                    })}
                  </div>
                  {unit.test && authored.length > 0 && (
                    <div className="unitTest">
                      {gate.state === "open" && <Link href={`/learn/test/${unit.test}`} className="testLink">Take the unit test →</Link>}
                      {gate.state === "passed" && <Link href={`/learn/test/${unit.test}`} className="testLink done">Test passed ✓ · retake</Link>}
                      {gate.state === "waiting" && <span className="muted small">Test opens in {formatWait((gate.availableAt ?? now) - now)}</span>}
                      {gate.state === "locked" && <span className="muted small">Finish the unit to unlock the test</span>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ))}

      <section className="stage anchorTarget" id="tracks" aria-labelledby="tracks-title">
        <h2 className="stageTitle" id="tracks-title">Reading specialisations</h2>
        <p className="muted stageBlurb">Apply the grammar you have learned to mythology, philosophy, history or civic life. These optional seven-lesson sequences develop subject vocabulary and author-specific reading skills using adapted and original texts. The first three lessons in each sequence open after Lesson 9.4; the remaining lessons open after Lesson 12.4. Choose one or more.</p>
        <div className="unitGrid trackGrid syllabusGrid">
          {course.tracks.map((t) => {
            const ts = trackState(cp, t);
            const label = ts.state === "locked" ? `OPENS AFTER ${t.side_after}` : ts.state === "side" ? "SIDE READINGS OPEN" : ts.state === "done" ? "DONE" : "OPEN";
            return (
              <Link key={t.id} href={`/learn/track/${t.id}`} className={`unitTile trackTile ${ts.state === "locked" ? "locked" : ts.state === "done" ? "done" : "open"} ${cp.track === t.id ? "chosen" : ""}`}>
                <span className="unitLabel">{cp.track === t.id ? "YOUR TRACK · " : ""}{label}{ts.total ? ` · ${ts.done}/${ts.total}` : ""}</span>
                <span className="unitTitle" lang="grc">{t.title_grc}</span>
                <span className="unitSub">{t.title_en}</span>
                <span className="syllabusTrackSkills">{syllabus.tracks[t.id as keyof typeof syllabus.tracks]}</span>
                <span className="muted small"><strong>Authors and texts: </strong>{t.blurb}</span>
                <div className="lessonDots" aria-hidden="true">
                  {t.lessons.map((l) => <span key={l.id} className={`dot ${l.available ? lessonStatus(course, cp, l.id) : "locked planned"}`} />)}
                </div>
                <span className="tileGo" aria-hidden="true">›</span>
              </Link>
            );
          })}
        </div>
      </section>

      {Object.keys(families).length > 0 && (
        <section className="card">
          <div className="sectionHead"><div><h2>Skills</h2><p>How your practice is going, by family. Mastery needs correct answers on several days.</p></div></div>
          <ul className="skillBars">
            {course.families.filter((f) => families[f.id]).map((f) => (
              <li key={f.id}>
                <span>{f.label}</span>
                <div className="meter"><div style={{ width: `${Math.round(families[f.id].ewma * 100)}%` }} /></div>
                <span className="muted small">{families[f.id].total}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="footnote">Progress is kept in this browser; add a sync code under Vocab › Settings to back it up. Images marked “image coming” will be replaced by Creative Commons photographs and drawings. {images.length ? <Link href="/learn/credits">{images.length} images in the manifest · credits</Link> : ""}</p>
    </main>
  );
}
