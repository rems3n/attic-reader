"use client";

import { useMemo, useState } from "react";
import type { OriginalText as Original, StoryParagraph } from "../../lib/course";
import { SpeakButton, useSpeaker } from "../Speak";

/**
 * The original passage a Stage 2 story adapts (Thucydides, Xenophon, Plato,
 * Lysias). Each original sentence can show, underneath, the story sentences
 * written from it (the story's `orig` indices), so the learner sees how the
 * adaptation simplified the real text.
 */
export default function OriginalText({ original, story, speed }: { original: Original; story: StoryParagraph[]; speed: number }) {
  const [open, setOpen] = useState(false);
  const [compare, setCompare] = useState(true);
  const { play, busy } = useSpeaker(speed);
  const adapted = useMemo(() => {
    const map = new Map<number, string[]>();
    for (const p of story) for (const s of p.sentences) for (const i of s.orig ?? []) map.set(i, [...(map.get(i) ?? []), s.text]);
    return map;
  }, [story]);
  const aligned = adapted.size > 0;
  const cite = [original.author, original.work, original.ref].filter(Boolean).join(", ");

  return (
    <section className="original" aria-label="The original text">
      <button type="button" className="originalToggle" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="eyebrow">ΤΟ ΑΡΧΑΙΟΝ · THE ORIGINAL</span>
        <span className="originalTitle">{cite}</span>
        <span className="muted small">{open ? "Hide" : aligned ? "Read the real text this story adapts" : "Read the real text"}</span>
      </button>
      {open && (
        <div className="originalBody">
          {original.note && <p className="stepHint">{original.note}</p>}
          {aligned && (
            <label className="checkRow small">
              <input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} /> Show the adapted sentences under each original sentence
            </label>
          )}
          <ol className="originalList">
            {original.sentences.map((s, i) => (
              <li key={i}>
                <p lang="grc" className="originalLine">
                  {s.length <= 600 && <SpeakButton text={s} play={play} busy={busy} small />} {s}
                </p>
                {compare && adapted.get(i) && (
                  <ul className="adaptedUnder">
                    {adapted.get(i)!.map((a, j) => <li key={j} lang="grc">{a}</li>)}
                  </ul>
                )}
              </li>
            ))}
          </ol>
          {original.source && (
            <p className="attribution">
              Greek text: {original.source.edition ?? "Perseus Digital Library"}
              {original.source.license ? `, ${original.source.license}` : ""}
              {original.source.url ? <> · <a href={original.source.url} target="_blank" rel="noreferrer">source</a></> : null}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
