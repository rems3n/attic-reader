"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ExerciseRunner, { type Outcome } from "../../../../components/course/ExerciseRunner";
import Markdown from "../../../../components/course/Markdown";
import Picture, { imageById } from "../../../../components/course/Picture";
import StoryReader from "../../../../components/course/StoryReader";
import { SpeakButton, useSpeaker } from "../../../../components/Speak";
import { getCourse, getCourseImages, getDrill, getLesson } from "../../../../lib/api";
import { hashString, keyText, scoreOf, updateSkill, weakSkills, type CourseIndex, type ImageRecord, type Item, type Lesson } from "../../../../lib/course";
import { addError, bumpActivity, loadProgress, saveProgress, setLesson, strictAccentsFor, type Progress } from "../../../../lib/progress";

const PASS = 0.75;
const SPEEDS = [0.6, 0.75, 1] as const;

type Step = { id: string; grc: string; en: string };

const ALL_STEPS: Step[] = [
  { id: "cover", grc: "Εἰκών", en: "Cover" },
  { id: "listen", grc: "Ἀκούσατε", en: "Listen first" },
  { id: "read", grc: "Ἀνάγνωσις", en: "Reading" },
  { id: "vocab", grc: "Λέξεις", en: "Words" },
  { id: "notice", grc: "Παρατηρήσατε", en: "Notice" },
  { id: "grammar", grc: "Γραμματική", en: "Grammar" },
  { id: "exercises", grc: "Μελετήματα", en: "Exercises" },
  { id: "questions", grc: "Ἐρωτήματα", en: "Questions" },
  { id: "culture", grc: "Πολιτισμός", en: "Culture" },
  { id: "quiz", grc: "Ἔλεγχος", en: "Lesson check" },
];

