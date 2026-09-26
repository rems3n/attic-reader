"use client";
import SessionSummary from "../../components/SessionSummary";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import FormsTable from "../../components/FormsTable";
import Highlight from "../../components/Highlight";
import { SpeakButton, SpeakList, useSpeaker } from "../../components/Speak";
import { getVocab, getVocabEntry, type Example, type Forms, type VocabEntry, type VocabIndex, type VocabItem } from "../../lib/api";
import {
  bumpLog,
  exportProgress,
  importProgress,
  loadProgress,
  saveProgress,
  syncPull,
  syncPush,
  type Direction,
  type Progress,
} from "../../lib/progress";
import { cardKey, describeInterval, grade, isNew, pickSession, shuffleSession, type CardType, type Grade } from "../../lib/srs";
import { PageError, PageLoading } from "../../components/PageState";

type Filters = { topics: Set<string>; tags: Set<string>; tiers: Set<number>; kinds: Set<string>; groups: Set<string>; readings: Set<string>; lessons: Set<string> };
type Mode = "build" | "study" | "done";
type Prompt = { key: string; id: string; item: VocabItem; type: CardType; fresh: boolean };
type FormsQuestion = { label: string; answer: string[] };

const TYPE_LABEL: Record<CardType, string> = { recognition: "Greek → English", production: "English → Greek", forms: "Forms drill", parts: "Principal parts" };
const DIRECTIONS: { id: Direction; label: string }[] = [
  { id: "grc-en", label: "Greek → English" },
  { id: "en-grc", label: "English → Greek" },
  { id: "both", label: "Both" },
];
const EXTRA_TYPES: CardType[] = ["forms", "parts"];
const SPEAK_MAX = 300; // /api/speak text cap
const CASE_LABEL: Record<string, string> = { nom: "nominative", gen: "genitive", dat: "dative", acc: "accusative", voc: "vocative" };
const GENDER_LABEL: Record<string, string> = { m: "masculine", f: "feminine", n: "neuter", mf: "masc./fem." };
const PERSON_LABEL: Record<string, string> = { "1sg": "1 sg.", "2sg": "2 sg.", "3sg": "3 sg.", "1pl": "1 pl.", "2pl": "2 pl.", "3pl": "3 pl.", inf: "infinitive", m: "participle masc.", f: "participle fem.", n: "participle neut.", mg: "participle gen. masc." };

function emptyFilters(): Filters {
  return { topics: new Set(), tags: new Set(), tiers: new Set(), kinds: new Set(), groups: new Set(), readings: new Set(), lessons: new Set() };
}

function toggle<T>(set: Set<T>, v: T): Set<T> {
  const next = new Set(set);
  if (next.has(v)) next.delete(v);
  else next.add(v);
  return next;
}

function matches(item: VocabItem, f: Filters): boolean {
  if (f.topics.size && !item.topics.some((t) => f.topics.has(t))) return false;
  if (f.tags.size && ![...f.tags].every((t) => item.tags.includes(t))) return false;
  if (f.tiers.size && !f.tiers.has(item.tier)) return false;
  if (f.kinds.size && !f.kinds.has(item.kind)) return false;
  if (f.groups.size && !f.groups.has(item.group)) return false;
  if (f.readings.size && !item.readings.some((r) => f.readings.has(r))) return false;
  if (f.lessons.size && !(item.lessons ?? []).some((l) => f.lessons.has(l))) return false;
  return true;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

/** A random cell from the word's tables, as a question. */
/** The example that fits on a card: the shortest one under 160 characters, else the shortest. */
function pickExample(entry: VocabEntry | null): Example | null {
  const all = entry?.examples ?? [];
  if (!all.length) return null;
  const sorted = [...all].sort((a, b) => a.text.length - b.text.length);
  return sorted.find((e) => e.text.length <= 160) ?? sorted[0];
}

function CardExample({ entry, play, busy }: { entry: VocabEntry | null; play: (t: string) => void; busy: string | null }) {
  const ex = pickExample(entry);
  if (!ex) return null;
  return (
    <div className="cardExample" onClick={(e) => e.stopPropagation()}>
      <p className="cardExampleText" lang="grc">
        <Highlight text={ex.text} form={ex.form} />
        {ex.text.length <= SPEAK_MAX && <SpeakButton text={ex.text} play={play} busy={busy} small />}
      </p>
      <p className="cardExampleMeta">
        {ex.author}, <em>{ex.title}</em>
      </p>
    </div>
  );
}

/** "λύω, λύσω, ἔλυσα, …" → the individual parts; parenthesised glosses and labels dropped. */
function headwordParts(headword: string): string[] {
  return headword
    .replace(/\([^)]*\)/g, "")
    .split(/,|;| or | and /)
    .map((p) => p.replace(/[A-Za-z0-9.]+/g, "").trim())
    .filter((p) => /[\u0370-\u03ff\u1f00-\u1fff]/.test(p));
}

