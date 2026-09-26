"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import ExerciseRunner, { type Outcome } from "../../../components/course/ExerciseRunner";
import ResultScore from "../../../components/course/ResultScore";
import Crumbs from "../../../components/Crumbs";
import { PageError, PageLoading } from "../../../components/PageState";
import { getCourseImages, getPlacement } from "../../../lib/api";
import { placementDecision, updateSkill, type ImageRecord, type Placement, type PlacementBlock } from "../../../lib/course";
import { bumpActivity, loadProgress, saveProgress, setLesson, strictAccentsFor, type Progress } from "../../../lib/progress";

type Phase = "intro" | "running" | "result";

/**
 * Placement: short blocks of unit-test items, one unit after another. The
 * walk stops after three misses in a row or a block under 60 %. The learner
 * is placed at the first unit not passed; every lesson before it is marked
 * skipped, so the course opens there. Nothing is lost: skipped lessons stay
 * openable from the course map.
 */
export default function PlacementPage() {
  const router = useRouter();
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [placement, setPlacement] = useState<Placement | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState<Phase>("intro");
  const [blockIndex, setBlockIndex] = useState(0);
  const [results, setResults] = useState<boolean[][]>([]);
  const [startedAt, setStartedAt] = useState(0);
  // random per run; `?seed=` pins it (tests, bug reports)
  const [seed] = useState(() => {
    const q = typeof window !== "undefined" ? Number(new URLSearchParams(window.location.search).get("seed")) : NaN;
    return Number.isFinite(q) && q > 0 ? q : Math.floor(Math.random() * 1000) + 1;
  });

  useEffect(() => {
    getPlacement(seed).then(setPlacement).catch((e) => setError(e instanceof Error ? e.message : "Could not load the placement test"));
    getCourseImages().then(setImages).catch(() => setImages([]));
  }, [seed]);
  useEffect(() => saveProgress(progress), [progress]);

  const blocks = placement?.blocks ?? [];
  const block: PlacementBlock | undefined = blocks[blockIndex];
  const decision = useMemo(() => (placement ? placementDecision(blocks, results, placement.pass_score, placement.stop_after_misses) : null), [placement, blocks, results]);

  function finishBlock(outs: Outcome[]) {
    if (!placement || !block) return;
    const now = Date.now();
    const nextResults = [...results, outs.map((o) => o.result.correct)];
    setResults(nextResults);
    setProgress((p) => {
      let course = { ...p.course, skills: { ...p.course.skills } };
      for (const o of outs) for (const s of o.item.skills) course.skills[s] = updateSkill(course.skills[s], o.result.correct, now);
      course = bumpActivity(course, outs.length, Math.min(30, (now - startedAt) / 60000), now);
      return { ...p, course };
    });
    const d = placementDecision(blocks, nextResults, placement.pass_score, placement.stop_after_misses);
    if (d.next !== null && d.next < blocks.length) {
      setBlockIndex(d.next);
    } else {
      place(d.passed, now);
      setPhase("result");
    }
  }

  function place(passed: PlacementBlock | null, now: number) {
    setProgress((p) => {
      let course: typeof p.course = { ...p.course, placement: { unit: passed ? passed.unit + 1 : 0, at: now } };
      if (passed) for (const id of passed.lessons) if (course.lessons[id]?.status !== "done") course = setLesson(course, id, { status: "skipped" }, now);
      return { ...p, course };
    });
  }

  const crumbs = [{ label: "Course", href: "/course" }, { label: "Placement" }];
  if (error) return <PageError message={error} crumbs={crumbs} back={{ href: "/course", label: "Back to the course" }} />;
  if (!placement) return <PageLoading label="Loading the placement test…" crumbs={crumbs} />;

  if (phase === "intro") {
    return (
      <main className="shell">
        <Crumbs items={crumbs} />
        <section className="card">
          <p className="eyebrow">PLACEMENT</p>
          <h1 lang="grc" className="testTitle">Ποῦ ἄρχομαι;</h1>
          <p className="lede">Already know some Greek? Answer a few items from each unit test. The walk stops when you miss three in a row, and the course opens at the unit you reached.</p>
          <ul className="testMeta">
            <li><strong>{blocks.length}</strong> unit{blocks.length === 1 ? "" : "s"} · up to <strong>{placement.per_unit}</strong> items each: forms and sentences, no vocabulary lists</li>
            <li>No feedback during a block · lessons you skip stay open on the course map</li>
            <li>Total beginner? Start at <Link href="/course/lesson/0.1">Lesson 0·1</Link> instead.</li>
          </ul>
          <div className="stepNav">
            <button type="button" className="primary" onClick={() => { setStartedAt(Date.now()); setPhase("running"); }}>Start</button>
            <Link href="/course" className="secondary buttonLike">Not now</Link>
          </div>
        </section>
      </main>
    );
  }

  if (phase === "running" && block) {
    return (
      <main className="shell lessonShell">
        <Crumbs items={[{ label: "Course", href: "/course" }, { label: "Placement" }, { label: `Unit ${block.unit} of ${blocks.length}` }]} />
        <h1 className="srOnly">Placement test</h1>
        <section className="card">
          <p className="sectionTag">UNIT {block.unit} · <span lang="grc">{block.title_grc}</span> · {block.title_en}</p>
          <ExerciseRunner
            key={block.test}
            items={block.items}
            images={images}
            mode="test"
            accents={strictAccentsFor(progress.settings, block.scope)}
            seed={seed}
            onDone={finishBlock}
          />
        </section>
      </main>
    );
  }

  const passed = decision?.passed ?? null;
  const target = passed ? passed.next_lesson : "0.1";
  const reached = passed ? `Unit ${passed.unit}` : null;
  return (
    <main className="shell">
      <Crumbs items={crumbs} />
      <section className="card">
        <h1 className="srOnly">Placement result</h1>
        <p className="eyebrow">PLACED</p>
        {passed ? (
          <>
            <ResultScore>{reached}</ResultScore>
            <p className="lede">You passed the {reached} block{results.length > 1 ? `s up to ${reached}` : ""}. Lessons 0·1 – {passed.lessons.at(-1)?.replace(".", "·")} are marked skipped; the course continues at {target ? `Lesson ${target.replace(".", "·")}` : "the next authored lesson"}.</p>
          </>
        ) : (
          <>
            <ResultScore lang="grc">ἄρχου</ResultScore>
            <p className="lede">Start from the beginning: Lesson 0·1 takes you through the alphabet in four short lessons, and Unit 1 begins the story.</p>
          </>
        )}
        <ul className="testMeta">
          {results.map((r, i) => <li key={blocks[i].test}>Unit {blocks[i].unit}: <strong>{r.filter(Boolean).length} / {r.length}</strong></li>)}
        </ul>
        <div className="stepNav">
          <button type="button" className="primary" onClick={() => router.push(target ? `/course/lesson/${target}` : "/course")}>{target ? `Open Lesson ${target.replace(".", "·")}` : "Back to the course"}</button>
          <Link href="/course" className="secondary buttonLike">Course map</Link>
        </div>
      </section>
    </main>
  );
}
