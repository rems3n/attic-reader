"use client";

import { useCallback, useRef, useState } from "react";
import { speak } from "../lib/api";

let shared: HTMLAudioElement | null = null;
function audioElement(): HTMLAudioElement {
  if (!shared) {
    shared = new Audio();
    shared.preload = "auto";
    shared.setAttribute("playsinline", "");
  }
  return shared;
}

/** Play a word or phrase through the shared audio element. */
export function useSpeaker(speed = 0.75) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const last = useRef<string>("");
  const play = useCallback(
    async (text: string) => {
      const clean = text.replace(/\(ν\)$/, "ν").replace(/[()]/g, "").split(" / ")[0].trim();
      if (!clean) return;
      setBusy(text);
      setError("");
      try {
        const url = await speak(clean, speed);
        const audio = audioElement();
        if (last.current !== url) {
          audio.src = url;
          audio.load();
          last.current = url;
        } else {
          audio.currentTime = 0;
        }
        await audio.play();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not play");
      } finally {
        setBusy(null);
      }
    },
    [speed],
  );
  return { play, busy, error };
}

export function SpeakButton({ text, play, busy, small }: { text: string; play: (t: string) => void; busy: string | null; small?: boolean }) {
  return (
    <button type="button" className={`speak ${small ? "small" : ""} ${busy === text ? "busy" : ""}`} onClick={() => play(text)} aria-label={`Play ${text}`}>
      ▶
    </button>
  );
}
