"use client";
import SessionSummary from "../../../../components/SessionSummary";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import ExerciseRunner, { type Outcome } from "../../../../components/course/ExerciseRunner";
import { SpeakButton, useSpeaker } from "../../../../components/Speak";
import Crumbs, { type Crumb } from "../../../../components/Crumbs";
import { PageError, PageLoading } from "../../../../components/PageState";
import ResultScore from "../../../../components/course/ResultScore";
import { getCourseImages, getCourseTest } from "../../../../lib/api";
import { keyText, scoreOf, updateSkill, type CourseTest, type ImageRecord, type Item } from "../../../../lib/course";
import { addError, bumpActivity, loadProgress, recordTest, saveProgress, strictAccentsFor, type Progress } from "../../../../lib/progress";

type Phase = "intro" | "running" | "result";

export default function TestPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(params.id);
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [test, setTest] = useState<CourseTest | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState<Phase>("intro");
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);
  const [startedAt, setStartedAt] = useState(0);
  const { play, busy } = useSpeaker();
  const stored = progress.course.tests[id];
  const attempt = (stored?.attempts.length ?? 0) + 1;
  const accents = strictAccentsFor(progress.settings, test?.scope ?? "1.1");

  useEffect(() => {
    getCourseTest(id, attempt).then(setTest).catch((e) => setError(e instanceof Error ? e.message : "Could not load the test"));
    getCourseImages().then(setImages).catch(() => setImages([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);
  useEffect(() => saveProgress(progress), [progress]);

  const items = useMemo(() => (test ? test.sections.flatMap((s) => s.items.map((i) => ({ ...i, _section: s.id }) as Item & { _section: string })) : []), [test]);
  const sectionOf = (item: Item) => test?.sections.find((s) => s.id === (item as Item & { _section?: string })._section);

  function finish(outs: Outcome[]) {
    setOutcomes(outs);
    setPhase("result");
    const now = Date.now();
    const score = scoreOf(outs.map((o) => o.result));
    setProgress((p) => {
      let course = { ...p.course, skills: { ...p.course.skills } };
      for (const o of outs) {
        for (const s of o.item.skills) course.skills[s] = updateSkill(course.skills[s], o.result.correct, now);
        if (!o.result.correct) course = addError(course, { item: o.item.id, lesson: test?.scope ?? id, answer: JSON.stringify(o.response).slice(0, 120), at: now });
      }
      course = recordTest(course, id, { at: now, score, misses: outs.filter((o) => !o.result.correct).map((o) => o.item.id) }, test?.pass_score ?? 0.8, test?.retake_after_days ?? 7);
      course = bumpActivity(course, outs.length, Math.min(60, (now - startedAt) / 60000), now);
      return { ...p, course };
    });
  }

  // Course › Unit 3 › Unit test  (a reading gate: Course › Reading gate)
  const unitN = /^unit-(\d+)$/.exec(id)?.[1];
  const crumbs: Crumb[] = [
    { label: "Learn", href: "/learn" },
    ...(unitN ? [{ label: `Unit ${unitN}`, href: `/learn#unit-${unitN}` }] : []),
    { label: unitN ? "Unit test" : test?.title_en ?? "Test" },
  ];
  if (error) return <PageError message={error} crumbs={crumbs} back={{ href: "/learn", label: "Back to the course" }} />;
  if (!test) return <PageLoading label="Loading the test…" crumbs={crumbs} />;

  if (phase === "intro") {
    return (
      <main className="shell">
        <Crumbs items={crumbs} />
        <section className="card">
          <p className="eyebrow">{id.startsWith("gate-") ? "READING GATE" : "UNIT TEST"} · ATTEMPT {attempt}</p>
          <h1 lang="grc" className="testTitle">{test.title_grc}</h1>
          <p className="lede">{test.blurb}</p>
          <ul className="testMeta">
            <li><strong>{test.item_count}</strong> items in {test.sections.length} parts: {test.sections.map((s) => s.title.split(" · ")[1] ?? s.title).join(", ")}</li>
            <li><strong>{Math.round(test.pass_score * 100)} %</strong> to pass · no feedback until the end</li>
            {stored?.attempts.length ? <li>Best so far: <strong>{Math.round(Math.max(...stored.attempts.map((a) => a.score)) * 100)} %</strong>{stored.passedAt ? " · passed" : ""}</li> : null}
          </ul>
          <div className="stepNav">
            <button type="button" className="primary" onClick={() => { setStartedAt(Date.now()); setPhase("running"); }}>Start</button>
          </div>
        </section>
      </main>
    );
  }

  if (phase === "running") {
    return (
      <main className="shell lessonShell">
        <Crumbs items={crumbs} />
        <h1 className="srOnly" lang="grc">{test.title_grc}</h1>
        <section className="card">
          <ExerciseRunner
            items={items}
            images={images}
            mode="test"
            accents={accents}
            seed={attempt}
            onDone={finish}
            renderAbove={(item) => {
              const s = sectionOf(item);
              if (!s?.passage) return <p className="sectionTag">{s?.title}</p>;
              return (
                <div className="passage">
                  <p className="sectionTag">{s.title}</p>
                  {s.passage_title && <h2 lang="grc">{s.passage_title}</h2>}
                  <p lang="grc" className="passageText"><SpeakButton text={s.passage} play={play} busy={busy} small /> {s.passage}</p>
                  {s.passage_source && <p className="muted small">{[s.passage_source.author, s.passage_source.work, s.passage_source.ref].filter(Boolean).join(", ")} · unadapted</p>}
                  {s.passage_note && <p className="muted small">{s.passage_note}</p>}
                  {s.glosses && Object.keys(s.glosses).length > 0 && (
                    <p className="passageGlosses small">
                      {Object.entries(s.glosses).map(([w, g]) => <span key={w}><span lang="grc">{w}</span> {g}</span>)}
                    </p>
                  )}
                </div>
              );
            }}
          />
        </section>
      </main>
    );
  }

  const score = scoreOf(outcomes.map((o) => o.result));
  const passed = score >= test.pass_score;
  return (
    <main className="shell">
      <Crumbs items={crumbs} />
      <section className="card">
        <h1 className="srOnly">{test.title_en}: result</h1>
        <p className="eyebrow">{passed ? "PASSED" : "NOT YET"}</p>
        <ResultScore>{Math.round(score * 100)} %</ResultScore>
        <SessionSummary title={passed ? "Test passed" : "Test complete"} reviewed={outcomes.length} correct={outcomes.filter((o) => o.result.correct).length} />
        <ul className="testMeta">
          {test.sections.map((s) => {
            const outs = outcomes.filter((o) => (o.item as Item & { _section?: string })._section === s.id);
            return <li key={s.id}>{s.title}: <strong>{outs.filter((o) => o.result.correct).length} / {outs.length}</strong></li>;
          })}
        </ul>
        {passed ? <p className="ok">Unit complete. A short retake of the items you missed will be suggested in a week.</p> : <p className="warnText">{Math.round(test.pass_score * 100)} % needed. Review the misses below, revisit the lessons, and try again; the forms section is regenerated each attempt.</p>}
        {outcomes.some((o) => !o.result.correct) && (
          <>
            <h2>Misses</h2>
            <ul className="missList">
              {outcomes.filter((o) => !o.result.correct).map((o) => (
                <li key={o.item.id}>
                  <span lang="grc">{o.item.prompt ?? o.item.form}</span>
                  <span className="muted"> → {keyText(o.item)}</span>
                  {o.item.explain && <span className="muted small"> · {o.item.explain}</span>}
                </li>
              ))}
            </ul>
          </>
        )}
        <div className="stepNav">
          <Link href="/learn" className="primary buttonLike">Back to the course</Link>
          <button type="button" className="secondary" onClick={() => { setPhase("intro"); getCourseTest(id, attempt + 1).then(setTest).catch(() => undefined); }}>Try again</button>
        </div>
      </section>
    </main>
  );
}
