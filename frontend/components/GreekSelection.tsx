"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { GreekLookup, lookupGreek, translateGreek } from "../lib/api";

type Pick = { text: string; context: string; left: number; top: number };
const greek = /[\u0370-\u03ff\u1f00-\u1fff]/;
const cache = new Map<string, GreekLookup>();

export default function GreekSelection() {
  const path = usePathname();
  const popup = useRef<HTMLDivElement>(null);
  const [pick, setPick] = useState<Pick | null>(null);
  const [result, setResult] = useState<GreekLookup | null>(null);
  const [error, setError] = useState("");
  const [translation, setTranslation] = useState("");
  const [translationError, setTranslationError] = useState("");
  const [retry, setRetry] = useState(0);

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
      let context = "";
      let rect: DOMRect | undefined;
      if (active instanceof HTMLTextAreaElement && active.lang === "grc") {
        text = active.value.slice(active.selectionStart, active.selectionEnd).trim();
        context = active.value.slice(Math.max(0, active.selectionStart - 800), active.selectionEnd + 800);
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
        const passage = parent?.closest("p, blockquote, [data-greek-context]") ?? parent;
        const surrounding = passage?.textContent ?? text;
        const index = surrounding.indexOf(text);
        const start = Math.max(0, index - 800);
        context = index < 0 ? text : surrounding.slice(start, start + 4000);
        rect = range.getBoundingClientRect();
      }
      if (!text) { dismissed = ""; setPick(null); return; }
      if (!greek.test(text) || text === dismissed || !rect) { setPick(null); return; }
      const width = Math.min(340, window.innerWidth - 24);
      setPick({ text, context: context.slice(0, 4000), left: Math.max(12, Math.min(rect.left, window.innerWidth - width - 12)),
        top: Math.max(12, Math.min(rect.bottom + 12, window.innerHeight - 380)) });
    };
    const schedule = () => { clearTimeout(timer); timer = setTimeout(inspect, 350); };
    const down = (event: PointerEvent) => {
      interacting = !!popup.current?.contains(event.target as Node);
      dragging = !interacting;
      if (!interacting) dismissed = "";
    };
    const up = () => { dragging = false; schedule(); setTimeout(() => { interacting = false; }, 0); };
    const dismiss = () => {
      dismissed = window.getSelection()?.toString().trim() ||
        (document.activeElement instanceof HTMLTextAreaElement ? document.activeElement.value.slice(document.activeElement.selectionStart, document.activeElement.selectionEnd).trim() : "");
      setPick(null);
    };
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") dismiss(); };
    const scroll = (event: Event) => {
      // Chrome can scroll/focus the page while making a native selection.
      // Never mark a selection dismissed before its popup has even opened.
      if (!popup.current || dragging) return;
      if (!(event.target instanceof Node) || !popup.current.contains(event.target)) dismiss();
    };
    const released = (event: MouseEvent) => { if (dragging && event.buttons === 0) up(); };
    const close = () => dismiss();
    document.addEventListener("selectionchange", schedule);
    document.addEventListener("select", schedule, true);
    window.addEventListener("pointerdown", down, true);
    window.addEventListener("pointerup", up, true);
    window.addEventListener("pointercancel", up, true);
    window.addEventListener("mouseup", up, true);
    window.addEventListener("mousemove", released, true);
    window.addEventListener("blur", up);
    document.addEventListener("keydown", key);
    document.addEventListener("scroll", scroll, true);
    document.addEventListener("close-greek-definition", close);
    window.addEventListener("resize", dismiss);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("selectionchange", schedule);
      document.removeEventListener("select", schedule, true);
      window.removeEventListener("pointerdown", down, true);
      window.removeEventListener("pointerup", up, true);
      window.removeEventListener("pointercancel", up, true);
      window.removeEventListener("mouseup", up, true);
      window.removeEventListener("mousemove", released, true);
      window.removeEventListener("blur", up);
      document.removeEventListener("keydown", key);
      document.removeEventListener("scroll", scroll, true);
      document.removeEventListener("close-greek-definition", close);
      window.removeEventListener("resize", dismiss);
    };
  }, [path]);

  useEffect(() => {
    setResult(null); setError("");
    if (!pick) return;
    if (pick.text.length > 2000 || pick.text.split(/\s+/).length > 200) {
      setError("Select up to 200 words and 2,000 characters."); return;
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

  useEffect(() => {
    setTranslation(""); setTranslationError("");
    if (!pick || pick.text.length > 2000 || pick.text.split(/\s+/).length > 200) return;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 22000);
    let current = true;
    translateGreek(pick.text, pick.context, controller.signal).then(data => {
      if (current) setTranslation(data.translation);
    }).catch(error => {
      if (current) setTranslationError(error instanceof Error && error.name !== "AbortError"
        ? error.message : "Translation timed out. Please try again.");
    }).finally(() => clearTimeout(timeout));
    return () => { current = false; clearTimeout(timeout); controller.abort(); };
  }, [pick?.text, pick?.context, retry]);

  if (!pick) return null;
  return <div ref={popup} className="greekDefinition" role="dialog" aria-modal="false" aria-labelledby="greek-definition-title"
    style={{ left: pick.left, top: pick.top }}>
    <header><strong id="greek-definition-title">English translation</strong>
      <button type="button" aria-label="Close translation" onClick={() => document.dispatchEvent(new Event("close-greek-definition"))}>×</button></header>
    <div className="greekDefinitionBody" aria-live="polite" aria-busy={!result && !error}>
      <p className="greekSelectionText" lang="grc" title={pick.text}>{pick.text.length > 80 ? `${pick.text.slice(0,80)}…` : pick.text}</p>
      {pick.text.length <= 2000 && pick.text.split(/\s+/).length <= 200 && <section className="greekPassageTranslation" aria-label="Translation" aria-busy={!translation && !translationError}>
        {translation ? <><p>{translation}</p><span className="muted">AI translation</span></>
          : translationError ? <><p>{translationError}</p><button type="button" onClick={() => setRetry(n => n + 1)}>Retry translation</button></>
          : <p>Translating selection…</p>}
      </section>}
      <h3 className="greekWordHeading">Word definitions</h3>
      {error ? <p>{error}</p> : !result ? <p>Looking up…</p> : result.words.map((word, i) => <section key={i}>
        {result.words.length > 1 && <strong lang="grc">{word.text}</strong>}
        {word.matches.length > 1 && <p className="muted">Possible matches</p>}
        {word.matches.length === 0 ? <p>No definition found in the app’s dictionary.</p> : word.matches.map(match => <div className="greekDefinitionEntry" key={match.id}>
          <Link href={`/words/${encodeURIComponent(match.id)}`} lang="grc">{match.lemma}</Link>
          <span className="muted"> {match.pos}</span><p>{match.definition}</p>
        </div>)}
      </section>)}
      {result && <p className="muted greekDefinitionNote">Dictionary meanings; the meaning depends on context.</p>}
    </div>
  </div>;
}
