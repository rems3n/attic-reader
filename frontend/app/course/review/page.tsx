"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ExerciseRunner, { type Outcome } from "../../../components/course/ExerciseRunner";
import { getCourse, getCourseImages, getDrill } from "../../../lib/api";
import { scoreOf, updateSkill, weakSkills, type CourseIndex, type ImageRecord, type Item } from "../../../lib/course";
import { lastDoneLesson } from "../../../lib/courseState";
import { addError, bumpActivity, loadProgress, saveProgress, type Progress } from "../../../lib/progress";

/** A 10-item quiz generated from the learner's weakest skills. */
export default function ReviewPage() {
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [items, setItems] = useState<Item[] | null>(null);
  const [error, setError] = useState("");
  const [done, setDone] = useState<number | null>(null);
  const [round, setRound] = useState(0);

  useEffect(() => {
    getCourse().then(setCourse).catch((e) => setError(e instanceof Error ? e.message : "Could not load the course"));
    getCourseImages().then(setImages).catch(() => setImages([]));
  }, []);
  useEffect(() => saveProgress(progress), [progress]);

  useEffect(() => {
    if (!course) return;
    const scope = lastDoneLesson(course, progress.course) ?? "0.4";
    const weak = weakSkills(progress.course.skills, 6).filter((s) => /^(noun|art|verb|adj)\./.test(s));
    if (!weak.length) {
      setItems([]);
      return;
    }
    getDrill(weak, scope, 10, Date.now() % 100000).then(setItems).catch((e) => setError(e instanceof Error ? e.message : "Could not build the quiz"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [course, round]);

  function record(o: Outcome) {
    const now = Date.now();
    setProgress((p) => {
      let c = { ...p.course, skills: { ...p.course.skills } };
      for (const s of o.item.skills) c.skills[s] = updateSkill(c.skills[s], o.result.correct, now);
      if (!o.result.correct) c = addError(c, { item: o.item.id, lesson: "review", answer: JSON.stringify(o.response).slice(0, 120), at: now });
      c = bumpActivity(c, 1, 0.5, now);
      return { ...p, course: c };
    });
  }

  if (error) return <main className="shell"><p className="error">{error}</p></main>;
  return (
    <main className="shell lessonShell">
      <p className="crumbs"><Link href="/course">← Course</Link></p>
      <section className="card">
        <p className="eyebrow">REVIEW QUIZ</p>
        {items === null && <p className="muted">Building your quiz…</p>}
        {items && items.length === 0 && <p className="muted">Nothing to review yet: finish a lesson with form exercises first.</p>}
        {items && items.length > 0 && done === null && (
          <ExerciseRunner key={round} items={items} images={images} mode="practice" accents={false} onOutcome={record} onDone={(outs) => setDone(scoreOf(outs.map((o) => o.result)))} seed={round} title="Review" />
        )}
        {done !== null && (
          <div className="stepDone">
            <p className="resultBig">{Math.round(done * 100)} %</p>
            <div className="stepNav">
              <button type="button" className="primary" onClick={() => { setDone(null); setItems(null); setRound(round + 1); }}>Another round</button>
              <Link href="/course" className="secondary buttonLike">Course home</Link>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
