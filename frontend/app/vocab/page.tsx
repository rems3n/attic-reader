"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import FormsTable from "../../components/FormsTable";
import { SpeakButton, useSpeaker } from "../../components/Speak";
import { getVocab, getVocabEntry, type Forms, type VocabEntry, type VocabIndex, type VocabItem } from "../../lib/api";
import {
  bumpLog,
  exportProgress,
  importProgress,
  loadProgress,
  newCardsToday,
  saveProgress,
  syncPull,
  syncPush,
  type Progress,
} from "../../lib/progress";
import { CARD_TYPES, cardKey, describeInterval, grade, isNew, pickSession, type CardType, type Grade } from "../../lib/srs";

type Filters = { topics: Set<string>; tiers: Set<number>; kinds: Set<string>; groups: Set<string>; readings: Set<string> };
type Mode = "build" | "study" | "done";
type Prompt = { key: string; item: VocabItem; type: CardType; fresh: boolean };
type FormsQuestion = { label: string; answer: string[] };

const TYPE_LABEL: Record<CardType, string> = { recognition: "Greek → English", production: "English → Greek", forms: "Forms drill", parts: "Principal parts" };
const CASE_LABEL: Record<string, string> = { nom: "nominative", gen: "genitive", dat: "dative", acc: "accusative", voc: "vocative" };
const GENDER_LABEL: Record<string, string> = { m: "masculine", f: "feminine", n: "neuter", mf: "masc./fem." };
const PERSON_LABEL: Record<string, string> = { "1sg": "1 sg.", "2sg": "2 sg.", "3sg": "3 sg.", "1pl": "1 pl.", "2pl": "2 pl.", "3pl": "3 pl.", inf: "infinitive", m: "participle masc.", f: "participle fem.", n: "participle neut.", mg: "participle gen. masc." };

function emptyFilters(): Filters {
  return { topics: new Set(), tiers: new Set(), kinds: new Set(), groups: new Set(), readings: new Set() };
}

function toggle<T>(set: Set<T>, v: T): Set<T> {
  const next = new Set(set);
  if (next.has(v)) next.delete(v);
  else next.add(v);
  return next;
}

function matches(item: VocabItem, f: Filters): boolean {
  if (f.topics.size && !item.topics.some((t) => f.topics.has(t))) return false;
  if (f.tiers.size && !f.tiers.has(item.tier)) return false;
  if (f.kinds.size && !f.kinds.has(item.kind)) return false;
  if (f.groups.size && !f.groups.has(item.group)) return false;
  if (f.readings.size && !item.readings.some((r) => f.readings.has(r))) return false;
  return true;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

/** A random cell from the word's tables, as a question. */
function formsQuestion(entry: VocabEntry): FormsQuestion | null {
  const forms: Forms | null = entry.forms;
  if (!forms) return null;
  if (forms.kind === "verb") {
    const tables = forms.systems.flatMap((s) => s.tables).filter((t) => t.cells.length && !t.note?.startsWith("Periphrastic") && !t.note?.startsWith("Usually"));
    if (!tables.length) return null;
    const table = pick(tables);
    const cell = pick(table.cells);
    return { label: `${table.tense} ${table.voice} ${table.mood} · ${PERSON_LABEL[cell.tag] ?? cell.tag}`, answer: cell.forms };
  }
  if (forms.kind === "noun") {
    const cells = forms.cells.filter((c) => c.forms.length);
    const cell = pick(cells);
    return { label: `${CASE_LABEL[cell.case]} ${cell.number === "sg" ? "singular" : "plural"}`, answer: cell.forms };
  }
  const cells = forms.cells.flatMap((c) => forms.genders.map((g) => ({ ...c, g, list: c.forms[g] ?? [] }))).filter((c) => c.list.length);
  if (!cells.length) return null;
  const cell = pick(cells);
  const gender = GENDER_LABEL[cell.g] ?? cell.g;
  return { label: `${gender} ${CASE_LABEL[cell.case]} ${cell.number === "sg" ? "singular" : "plural"}`.trim(), answer: cell.list };
}

function normalizeGreek(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^Ͱ-Ͽ]/g, "");
}

