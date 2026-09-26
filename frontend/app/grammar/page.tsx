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
      {error && <p className="error" role="alert">{error}</p>}
      {!sections && !error && (
        <div aria-busy="true">
          <p className="loadingLine" role="status">Loading the paradigms…</p>
          <div className="skeleton skCard" aria-hidden="true" />
        </div>
      )}
      {sections && sections.length > 1 && (
        <nav className="card jumpLinks" aria-label="Sections">
          <ul className="chips">
            {sections.map((s) => (
              <li key={s.id}><a className="chip" href={`#${s.id}`}>{s.title}</a></li>
            ))}
          </ul>
        </nav>
      )}
      {sections?.map((s) => (
        <section className="card anchorTarget" key={s.id} id={s.id} aria-labelledby={`h-${s.id}`}>
          <h2 id={`h-${s.id}`}>{s.title}</h2>
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
