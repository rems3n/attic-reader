"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader";
import { getCourse } from "../lib/api";
import type { CourseIndex } from "../lib/course";
import { weakSkills } from "../lib/course";
import {
  completedCount,
  findLesson,
  nextLesson,
  rereadSuggestion,
  trackState,
} from "../lib/courseState";
import { emptyProgress, loadProgress, streakDays } from "../lib/progress";
import {
  hasLearningProgress,
  weeklyMinutes,
  wordCounts,
} from "../lib/dashboard";
import { mistakeCount } from "../lib/skills";
export default function Home() {
  const [progress, setProgress] = useState(emptyProgress);
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  useEffect(() => {
    setProgress(loadProgress());
    setReady(true);
    getCourse()
      .then(setCourse)
      .catch(() => setError(true));
  }, []);
  if (!ready)
    return (
      <main className="shell hubShell">
        <p role="status">Loading your home…</p>
      </main>
    );
  if (!hasLearningProgress(progress))
    return (
      <main className="shell hubShell">
        <section className="homeHero">
          <div>
            <p className="eyebrow">
              CLASSICAL GREEK · FROM THE ALPHABET TO ORIGINAL TEXTS
            </p>
            <h1>
              Learn to read
              <br />
              Ancient Greek.
            </h1>
            <p className="lede">
              Follow a structured course, practise the words you need, and read
              Greek authors with reconstructed Classical Attic audio.
            </p>
            <div className="actions">
              <Link href="/start" className="primary buttonLike">
                Start learning
              </Link>
              <Link href="/library" className="secondary buttonLike">
                Explore the library
              </Link>
            </div>
            <p className="muted small">
              No account needed. Your progress stays on this device.
            </p>
          </div>
          <div className="homeSpecimen" aria-label="Greek reading example">
            <span className="eyebrow">LEARN · READ · LISTEN</span>
            <p lang="grc">
              Α Β Γ Δ Ε<br />α β γ δ ε
            </p>
            <span>Begin with the letters. Build toward reading.</span>
            <small>A structured course in Classical Attic</small>
          </div>
        </section>
        <section className="featureGrid" aria-label="Ways to learn">
          <article className="card">
            <span className="eyebrow">01 · LEARN</span>
            <h2>A course with a story</h2>
            <p>
              Start with the alphabet. Build your reading skills through the
              story of an Athenian family, with lessons, exercises, and unit
              tests.
            </p>
            <Link href="/learn">Browse the course →</Link>
          </article>
          <article className="card">
            <span className="eyebrow">02 · READ</span>
            <h2>Read original Greek</h2>
            <p>
              Explore passages by Xenophon, Plato, and other Greek authors.
              Listen sentence by sentence and study unfamiliar words.
            </p>
            <Link href="/library">Browse readings →</Link>
          </article>
          <article className="card">
            <span className="eyebrow">03 · PRACTISE</span>
            <h2>Remember what you learn</h2>
            <p>
              Review vocabulary with spaced repetition and practise grammar
              based on the skills you have studied.
            </p>
            <Link href="/practice">Explore practice →</Link>
          </article>
        </section>
        <section className="homeTextLink">
          <h2>Already have a text?</h2>
          <p>
            <Link href="/library/new">Paste Greek or photograph a page</Link> to
            read and listen.
          </p>
        </section>
      </main>
    );
  const cp = progress.course;
  const chosen = course?.tracks.find((t) => t.id === cp.track);
  const trackResume = course?.tracks
    .flatMap((t) => t.lessons)
    .find((l) => cp.lessons[l.id]?.status === "in-progress");
  const next = course
    ? (trackResume?.id ??
      nextLesson(course, cp) ??
      (chosen ? trackState(cp, chosen).next : null))
    : null;
  const lesson = course && next ? findLesson(course, next) : null;
  const counts = course ? completedCount(course, cp) : null;
  const words = wordCounts(progress);
  const due = Object.values(progress.cards).filter(
    (c) => c.updated && c.due <= Date.now(),
  ).length;
  const weak = weakSkills(cp.skills, 6);
  const reread = course ? rereadSuggestion(course, cp, Date.now()) : null;
  const minutes = weeklyMinutes(progress);
  return (
    <main className="shell hubShell">
      <PageHeader
        eyebrow="YOUR LEARNING"
        title="Continue learning"
        action={
          <Link href="/practice/quick" className="secondary buttonLike">
            Quick 5 minutes
          </Link>
        }
      >
        Your course, reading, and practice in one place.
      </PageHeader>
      <div className="dashboardStats">
        <div className="statTile">
          <span className="statLabel">Known words</span>
          <strong className="statValue">{words.known}</strong>
          <span className="small muted">
            {words.learning} learning · recognition interval ≥ 7 days
          </span>
        </div>
        <div className="statTile">
          <span className="statLabel">Course streak</span>
          <strong className="statValue">
            {streakDays(cp)} <small>days</small>
          </strong>
        </div>
        <div className="statTile">
          <span className="statLabel">Weekly course goal</span>
          <strong className="statValue">
            {minutes} <small>/ {cp.goal.minutesPerDay * 7} min</small>
          </strong>
          <span className="small muted">
            Monday–Sunday · <Link href="/settings">Change daily goal</Link>
          </span>
        </div>
      </div>
      <div className="dashboardGrid">
        <section className="card">
          <p className="eyebrow">CONTINUE</p>
          {lesson ? (
            <>
              <h2 lang="grc">{lesson.title_grc}</h2>
              <p>
                Lesson {lesson.id} · {lesson.title_en}
              </p>
              <p className="muted">
                {cp.lessons[lesson.id]?.step != null
                  ? `Step ${cp.lessons[lesson.id].step! + 1} of 10`
                  : "Ready to begin"}
              </p>
              <Link
                href={`/learn/lesson/${lesson.id}`}
                className="primary buttonLike"
              >
                Resume lesson
              </Link>
            </>
          ) : (
            <>
              <h2>
                {error
                  ? "Course unavailable"
                  : course
                    ? "Choose your next reading"
                    : "Loading your course…"}
              </h2>
              <Link href={error ? "/learn" : "/library"}>
                {error ? "Try loading the course" : "Open the library"}
              </Link>
            </>
          )}
        </section>
        <section className="card">
          <h2>Today</h2>
          <ul className="reviewList">
            <li>
              <Link href="/words">Vocabulary cards due</Link>
              <strong>{due}</strong>
            </li>
            <li>
              <Link href="/practice/review">Skills to review</Link>
              <strong>{weak.length}</strong>
            </li>
            <li>
              <Link href="/practice/review?mode=mistakes">
                Mistakes to revisit
              </Link>
              <strong>{mistakeCount(cp.errors)}</strong>
            </li>
            {reread && (
              <li>
                <Link href={`/learn/lesson/${reread.id}?step=2&reread=1`}>
                  Reread Lesson {reread.id}
                </Link>
              </li>
            )}
          </ul>
        </section>
        <section className="card">
          <h2>Your path</h2>
          <p>
            {counts
              ? `${counts.done} of ${counts.total} main-course lessons complete`
              : "Course progress will appear here."}
          </p>
          <p className="muted">
            {chosen
              ? `Your track: ${chosen.title_en}`
              : "Interest tracks open after Unit 9."}
          </p>
          <Link href="/learn">View the course →</Link>
        </section>
        <section className="card">
          <h2>Read and listen</h2>
          <p>Explore original passages or bring a text of your own.</p>
          <Link href="/library">Open the library →</Link>
        </section>
      </div>
    </main>
  );
}
