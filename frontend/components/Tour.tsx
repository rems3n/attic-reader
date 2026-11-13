"use client";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

/**
 * First-visit product tour. A spotlight moves over the real navigation and a
 * card explains each area. It starts when `attic.tour` holds a step number
 * (set by /start, the home page and Help → "Replay the tour") and ends by
 * storing "done". `startTour()` restarts it from anywhere.
 */
export const TOUR_KEY = "attic.tour";
export const TOUR_EVENT = "attic-tour";
export function startTour() {
  try {
    localStorage.setItem(TOUR_KEY, "0");
  } catch {}
  window.dispatchEvent(new Event(TOUR_EVENT));
}

/** Restarts the tour; used on the Help page. */
export function ReplayTourButton() {
  return (
    <button type="button" className="secondary" onClick={startTour}>
      Replay the tour
    </button>
  );
}

type Step = { target?: string; title: string; body: string };
export const TOUR_STEPS: Step[] = [
  {
    title: "Welcome to Attic Academy",
    body: "Here is a one-minute look at where everything lives. You can skip it and replay it later from Help.",
  },
  {
    target: "learn",
    title: "Learn: the course",
    body: "Eighty lessons that follow a potter's family through Athens, from the alphabet to real authors. Each lesson has a story, listening, grammar and a final check.",
  },
  {
    target: "library",
    title: "Library: read and listen",
    body: "Passages from Plato, Xenophon and others, or a page you photograph or paste. Tap a sentence to hear it in Classical Attic, and select any word to see its meaning.",
  },
  {
    target: "practice",
    title: "Practice: make it stick",
    body: "Flash cards that come back just before you forget them, drills on your weak skills, and a Quick 5 minutes session for busy days.",
  },
  {
    target: "grammar",
    title: "Grammar: every form, spoken",
    body: "Model tables for nouns, adjectives and verbs with the rules behind them. Tap any form to hear it.",
  },
  {
    target: "progress",
    title: "Progress: see how far you have come",
    body: "Your skills, streak, known words and the mistakes worth revisiting.",
  },
  {
    target: "help",
    title: "Help for the page you are on",
    body: "Help explains whichever page you are on, including how the pronunciation works.",
  },
  {
    target: "account",
    title: "Keep your progress",
    body: "As a guest, progress is saved on this device. Create a free account to carry it to your phone and laptop.",
  },
];

type Box = { top: number; left: number; width: number; height: number };
const PAD = 6;

/** The visible element for a step: sidebar link on desktop, tab on a phone,
 *  or the More button when the link lives in the More sheet. */
function locate(target: string): { el: HTMLElement; viaMore: boolean } | null {
  const visible = (el: Element) => {
    const r = (el as HTMLElement).getBoundingClientRect();
    return r.width > 0 && r.height > 0 && !(el as HTMLElement).closest("dialog");
  };
  const hit = [...document.querySelectorAll(`[data-tour="${target}"]`)].find(visible);
  if (hit) return { el: hit as HTMLElement, viaMore: false };
  const more = [...document.querySelectorAll('[data-tour="more"]')].find(visible);
  return more ? { el: more as HTMLElement, viaMore: true } : null;
}

