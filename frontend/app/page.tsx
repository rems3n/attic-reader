"use client";

import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  base64ToObjectUrl,
  getTtsStatus,
  phonemize,
  runOcr,
  synthesizeBatch,
  TtsProvider,
} from "../lib/api";

type Status = "idle" | "ocr" | "phonemize" | "synthesize";
type PlayMode = "one" | "all";

type Clip = {
  index: number;
  text: string;
  ipa: string;
  url: string | null;
  duration: number | null;
};

type Reading = {
  provider: string;
  normalizedText: string;
  speed: number;
  clips: Clip[];
};

const SPEEDS = [0.6, 0.75, 1, 1.25] as const;

function formatSeconds(seconds: number | null): string {
  if (seconds == null) return "";
  return `${seconds.toFixed(1)}s`;
}

function releaseReading(reading: Reading | null) {
  reading?.clips.forEach((clip) => clip.url && URL.revokeObjectURL(clip.url));
}

export default function Home() {
  const [text, setText] = useState("");
  const [imageName, setImageName] = useState("");
  const [ipa, setIpa] = useState("");
  const [providers, setProviders] = useState<TtsProvider[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");

  // Reading state: the sentence clips currently loaded in the player.
  const [reading, setReading] = useState<Reading | null>(null);
  const [speed, setSpeed] = useState<number>(1);
  const [current, setCurrent] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [repeat, setRepeat] = useState(false);
  const [rerendering, setRerendering] = useState(false);

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

  useEffect(() => {
    getTtsStatus().then(setProviders).catch(() => setProviders([]));
  }, []);

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
      setText(recognized);
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

  const fetchReading = useCallback(async (source: string, atSpeed: number): Promise<Reading> => {
    const cached = cacheRef.current.get(atSpeed);
    if (cached && cached.normalizedText === source.trim()) return cached;
    const batch = await synthesizeBatch(source, atSpeed);
    const built: Reading = {
      provider: batch.provider,
      normalizedText: batch.normalized_text,
      speed: batch.speed,
      clips: batch.sentences.map((s) => ({
        index: s.index,
        text: s.text,
        ipa: s.ipa,
        url: s.audio_base64 ? base64ToObjectUrl(s.audio_base64, s.mime_type) : null,
        duration: s.duration_seconds,
      })),
    };
    cacheRef.current.set(atSpeed, built);
    return built;
  }, []);

  async function generateAudio() {
    if (!text.trim()) return;
    setStatus("synthesize");
    setError("");
    try {
      stopPlayback();
      cacheRef.current.forEach(releaseReading);
      cacheRef.current.clear();
      const built = await fetchReading(text, speed);
      setText(built.normalizedText);
      setIpa(built.clips.map((c) => c.ipa).join(" "));
      setReading(built);
      getTtsStatus().then(setProviders).catch(() => undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audio generation failed");
    } finally {
      setStatus("idle");
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
        {imageName && <p className="muted">{imageName}</p>}
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
            clearGenerated();
          }}
          placeholder="Ἐπεὶ δὲ ὁ Κῦρος…"
          spellCheck={false}
        />
        <div className="actions">
          <button className="secondary" onClick={previewPronunciation} disabled={!text.trim() || busy}>
            {status === "phonemize" ? "Converting…" : "Preview pronunciation"}
          </button>
          <button className="primary" onClick={generateAudio} disabled={!text.trim() || busy}>
            {status === "synthesize" ? "Generating…" : reading ? "Regenerate audio" : "Generate neural audio"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
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
                  className={`sentence ${isCurrent ? "active" : ""} ${clip.url ? "" : "silent"}`}
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
                    {clip.text}
                    <span className="sentenceMeta">{clip.url ? formatSeconds(clip.duration) : "no speech"}</span>
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
                ? "Re-rendering…"
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
