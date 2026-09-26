"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getVocab } from "../../../lib/api";
import { loadProgress } from "../../../lib/progress";
import { weakSkills } from "../../../lib/course";
import PageHeader from "../../../components/PageHeader";
export default function Quick() {
  const [target, setTarget] = useState<string | null>(null);
  useEffect(() => {
    const p = loadProgress();
    const due = Object.entries(p.cards)
      .filter(([, c]) => c.updated && c.due <= Date.now())
      .sort((a, b) => a[1].due - b[1].due)
      .map(([k]) => k.split(":")[0]);
    if (due.length)
      setTarget(
        `/words?words=${[...new Set(due)].slice(0, 10).join(",")}&from=Quick%205%20minutes&quick=1`,
      );
    else if (weakSkills(p.course.skills, 6).length)
      setTarget("/practice/review?quick=1");
    else
      getVocab()
        .then((v) =>
          setTarget(
            `/words?words=${v.items
              .slice(0, 5)
              .map((w) => w.id)
              .join(",")}&from=Quick%205%20minutes&quick=1`,
          ),
        )
        .catch(() => setTarget("/learn/lesson/0.1?quick=1"));
  }, []);
  return (
    <main className="shell narrowShell">
      <PageHeader title="Quick 5 minutes">
        A short session based on your progress.
      </PageHeader>
      <section className="card">
        <h2>Practise a little now</h2>
        <p>
          Start with due vocabulary, then weak skills. If you are new, begin
          with a few common words. The timer will remind you when five minutes
          have passed; it will not interrupt an answer.
        </p>
        {target ? (
          <Link href={target} className="primary buttonLike">
            Start five minutes
          </Link>
        ) : (
          <p role="status">Preparing your session…</p>
        )}
      </section>
    </main>
  );
}
