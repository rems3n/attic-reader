"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getGrammar, type GrammarSection } from "../../lib/api";

export default function GrammarPage() {
  const [sections, setSections] = useState<GrammarSection[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getGrammar()
      .then((g) => setSections(g.sections))
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load grammar"));
  }, []);

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">CLASSICAL ATTIC · REFERENCE</p>
        <h1>Grammar</h1>
        <p className="lede">Model paradigms with the rules behind them. Every form can be tapped to hear it; the same engine builds the tables on each vocabulary page.</p>
      </section>
      {error && <p className="error">{error}</p>}
      {!sections && !error && <p className="muted">Loading…</p>}
      {sections?.map((s) => (
        <section className="card" key={s.id}>
          <h2>{s.title}</h2>
          <p>{s.blurb}</p>
          <ul className="paradigmList">
            {s.items.map((p) => (
              <li key={p.id}>
                <Link className="paradigmRow" href={`/grammar/${encodeURIComponent(p.id)}`}>
                  <span lang="grc" className="paradigmLemma">{p.lemma}</span>
                  <span className="paradigmTitle">{p.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