export default function VocabPage() {
  const [index, setIndex] = useState<VocabIndex | null>(null);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [showGroups, setShowGroups] = useState(false);
  const [showWords, setShowWords] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [mode, setMode] = useState<Mode>("build");
  const [queue, setQueue] = useState<Prompt[]>([]);
  const [pos, setPos] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [typed, setTyped] = useState("");
  const [entry, setEntry] = useState<VocabEntry | null>(null);
  const [question, setQuestion] = useState<FormsQuestion | null>(null);
  const [stats, setStats] = useState({ reviewed: 0, again: 0 });
  const [syncMsg, setSyncMsg] = useState("");
  const entryCache = useRef(new Map<string, VocabEntry>());
  const fileRef = useRef<HTMLInputElement | null>(null);
  const { play, busy } = useSpeaker();

  useEffect(() => {
    getVocab().then(setIndex).catch((e) => setError(e instanceof Error ? e.message : "Could not load vocabulary"));
  }, []);

  useEffect(() => {
    saveProgress(progress);
  }, [progress]);

  const deck = useMemo(() => (index ? index.items.filter((i) => matches(i, filters)) : []), [index, filters]);

  const keys = useMemo(() => {
    const out: { key: string; item: VocabItem; type: CardType }[] = [];
    for (const item of deck) {
      for (const type of progress.settings.cardTypes) {
        if (type === "parts" && item.kind !== "verb") continue;
        if (type === "forms" && !["noun", "verb", "adjective", "pronoun", "article", "numeral"].includes(item.kind)) continue;
        out.push({ key: cardKey(item.id, type), item, type });
      }
    }
    return out;
  }, [deck, progress.settings.cardTypes]);

  const counts = useMemo(() => {
    const now = Date.now();
    const due = keys.filter((k) => progress.cards[k.key] && !isNew(progress.cards[k.key]) && progress.cards[k.key].due <= now).length;
    const fresh = keys.filter((k) => isNew(progress.cards[k.key])).length;
    const learned = keys.filter((k) => progress.cards[k.key] && !isNew(progress.cards[k.key])).length;
    return { due, fresh, learned };
  }, [keys, progress.cards]);

  const loadEntry = useCallback(async (id: string) => {
    const hit = entryCache.current.get(id);
    if (hit) return hit;
    const e = await getVocabEntry(id);
    entryCache.current.set(id, e);
    return e;
  }, []);

  const prepare = useCallback(
    async (p: Prompt | undefined) => {
      setFlipped(false);
      setTyped("");
      setQuestion(null);
      setEntry(null);
      if (!p) return;
      if (p.type === "forms" || p.type === "parts" || p.type === "recognition" || p.type === "production") {
        try {
          const e = await loadEntry(p.item.id);
          setEntry(e);
          if (p.type === "forms") setQuestion(formsQuestion(e));
        } catch {
          setEntry(null);
        }
      }
    },
    [loadEntry],
  );

  function startSession() {
    const now = Date.now();
    const newLimit = Math.max(0, progress.settings.newPerDay - newCardsToday(progress, now));
    const byKey = new Map(keys.map((k) => [k.key, k]));
    const { due, fresh } = pickSession(
      keys.map((k) => k.key),
      progress.cards,
      now,
      newLimit,
    );
    const prompts: Prompt[] = [
      ...due.map((k) => ({ ...byKey.get(k)!, fresh: false })),
      ...fresh.map((k) => ({ ...byKey.get(k)!, fresh: true })),
    ];
    if (!prompts.length) return;
    setQueue(prompts);
    setPos(0);
    setStats({ reviewed: 0, again: 0 });
    setMode("study");
    void prepare(prompts[0]);
  }

  function answer(q: Grade) {
    const current = queue[pos];
    if (!current) return;
    const now = Date.now();
    const before = progress.cards[current.key];
    const next = grade(before, q, now);
    let updated: Progress = { ...progress, cards: { ...progress.cards, [current.key]: next } };
    updated = bumpLog(updated, isNew(before), now);
    setProgress(updated);
    setStats((s) => ({ reviewed: s.reviewed + 1, again: s.again + (q === 0 ? 1 : 0) }));
    const rest = [...queue];
    if (q === 0) rest.push({ ...current, fresh: false }); // see it again this session
    const nextPos = pos + 1;
    setQueue(rest);
    if (nextPos >= rest.length) {
      setMode("done");
      return;
    }
    setPos(nextPos);
    void prepare(rest[nextPos]);
  }

  const current = mode === "study" ? queue[pos] : undefined;
  const typedOk = current && current.type === "production" && typed.trim() ? normalizeGreek(typed) === normalizeGreek(current.item.lemma) : null;

  async function doSync(kind: "push" | "pull") {
    setSyncMsg("…");
    try {
      if (kind === "push") {
        const p = await syncPush(progress);
        setProgress(p);
        setSyncMsg("Saved to the server.");
      } else {
        const { progress: p, found } = await syncPull(progress);
        setProgress(p);
        setSyncMsg(found ? "Loaded and merged." : "Nothing saved under that code yet.");
      }
    } catch (e) {
      setSyncMsg(e instanceof Error ? e.message : "Sync failed");
    }
  }

  if (error) return <main className="shell"><p className="error">{error}</p></main>;
  if (!index) return <main className="shell"><p className="muted">Loading vocabulary…</p></main>;

  // ------------------------------------------------------------------ study
  if (mode === "study" && current) {
    const item = current.item;
    return (
      <main className="shell studyShell">
        <div className="studyTop">
          <button type="button" className="linkButton" onClick={() => setMode("build")}>← Deck</button>
          <span className="muted">{pos + 1} / {queue.length} · {TYPE_LABEL[current.type]}{current.fresh ? " · new" : ""}</span>
        </div>
        <section className={`flashcard ${flipped ? "flipped" : ""}`} onClick={() => !flipped && setFlipped(true)}>
          {current.type === "recognition" && (
            <>
              <div className="flashFront">
                <p className="flashGreek">{item.headword}</p>
                <p className="flashHint">{item.pos}</p>
                <SpeakButton text={item.lemma} play={play} busy={busy} />
              </div>
              {flipped && (
                <div className="flashBack">
                  <p className="flashAnswer">{entry?.definition ?? item.short}</p>
                  <p className="flashHint">{item.group} · rank {item.rank}</p>
                  {entry?.notes && <p className="flashNote">{entry.notes}</p>}
                </div>
              )}
            </>
          )}
          {current.type === "production" && (
            <>
              <div className="flashFront">
                <p className="flashEnglish">{item.short}</p>
                <p className="flashHint">{item.pos}</p>
                <input
                  className="typeInput"
                  lang="grc"
                  placeholder="type the Greek (optional)"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") setFlipped(true);
                  }}
                />
                {!flipped && (
                  <button type="button" className="secondary" onClick={() => setFlipped(true)}>Reveal</button>
                )}
              </div>
              {flipped && (
                <div className="flashBack">
                  <p className="flashGreek">{item.headword}</p>
                  {typedOk != null && <p className={typedOk ? "ok" : "warnText"}>{typedOk ? "✓ correct" : "✗ compare"}</p>}
                  <SpeakButton text={item.lemma} play={play} busy={busy} />
                  <p className="flashHint">{entry?.definition ?? item.short}</p>
                </div>
              )}
            </>
          )}
          {current.type === "forms" && (
            <>
              <div className="flashFront">
                <p className="flashGreek">{item.lemma}</p>
                <p className="flashHint">{question ? question.label : "loading…"}</p>
              </div>
              {flipped && question && (
                <div className="flashBack">
                  <p className="flashGreek">{question.answer.join(" / ")}</p>
                  <SpeakButton text={question.answer[0]} play={play} busy={busy} />
                  <p className="flashHint">{item.short}</p>
                </div>
              )}
            </>
          )}
          {current.type === "parts" && (
            <>
              <div className="flashFront">
                <p className="flashGreek">{item.lemma}</p>
                <p className="flashHint">principal parts?</p>
              </div>
              {flipped && (
                <div className="flashBack">
                  <p className="flashAnswer">{item.headword}</p>
                  <p className="flashHint">{item.short}</p>
                </div>
              )}
            </>
          )}
          {!flipped && <p className="tapHint">tap to reveal</p>}
        </section>
        {flipped && (
          <div className="gradeBar">
            <button type="button" className="gradeButton again" onClick={() => answer(0)}>Again</button>
            <button type="button" className="gradeButton hard" onClick={() => answer(1)}>Hard</button>
            <button type="button" className="gradeButton good" onClick={() => answer(2)}>Good</button>
            <button type="button" className="gradeButton easy" onClick={() => answer(3)}>Easy</button>
          </div>
        )}
        {flipped && (
          <p className="footnote">
            <Link href={`/vocab/${encodeURIComponent(item.id)}`}>All forms and examples →</Link>
          </p>
        )}
      </main>
    );
  }

  if (mode === "done") {
    return (
      <main className="shell">
        <section className="card">
          <h2>Session done</h2>
          <p>{stats.reviewed} cards reviewed, {stats.again} marked “again”.</p>
          <div className="actions">
            <button type="button" className="primary" onClick={startSession}>Study more</button>
            <button type="button" className="secondary" onClick={() => setMode("build")}>Back to deck</button>
          </div>
        </section>
      </main>
    );
  }

  // ------------------------------------------------------------------ deck builder
  const f = index.facets;
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">DCC CORE VOCABULARY · 524 WORDS</p>
        <h1>Vocab</h1>
        <p className="lede">Pick what to focus on today, then study with spaced repetition. Every word has all its forms and hears itself in Classical Attic.</p>
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Build a deck</h2>
            <p>Leave a row empty to include everything in it.</p>
          </div>
          <span className="badge">{deck.length} words</span>
        </div>
        <h3 className="chipTitle">Topic</h3>
        <div className="chips">
          {f.topics.map((t) => (
            <button key={t.id} type="button" className={`chip ${filters.topics.has(String(t.id)) ? "on" : ""}`} onClick={() => setFilters({ ...filters, topics: toggle(filters.topics, String(t.id)) })}>
              {t.label} <span className="chipCount">{t.count}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Level (by frequency)</h3>
        <div className="chips">
          {f.tiers.map((t) => (
            <button key={t.id} type="button" className={`chip ${filters.tiers.has(Number(t.id)) ? "on" : ""}`} onClick={() => setFilters({ ...filters, tiers: toggle(filters.tiers, Number(t.id)) })}>
              {t.label} <span className="chipCount">{t.ranks}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Part of speech</h3>
        <div className="chips">
          {f.kinds.map((k) => (
            <button key={k.id} type="button" className={`chip ${filters.kinds.has(String(k.id)) ? "on" : ""}`} onClick={() => setFilters({ ...filters, kinds: toggle(filters.kinds, String(k.id)) })}>
              {k.label} <span className="chipCount">{k.count}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">
          <button type="button" className="linkButton" onClick={() => setShowGroups(!showGroups)}>
            DCC semantic group {showGroups ? "▾" : "▸"}{filters.groups.size ? ` (${filters.groups.size} chosen)` : ""}
          </button>
        </h3>
        {showGroups && (
          <div className="chips">
            {f.groups.map((g) => (
              <button key={g.id} type="button" className={`chip ${filters.groups.has(String(g.id)) ? "on" : ""}`} onClick={() => setFilters({ ...filters, groups: toggle(filters.groups, String(g.id)) })}>
                {g.label} <span className="chipCount">{g.count}</span>
              </button>
            ))}
          </div>
        )}
        <h3 className="chipTitle">Words from a reading</h3>
        <div className="chips">
          {f.readings.map((r) => (
            <button key={r.id} type="button" className={`chip ${filters.readings.has(String(r.id)) ? "on" : ""}`} onClick={() => setFilters({ ...filters, readings: toggle(filters.readings, String(r.id)) })}>
              {String(r.id)} <span className="chipCount">{r.count}</span>
            </button>
          ))}
        </div>
        <div className="deckStats">
          <span><b>{counts.due}</b> due</span>
          <span><b>{Math.min(counts.fresh, Math.max(0, progress.settings.newPerDay - newCardsToday(progress)))}</b> new today ({counts.fresh} unseen)</span>
          <span><b>{counts.learned}</b> learning</span>
        </div>
        <div className="actions">
          <button type="button" className="primary" onClick={startSession} disabled={!keys.length || (counts.due === 0 && (counts.fresh === 0 || progress.settings.newPerDay - newCardsToday(progress) <= 0))}>
            Study {counts.due + Math.min(counts.fresh, Math.max(0, progress.settings.newPerDay - newCardsToday(progress)))} cards
          </button>
          <button type="button" className="secondary" onClick={() => setFilters(emptyFilters())}>Clear filters</button>
        </div>
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Words in this deck</h2>
            <p>Tap a word for its full tables and example sentences.</p>
          </div>
          <button type="button" className="linkButton" onClick={() => setShowWords(!showWords)}>{showWords ? "Hide" : "Show"}</button>
        </div>
        {showWords && (
          <ul className="wordList">
            {deck.map((w) => {
              const st = progress.cards[cardKey(w.id, "recognition")];
              return (
                <li key={w.id}>
                  <Link className="wordRow" href={`/vocab/${encodeURIComponent(w.id)}`}>
                    <span className="wordLemma">{w.lemma}</span>
                    <span className="wordShort">{w.short}</span>
                    <span className={`level ${w.level}`}>{w.level}</span>
                    <span className="wordDue">{describeInterval(st, Date.now())}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Settings & sync</h2>
            <p>Progress lives in this browser; a sync code backs it up on the server so you can restore it on another device.</p>
          </div>
          <button type="button" className="linkButton" onClick={() => setShowSettings(!showSettings)}>{showSettings ? "Hide" : "Show"}</button>
        </div>
        {showSettings && (
          <div className="settingsGrid">
            <label>
              New cards per day
              <input type="number" min={0} max={100} value={progress.settings.newPerDay} onChange={(e) => setProgress({ ...progress, settings: { ...progress.settings, newPerDay: Number(e.target.value) } })} />
            </label>
            <div>
              Card types
              <div className="chips">
                {CARD_TYPES.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`chip ${progress.settings.cardTypes.includes(t) ? "on" : ""}`}
                    onClick={() => {
                      const has = progress.settings.cardTypes.includes(t);
                      const next = has ? progress.settings.cardTypes.filter((x) => x !== t) : [...progress.settings.cardTypes, t];
                      if (next.length) setProgress({ ...progress, settings: { ...progress.settings, cardTypes: next } });
                    }}
                  >
                    {TYPE_LABEL[t]}
                  </button>
                ))}
              </div>
            </div>
            <label>
              Sync code (8+ characters, keep it private)
              <input type="text" value={progress.settings.syncCode} onChange={(e) => setProgress({ ...progress, settings: { ...progress.settings, syncCode: e.target.value } })} placeholder="e.g. xenophon-anabasis-42" />
            </label>
            <div className="actions">
              <button type="button" className="secondary" onClick={() => doSync("push")}>Save to server</button>
              <button type="button" className="secondary" onClick={() => doSync("pull")}>Load from server</button>
            </div>
            {syncMsg && <p className="muted">{syncMsg}{progress.lastSync ? ` Last sync ${new Date(progress.lastSync).toLocaleString()}.` : ""}</p>}
            <div className="actions">
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  const blob = new Blob([exportProgress(progress)], { type: "application/json" });
                  const a = document.createElement("a");
                  a.href = URL.createObjectURL(blob);
                  a.download = "attic-reader-progress.json";
                  a.click();
                }}
              >
                Export JSON
              </button>
              <button type="button" className="secondary" onClick={() => fileRef.current?.click()}>Import JSON</button>
              <input
                ref={fileRef}
                type="file"
                accept="application/json"
                hidden
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  try {
                    setProgress(importProgress(await file.text(), progress));
                    setSyncMsg("Imported.");
                  } catch {
                    setSyncMsg("Could not read that file.");
                  }
                }}
              />
            </div>
            <button
              type="button"
              className="linkButton danger"
              onClick={() => {
                if (window.confirm("Forget all flash-card progress on this device?")) setProgress({ ...progress, cards: {}, log: [] });
              }}
            >
              Reset progress
            </button>
          </div>
        )}
      </section>

      <p className="attribution">
        {index.attribution} <a href={index.attribution_url} target="_blank" rel="noreferrer">dcc.dickinson.edu</a>
      </p>
    </main>
  );
}