export default function LessonPage() {
  const params = useParams<{ id: string }>();
  const search = useSearchParams();
  const id = decodeURIComponent(params.id);
  const [lesson, setLessonData] = useState<Lesson | null>(null);
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [step, setStep] = useState<number>(0);
  const [speed, setSpeed] = useState<number>(0.75);
  const [review, setReview] = useState<Item[]>([]);
  const [quizResult, setQuizResult] = useState<{ score: number; outcomes: Outcome[] } | null>(null);
  const [exerciseSummary, setExerciseSummary] = useState<{ score: number } | null>(null);
  const startedAt = useRef(Date.now());
  const { play, busy } = useSpeaker(speed);
  const showEnglish = progress.settings.showEnglish;
  const accents = strictAccentsFor(progress.settings, id);

  useEffect(() => {
    setLessonData(null);
    setQuizResult(null);
    setExerciseSummary(null);
    getLesson(id).then(setLessonData).catch((e) => setError(e instanceof Error ? e.message : "Could not load the lesson"));
    getCourse().then(setCourse).catch(() => setCourse(null));
    getCourseImages().then(setImages).catch(() => setImages([]));
    const stored = loadProgress();
    const fromQuery = Number(search.get("step"));
    const saved = stored.course.lessons[id]?.step;
    setStep(Number.isFinite(fromQuery) && search.get("step") ? fromQuery : saved ?? 0);
    startedAt.current = Date.now();
    if (search.get("reread")) {
      const now = Date.now();
      const next = { ...stored, course: { ...stored.course, rereads: { ...stored.course.rereads, [id]: [...(stored.course.rereads[id] ?? []), now] } } };
      setProgress(next);
    }
  }, [id, search]);

  useEffect(() => saveProgress(progress), [progress]);

  // Steps that apply to this lesson (alphabet lessons have no words/questions).
  const steps = useMemo(() => {
    if (!lesson) return ALL_STEPS;
    return ALL_STEPS.filter((s) => {
      if (s.id === "vocab") return lesson.vocab.length > 0;
      if (s.id === "questions") return lesson.questions.length > 0;
      if (s.id === "culture") return !!lesson.culture;
      if (s.id === "listen") return lesson.story.some((p) => p.sentences.length > 1);
      return true;
    });
  }, [lesson]);
  const stepIndex = Math.min(step, steps.length - 1);
  const current = steps[stepIndex];

  // Persist the step and mark the lesson in progress.
  const markStep = useCallback(
    (n: number) => {
      setStep(n);
      setProgress((p) => {
        const prev = p.course.lessons[id];
        const status = prev?.status === "done" ? "done" : "in-progress";
        return { ...p, course: setLesson(p.course, id, { status, step: n }) };
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [id],
  );

  // Spiral review: a few generated items on the weakest skills met so far.
  useEffect(() => {
    if (!lesson || !course) return;
    const prev = lesson.position.prev;
    if (!prev || prev.startsWith("0.")) {
      setReview([]);
      return;
    }
    const weak = weakSkills(progress.course.skills, 3).filter((s) => /^(noun|art|verb|adj)\./.test(s));
    if (!weak.length) {
      setReview([]);
      return;
    }
    getDrill(weak, prev, 4, hashString(id) % 1000)
      .then(setReview)
      .catch(() => setReview([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson?.id, course?.lesson_order.length]);

  const record = useCallback(
    (o: Outcome) => {
      const now = Date.now();
      setProgress((p) => {
        let course = { ...p.course, skills: { ...p.course.skills } };
        for (const s of o.item.skills) course.skills[s] = updateSkill(course.skills[s], o.result.correct, now);
        if (!o.result.correct) course = addError(course, { item: o.item.id, lesson: id, answer: JSON.stringify(o.response).slice(0, 120), at: now });
        course = bumpActivity(course, 1, 0.5, now);
        return { ...p, course };
      });
    },
    [id],
  );

  function finishQuiz(outcomes: Outcome[]) {
    const score = scoreOf(outcomes.map((o) => o.result));
    setQuizResult({ score, outcomes });
    const now = Date.now();
    const minutes = Math.min(60, (now - startedAt.current) / 60000);
    setProgress((p) => {
      const prev = p.course.lessons[id];
      const passed = score >= PASS;
      let course = setLesson(p.course, id, {
        status: passed ? "done" : "in-progress",
        best: Math.max(prev?.best ?? 0, score),
        attempts: (prev?.attempts ?? 0) + 1,
        firstDone: passed ? prev?.firstDone ?? now : prev?.firstDone,
        lastDone: passed ? now : prev?.lastDone,
        step: passed ? 0 : stepIndex,
      }, now);
      course = bumpActivity(course, 0, minutes, now);
      return { ...p, course };
    });
  }

  if (error) return <main className="shell"><p className="error">{error}</p></main>;
  if (!lesson) return <main className="shell"><p className="muted">Loading lesson {id}…</p></main>;

  const imageMap = new Map(images.map((i) => [i.id, i]));
  const exercisesWithReview = review.length ? [...lesson.exercises, ...review] : lesson.exercises;
  const lessonState = progress.course.lessons[id];

  return (
    <main className="shell lessonShell">
      <header className="lessonHead">
        <div className="lessonCrumbs">
          <Link href="/course">← Course</Link>
          <span className="muted"> · Unit {lesson.unit.n} · Lesson {lesson.position.in_unit} of {lesson.position.unit_size}</span>
          <label className="englishToggle">
            <input type="checkbox" checked={showEnglish} onChange={(e) => setProgress({ ...progress, settings: { ...progress.settings, showEnglish: e.target.checked } })} /> English
          </label>
        </div>
        <h1 lang="grc" className="lessonTitle">{lesson.title_grc}</h1>
        {showEnglish && <p className="lessonSub">{lesson.title_en}</p>}
        <ol className="stepper" aria-label="Lesson steps">
          {steps.map((s, i) => (
            <li key={s.id}>
              <button type="button" className={`stepDot ${i === stepIndex ? "on" : ""} ${i < stepIndex ? "done" : ""}`} onClick={() => markStep(i)} aria-current={i === stepIndex ? "step" : undefined} title={`${s.grc} · ${s.en}`}>
                <span className="stepNum">{i + 1}</span>
              </button>
            </li>
          ))}
        </ol>
        <p className="stepName"><span lang="grc">{current.grc}</span>{showEnglish && <span className="muted"> · {current.en}</span>}</p>
      </header>

      {current.id === "cover" && (
        <section className="card coverCard">
          <Picture image={lesson.cover_image ?? imageById(imageMap, lesson.cover)} size="panel" />
          {lesson.caption_grc && (
            <p className="caption" lang="grc"><SpeakButton text={lesson.caption_grc} play={play} busy={busy} small /> {lesson.caption_grc}</p>
          )}
          {lesson.summary_grc && <p className="summaryGrc" lang="grc">{lesson.summary_grc}</p>}
          {showEnglish && lesson.summary_en && <p className="muted">{lesson.summary_en}</p>}
          <p className="muted small">{lesson.vocab.length ? `${lesson.vocab.length} words · ` : ""}{lesson.exercises.length + lesson.questions.length} exercises · {lesson.quiz.length}-item check{lessonState?.best ? ` · best ${Math.round(lessonState.best * 100)} %` : ""}</p>
          <div className="stepNav"><button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Begin →</button></div>
        </section>
      )}

      {current.id === "listen" && (
        <section className="card">
          <p className="stepHint">Listen to the whole story once with the text hidden. Look at the pictures. You are not expected to understand everything.</p>
          <SpeedPicker speed={speed} setSpeed={setSpeed} />
          <StoryReader paragraphs={lesson.story} storyText={lesson.story_text} images={images} speed={speed} showEnglish={showEnglish} hideText />
          <div className="stepNav"><button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Now read it →</button></div>
        </section>
      )}

      {current.id === "read" && (
        <section className="card">
          <p className="stepHint">Tap any word to hear it; underlined words have a gloss. ▶ plays a sentence and follows the words.</p>
          <SpeedPicker speed={speed} setSpeed={setSpeed} />
          <StoryReader paragraphs={lesson.story} storyText={lesson.story_text} images={images} speed={speed} showEnglish={showEnglish} />
          <div className="stepNav"><button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Next →</button></div>
        </section>
      )}

      {current.id === "vocab" && (
        <section className="card">
          <p className="stepHint">The words of this lesson. They join your flash-card deck automatically (Vocab › Words from a lesson).</p>
          <ul className="vocabGrid">
            {lesson.vocab.map((v) => (
              <li key={v.id} className="vocabTile">
                <Picture image={imageById(imageMap, v.pic)} size="thumb" caption={false} />
                <div className="vocabText">
                  <Link href={`/vocab/${encodeURIComponent(v.id)}`} lang="grc" className="vocabLemma">{v.headword}</Link>
                  {v.gloss_grc && <span lang="grc" className="vocabGloss">{v.gloss_grc}</span>}
                  {showEnglish && <span className="vocabShort">{v.short}</span>}
                  <span className="muted small">{v.pos}</span>
                </div>
                <SpeakButton text={v.lemma} play={play} busy={busy} small />
              </li>
            ))}
          </ul>
          <div className="stepNav">
            <Link href="/vocab" className="secondary buttonLike">Study cards</Link>
            <button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Next →</button>
          </div>
        </section>
      )}

      {current.id === "notice" && (
        <section className="card">
          <p className="stepHint">Read these lines from the story again. What changes, and why?</p>
          <ul className="noticeList">
            {lesson.notice.map((n, i) => (
              <li key={i} lang="grc"><SpeakButton text={n} play={play} busy={busy} small /> {n}</li>
            ))}
          </ul>
          <div className="stepNav"><button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Explain it →</button></div>
        </section>
      )}

      {current.id === "grammar" && (
        <section className="card grammarCard">
          <Markdown text={lesson.grammar.md} />
          {lesson.grammar.diagram && <Picture image={imageById(imageMap, lesson.grammar.diagram)} size="panel" />}
          {lesson.grammar.paradigms.length > 0 && (
            <p className="paradigmLinks">
              Tables: {lesson.grammar.paradigms.map((p) => <Link key={p} href={`/grammar/${p}`} className="chip">{p}</Link>)}
            </p>
          )}
          <div className="stepNav"><button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Practise →</button></div>
        </section>
      )}

      {current.id === "exercises" && (
        <section className="card">
          {exerciseSummary ? (
            <div className="stepDone">
              <p className="resultBig">{Math.round(exerciseSummary.score * 100)} %</p>
              <p className="muted">{review.length ? `${review.length} review items on your weakest skills were mixed in.` : ""}</p>
              <div className="stepNav">
                <button type="button" className="secondary" onClick={() => setExerciseSummary(null)}>Again</button>
                <button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Next →</button>
              </div>
            </div>
          ) : (
            <ExerciseRunner key={`ex-${id}-${exercisesWithReview.length}`} items={exercisesWithReview} images={images} mode="practice" accents={accents} scope={id} onOutcome={record} onDone={(outs) => setExerciseSummary({ score: scoreOf(outs.map((o) => o.result)) })} seed={hashString(id)} />
          )}
          <p className="muted small accentNote">{accents ? "Accents count in typed answers." : "Accents are optional in typed answers until Unit 4; breathings count."}</p>
        </section>
      )}

      {current.id === "questions" && (
        <section className="card">
          <p className="stepHint" lang="grc">ἀποκρίνεσθε Ἑλληνιστί.</p>
          <ExerciseRunner key={`q-${id}`} items={lesson.questions} images={images} mode="practice" accents={accents} scope={id} onOutcome={record} onDone={() => markStep(stepIndex + 1)} seed={hashString(id) + 1} title="Ἐρωτήματα" />
        </section>
      )}

      {current.id === "culture" && lesson.culture && (
        <section className="card cultureCard">
          <h2>{lesson.culture.title}</h2>
          <Picture image={lesson.culture.image_record ?? imageById(imageMap, lesson.culture.image)} size="panel" />
          <Markdown text={lesson.culture.md} />
          <div className="stepNav"><button type="button" className="primary" onClick={() => markStep(stepIndex + 1)}>Lesson check →</button></div>
        </section>
      )}

      {current.id === "quiz" && (
        <section className="card">
          {quizResult ? (
            <div className="stepDone">
              <p className="resultBig">{Math.round(quizResult.score * 100)} %</p>
              <p className={quizResult.score >= PASS ? "ok" : "warnText"}>{quizResult.score >= PASS ? "Lesson complete." : `Not yet: ${Math.round(PASS * 100)} % needed. Look at the misses and try again.`}</p>
              {quizResult.outcomes.some((o) => !o.result.correct) && (
                <ul className="missList">
                  {quizResult.outcomes.filter((o) => !o.result.correct).map((o) => (
                    <li key={o.item.id}><span lang="grc">{o.item.prompt}</span> <span className="muted">→ {keyText(o.item)}</span></li>
                  ))}
                </ul>
              )}
              <div className="stepNav">
                <button type="button" className="secondary" onClick={() => setQuizResult(null)}>Retake</button>
                {quizResult.score >= PASS && lesson.position.next && <Link href={`/course/lesson/${lesson.position.next}`} className="primary buttonLike">Next lesson →</Link>}
                {quizResult.score >= PASS && !lesson.position.next && <Link href="/course" className="primary buttonLike">Back to the course</Link>}
                {quizResult.score >= PASS && lesson.unit.test && <Link href="/course" className="secondary buttonLike">Course home</Link>}
              </div>
            </div>
          ) : (
            <>
              <p className="stepHint">{lesson.quiz.length} questions, all types. {Math.round(PASS * 100)} % to complete the lesson. You can always retake.</p>
              <ExerciseRunner key={`quiz-${id}-${lessonState?.attempts ?? 0}`} items={lesson.quiz} images={images} mode="practice" accents={accents} scope={id} onOutcome={record} onDone={finishQuiz} seed={hashString(id) + (lessonState?.attempts ?? 0)} title="Ἔλεγχος" />
            </>
          )}
        </section>
      )}

      <nav className="lessonFooter">
        <button type="button" className="secondary" disabled={stepIndex === 0} onClick={() => markStep(stepIndex - 1)}>← Back</button>
        <span className="muted small">{lesson.position.prev && <Link href={`/course/lesson/${lesson.position.prev}`}>prev</Link>}{lesson.position.prev && lesson.position.next && " · "}{lesson.position.next && <Link href={`/course/lesson/${lesson.position.next}`}>next</Link>}</span>
        <button type="button" className="secondary" disabled={stepIndex >= steps.length - 1} onClick={() => markStep(stepIndex + 1)}>Skip →</button>
      </nav>
    </main>
  );
}

function SpeedPicker({ speed, setSpeed }: { speed: number; setSpeed: (s: number) => void }) {
  return (
    <div className="speedRow" role="group" aria-label="Speed">
      {SPEEDS.map((s) => (
        <button key={s} type="button" className={`speedButton ${speed === s ? "on" : ""}`} onClick={() => setSpeed(s)}>{s}×</button>
      ))}
    </div>
  );
}
