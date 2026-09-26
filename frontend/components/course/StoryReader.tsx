"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { base64ToObjectUrl, synthesizeStream, type WordTiming } from "../../lib/api";
import type { Gloss, ImageRecord, StoryParagraph } from "../../lib/course";
import { normalizeAnswer } from "../../lib/normalize";
import { useSpeaker } from "../Speak";
import Picture, { imageById } from "./Picture";

type Clip = { start: number; end: number; url: string | null; words: WordTiming[] | null; text: string };

/**
 * The illustrated story: one paragraph per picture, sentences with LOGOS-style
 * glosses (tap a word), ▶ per sentence with spoken-word highlighting, and a
 * "listen to all" control. Audio comes from /api/synthesize/stream over the
 * whole story so the clips are cached server-side like a library passage.
 */
export default function StoryReader({ paragraphs, storyText, images, speed, showEnglish, hideText = false, autoStart = false }: { paragraphs: StoryParagraph[]; storyText: string; images: ImageRecord[]; speed: number; showEnglish: boolean; hideText?: boolean; autoStart?: boolean }) {
  const [clips, setClips] = useState<Clip[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [current, setCurrent] = useState<number | null>(null); // clip index
  const [wordIndex, setWordIndex] = useState<number | null>(null);
  const [playAll, setPlayAll] = useState(false);
  const [gloss, setGloss] = useState<{ key: string; gloss: Gloss } | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const clipsRef = useRef<Clip[] | null>(null);
  const playAllRef = useRef(false);
  const imageMap = useMemo(() => new Map(images.map((i) => [i.id, i])), [images]);
  const { play: speakWord, busy } = useSpeaker(speed);
  clipsRef.current = clips;
  playAllRef.current = playAll;

  // Flat sentence list with character offsets into the normalized story text.
  const sentences = useMemo(() => {
    const norm = storyText.replace(/\s+/g, " ").trim();
    let cursor = 0;
    const out: { pi: number; si: number; text: string; start: number; end: number }[] = [];
    paragraphs.forEach((p, pi) =>
      p.sentences.forEach((s, si) => {
        const text = s.text.replace(/\s+/g, " ").trim();
        const at = norm.indexOf(text, cursor);
        const start = at >= 0 ? at : cursor;
        out.push({ pi, si, text, start, end: start + text.length });
        cursor = start + text.length;
      }),
    );
    return out;
  }, [paragraphs, storyText]);

  const clipsFor = useCallback(
    (sentenceIndex: number): number[] => {
      const s = sentences[sentenceIndex];
      if (!clips || !s) return [];
      return clips.map((c, i) => (c.start >= s.start && c.start < s.end ? i : -1)).filter((i) => i >= 0);
    },
    [clips, sentences],
  );

  const load = useCallback(async () => {
    if (clips || loading) return clips;
    setLoading(true);
    setError("");
    const built: Clip[] = [];
    try {
      await synthesizeStream(storyText, speed, (event) => {
        if (event.type === "start") {
          event.sentences.forEach((s) => built.push({ start: s.start, end: s.end, url: null, words: null, text: s.text }));
          setClips([...built]);
        } else if (event.type === "clip") {
          const c = built[event.index];
          if (c) {
            c.url = event.audio_base64 ? base64ToObjectUrl(event.audio_base64, event.mime_type) : null;
            c.words = event.words ?? null;
          }
          setClips([...built]);
        } else if (event.type === "error") {
          setError(event.detail);
        }
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Audio unavailable");
    } finally {
      setLoading(false);
    }
    return built;
  }, [clips, loading, storyText, speed]);

  // Speed change → drop the clips; they reload on the next play.
  useEffect(() => {
    setClips(null);
    setCurrent(null);
  }, [speed, storyText]);

  useEffect(() => {
    if (autoStart) void startAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart]);

  function audio(): HTMLAudioElement {
    if (!audioRef.current) {
      const a = new Audio();
      a.preload = "auto";
      a.setAttribute("playsinline", "");
      a.addEventListener("ended", () => {
        setWordIndex(null);
        if (playAllRef.current) {
          const list = clipsRef.current ?? [];
          setCurrent((prev) => {
            const next = prev == null ? null : prev + 1;
            if (next != null && next < list.length) {
              queueMicrotask(() => void playClip(next));
              return next;
            }
            setPlayAll(false);
            return null;
          });
        } else {
          setCurrent(null);
        }
      });
      audioRef.current = a;
    }
    return audioRef.current;
  }

  async function playClip(i: number): Promise<void> {
    const list = clipsRef.current ?? (await load());
    const c = list?.[i];
    if (!c) return;
    if (!c.url) {
      // still rendering: wait a moment and retry (the stream fills in order)
      await new Promise((r) => setTimeout(r, 400));
      return playClip(i);
    }
    const a = audio();
    a.src = c.url;
    a.load();
    setCurrent(i);
    setWordIndex(null);
    try {
      await a.play();
    } catch {
      /* autoplay blocked: the user taps ▶ */
    }
  }

  async function playSentence(sentenceIndex: number) {
    setPlayAll(false);
    const list = clipsRef.current ?? (await load());
    if (!list) return;
    const ids = clipsFor(sentenceIndex);
    if (!ids.length) return;
    // play the sentence's clips in a row
    playAllRef.current = false;
    for (const id of ids) {
      await playClip(id);
      await new Promise<void>((resolve) => {
        const a = audio();
        const done = () => {
          a.removeEventListener("ended", done);
          resolve();
        };
        a.addEventListener("ended", done);
      });
    }
  }

  async function startAll() {
    const list = clipsRef.current ?? (await load());
    if (!list?.length) return;
    setPlayAll(true);
    playAllRef.current = true;
    setCurrent(0);
    await playClip(0);
  }

  function stop() {
    setPlayAll(false);
    playAllRef.current = false;
    audioRef.current?.pause();
    setCurrent(null);
    setWordIndex(null);
  }

  // Follow the playhead for the active clip.
  useEffect(() => {
    if (current == null) return;
    let frame = 0;
    const tick = () => {
      const a = audioRef.current;
      const words = clipsRef.current?.[current]?.words;
      if (a && words && words.length) {
        const t = a.currentTime;
        let lo = 0;
        let hi = words.length - 1;
        let found = -1;
        while (lo <= hi) {
          const mid = (lo + hi) >> 1;
          if (words[mid].t0 <= t) {
            found = mid;
            lo = mid + 1;
          } else hi = mid - 1;
        }
        setWordIndex(found >= 0 ? found : null);
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [current]);

  const glossMap = useMemo(() => {
    const m = new Map<string, Gloss>();
    paragraphs.forEach((p) => p.sentences.forEach((s) => (s.glosses ?? []).forEach((g) => m.set(normalizeAnswer(g.word), g))));
    return m;
  }, [paragraphs]);

  function renderSentence(sIndex: number) {
    const s = sentences[sIndex];
    const ids = clipsFor(sIndex);
    const active = current != null && ids.includes(current);
    const pieces: React.ReactNode[] = [];
    // Split into words; highlight by clip timing when this sentence is active.
    const activeClip = active && current != null ? clips?.[current] : null;
    const activeWords = activeClip?.words ?? null;
    const clipOffset = activeClip ? activeClip.start - s.start : 0;
    let k = 0;
    const re = /(\s+)/g;
    let last = 0;
    let match: RegExpExecArray | null;
    const words: { text: string; start: number }[] = [];
    while ((match = re.exec(s.text))) {
      if (match.index > last) words.push({ text: s.text.slice(last, match.index), start: last });
      words.push({ text: match[0], start: match.index });
      last = match.index + match[0].length;
    }
    if (last < s.text.length) words.push({ text: s.text.slice(last), start: last });
    for (const w of words) {
      if (/^\s+$/.test(w.text)) {
        pieces.push(w.text);
        continue;
      }
      const key = normalizeAnswer(w.text);
      const g = glossMap.get(key);
      let lit = false;
      if (activeWords && wordIndex != null && activeWords[wordIndex]) {
        const t = activeWords[wordIndex];
        const localStart = w.start - clipOffset;
        lit = localStart >= t.start && localStart < t.end;
      }
      pieces.push(
        <button key={k++} type="button" className={`storyWord ${g ? "glossed" : ""} ${lit ? "lit" : ""}`} lang="grc" aria-expanded={g ? gloss?.key === `${sIndex}-${w.start}` : undefined} onClick={() => {
          if (g) setGloss(gloss?.key === `${sIndex}-${w.start}` ? null : { key: `${sIndex}-${w.start}`, gloss: g });
          else void speakWord(w.text.replace(/[.,;·!?«»]/g, ""));
        }}>
          {w.text}
        </button>,
      );
    }
    return pieces;
  }

  return (
    <div className={`story ${hideText ? "hidden" : ""}`}>
      <div className="storyControls">
        {playAll ? (
          <button type="button" className="primary" onClick={stop}>■ Stop</button>
        ) : (
          <button type="button" className="primary" onClick={() => void startAll()} disabled={loading}>{loading ? "rendering…" : "▶ Ἀκούσατε · listen to all"}</button>
        )}
        {error && <span className="warnText">{error}</span>}
      </div>
      {paragraphs.map((p, pi) => (
        <div key={pi} className="storyPara">
          <Picture image={p.image_record ?? imageById(imageMap, p.image)} size="panel" />
          {!hideText && (
            <div className="storyText">
              {p.sentences.map((s, si) => {
                const sIndex = sentences.findIndex((x) => x.pi === pi && x.si === si);
                const active = current != null && clipsFor(sIndex).includes(current);
                return (
                  <div key={si} className={`storySentence ${active ? "active" : ""}`}>
                    <button type="button" className="sentencePlay" aria-label={`Play sentence ${sIndex + 1}`} onClick={() => void playSentence(sIndex)}><span aria-hidden="true">▶</span></button>
                    <p className="storyLine" lang="grc">{renderSentence(sIndex)}</p>
                    {gloss && gloss.key.startsWith(`${sIndex}-`) && <GlossCard gloss={gloss.gloss} images={imageMap} showEnglish={showEnglish} onSpeak={speakWord} busy={busy} />}
                  </div>
                );
              })}
              <aside className="glossMargin" aria-label={`Glosses, picture ${pi + 1}`}>
                {p.sentences.flatMap((s) => s.glosses ?? []).map((g, i) => (
                  <GlossLine key={i} gloss={g} images={imageMap} showEnglish={showEnglish} onSpeak={speakWord} />
                ))}
              </aside>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function GlossLine({ gloss, images, showEnglish, onSpeak }: { gloss: Gloss; images: Map<string, ImageRecord>; showEnglish: boolean; onSpeak: (t: string) => void }) {
  if (gloss.kind === "en" && !showEnglish) return null;
  if (gloss.kind === "note" && !showEnglish) return null;
  return (
    <div className={`glossLine kind-${gloss.kind === "pic" ? "pic" : "text"}`}>
      <button type="button" className="glossWord" lang="grc" onClick={() => onSpeak(gloss.word)}>{gloss.word}</button>
      {gloss.kind === "pic" ? (
        <Picture image={imageById(images, gloss.value)} size="thumb" caption={false} />
      ) : (
        <span className="glossValue" lang={gloss.kind === "en" || gloss.kind === "note" ? "en" : "grc"}>
          {gloss.kind === "=" || gloss.kind === "↔" || gloss.kind === "<" ? `${gloss.kind} ` : gloss.kind === "en" ? "= " : ""}{gloss.value}
        </span>
      )}
    </div>
  );
}

function GlossCard({ gloss, images, showEnglish, onSpeak, busy }: { gloss: Gloss; images: Map<string, ImageRecord>; showEnglish: boolean; onSpeak: (t: string) => void; busy: string | null }) {
  return (
    <div className="glossCard" role="status">
      <GlossLine gloss={gloss} images={images} showEnglish={true} onSpeak={onSpeak} />
      {!showEnglish && (gloss.kind === "en" || gloss.kind === "note") && <span className="muted">(English shown on tap)</span>}
      {busy === gloss.word && <span className="muted"> …</span>}
    </div>
  );
}