export default function Tour() {
  const path = usePathname();
  const [step, setStep] = useState<number | null>(null);
  const [box, setBox] = useState<Box | null>(null);
  const [viaMore, setViaMore] = useState(false);
  const [pop, setPop] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const card = useRef<HTMLDivElement>(null);
  const next = useRef<HTMLButtonElement>(null);

  const read = useCallback(() => {
    try {
      const s = localStorage.getItem(TOUR_KEY);
      const n = s && s !== "done" ? Number(s) : NaN;
      setStep(Number.isInteger(n) && n >= 0 && n < TOUR_STEPS.length ? n : null);
    } catch {
      setStep(null);
    }
  }, []);
  useEffect(() => {
    read();
    window.addEventListener(TOUR_EVENT, read);
    return () => window.removeEventListener(TOUR_EVENT, read);
  }, [path, read]);

  const active = step != null && path !== "/start" && path !== "/account";
  const current = active ? TOUR_STEPS[step] : null;

  const go = (value: number | null) => {
    setStep(value);
    try {
      localStorage.setItem(TOUR_KEY, value == null ? "done" : String(value));
    } catch {}
  };

  const place = useCallback(() => {
    if (!current) return;
    const found = current.target ? locate(current.target) : null;
    setViaMore(!!found?.viaMore);
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const cw = card.current?.offsetWidth ?? 360;
    const ch = card.current?.offsetHeight ?? 220;
    if (!found) {
      setBox(null);
      setPop({ top: Math.max(12, (vh - ch) / 2), left: Math.max(12, (vw - cw) / 2) });
      return;
    }
    const r = found.el.getBoundingClientRect();
    const b = { top: r.top - PAD, left: r.left - PAD, width: r.width + PAD * 2, height: r.height + PAD * 2 };
    setBox(b);
    const gap = 14;
    let top: number;
    let left: number;
    if (b.left + b.width + gap + cw <= vw - 12 && b.width < vw * 0.5) {
      // beside (desktop sidebar)
      left = b.left + b.width + gap;
      top = b.top;
    } else if (b.top + b.height + gap + ch <= vh - 12) {
      left = b.left + b.width / 2 - cw / 2; // below (top bar)
      top = b.top + b.height + gap;
    } else {
      left = b.left + b.width / 2 - cw / 2; // above (phone tab bar)
      top = b.top - gap - ch;
    }
    setPop({
      top: Math.min(Math.max(12, top), Math.max(12, vh - ch - 12)),
      left: Math.min(Math.max(12, left), Math.max(12, vw - cw - 12)),
    });
  }, [current]);

  useLayoutEffect(() => {
    if (!current) return;
    place();
    const again = () => place();
    window.addEventListener("resize", again);
    window.addEventListener("scroll", again, true);
    const t = setTimeout(again, 60); // after the card has its real height
    return () => {
      clearTimeout(t);
      window.removeEventListener("resize", again);
      window.removeEventListener("scroll", again, true);
    };
  }, [current, place, viaMore]);

  useEffect(() => {
    if (current) next.current?.focus({ preventScroll: true });
  }, [current]);

  if (!current || step == null) return null;
  const last = step === TOUR_STEPS.length - 1;
  return (
    <div
      className="tourLayer"
      role="dialog"
      aria-modal="true"
      aria-label="App tour"
      onKeyDown={(e) => {
        if (e.key === "Escape") go(null);
        if (e.key === "ArrowRight" && !last) go(step + 1);
        if (e.key === "ArrowLeft" && step > 0) go(step - 1);
        if (e.key === "Tab") {
          // keep focus inside the card
          const items = card.current?.querySelectorAll<HTMLElement>("button");
          if (!items?.length) return;
          const first = items[0];
          const end = items[items.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            end.focus();
          } else if (!e.shiftKey && document.activeElement === end) {
            e.preventDefault();
            first.focus();
          }
        }
      }}
    >
      <div className={`tourSpot ${box ? "" : "none"}`} style={box ?? undefined} aria-hidden="true" />
      <div className="tourPop" ref={card} style={pop}>
        <p className="tourCount">
          Quick tour · {step + 1} of {TOUR_STEPS.length}
        </p>
        <h2>{current.title}</h2>
        <p>{current.body}</p>
        {viaMore && <p className="tourNote">On a phone you will find it under More.</p>}
        <div className="tourDots" aria-hidden="true">
          {TOUR_STEPS.map((_, i) => (
            <span key={i} className={i === step ? "on" : ""} />
          ))}
        </div>
        <div className="tourActions">
          {step > 0 && (
            <button type="button" className="secondary" onClick={() => go(step - 1)}>
              Back
            </button>
          )}
          <button type="button" className="primary" ref={next} onClick={() => go(last ? null : step + 1)}>
            {last ? "Finish tour" : "Next"}
          </button>
          {!last && (
            <button type="button" className="linkButton" onClick={() => go(null)}>
              Skip tour
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
