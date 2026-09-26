"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import EmptyState from "../../components/EmptyState";
import { emptyProgress, loadProgress } from "../../lib/progress";
import { weakSkills } from "../../lib/course";
import { mistakeCount } from "../../lib/skills";
export default function Practice() {
  const [p, setP] = useState(emptyProgress);
  useEffect(() => setP(loadProgress()), []);
  const weak = weakSkills(p.course.skills, 6).length;
  const mistakes = mistakeCount(p.course.errors);
  const due = Object.values(p.cards).filter(
    (c) => c.updated && c.due <= Date.now(),
  ).length;
  return (
    <main className="shell hubShell">
      <PageHeader
        title="Practice"
        eyebrow="REVIEW · WORDS · DRILLS"
        action={
          <Link href="/practice/quick" className="secondary buttonLike">
            Quick 5 minutes
          </Link>
        }
      >
        Review vocabulary and revisit the skills that need more practice.
      </PageHeader>
      <div className="featureGrid">
        <section className="card">
          <h2>Words</h2>
          <p>{due} vocabulary cards due.</p>
          <p>Choose a deck, study new words, or review due cards.</p>
          <Link href="/words" className="primary buttonLike">
            Open Words
          </Link>
        </section>
        <section className="card">
          <h2>Skills review</h2>
          <p>{weak} skills to revisit.</p>
          <Link href="/practice/review" className="secondary buttonLike">
            Review skills
          </Link>
          <p>
            <Link href="/progress">Browse skills and drills →</Link>
          </p>
        </section>
        <section className="card">
          <h2>Mistakes</h2>
          <p>{mistakes} items to revisit.</p>
          <Link
            href="/practice/review?mode=mistakes"
            className="secondary buttonLike"
          >
            Review mistakes
          </Link>
        </section>
      </div>
      {!due && !weak && !mistakes && (
        <EmptyState
          title="Your review starts with learning"
          href="/learn"
          action="Open the course"
        >
          Complete a lesson or study a vocabulary deck. Due cards, weak skills,
          and mistakes will appear here.
        </EmptyState>
      )}
    </main>
  );
}
