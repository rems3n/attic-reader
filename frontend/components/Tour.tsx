"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
export default function Tour() {
  const path = usePathname();
  const [step, setStep] = useState<number | null>(null);
  useEffect(() => {
    try {
      const s = localStorage.getItem("attic.tour");
      setStep(s && s !== "done" ? Number(s) : null);
    } catch {}
  }, [path]);
  if (step == null || path === "/start") return null;
  const items = [
    [
      "Move between sections",
      "Use the sidebar on desktop or the tabs at the bottom of your phone. More contains Grammar, Progress, Settings, and Help.",
    ],
    [
      "Pick up where you left off",
      "Home shows your Continue card after you begin a lesson. Lesson steps and vocabulary reviews are saved on this device.",
    ],
    [
      "Find help when you need it",
      "Help in the top bar explains the page you are on. Settings lets you change learning preferences and back up progress.",
    ],
  ];
  const current = items[step] ?? items[0];
  const advance = (value: number | null) => {
    setStep(value);
    try {
      localStorage.setItem(
        "attic.tour",
        value == null ? "done" : String(value),
      );
    } catch {}
  };
  return (
    <aside className="tourCard" aria-label="App tour">
      <p className="eyebrow">QUICK TOUR · {step + 1} / 3</p>
      <h2>{current[0]}</h2>
      <p>{current[1]}</p>
      <div className="actions">
        <button
          type="button"
          className="primary"
          onClick={() => advance(step === 2 ? null : step + 1)}
        >
          {step === 2 ? "Finish tour" : "Next"}
        </button>
        <button
          type="button"
          className="linkButton"
          onClick={() => advance(null)}
        >
          Dismiss tour
        </button>
      </div>
    </aside>
  );
}
