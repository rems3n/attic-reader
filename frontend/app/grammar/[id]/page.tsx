"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import FormsTable from "../../../components/FormsTable";
import { SpeakButton, useSpeaker } from "../../../components/Speak";
import { getGrammarItem, type GrammarItem } from "../../../lib/api";

export default function ParadigmPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(String(params?.id ?? ""));
  const [item, setItem] = useState<GrammarItem | null>(null);
  const [error, setError] = useState("");
  const { play, busy } = useSpeaker();

  useEffect(() => {
    if (!id) return;
    getGrammarItem(id)
      .then(setItem)
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load the paradigm"));
  }, [id]);

  if (error) return <main className="shell"><p className="error">{error}</p></main>;
  if (!item) return <main className="shell"><p className="muted">Loading…</p></main>;

  return (
    <main className="shell">
      <p className="crumbs"><Link href="/grammar">← Grammar</Link></p>
      <section className="wordHeader">
        <div className="wordTitle">
          <h1 lang="grc">{item.title}</h1>
          <SpeakButton text={item.lemma} play={play} busy={busy} />
        </div>
        <p className="wordDef">{item.explanation}</p>
      </section>
      {item.table && (
        <section className="card">
          <h2>Paradigm</h2>
          <p className="muted small">Tap any form to hear it.</p>
          <FormsTable forms={item.table} play={play} />
        </section>
      )}
      {item.examples.length > 0 && (
        <section className="card">
          <h2>Examples</h2>
          <ul className="examples">
            {item.examples.map((ex, i) => (
              <li key={i}>
                <p className="exampleText" lang="grc">
                  {ex.greek} <SpeakButton text={ex.greek} play={play} busy={busy} small />
                </p>
                <p className="exampleMeta">{ex.english}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
      <p className="footnote">
        <Link href="/vocab">Study this word in Vocab →</Link>
      </p>
    </main>
  );
}
