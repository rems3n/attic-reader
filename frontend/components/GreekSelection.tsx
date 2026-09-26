"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { GreekLookup, lookupGreek } from "../lib/api";

type Pick = { text: string; left: number; top: number };
const greek = /[\u0370-\u03ff\u1f00-\u1fff]/;
const cache = new Map<string, GreekLookup>();

export default function GreekSelection() {
  const path = usePathname();
  const popup = useRef<HTMLDivElement>(null);
  const [pick, setPick] = useState<Pick | null>(null);
  const [result, setResult] = useState<GreekLookup | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let dragging = false;
    let interacting = false;
    let dismissed = "";
    setPick(null);
    const inspect = () => {
      if (dragging || interacting) return;
      const selection = window.getSelection();
      const active = document.activeElement;
      let text = "";
      let rect: DOMRect | undefined;
      if (active instanceof HTMLTextAreaElement && active.lang === "grc") {
        text = active.value.slice(active.selectionStart, active.selectionEnd).trim();
        rect = active.getBoundingClientRect();
      } else if (selection?.rangeCount && !selection.isCollapsed) {
        const range = selection.getRangeAt(0);
        const parent = range.commonAncestorContainer instanceof Element
          ? range.commonAncestorContainer : range.commonAncestorContainer.parentElement;
        if (parent?.closest(".greekDefinition")) return;
        if (!parent?.closest("main") || parent.closest("input, textarea, [contenteditable=true]")) {
          setPick(null); return;
        }
        text = selection.toString().trim();
        rect = range.getBoundingClientRect();
      }
      if (!text) { dismissed = ""; setPick(null); return; }
      if (!greek.test(text) || text === dismissed || !rect) { setPick(null); return; }
      const width = Math.min(340, window.innerWidth - 24);
      setPick({ text, left: Math.max(12, Math.min(rect.left, window.innerWidth - width - 12)),
        top: Math.max(12, Math.min(rect.bottom + 12, window.innerHeight - 380)) });
    };
    const schedule = () => { clearTimeout(timer); timer = setTimeout(inspect, 350); };
    const down = (event: PointerEvent) => {
      interacting = !!popup.current?.contains(event.target as Node);
      dragging = !interacting;
    };
    const up = () => { dragging = false; schedule(); setTimeout(() => { interacting = false; }, 0); };
    const dismiss = () => {
      dismissed = window.getSelection()?.toString().trim() ||
        (document.activeElement instanceof HTMLTextAreaElement ? document.activeElement.value.slice(document.activeElement.selectionStart, document.activeElement.selectionEnd).trim() : "");
      setPick(null);
    };
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") dismiss(); };
    const scroll = (event: Event) => { if (!(event.target instanceof Node) || !popup.current?.contains(event.target)) dismiss(); };
    const close = () => dismiss();
    document.addEventListener("selectionchange", schedule);
    document.addEventListener("select", schedule, true);
    document.addEventListener("pointerdown", down);
    document.addEventListener("pointerup", up);
    document.addEventListener("pointercancel", up);
    document.addEventListener("keydown", key);
    document.addEventListener("scroll", scroll, true);
    document.addEventListener("close-greek-definition", close);
    window.addEventListener("resize", dismiss);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("selectionchange", schedule);
      document.removeEventListener("select", schedule, true);
      document.removeEventListener("pointerdown", down);
      document.removeEventListener("pointerup", up);
      document.removeEventListener("pointercancel", up);
      document.removeEventListener("keydown", key);
      document.removeEventListener("scroll", scroll, true);
      document.removeEventListener("close-greek-definition", close);
      window.removeEventListener("resize", dismiss);
    };
  }, [path]);

  useEffect(() => {
    setResult(null); setError("");
    if (!pick) return;
    if (pick.text.length > 240 || pick.text.split(/\s+/).length > 12) {
      setError("Select up to 12 words to see their definitions."); return;
    }
    const saved = cache.get(pick.text);
    if (saved) { setResult(saved); return; }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    let current = true;
    lookupGreek(pick.text, controller.signal).then(data => {
      if (!current) return;
      if (cache.size >= 100) cache.delete(cache.keys().next().value!);
      cache.set(pick.text, data); setResult(data);
    }).catch(() => {
      if (current) setError("Definitions could not be loaded. Check your connection and select the word again.");
    }).finally(() => clearTimeout(timeout));
    return () => { current = false; clearTimeout(timeout); controller.abort(); };
  }, [pick?.text]);

  if (!pick) return null;
  return <div ref={popup} className="greekDefinition" role="dialog" aria-modal="false" aria-labelledby="greek-definition-title"
    style={{ left: pick.left, top: pick.top }}>
    <header><strong id="greek-definition-title">English definition</strong>
      <button type="button" aria-label="Close definition" onClick={() => document.dispatchEvent(new Event("close-greek-definition"))}>×</button></header>
    <div className="greekDefinitionBody" aria-live="polite" aria-busy={!result && !error}>
      <p className="greekSelectionText" lang="grc">{pick.text.length > 240 ? `${pick.text.slice(0,240)}…` : pick.text}</p>
      {error ? <p>{error}</p> : !result ? <p>Looking up…</p> : result.words.map((word, i) => <section key={i}>
        {result.words.length > 1 && <strong lang="grc">{word.text}</strong>}
        {word.matches.length > 1 && <p className="muted">Possible matches</p>}
        {word.matches.length === 0 ? <p>No definition found in the app’s dictionary.</p> : word.matches.map(match => <div className="greekDefinitionEntry" key={match.id}>
          <Link href={`/words/${encodeURIComponent(match.id)}`} lang="grc">{match.lemma}</Link>
          <span className="muted"> {match.pos}</span><p>{match.definition}</p>
        </div>)}
      </section>)}
      {result && <p className="muted greekDefinitionNote">Dictionary meanings; the meaning depends on context.{result.words.length > 1 ? " This is a word-by-word lookup." : ""}</p>}
    </div>
  </div>;
}