/** Playable principal parts: the engine's list when available, else the headword split. */
function principalParts(entry: VocabEntry | null, headword: string): string[] {
  const forms = entry?.forms;
  if (forms && forms.kind === "verb" && forms.principal_parts?.length) {
    return forms.principal_parts.flatMap((pp) => pp.forms);
  }
  return headwordParts(headword);
}

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

/** "English: logic, dialogue · ≈ father" from the curated cognate map. */
function CognateLine({ item }: { item: VocabItem }) {
  const c = item.cognates;
  if (!c) return null;
  return (
    <p className="cognateLine">
      {c.derivatives && c.derivatives.length > 0 && <>English: <b>{c.derivatives.join(", ")}</b></>}
      {c.derivatives && c.derivatives.length > 0 && c.cognates && c.cognates.length > 0 && " · "}
      {c.cognates && c.cognates.length > 0 && <>≈ <b>{c.cognates.join(", ")}</b></>}
    </p>
  );
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
  const [quick, setQuick] = useState(false);
  const quickStarted = useRef(false);
  const sessionStarted = useRef(Date.now());
  const initialProgress = useRef(progress);
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
  const backRef = useRef<HTMLDivElement | null>(null);
  const { play, busy } = useSpeaker();

  // Revealed: move focus to the answer (the Show answer button is gone).
  useEffect(() => {
    if (flipped) backRef.current?.focus({ preventScroll: true });
  }, [flipped]);

  useEffect(() => {
    getVocab().then(setIndex).catch((e) => setError(e instanceof Error ? e.message : "Could not load vocabulary"));
  }, []);

  useEffect(() => {
    saveProgress(progress);
  }, [progress]);

  // ?words=id,id&from=label: a deck of given words (a reading's new words, a track list)
  const [only, setOnly] = useState<{ ids: Set<string>; from: string } | null>(null);
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const words = q.get("words");
    setQuick(q.get("quick") === "1");
    if (words) setOnly({ ids: new Set(words.split(",").filter(Boolean)), from: q.get("from") ?? "a list" });
  }, []);

  const deck = useMemo(() => (index ? index.items.filter((i) => matches(i, filters) && (!only || only.ids.has(i.id))) : []), [index, filters, only]);

  const { direction, cardTypes: extras, sessionSize } = progress.settings;
  const keys = useMemo(() => {
    const basic: CardType[] = direction === "grc-en" ? ["recognition"] : direction === "en-grc" ? ["production"] : ["recognition", "production"];
    const types = [...basic, ...extras];
    const out: { key: string; id: string; item: VocabItem; type: CardType }[] = [];
    for (const item of deck) {
      for (const type of types) {
        if (type === "parts" && item.kind !== "verb") continue;
        if (type === "forms" && !["noun", "verb", "adjective", "pronoun", "article", "numeral"].includes(item.kind)) continue;
        out.push({ key: cardKey(item.id, type), id: item.id, item, type });
      }
    }
    return out;
  }, [deck, direction, extras]);

  const counts = useMemo(() => {
    const now = Date.now();
    const due = keys.filter((k) => progress.cards[k.key] && !isNew(progress.cards[k.key]) && progress.cards[k.key].due <= now).length;
    const fresh = keys.filter((k) => isNew(progress.cards[k.key])).length;
    const learned = keys.filter((k) => progress.cards[k.key] && !isNew(progress.cards[k.key])).length;
    return { due, fresh, learned };
  }, [keys, progress.cards]);

  // What the next session would contain at the chosen size.
  const plan = useMemo(() => {
    const { due, fresh } = pickSession(keys.map((k) => k.key), progress.cards, Date.now(), sessionSize);
    return { due: due.length, fresh: fresh.length, total: due.length + fresh.length };
  }, [keys, progress.cards, sessionSize]);
  const maxSize = Math.max(5, Math.min(100, keys.length));
  function setSessionSize(n: number) {
    const v = Math.max(1, Math.min(maxSize, Math.round(n) || 1));
    setProgress({ ...progress, settings: { ...progress.settings, sessionSize: v } });
  }

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
    const byKey = new Map(keys.map((k) => [k.key, k]));
    const { due, fresh } = pickSession(keys.map((k) => k.key), progress.cards, now, quick ? Math.min(10, sessionSize) : sessionSize);
    const prompts: Prompt[] = shuffleSession([
      ...due.map((k) => ({ ...byKey.get(k)!, fresh: false })),
      ...fresh.map((k) => ({ ...byKey.get(k)!, fresh: true })),
    ]);
    if (!prompts.length) return;
    initialProgress.current = progress;
    sessionStarted.current = now;
    setQueue(prompts);
    setPos(0);
    setStats({ reviewed: 0, again: 0 });
    setMode("study");
    void prepare(prompts[0]);
  }

  // Quick sessions open directly on the first card after the requested deck loads.
  useEffect(() => {
    if (!quick || !index || !only || !keys.length || quickStarted.current) return;
    quickStarted.current = true;
    startSession();
    // The deck is loaded once; subsequent ratings must not restart the session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quick, index, only, keys.length]);

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
    if (nextPos >= rest.length || (quick && now - sessionStarted.current >= 300000)) {
      setMode("done");
      return;
    }
    setPos(nextPos);
    void prepare(rest[nextPos]);
  }

  const current = mode === "study" ? queue[pos] : undefined;

  // Auto-speak: the Greek on the front when a card appears, the answer on reveal.
  const autoSpeak = progress.settings.autoSpeak;
  useEffect(() => {
    if (!autoSpeak || !current) return;
    if (!flipped) {
      if (current.type !== "production") play(current.item.lemma);
      return;
    }
    if (current.type === "production") play(current.item.lemma);
    else if (current.type === "forms" && question?.answer[0]) play(question.answer[0]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoSpeak, current, flipped, question]);
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

  if (error) return <PageError message={error} back={{ href: "/library", label: "Open the Library instead" }} />;
  if (!index) return <PageLoading label="Loading vocabulary…" />;

  // ------------------------------------------------------------------ study
  if (mode === "study" && current) {
    const item = current.item;
    return (
      <main className="shell studyShell">
        <h1 className="srOnly">Vocab study: card {pos + 1} of {queue.length}</h1>
        <div className="studyTop">
          <button type="button" className="linkButton" onClick={() => setMode("build")}>← Deck</button>
          <span className="muted">{pos + 1} / {queue.length} · {TYPE_LABEL[current.type]}{current.fresh ? " · new" : ""}</span>
        </div>
        <section className={`flashcard ${flipped ? "flipped" : ""}`} onClick={() => !flipped && setFlipped(true)}>
          {current.type === "recognition" && (
            <>
              <div className="flashFront">
                <p className="flashGreek" lang="grc">{item.headword}</p>
                <p className="flashHint">{item.pos}</p>
                <div className="speakRow">
                  <SpeakButton text={item.lemma} play={play} busy={busy} />
                  {item.kind === "verb" && headwordParts(item.headword).length > 1 && <SpeakButton text={item.headword} play={play} busy={busy} label="all parts" />}
                </div>
              </div>
              {flipped && (
                <div className="flashBack" ref={backRef} tabIndex={-1}>
                  <p className="flashAnswer">{entry?.definition ?? item.short}</p>
                  <CognateLine item={item} />
                  <CardExample entry={entry} play={play} busy={busy} />
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
                  aria-label="Type the Greek (optional)"
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
                <div className="flashBack" ref={backRef} tabIndex={-1}>
                  <p className="flashGreek" lang="grc">{item.headword}</p>
                  {typedOk != null && <p className={typedOk ? "ok" : "warnText"} role="status">{typedOk ? "✓ correct" : "✗ compare"}</p>}
                  <div className="speakRow">
                    <SpeakButton text={item.lemma} play={play} busy={busy} />
                    {item.kind === "verb" && headwordParts(item.headword).length > 1 && <SpeakButton text={item.headword} play={play} busy={busy} label="all parts" />}
                  </div>
                  <p className="flashHint">{entry?.definition ?? item.short}</p>
                  <CognateLine item={item} />
                  <CardExample entry={entry} play={play} busy={busy} />
                </div>
              )}
            </>
          )}
          {current.type === "forms" && (
            <>
              <div className="flashFront">
                <p className="flashGreek" lang="grc">{item.lemma}</p>
                <p className="flashHint">{question ? question.label : "loading…"}</p>
                <SpeakButton text={item.lemma} play={play} busy={busy} />
              </div>
              {flipped && question && (
                <div className="flashBack" ref={backRef} tabIndex={-1}>
                  <p className="flashGreek" lang="grc">{question.answer.join(" / ")}</p>
                  <SpeakList forms={question.answer} play={play} busy={busy} />
                  <p className="flashHint">{item.short}</p>
                  <CardExample entry={entry} play={play} busy={busy} />
                </div>
              )}
            </>
          )}
          {current.type === "parts" && (
            <>
              <div className="flashFront">
                <p className="flashGreek" lang="grc">{item.lemma}</p>
                <p className="flashHint">principal parts?</p>
                <SpeakButton text={item.lemma} play={play} busy={busy} />
              </div>
              {flipped && (
                <div className="flashBack" ref={backRef} tabIndex={-1}>
                  <p className="flashAnswer" lang="grc">{item.headword}</p>
                  <SpeakList forms={principalParts(entry, item.headword)} play={play} busy={busy} />
                  <SpeakButton text={item.headword} play={play} busy={busy} label="all parts" />
                  <p className="flashHint">{item.short}</p>
                  <CardExample entry={entry} play={play} busy={busy} />
                </div>
              )}
            </>
          )}
          {!flipped && <p className="tapHint" aria-hidden="true">tap to reveal</p>}
        </section>
        {!flipped && current.type !== "production" && (
          <div className="revealRow">
            <button type="button" className="primary" onClick={() => setFlipped(true)}>Show answer</button>
          </div>
        )}
        {flipped && (
          <div className="gradeBar" role="group" aria-label="How well did you know it?">
            <button type="button" className="gradeButton again" onClick={() => answer(0)}>Again</button>
            <button type="button" className="gradeButton hard" onClick={() => answer(1)}>Hard</button>
            <button type="button" className="gradeButton good" onClick={() => answer(2)}>Good</button>
            <button type="button" className="gradeButton easy" onClick={() => answer(3)}>Easy</button>
          </div>
        )}
        {flipped && (
          <p className="footnote">
            <Link href={`/words/${encodeURIComponent(item.id)}`}>All forms and examples →</Link>
          </p>
        )}
      </main>
    );
  }

  if (mode === "done") {
    return (
      <main className="shell">
        <section className="card">
          <h1 className="pageTitle">Session done</h1>
          <SessionSummary before={initialProgress.current} progress={progress} minutes={Math.min(60, (Date.now() - sessionStarted.current) / 60000)} reviewed={stats.reviewed}><p>{stats.reviewed - stats.again} recalled (self-rated); {stats.again} cards marked “again”.</p></SessionSummary>
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
        <h1>Words</h1>
        <p className="lede">Pick what to focus on today, then study with spaced repetition. Explore each word’s forms and hear it in Classical Attic.</p>
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Build a deck</h2>
            <p>Leave a row empty to include everything in it.</p>
          </div>
          <span className="badge">{deck.length} words</span>
        </div>
        {only && (
          <div className="chips">
            <button type="button" className="chip on" aria-label={`Remove the filter: words from ${only.from} (${only.ids.size})`} onClick={() => { setOnly(null); window.history.replaceState(null, "", "/words"); }}>
              Words from {only.from} <span className="chipCount">{only.ids.size}</span> <span aria-hidden="true">✕</span>
            </button>
          </div>
        )}
        <h3 className="chipTitle">Topic</h3>
        <div className="chips">
          {f.topics.map((t) => (
            <button key={t.id} type="button" className={`chip ${filters.topics.has(String(t.id)) ? "on" : ""}`} aria-pressed={filters.topics.has(String(t.id))} onClick={() => setFilters({ ...filters, topics: toggle(filters.topics, String(t.id)) })}>
              {t.label} <span className="chipCount">{t.count}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Extras</h3>
        <div className="chips">
          {f.tags.map((t) => (
            <button key={t.id} type="button" className={`chip ${filters.tags.has(String(t.id)) ? "on" : ""}`} aria-pressed={filters.tags.has(String(t.id))} onClick={() => setFilters({ ...filters, tags: toggle(filters.tags, String(t.id)) })}>
              {t.label} <span className="chipCount">{t.count}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Level (by frequency)</h3>
        <div className="chips">
          {f.tiers.map((t) => (
            <button key={t.id} type="button" className={`chip ${filters.tiers.has(Number(t.id)) ? "on" : ""}`} aria-pressed={filters.tiers.has(Number(t.id))} onClick={() => setFilters({ ...filters, tiers: toggle(filters.tiers, Number(t.id)) })}>
              {t.label} <span className="chipCount">{t.ranks}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Part of speech</h3>
        <div className="chips">
          {f.kinds.map((k) => (
            <button key={k.id} type="button" className={`chip ${filters.kinds.has(String(k.id)) ? "on" : ""}`} aria-pressed={filters.kinds.has(String(k.id))} onClick={() => setFilters({ ...filters, kinds: toggle(filters.kinds, String(k.id)) })}>
              {k.label} <span className="chipCount">{k.count}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">
          <button type="button" className="linkButton" aria-expanded={showGroups} onClick={() => setShowGroups(!showGroups)}>
            DCC semantic group {showGroups ? "▾" : "▸"}{filters.groups.size ? ` (${filters.groups.size} chosen)` : ""}
          </button>
        </h3>
        {showGroups && (
          <div className="chips">
            {f.groups.map((g) => (
              <button key={g.id} type="button" className={`chip ${filters.groups.has(String(g.id)) ? "on" : ""}`} aria-pressed={filters.groups.has(String(g.id))} onClick={() => setFilters({ ...filters, groups: toggle(filters.groups, String(g.id)) })}>
                {g.label} <span className="chipCount">{g.count}</span>
              </button>
            ))}
          </div>
        )}
        <h3 className="chipTitle">Words from a course lesson</h3>
        <div className="chips">
          {(f.lessons ?? []).map((l) => (
            <button key={l.id} type="button" className={`chip ${filters.lessons.has(String(l.id)) ? "on" : ""}`} aria-pressed={filters.lessons.has(String(l.id))} onClick={() => setFilters({ ...filters, lessons: toggle(filters.lessons, String(l.id)) })}>
              {String(l.id)} <span className="chipCount">{l.count}</span>
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Words from a reading</h3>
        <div className="chips">
          {f.readings.map((r) => (
            <button key={r.id} type="button" className={`chip ${filters.readings.has(String(r.id)) ? "on" : ""}`} aria-pressed={filters.readings.has(String(r.id))} onClick={() => setFilters({ ...filters, readings: toggle(filters.readings, String(r.id)) })}>
              {String(r.id)} <span className="chipCount">{r.count}</span>
            </button>
          ))}
        </div>
        <div className="deckStats">
          <span><b>{counts.due}</b> due</span>
          <span><b>{counts.fresh}</b> unseen</span>
          <span><b>{counts.learned}</b> learning</span>
        </div>
        <div className="actions">
          <button type="button" className="secondary" onClick={() => setFilters(emptyFilters())}>Clear filters</button>
        </div>
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Study</h2>
            <p>Cards are shuffled; anything due comes first, new words fill the rest.</p>
          </div>
        </div>
        <h3 className="chipTitle">Test</h3>
        <div className="chips">
          {DIRECTIONS.map((d) => (
            <button key={d.id} type="button" className={`chip ${direction === d.id ? "on" : ""}`} aria-pressed={direction === d.id} onClick={() => setProgress({ ...progress, settings: { ...progress.settings, direction: d.id } })}>
              {d.label}
            </button>
          ))}
          {EXTRA_TYPES.map((t) => (
            <button
              key={t}
              type="button"
              className={`chip ${extras.includes(t) ? "on" : ""}`} aria-pressed={extras.includes(t)}
              onClick={() => {
                const next = extras.includes(t) ? extras.filter((x) => x !== t) : [...extras, t];
                setProgress({ ...progress, settings: { ...progress.settings, cardTypes: next } });
              }}
            >
              + {TYPE_LABEL[t]}
            </button>
          ))}
        </div>
        <h3 className="chipTitle">Cards this session</h3>
        <div className="sizeRow">
          <input type="range" min={1} max={maxSize} step={1} value={Math.min(sessionSize, maxSize)} onChange={(e) => setSessionSize(Number(e.target.value))} aria-label="Cards this session" />
          <input type="number" min={1} max={maxSize} value={Math.min(sessionSize, maxSize)} onChange={(e) => setSessionSize(Number(e.target.value))} aria-label="Cards this session (number)" />
        </div>
        <p className="muted sizeHint">
          {plan.total ? <>{plan.total} cards: {plan.due} due, {plan.fresh} new</> : "Nothing to study in this deck yet."}
          {keys.length > maxSize ? ` · deck has ${keys.length} cards` : ""}
        </p>
        <div className="actions">
          <button type="button" className="primary" onClick={startSession} disabled={!plan.total}>
            Study {plan.total} cards
          </button>
        </div>
      </section>

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Words in this deck</h2>
            <p>Tap a word for its full tables and example sentences.</p>
          </div>
          <button type="button" className="linkButton" aria-expanded={showWords} aria-controls="deck-words" onClick={() => setShowWords(!showWords)}>{showWords ? "Hide" : "Show"}<span className="srOnly"> the words</span></button>
        </div>
        {showWords && (
          <ul className="wordList" id="deck-words">
            {deck.map((w) => {
              const st = progress.cards[cardKey(w.id, "recognition")];
              return (
                <li key={w.id} className="wordRow">
                  {/* the lemma link stretches over the row; ▶ sits above it */}
                  <Link className="wordLemma" lang="grc" href={`/words/${encodeURIComponent(w.id)}`}>{w.lemma}</Link>
                  <span className="wordShort">
                    {w.short}
                    {w.cognates?.derivatives?.[0] && <span className="wordCognate"> · {w.cognates.derivatives[0]}</span>}
                  </span>
                  <span className={`level ${w.level}`}>{w.level}</span>
                  <span className="wordDue">{describeInterval(st, Date.now())}</span>
                  <SpeakButton text={w.lemma} play={play} busy={busy} small />
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
          <button type="button" className="linkButton" aria-expanded={showSettings} aria-controls="deck-settings" onClick={() => setShowSettings(!showSettings)}>{showSettings ? "Hide" : "Show"}<span className="srOnly"> settings</span></button>
        </div>
        {showSettings && (
          <div className="settingsGrid" id="deck-settings">
            <label className="checkRow">
              <input type="checkbox" checked={progress.settings.autoSpeak} onChange={(e) => setProgress({ ...progress, settings: { ...progress.settings, autoSpeak: e.target.checked } })} />
              Speak cards automatically (the Greek when a card appears, the answer on reveal)
            </label>
            <label>
              Sync code (8+ characters, keep it private)
              <input type="text" value={progress.settings.syncCode} onChange={(e) => setProgress({ ...progress, settings: { ...progress.settings, syncCode: e.target.value } })} placeholder="e.g. xenophon-anabasis-42" />
            </label>
            <div className="actions">
              <button type="button" className="secondary" onClick={() => doSync("push")}>Save to server</button>
              <button type="button" className="secondary" onClick={() => doSync("pull")}>Load from server</button>
            </div>
            {syncMsg && <p className="muted" role="status">{syncMsg}{progress.lastSync ? ` Last sync ${new Date(progress.lastSync).toLocaleString()}.` : ""}</p>}
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
