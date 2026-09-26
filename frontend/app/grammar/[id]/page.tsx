"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import FormsTable from "../../../components/FormsTable";
import { SpeakButton, useSpeaker } from "../../../components/Speak";
import { getGrammar, getGrammarItem, type GrammarItem, type GrammarSection } from "../../../lib/api";
import Crumbs from "../../../components/Crumbs";
import { PageError, PageLoading } from "../../../components/PageState";

export default function ParadigmPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(String(params?.id ?? ""));
  const [item, setItem] = useState<GrammarItem | null>(null);
  const [error, setError] = useState("");
  const [sections, setSections] = useState<GrammarSection[]>([]);
  const { play, busy } = useSpeaker();

  useEffect(() => {
    getGrammar().then((g) => setSections(g.sections)).catch(() => setSections([]));
  }, []);

  useEffect(() => {
    if (!id) return;
    getGrammarItem(id)
      .then(setItem)
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load the paradigm"));
  }, [id]);

  if (error) return <PageError message={error} crumbs={[{ label: "Grammar", href: "/grammar" }, { label: id }]} back={{ href: "/grammar", label: "All paradigms" }} />;
  if (!item) return <PageLoading label="Loading the paradigm…" crumbs={[{ label: "Grammar", href: "/grammar" }, { label: "…" }]} />;

  // neighbours in the reference order, across sections
  const flat = sections.flatMap((s) => s.items.map((i) => ({ ...i, section: s })));
  const at = flat.findIndex((i) => i.id === item.id);
  const prev = at > 0 ? flat[at - 1] : null;
  const next = at >= 0 && at < flat.length - 1 ? flat[at + 1] : null;
  const section = sections.find((s) => s.id === item.section) ?? flat[at]?.section;

  return (
    <main className="shell">
      <Crumbs items={[{ label: "Grammar", href: "/grammar" }, ...(section ? [{ label: section.title, href: `/grammar#${section.id}` }] : []), { label: item.lemma, lang: "grc" }]} />
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
      {(prev || next) && (
        <nav className="pager" aria-label="Other paradigms">
          {prev ? (
            <Link href={`/grammar/${encodeURIComponent(prev.id)}`} className="pagerLink prev">
              <span className="pagerDir">‹ Previous</span>
              <span className="pagerTitle">{prev.title}</span>
            </Link>
          ) : <span />}
          {next ? (
            <Link href={`/grammar/${encodeURIComponent(next.id)}`} className="pagerLink next">
              <span className="pagerDir">Next ›</span>
              <span className="pagerTitle">{next.title}</span>
            </Link>
          ) : <span />}
        </nav>
      )}
      <p className="footnote">
        <Link href="/grammar">All paradigms</Link> · <Link href="/words">Vocab</Link>
      </p>
    </main>
  );
}
