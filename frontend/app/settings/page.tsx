"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import PageHeader from "../../components/PageHeader";
import {
  emptyProgress,
  exportProgress,
  importProgress,
  loadProgress,
  saveProgress,
  syncPull,
  syncPush,
} from "../../lib/progress";
export default function Settings() {
  const [p, setP] = useState(emptyProgress);
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const file = useRef<HTMLInputElement>(null);
  useEffect(() => {
    setP(loadProgress());
    setReady(true);
  }, []);
  useEffect(() => {
    if (ready) saveProgress(p);
  }, [p, ready]);
  async function sync(pull: boolean) {
    setBusy(true);
    setMessage("");
    try {
      if (pull) {
        const r = await syncPull(p);
        setP(r.progress);
        setMessage(
          r.found ? "Progress imported." : "No progress found for this code.",
        );
      } else {
        setP(await syncPush(p));
        setMessage("Progress saved to your sync code.");
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Sync failed.");
    } finally {
      setBusy(false);
    }
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([exportProgress(p)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "attic-reader-progress.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <main className="shell narrowShell">
      <PageHeader title="Settings">
        Learning preferences and progress backup.
      </PageHeader>
      <section className="card">
        <h2>Guest mode</h2>
        <p>
          Your progress is saved in this browser. Export a backup before
          clearing browser data or moving to another device.
        </p>
      </section>
      <section className="card settingsFields">
        <h2>Learning</h2>
        <label>
          Daily course goal (minutes)
          <input
            type="number"
            min="1"
            max="120"
            value={p.course.goal.minutesPerDay}
            onChange={(e) =>
              setP({
                ...p,
                course: {
                  ...p.course,
                  goal: {
                    minutesPerDay: Math.max(
                      1,
                      Math.min(120, Number(e.target.value) || 1),
                    ),
                  },
                },
              })
            }
          />
        </label>
        <label>
          Accent marking
          <select
            value={p.settings.accents}
            onChange={(e) =>
              setP({
                ...p,
                settings: {
                  ...p.settings,
                  accents: e.target.value as typeof p.settings.accents,
                },
              })
            }
          >
            <option value="auto">Course default (strict from Unit 4)</option>
            <option value="lenient">Lenient</option>
            <option value="strict">Strict</option>
          </select>
        </label>
        <label>
          <input
            type="checkbox"
            checked={p.settings.showEnglish}
            onChange={(e) =>
              setP({
                ...p,
                settings: { ...p.settings, showEnglish: e.target.checked },
              })
            }
          />{" "}
          Show English explanations
        </label>
        <label>
          <input
            type="checkbox"
            checked={p.settings.autoSpeak}
            onChange={(e) =>
              setP({
                ...p,
                settings: { ...p.settings, autoSpeak: e.target.checked },
              })
            }
          />{" "}
          Speak flash cards automatically
        </label>
      </section>
      <section className="card settingsFields">
        <h2>Data</h2>
        <div className="actions">
          <button className="secondary" onClick={download}>
            Export progress
          </button>
          <button className="secondary" onClick={() => file.current?.click()}>
            Import backup
          </button>
        </div>
        <input
          ref={file}
          hidden
          type="file"
          accept=".json,application/json"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            if (f.size > 2 * 1024 * 1024) {
              setMessage("Choose a backup smaller than 2 MB.");
              return;
            }
            try {
              const text = await f.text();
              const doc = JSON.parse(text);
              if (
                !doc ||
                !doc.cards ||
                typeof doc.cards !== "object" ||
                ![1, 2].includes(doc.version)
              )
                throw new Error("Choose an Attic Reader progress backup.");
              setP(importProgress(text, p));
              setMessage("Backup imported.");
            } catch {
              setMessage(
                "Could not import this backup. Choose an Attic Reader progress JSON file.",
              );
            }
            e.target.value = "";
          }}
        />
        <label>
          Sync code
          <input
            value={p.settings.syncCode}
            onChange={(e) =>
              setP({
                ...p,
                settings: { ...p.settings, syncCode: e.target.value },
              })
            }
            autoComplete="off"
          />
        </label>
        <p className="muted small">
          Use a long, private code. Anyone with the code can read or replace its
          saved progress.
        </p>
        <div className="actions">
          <button
            className="secondary"
            disabled={busy || !p.settings.syncCode.trim()}
            onClick={() => sync(true)}
          >
            Import from sync code
          </button>
          <button
            className="secondary"
            disabled={busy || !p.settings.syncCode.trim()}
            onClick={() => sync(false)}
          >
            Save to sync code
          </button>
        </div>
        <p role="status">{message}</p>
      </section>
      <p>
        <Link href="/learn/credits">Image credits</Link> ·{" "}
        <Link href="/help#data">Offline and progress help</Link>
      </p>
    </main>
  );
}
