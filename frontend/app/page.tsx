"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { getTtsStatus, phonemize, runOcr, synthesize, TtsProvider } from "../lib/api";

type Status = "idle" | "ocr" | "phonemize" | "synthesize";

export default function Home() {
  const [text, setText] = useState("");
  const [imageName, setImageName] = useState("");
  const [ipa, setIpa] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioProvider, setAudioProvider] = useState<string | null>(null);
  const [providers, setProviders] = useState<TtsProvider[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    getTtsStatus().then(setProviders).catch(() => setProviders([]));
  }, []);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const activeNeural = useMemo(
    () => providers.find((p) => p.enabled && p.available && p.quality === "neural"),
    [providers],
  );

  const providerLabel = providers.find((p) => p.id === audioProvider)?.name ?? audioProvider;

  function clearGenerated() {
    setIpa("");
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setAudioProvider(null);
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

  async function generateAudio() {
    if (!text.trim()) return;
    setStatus("synthesize");
    setError("");
    try {
      const result = await phonemize(text);
      setText(result.normalized_text);
      setIpa(result.ipa);
      const generated = await synthesize(result.normalized_text);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(URL.createObjectURL(generated.audio));
      setAudioProvider(generated.provider);
      getTtsStatus().then(setProviders).catch(() => undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audio generation failed");
    } finally {
      setStatus("idle");
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">CLASSICAL ATTIC · READ ALOUD</p>
        <h1>Attic Reader</h1>
        <p className="lede">Photograph a page or paste polytonic Greek. Check the text, then generate a neural Ancient Greek reading.</p>
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
            disabled={status !== "idle"}
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
      </section>

      <section className="card">
        <h2>3. Listen</h2>
        <p>Pronunciation is driven by our Classical Attic rules and rendered by a phoneme-controlled neural voice — never Modern Greek phonology.</p>
        <div className="actions">
          <button className="secondary" onClick={previewPronunciation} disabled={!text.trim() || status !== "idle"}>
            {status === "phonemize" ? "Converting…" : "Preview pronunciation"}
          </button>
          <button className="primary" onClick={generateAudio} disabled={!text.trim() || status !== "idle"}>
            {status === "synthesize" ? "Generating…" : "Generate neural audio"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {audioUrl && (
          <div className="player">
            <div className="playerMeta">
              <span>Voice</span>
              <strong>{providerLabel}</strong>
            </div>
            <audio src={audioUrl} controls preload="metadata" />
          </div>
        )}

        {ipa && (
          <details className="ipaPanel">
            <summary>Show Classical Attic pronunciation audit</summary>
            <p>{ipa}</p>
          </details>
        )}
      </section>

      <p className="footnote">Current target: natural non-Modern Ancient Greek audio. The dedicated neural model is being audited against a Classical Attic reconstruction before we call the pronunciation final.</p>
    </main>
  );
}
