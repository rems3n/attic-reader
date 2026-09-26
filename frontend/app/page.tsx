"use client";

import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import WordCoverage from "../components/WordCoverage";
import { loadProgress } from "../lib/progress";
import type { CardState } from "../lib/srs";
import {
  base64ToObjectUrl,
  getLibrary,
  getLibraryCoverage,
  LibraryCoverage,
  getLibraryItem,
  getTtsStatus,
  phonemize,
  runOcr,
  synthesizeStream,
  LibraryIndex,
  LibraryItem,
  OcrReport,
  TtsProvider,
  WordTiming,
} from "../lib/api";

type Status = "idle" | "ocr" | "phonemize" | "synthesize";
type PlayMode = "one" | "all";

type Clip = {
  index: number;
  text: string;
  ipa: string;
  url: string | null;
  duration: number | null;
  words: WordTiming[] | null;
};

type Reading = {
  provider: string;
  normalizedText: string;
  speed: number;
  clips: Clip[];
};

// Learner multipliers on the backend base pace (KOKORO_SPEED). 1× is the
// narration pace accepted in the listening test; the default is deliberately
// slower for a beginner, and nothing faster than 1× is offered.
const SPEEDS = [0.5, 0.6, 0.75, 1] as const;
const DEFAULT_SPEED = 0.75;

function formatSeconds(seconds: number | null): string {
  if (seconds == null) return "";
  return `${seconds.toFixed(1)}s`;
}

/** Split a sentence into word spans so the spoken word can be highlighted. */
function renderWords(clip: Clip, activeWord: number | null) {
  if (!clip.words || clip.words.length === 0) return clip.text;
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  clip.words.forEach((w, i) => {
    if (w.start > cursor) parts.push(clip.text.slice(cursor, w.start));
    parts.push(
      <span key={i} className={`word ${activeWord === i ? "on" : ""}`}>
        {clip.text.slice(w.start, w.end)}
      </span>,
    );
    cursor = w.end;
  });
  if (cursor < clip.text.length) parts.push(clip.text.slice(cursor));
  return parts;
}

function releaseReading(reading: Reading | null) {
  reading?.clips.forEach((clip) => clip.url && URL.revokeObjectURL(clip.url));
}

