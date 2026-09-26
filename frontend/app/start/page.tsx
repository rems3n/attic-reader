"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import ExerciseRunner, {
  type Outcome,
} from "../../components/course/ExerciseRunner";
import { getPlacement } from "../../lib/api";
import type { PlacementBlock } from "../../lib/course";
export default function Start() {
  const [goal, setGoal] = useState("beginner");
  const [level, setLevel] = useState("alphabet");
  const [checking, setChecking] = useState(false);
  const [block, setBlock] = useState<PlacementBlock | null>(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState<number | null>(null);
  useEffect(() => {
    if (checking)
      getPlacement(1)
        .then((p) => setBlock(p.blocks[0]))
        .catch(() =>
          setError(
            "The check could not load. You can start at the alphabet or use the full placement test.",
          ),
        );
  }, [checking]);
  const tour = () => {
    try {
      localStorage.setItem("attic.tour", "0");
    } catch {}
  };
  const target =
    goal === "reader"
      ? "/library"
      : goal === "beginner" ||
          level === "alphabet" ||
          (result != null && result < 4)
        ? "/learn/lesson/0.1"
        : "/learn/lesson/1.1";
  return (
    <main className="shell narrowShell">
      <PageHeader eyebrow="GET STARTED" title="Where would you like to begin?">
        Choose a starting point. You can explore every section without an
        account.
      </PageHeader>
      {!checking ? (
        <section className="card">
          <fieldset className="onboardOptions">
            <legend>Your goal</legend>
            {[
              [
                "beginner",
                "Learn from the beginning",
                "Start with the alphabet, then follow the course.",
              ],
              [
                "brush",
                "Return to Greek",
                "Choose your level or take a short starting check.",
              ],
              [
                "reader",
                "Read and listen",
                "Go straight to original texts and audio.",
              ],
            ].map(([id, title, detail]) => (
              <label
                key={id}
                className={`choiceCard ${goal === id ? "selected" : ""}`}
              >
                <input
                  type="radio"
                  name="goal"
                  value={id}
                  checked={goal === id}
                  onChange={() => setGoal(id)}
                />
                <span>
                  <strong>{title}</strong>
                  <small>{detail}</small>
                </span>
              </label>
            ))}
          </fieldset>
          {goal === "brush" && (
            <fieldset className="onboardOptions">
              <legend>Your level</legend>
              {[
                ["alphabet", "I need to revisit the alphabet"],
                ["basics", "I can read the alphabet and know some basic forms"],
              ].map(([id, title]) => (
                <label key={id} className="choiceCard">
                  <input
                    type="radio"
                    name="level"
                    checked={level === id}
                    onChange={() => setLevel(id)}
                  />
                  {title}
                </label>
              ))}
            </fieldset>
          )}
          <div className="actions">
            <Link href={target} className="primary buttonLike" onClick={tour}>
              Continue
            </Link>
            {goal === "brush" && level === "basics" && (
              <button
                type="button"
                className="secondary"
                onClick={() => setChecking(true)}
              >
                Take a 6-question check
              </button>
            )}
          </div>
          <p className="muted small">
            For placement beyond Unit 1, use the{" "}
            <Link href="/learn/placement">full placement test</Link>.
          </p>
        </section>
      ) : (
        <section className="card">
          <h2>Starting check</h2>
          <p>
            Six questions from Unit 1. This recommends a starting point; it does
            not skip lessons or change your mastery.
          </p>
          {error ? (
            <p role="alert">
              {error} <Link href="/learn/placement">Full placement test</Link>
            </p>
          ) : result != null ? (
            <>
              <p>
                <strong>
                  {result} / {Math.min(6, block?.items.length ?? 6)}
                </strong>{" "}
                correct.
              </p>
              <p>
                {result >= 4
                  ? "Start with Unit 1, or use the full placement test if this felt familiar."
                  : "Begin with the alphabet and work through the foundations."}
              </p>
              <Link href={target} onClick={tour} className="primary buttonLike">
                Open recommended lesson
              </Link>
            </>
          ) : block ? (
            <ExerciseRunner
              items={block.items.slice(0, 6)}
              images={[]}
              mode="test"
              accents={false}
              seed={1}
              onDone={(out: Outcome[]) =>
                setResult(out.filter((o) => o.result.correct).length)
              }
            />
          ) : (
            <p role="status">Loading six questions…</p>
          )}
          <p>
            <button
              type="button"
              className="linkButton"
              onClick={() => {
                setChecking(false);
                setResult(null);
              }}
            >
              Back to starting options
            </button>
          </p>
        </section>
      )}
    </main>
  );
}
