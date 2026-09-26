"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { analyzeText, type Analysis } from "../lib/api";
import type { CardState } from "../lib/srs";

/** Words studied = any flash card of that word graded at least once. */
export function studiedIds(cards: Record<string, CardState>): Set<string> {
  const out = new Set<string>();
  for (const [key, card] of Object.entries(cards)) if (card.updated > 0) out.add(key.split(":")[0]);
  return out;
}

/**
 * Guided reading (Stage 4): how much of the text the core list covers, which
 * of its words the learner has not studied yet (one tap → a deck of them),
 * and which words the lexicon does not know (to look up or gloss).
 */
export default function WordCoverage({ text, cards, label }: { text: string; cards: Record<string, CardState>; label: string }) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setAnalysis(null);
    setFailed(false);
    if (!text.trim()) return;
    const handle = window.setTimeout(() => {
      analyzeText(text).then(setAnalysis).catch(() => setFailed(true));
    }, 500);
    return () => window.clearTimeout(handle);
  }, [text]);

  const studied = useMemo(() => studiedIds(cards), [cards]);
  if (!text.trim() || failed) return null;
  if (!analysis) return <p className="muted small coverageLine">Checking the words…</p>;
  if (!analysis.words) return null;

  const fresh = analysis.entries.filter((e) => !studied.has(e.id));
  const pct = Math.round(analysis.coverage * 100);
  const known = analysis.entries.length - fresh.length;
  const knownPct = analysis.entries.length ? Math.round((known / analysis.entries.length) * 100) : 0;

  return (
    <div className="coverage">
      <div className="coverageStats">
        <div><strong>{pct} %</strong><span>of the words are in the lexicon ({Math.round(analysis.dcc_coverage * 100)} % core list)</span></div>
        <div><strong>{analysis.entries.length}</strong><span>different words · you have studied {known} ({knownPct} %)</span></div>
        <div><strong>{analysis.unknown.length}</strong><span>not in the lexicon (look up or gloss)</span></div>
      </div>
      <div className="actions">
        {fresh.length > 0 && (
          <Link href={`/vocab?words=${fresh.map((e) => e.id).join(",")}&from=${encodeURIComponent(label)}`} className="secondary buttonLike">
            Study the {fresh.length} new word{fresh.length === 1 ? "" : "s"}
          </Link>
        )}
        <button type="button" className="linkButton" aria-expanded={open} onClick={() => setOpen((o) => !o)}>{open ? "Hide words" : "Show words"}</button>
      </div>
      {open && (
        <div className="coverageLists">
          {fresh.length > 0 && (
            <>
              <h3 className="chipTitle">New to you</h3>
              <ul className="trackWords">
                {fresh.map((e) => (
                  <li key={e.id}><Link href={`/vocab/${e.id}`} lang="grc" className="trackWordLemma">{e.lemma}</Link><span className="muted">{e.short}</span></li>
                ))}
              </ul>
            </>
          )}
          {analysis.unknown.length > 0 && (
            <>
              <h3 className="chipTitle">Not in the lexicon</h3>
              <p lang="grc" className="unknownWords">{analysis.unknown.map((u) => u.text).join(" · ")}</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