export default function Home() {
  const [text, setText] = useState("");
  const [imageName, setImageName] = useState("");
  const [ocrReport, setOcrReport] = useState<OcrReport | null>(null);
  const [ipa, setIpa] = useState("");
  const [providers, setProviders] = useState<TtsProvider[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");

  // Reading state: the sentence clips currently loaded in the player.
  const [reading, setReading] = useState<Reading | null>(null);
  const [speed, setSpeed] = useState<number>(DEFAULT_SPEED);
  const [current, setCurrent] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [repeat, setRepeat] = useState(false);
  const [rerendering, setRerendering] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  // Index (into clip.words) of the word under the playhead of the active sentence.
  const [wordIndex, setWordIndex] = useState<number | null>(null);

  // Built-in library of Perseus passages.
  const [library, setLibrary] = useState<LibraryIndex | null>(null);
  const [libraryTab, setLibraryTab] = useState<string>("history");
  const [libraryItem, setLibraryItem] = useState<LibraryItem | null>(null);
  const [libraryOpen, setLibraryOpen] = useState(true);
  const [coverage, setCoverage] = useState<LibraryCoverage>({});
  const [cards, setCards] = useState<Record<string, CardState>>({});

  // One <audio> element for the whole app so iOS keeps it "user-activated"
  // after the first tap; play-all chains clips on this same element.
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const modeRef = useRef<PlayMode>("one");
  const repeatRef = useRef(false);
  const readingRef = useRef<Reading | null>(null);
  const currentRef = useRef<number | null>(null);
  const cacheRef = useRef<Map<number, Reading>>(new Map());
  const listRef = useRef<HTMLOListElement | null>(null);

  repeatRef.current = repeat;
  readingRef.current = reading;
  currentRef.current = current;

  const deepLink = useRef<{ reading: string; sentence: number } | null>(null);

  useEffect(() => {
    getTtsStatus().then(setProviders).catch(() => setProviders([]));
    getLibrary().then(setLibrary).catch(() => setLibrary(null));
    getLibraryCoverage().then(setCoverage).catch(() => setCoverage({}));
    setCards(loadProgress().cards);
    // /?reading=<id>&sentence=<n> (from vocabulary example sentences)
    const params = new URLSearchParams(window.location.search);
    const reading = params.get("reading");
    if (reading) deepLink.current = { reading, sentence: Number(params.get("sentence") ?? 0) || 0 };
  }, []);

  // Open the deep-linked passage once the library index has loaded.
  useEffect(() => {
    const link = deepLink.current;
    if (!library || !link) return;
    const item = library.items.find((i) => i.id === link.reading);
    if (!item) return;
    deepLink.current = null;
    void chooseReading(item).then(() => setCurrent(link.sentence));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [library]);

  useEffect(() => {
    const cache = cacheRef.current;
    return () => {
      cache.forEach(releaseReading);
      cache.clear();
    };
  }, []);

  const activeNeural = useMemo(
    () => providers.find((p) => p.enabled && p.available && p.quality === "neural"),
    [providers],
  );

  const providerLabel = reading ? (providers.find((p) => p.id === reading.provider)?.name ?? reading.provider) : "";

  function stopPlayback() {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
    }
    setPlaying(false);
    setCurrent(null);
  }

  function clearGenerated() {
    setIpa("");
    stopPlayback();
    cacheRef.current.forEach(releaseReading);
    cacheRef.current.clear();
    setReading(null);
  }

  async function handleImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setImageName(file.name);
    setError("");
    setStatus("ocr");
    try {
      const recognized = await runOcr(file);
      setText(recognized.text);
      setOcrReport(recognized.report);
      setLibraryItem(null);
      clearGenerated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "OCR failed");
    } finally {
      setStatus("idle");
    }
  }

  async function previewPronunciation() {
    if (!text.trim()) return;
    setStatus("phonemize");
    setError("");
    try {
      const result = await phonemize(text);
      setText(result.normalized_text);
      setIpa(result.ipa);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pronunciation conversion failed");
    } finally {
      setStatus("idle");
    }
  }

  /**
   * Render a reading at a given speed, streaming clips in. `onUpdate` receives
   * the reading each time a sentence arrives (same object identity is never
   * reused, so React re-renders). Resolves with the completed reading.
   */
  const fetchReading = useCallback(
    async (source: string, atSpeed: number, onUpdate?: (r: Reading) => void): Promise<Reading> => {
      const cached = cacheRef.current.get(atSpeed);
      if (cached && cached.normalizedText === source.trim()) return cached;
      let building: Reading | null = null;
      let failure = "";
      await synthesizeStream(source, atSpeed, (event) => {
        if (event.type === "start") {
          building = {
            provider: event.provider,
            normalizedText: event.normalized_text,
            speed: event.speed,
            clips: event.sentences.map((s) => ({ index: s.index, text: s.text, ipa: s.ipa, url: null, duration: null, words: null })),
          };
          setProgress({ done: 0, total: building.clips.length });
          onUpdate?.(building);
        } else if (event.type === "clip" && building) {
          const clips = building.clips.slice();
          const clip = clips[event.index];
          clips[event.index] = {
            ...clip,
            url: event.audio_base64 ? base64ToObjectUrl(event.audio_base64, event.mime_type) : null,
            duration: event.duration_seconds,
            words: event.words ?? null,
          };
          building = { ...building, clips };
          setProgress({ done: event.index + 1, total: clips.length });
          onUpdate?.(building);
        } else if (event.type === "error") {
          failure = event.detail;
        }
      });
      setProgress(null);
      if (failure) throw new Error(failure);
      if (!building) throw new Error("The server sent no audio.");
      cacheRef.current.set(atSpeed, building);
      return building;
    },
    [],
  );

  async function generateAudio(sourceText: string = text) {
    if (!sourceText.trim()) return;
    setStatus("synthesize");
    setError("");
    try {
      stopPlayback();
      cacheRef.current.forEach(releaseReading);
      cacheRef.current.clear();
      // Sentences appear as soon as the plan arrives; each becomes tappable
      // the moment its clip lands, while the rest are still rendering.
      const built = await fetchReading(sourceText, speed, (partial) => {
        readingRef.current = partial;
        setReading(partial);
        setText(partial.normalizedText);
      });
      setIpa(built.clips.map((c) => c.ipa).join(" "));
      setReading(built);
      getTtsStatus().then(setProviders).catch(() => undefined);
      getLibrary().then(setLibrary).catch(() => undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audio generation failed");
    } finally {
      setStatus("idle");
    }
  }

  /** Pick a library passage: load its text and start rendering immediately. */
  async function chooseReading(item: LibraryItem) {
    if (busy) return;
    setError("");
    setStatus("synthesize");
    try {
      const full = await getLibraryItem(item.id);
      setLibraryItem(full);
      setImageName("");
      setOcrReport(null);
      setText(full.text);
      clearGenerated();
      setLibraryOpen(false);
      setStatus("idle");
      await generateAudio(full.text);
    } catch (err) {
      setStatus("idle");
      setError(err instanceof Error ? err.message : "Could not load the reading");
    }
  }

  /** Load a clip into the shared element and play it. */
  const playIndex = useCallback((index: number, mode: PlayMode) => {
    const audio = audioRef.current;
    const active = readingRef.current;
    if (!audio || !active) return;
    const clip = active.clips[index];
    if (!clip?.url) return;
    modeRef.current = mode;
    setCurrent(index);
    setPlaying(true);
    if (audio.src !== clip.url) {
      audio.src = clip.url;
      audio.load();
    } else {
      audio.currentTime = 0;
    }
    void audio.play().catch(() => setPlaying(false));
  }, []);

  const nextPlayable = useCallback((from: number): number | null => {
    const active = readingRef.current;
    if (!active) return null;
    for (let i = from + 1; i < active.clips.length; i += 1) {
      if (active.clips[i].url) return i;
    }
    return null;
  }, []);

  const firstPlayable = useCallback((): number | null => nextPlayable(-1), [nextPlayable]);

  function handleEnded() {
    const audio = audioRef.current;
    const index = currentRef.current;
    if (!audio || index == null) return;
    if (repeatRef.current) {
      audio.currentTime = 0;
      void audio.play().catch(() => setPlaying(false));
      return;
    }
    if (modeRef.current === "all") {
      const next = nextPlayable(index);
      if (next != null) {
        playIndex(next, "all");
        return;
      }
    }
    setPlaying(false);
  }

  function toggleSentence(index: number) {
    const audio = audioRef.current;
    if (current === index && playing && audio) {
      audio.pause();
      setPlaying(false);
      return;
    }
    if (current === index && !playing && audio && audio.src) {
      modeRef.current = "one";
      setPlaying(true);
      void audio.play().catch(() => setPlaying(false));
      return;
    }
    playIndex(index, "one");
  }

  function togglePlayAll() {
    const audio = audioRef.current;
    if (playing && audio) {
      audio.pause();
      setPlaying(false);
      return;
    }
    if (current != null && audio && audio.src && modeRef.current === "all") {
      setPlaying(true);
      void audio.play().catch(() => setPlaying(false));
      return;
    }
    const start = current ?? firstPlayable();
    if (start != null) playIndex(start, "all");
  }

  function step(direction: -1 | 1) {
    const active = readingRef.current;
    if (!active) return;
    let index = current ?? (direction === 1 ? -1 : active.clips.length);
    for (;;) {
      index += direction;
      if (index < 0 || index >= active.clips.length) return;
      if (active.clips[index].url) break;
    }
    playIndex(index, modeRef.current);
  }

  async function changeSpeed(next: number) {
    setSpeed(next);
    const active = readingRef.current;
    const audio = audioRef.current;
    if (!active) return;
    // Immediate feedback: rate-shift the current clips while the neural voice
    // re-renders at the new pace (the re-render sounds better than rate-shift).
    if (audio) audio.playbackRate = next / active.speed;
    const cached = cacheRef.current.get(next);
    if (cached && cached.normalizedText === active.normalizedText) {
      swapReading(cached);
      return;
    }
    setRerendering(true);
    try {
      const built = await fetchReading(active.normalizedText, next);
      swapReading(built);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change speed");
    } finally {
      setRerendering(false);
    }
  }

  /** Replace clips in place; if something is playing, continue on the same sentence. */
  function swapReading(next: Reading) {
    const audio = audioRef.current;
    const index = currentRef.current;
    const wasPlaying = audio ? !audio.paused && !audio.ended : false;
    setReading(next);
    readingRef.current = next;
    if (audio) audio.playbackRate = 1;
    if (index != null && audio) {
      const clip = next.clips[index];
      if (clip?.url) {
        audio.src = clip.url;
        audio.load();
        if (wasPlaying) void audio.play().catch(() => setPlaying(false));
      }
    }
  }

  // Follow the playhead: while audio plays, find the word whose span covers
  // currentTime (binary search on t0) and highlight it. requestAnimationFrame
  // gives smoother tracking than the ~4 Hz 'timeupdate' event on iOS.
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !playing || current == null) {
      setWordIndex(null);
      return;
    }
    let frame = 0;
    let last = -1;
    const tick = () => {
      const words = readingRef.current?.clips[current]?.words;
      if (words && words.length) {
        const t = audio.currentTime;
        let lo = 0;
        let hi = words.length - 1;
        let found = -1;
        while (lo <= hi) {
          const mid = (lo + hi) >> 1;
          if (words[mid].t0 <= t) {
            found = mid;
            lo = mid + 1;
          } else {
            hi = mid - 1;
          }
        }
        // Between words (found.t1 < t < next.t0) keep the previous word lit so
        // the highlight never flickers off on short pauses.
        if (found !== last) {
          last = found;
          setWordIndex(found >= 0 ? found : null);
        }
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, current]);

  // Keep the active sentence in view during play-all.
  useEffect(() => {
    if (current == null || !listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(`[data-index="${current}"]`);
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [current]);

  const busy = status !== "idle";
  const hasClips = !!reading && reading.clips.some((c) => c.url);
  const currentClip = reading && current != null ? reading.clips[current] : null;

  return (
    <main className={`shell ${reading ? "hasPlayer" : ""}`}>
      <section className="hero">
        <p className="eyebrow">CLASSICAL ATTIC · READ ALOUD</p>
        <h1>Attic Reader</h1>
        <p className="lede">Photograph a page or paste polytonic Greek. Check the text, then listen sentence by sentence.</p>
      </section>

      <section className="voiceStrip" aria-live="polite">
        <div>
          <span className={`statusDot ${activeNeural ? "online" : "offline"}`} />
          <strong>{activeNeural ? activeNeural.name : "Neural voice not ready"}</strong>
        </div>
        <span>{activeNeural ? activeNeural.note : "Neural voice unavailable. Install/enable Kokoro on the backend; robotic eSpeak playback is disabled."}</span>
      </section>

      <section className="card libraryCard">
        <div className="sectionHead">
          <div>
            <h2>Choose a reading</h2>
            <p>Classic passages from the Perseus Digital Library, read in Classical Attic. Tap one to listen. The percentage is how many of its words are in the vocabulary lists: start with the highest.</p>
          </div>
          {library && (
            <button type="button" className="linkButton" onClick={() => setLibraryOpen((o) => !o)}>
              {libraryOpen ? "Hide" : `Show ${library.items.length}`}
            </button>
          )}
        </div>
        {library && libraryOpen && (
          <>
            <div className="tabs" role="tablist">
              {library.categories.map((c) => (
                <button
                  type="button"
                  key={c.id}
                  role="tab"
                  aria-selected={libraryTab === c.id}
                  className={`tab ${libraryTab === c.id ? "on" : ""}`}
                  onClick={() => setLibraryTab(c.id)}
                >
                  {c.label}
                </button>
              ))}
            </div>
            <ul className="readings">
              {library.items
                .filter((item) => item.category === libraryTab)
                .map((item) => {
                  const ready = item.ready_speeds.includes(speed);
                  const minutes = Math.max(1, Math.round(item.estimated_seconds / speed / 60));
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={`reading ${libraryItem?.id === item.id ? "on" : ""}`}
                        disabled={busy}
                        onClick={() => chooseReading(item)}
                      >
                        <span className="readingTop">
                          <span className="readingTitle">{item.title}</span>
                          <span className={`level ${item.level}`}>{item.level}</span>
                        </span>
                        <span className="readingRef">
                          {item.author}, <em>{item.work}</em> {item.ref} · {item.sentence_count} sentences · ~{minutes} min
                          {coverage[item.id] ? ` · ${Math.round(coverage[item.id].coverage * 100)} % known words` : ""}
                          {ready ? " · ready" : ""}
                        </span>
                        <span className="readingBlurb">{item.blurb}</span>
                      </button>
                    </li>
                  );
                })}
            </ul>
            {library.prerender.state === "running" && (
              <p className="muted">
                Preparing recordings on the server: {library.prerender.rendered}/{library.prerender.total} clips. Passages without
                &ldquo;ready&rdquo; still play, a sentence at a time.
              </p>
            )}
          </>
        )}
        {!library && <p className="muted">Library unavailable (backend not reachable).</p>}
      </section>

      <section className="card captureCard">
        <div>
          <h2>1. Add Greek</h2>
          <p>Use your camera, choose an image, or paste text below.</p>
        </div>
        <label className="cameraButton">
          <span>{status === "ocr" ? "Reading photo…" : "Take or upload photo"}</span>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleImage}
            disabled={busy}
          />
        </label>
        {imageName && (
          <p className="muted">
            {imageName}
            {ocrReport && ocrReport.engine.startsWith("opencv") && (
              <>
                {" · "}
                {ocrReport.lines ? `${ocrReport.lines} lines read` : "photo cleaned"}
                {ocrReport.deskewed ? `, straightened ${Math.abs(ocrReport.skew_degrees).toFixed(1)}°` : ""}
              </>
            )}
            {ocrReport && !ocrReport.engine.startsWith("opencv") && (
              <> · <span className="warnText">basic OCR mode: photo cleanup unavailable on the server</span></>
            )}
          </p>
        )}
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>2. Check the text</h2>
            <p>Correct OCR mistakes before generating audio.</p>
          </div>
          <span className="badge">Polytonic Greek</span>
        </div>
        <textarea
          className="greekInput"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setLibraryItem(null);
            clearGenerated();
          }}
          placeholder="Ἐπεὶ δὲ ὁ Κῦρος…"
          spellCheck={false}
        />
        <div className="actions">
          <button className="secondary" onClick={previewPronunciation} disabled={!text.trim() || busy}>
            {status === "phonemize" ? "Converting…" : "Preview pronunciation"}
          </button>
          <button className="primary" onClick={() => generateAudio()} disabled={!text.trim() || busy}>
            {status === "synthesize"
              ? progress
                ? `Rendering ${progress.done}/${progress.total}…`
                : "Starting the voice…"
              : reading
                ? "Regenerate audio"
                : "Generate neural audio"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        <WordCoverage text={text} cards={cards} label={libraryItem ? libraryItem.title : "this text"} />
        {ipa && !reading && (
          <details className="ipaPanel">
            <summary>Show Classical Attic pronunciation audit</summary>
            <p>{ipa}</p>
          </details>
        )}
      </section>

      {reading && (
        <section className="card readerCard">
          <div className="sectionHead">
            <div>
              <h2>3. Listen</h2>
              <p>Tap a sentence to hear it. Use the bar below to play everything.</p>
            </div>
            <span className="badge">{providerLabel}</span>
          </div>

          <ol className="sentences" ref={listRef}>
            {reading.clips.map((clip) => {
              const isCurrent = current === clip.index;
              const isPlaying = isCurrent && playing;
              return (
                <li
                  key={clip.index}
                  data-index={clip.index}
                  className={`sentence ${isCurrent ? "active" : ""} ${clip.url ? "" : status === "synthesize" ? "pending" : "silent"}`}
                >
                  <button
                    type="button"
                    className="sentenceButton"
                    aria-label={isPlaying ? "Stop sentence" : "Play sentence"}
                    aria-pressed={isPlaying}
                    disabled={!clip.url}
                    onClick={() => toggleSentence(clip.index)}
                  >
                    {isPlaying ? "■" : "▶"}
                  </button>
                  <button
                    type="button"
                    className="sentenceText"
                    lang="grc"
                    disabled={!clip.url}
                    onClick={() => toggleSentence(clip.index)}
                  >
                    <span className="sentenceWords">{renderWords(clip, isCurrent ? wordIndex : null)}</span>
                    <span className="sentenceMeta">
                      {clip.url ? formatSeconds(clip.duration) : status === "synthesize" ? "rendering…" : "no speech"}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>

          {currentClip && (
            <details className="ipaPanel">
              <summary>Pronunciation of the selected sentence</summary>
              <p>{currentClip.ipa}</p>
            </details>
          )}
          {libraryItem && (
            <p className="attribution">
              Text: {libraryItem.author}, <em>{libraryItem.work}</em> {libraryItem.ref}. {libraryItem.source.edition} ({libraryItem.source.license}).
            </p>
          )}
        </section>
      )}

      <p className="footnote">Pronunciation is driven by our Classical Attic rules and rendered by a phoneme-controlled neural voice — never Modern Greek phonology.</p>

      {/* The single shared audio element. playsInline keeps iOS from opening the full-screen player. */}
      <audio
        ref={audioRef}
        playsInline
        preload="auto"
        onEnded={handleEnded}
        onPause={() => setPlaying(false)}
        onPlay={() => setPlaying(true)}
      />

      {reading && (
        <nav className="playerBar" aria-label="Playback">
          <div className="playerRow">
            <button type="button" className="barButton" onClick={() => step(-1)} disabled={!hasClips} aria-label="Previous sentence">
              ⏮
            </button>
            <button type="button" className="barButton playAll" onClick={togglePlayAll} disabled={!hasClips} aria-label={playing ? "Pause" : "Play all"}>
              {playing ? "❚❚" : "▶ Play all"}
            </button>
            <button type="button" className="barButton" onClick={() => step(1)} disabled={!hasClips} aria-label="Next sentence">
              ⏭
            </button>
            <button
              type="button"
              className={`barButton repeat ${repeat ? "on" : ""}`}
              onClick={() => setRepeat((r) => !r)}
              aria-pressed={repeat}
              aria-label="Repeat this sentence"
              title="Repeat this sentence"
            >
              ↻
            </button>
          </div>
          <div className="playerRow speeds" role="group" aria-label="Speed">
            {SPEEDS.map((value) => (
              <button
                type="button"
                key={value}
                className={`speedButton ${speed === value ? "on" : ""}`}
                onClick={() => changeSpeed(value)}
                disabled={rerendering}
                aria-pressed={speed === value}
              >
                {value}×
              </button>
            ))}
            <span className="playerStatus">
              {rerendering
                ? progress
                  ? `Re-rendering ${progress.done}/${progress.total}…`
                  : "Re-rendering…"
                : current != null
                  ? `${current + 1} / ${reading.clips.length}${repeat ? " · repeat" : ""}`
                  : `${reading.clips.length} sentences`}
            </span>
          </div>
        </nav>
      )}
    </main>
  );
}
