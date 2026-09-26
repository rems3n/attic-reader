"use client";

import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { checkItem, type CheckFeedback } from "../../lib/api";
import { gradeItem, hashString, itemOptions, itemTokens, keyText, modality, seededShuffle, type GradeResult, type ImageRecord, type Item, type Response } from "../../lib/course";
import { SpeakButton, useSpeaker } from "../Speak";
import GreekInput from "./GreekInput";
import Picture, { imageById } from "./Picture";

export type Outcome = { item: Item; response: Response; result: GradeResult };

const GREEK = /[Ͱ-Ͽἀ-῿]/;
const isGreek = (s: string | undefined | null) => !!s && GREEK.test(s);

type Mode = "practice" | "test";

const TYPE_LABEL: Record<string, string> = {
  "pick-picture": "Pick the picture",
  "listen-pick": "Listen",
  "cloze-choice": "Choose",
  "true-false-grc": "ἀληθὲς ἢ ψευδές;",
  "bank-cloze": "Fill from the bank",
  label: "Label",
  "cloze-type": "Type",
  "produce-form": "Give the form",
  transform: "Transform",
  "compose-grc": "Write in Greek",
  dictation: "Dictation",
  "endings-cloze": "Endings",
  "answer-grc": "Answer in Greek",
  parse: "Parse",
  locate: "Find in the text",
  reorder: "Put in order",
  match: "Match",
  "word-family": "Word study",
  "translate-en": "Translate",
  "describe-picture": "Describe",
  retell: "Retell",
  "read-aloud": "Read aloud",
  "continue-story": "Continue the story",
};

/**
 * Runs a list of items. In practice mode each answer is checked at once
 * with an explanation; in test mode answers are collected and graded at the
 * end. `onOutcome` fires per item (practice) or once per item on submit (test).
 */
export default function ExerciseRunner({ items, images, mode, accents, onOutcome, onDone, seed = 0, title, renderAbove, scope }: { items: Item[]; images: ImageRecord[]; mode: Mode; accents: boolean; onOutcome?: (o: Outcome) => void; onDone: (outcomes: Outcome[]) => void; seed?: number; title?: string; renderAbove?: (item: Item, index: number) => React.ReactNode; /** lesson id: enables "you typed the genitive" feedback from the server */ scope?: string }) {
  const [index, setIndex] = useState(0);
  const [response, setResponse] = useState<Response>(null);
  const [checked, setChecked] = useState<GradeResult | null>(null);
  const [feedback, setFeedback] = useState<CheckFeedback | null>(null);
  const feedbackFor = useRef<string | null>(null); // item whose server feedback is awaited
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);
  const { play, busy } = useSpeaker();
  const item = items[index];
  const imageMap = useMemo(() => new Map(images.map((i) => [i.id, i])), [images]);
  const sectionRef = useRef<HTMLElement | null>(null);
  const nextRef = useRef<HTMLButtonElement | null>(null);
  const moved = useRef(false);

  // Keyboard and screen-reader users: after "Check", focus lands on "Next";
  // on a new item, on the exercise (typed items focus their input instead).
  useEffect(() => {
    if (checked) nextRef.current?.focus({ preventScroll: true });
  }, [checked]);
  useEffect(() => {
    if (!moved.current) {
      moved.current = true;
      return;
    }
    if (items[index] && modality(items[index]) !== "typed") sectionRef.current?.focus({ preventScroll: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  // A new item list (e.g. review items arriving) restarts the runner.
  useEffect(() => {
    setIndex(0);
    setResponse(null);
    setChecked(null);
    setFeedback(null);
    setOutcomes([]);
  }, [items]);

  if (!item) return null;
  const m = modality(item);
  const audioText = item.audio === "prompt" ? item.prompt : item.audio;
  const canCheck = responseComplete(item, response);

  function check() {
    if (!item || !canCheck) return;
    const result = gradeItem(item, response, accents);
    const outcome = { item, response, result };
    if (mode === "practice") {
      setChecked(result);
      setOutcomes([...outcomes, outcome]);
      onOutcome?.(outcome);
      if (!result.correct && scope && m === "typed") {
        const asked = (feedbackFor.current = item.id);
        checkItem(item, response, accents, scope)
          .then((r) => { if (feedbackFor.current === asked && r.feedback?.some((f) => f.label)) setFeedback(r.feedback); })
          .catch(() => undefined);
      }
    } else {
      advance(outcome);
    }
  }

  function advance(outcome?: Outcome) {
    const next = outcome ? [...outcomes, outcome] : outcomes;
    setOutcomes(next);
    if (index + 1 >= items.length) {
      onDone(next);
      return;
    }
    // Reset in the same batch as the index change so the next item never
    // renders with the previous item's response.
    setResponse(null);
    setChecked(null);
    setFeedback(null);
    feedbackFor.current = null;
    setIndex(index + 1);
  }

  return (
    <section className="exercise" ref={sectionRef} tabIndex={-1} aria-labelledby={`ex-kind-${index}`}>
      <div className="exerciseTop">
        <span className="exerciseKind" id={`ex-kind-${index}`}>{title ? `${title} · ` : ""}{TYPE_LABEL[item.type] ?? item.type}<span className="srOnly">, item {index + 1} of {items.length}</span></span>
        <span className="exerciseCount" aria-hidden="true">{index + 1} / {items.length}</span>
      </div>
      {renderAbove?.(item, index)}

      {item.prompt && (
        <p id={`ex-prompt-${index}`} className={`exercisePrompt ${isGreek(item.prompt) ? "grc" : ""}`} lang={isGreek(item.prompt) ? "grc" : "en"}>
          {audioText && <SpeakButton text={audioText} play={play} busy={busy} small />}{" "}
          {item.prompt}
        </p>
      )}
      {!item.prompt && audioText && (
        <p className="exercisePrompt">
          <SpeakButton text={audioText} play={play} busy={busy} label="listen" />
        </p>
      )}
      {item.image && <Picture image={imageById(imageMap, item.image)} size="tile" caption={false} />}

      {m === "choice" && <ChoiceItem key={item.id} item={item} images={imageMap} response={response} setResponse={setResponse} checked={checked} play={play} busy={busy} seed={seed} labelledBy={item.prompt ? `ex-prompt-${index}` : `ex-kind-${index}`} />}
      {m === "typed" && <TypedItem key={item.id} item={item} response={response} setResponse={setResponse} checked={checked} onEnter={() => (checked ? advance() : check())} />}
      {m === "parse" && <ParseItem key={item.id} item={item} response={response} setResponse={setResponse} checked={checked} />}
      {m === "locate" && <LocateItem key={item.id} item={item} response={response} setResponse={setResponse} checked={checked} />}
      {m === "reorder" && <ReorderItem key={item.id} item={item} response={response} setResponse={setResponse} checked={checked} seed={seed} />}
      {m === "match" && <MatchItem key={item.id} item={item} response={response} setResponse={setResponse} checked={checked} seed={seed} />}
      {m === "self" && <SelfItem key={item.id} item={item} response={response} setResponse={setResponse} mode={mode} />}

      <div className="feedbackRegion" aria-live="polite">
      {checked && (
        <div className={`feedback ${checked.correct ? "good" : "bad"}`}>
          <p className="feedbackHead">{checked.correct ? "✓ Right" : "✗ Not quite"}</p>
          {!checked.correct && m !== "self" && (
            <p className="feedbackKey" lang="grc">
              {keyText(item)} {audioText && <SpeakButton text={keyText(item) || audioText} play={play} busy={busy} small />}
            </p>
          )}
          {!checked.correct && feedback && (
            <p className="feedbackExplain feedbackForm">
              {feedback.filter((f) => f.label).map((f, i) => <span key={i}>You typed the <strong>{f.label}</strong> of <span lang="grc">{f.lemma}</span>. </span>)}
            </p>
          )}
          {item.explain && <p className="feedbackExplain">{item.explain}</p>}
        </div>
      )}
      </div>

      <div className="exerciseActions">
        {mode === "practice" && !checked && m !== "self" && (
          <button type="button" className="primary" disabled={!canCheck} onClick={check}>Check</button>
        )}
        {mode === "practice" && !checked && m === "self" && (
          <button type="button" className="primary" disabled={!canCheck} onClick={check}>Continue</button>
        )}
        {mode === "practice" && checked && (
          <button type="button" className="primary" ref={nextRef} onClick={() => advance()}>{index + 1 >= items.length ? "Finish" : "Next"}</button>
        )}
        {mode === "test" && (
          <button type="button" className="primary" disabled={!canCheck} onClick={check}>{index + 1 >= items.length ? "Submit" : "Next"}</button>
        )}
      </div>
    </section>
  );
}

function responseComplete(item: Item, r: Response): boolean {
  const m = modality(item);
  if (m === "choice") return typeof r === "string" && r.length > 0;
  if (m === "typed") {
    const gaps = item.gaps?.length ?? 1;
    return Array.isArray(r) && r.length >= gaps && (r as string[]).every((s) => String(s).trim().length > 0);
  }
  if (m === "parse") return !!r && typeof r === "object" && !Array.isArray(r) && (item.groups ?? []).every((g) => (r as Record<string, string>)[g.id]);
  if (m === "locate") return Array.isArray(r) && r.length > 0;
  if (m === "reorder") return Array.isArray(r) && r.length === itemTokens(item).length;
  if (m === "match") return !!r && typeof r === "object" && !Array.isArray(r) && (item.pairs ?? []).every((p) => (r as Record<string, string>)[p.left]);
  return r === true || r === false;
}

// ------------------------------------------------------------------ choice

/**
 * A radio group: one Tab stop, arrow keys move and select (Home/End jump),
 * Space/Enter selects. An option's ▶ sits beside its button, not inside it.
 */
function ChoiceItem({ item, images, response, setResponse, checked, play, busy, seed, labelledBy }: { item: Item; images: Map<string, ImageRecord>; response: Response; setResponse: (r: Response) => void; checked: GradeResult | null; play: (t: string) => void; busy: string | null; seed: number; labelledBy?: string }) {
  const options = useMemo(() => {
    const opts = itemOptions(item);
    return item.type === "true-false-grc" ? opts : seededShuffle(opts, seed + hashString(item.id));
  }, [item, seed]);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const pictures = options.some((o) => o.image);
  const selected = options.findIndex((o) => o.id === response);
  const tabStop = selected >= 0 ? selected : 0;
  function onKey(e: KeyboardEvent<HTMLButtonElement>, i: number) {
    const n = options.length;
    const to = e.key === "ArrowDown" || e.key === "ArrowRight" ? (i + 1) % n : e.key === "ArrowUp" || e.key === "ArrowLeft" ? (i - 1 + n) % n : e.key === "Home" ? 0 : e.key === "End" ? n - 1 : -1;
    if (to < 0) return;
    e.preventDefault();
    refs.current[to]?.focus();
    setResponse(options[to].id);
  }
  return (
    <div className={`options ${pictures ? "pictures" : ""}`} role="radiogroup" aria-labelledby={labelledBy}>
      {options.map((o, i) => {
        const on = response === o.id;
        const state = checked ? (o.id === item.answer ? "right" : on ? "wrong" : "") : "";
        return (
          <div key={o.id} className={`optionCell ${o.audio ? "withAudio" : ""}`}>
            <button
              ref={(el) => { refs.current[i] = el; }}
              type="button"
              role="radio"
              aria-checked={on}
              tabIndex={i === tabStop ? 0 : -1}
              className={`option ${on ? "on" : ""} ${state}`}
              disabled={!!checked}
              onClick={() => setResponse(o.id)}
              onKeyDown={(e) => onKey(e, i)}
            >
              {o.image && <Picture image={imageById(images, o.image)} size="tile" caption={false} />}
              {o.text && <span lang={isGreek(o.text) ? "grc" : "en"}>{o.text}</span>}
              {state && <span className="srOnly">{state === "right" ? " (correct answer)" : " (your answer, wrong)"}</span>}
            </button>
            {o.audio && <SpeakButton text={o.audio} play={play} busy={busy} small />}
          </div>
        );
      })}
    </div>
  );
}

// ------------------------------------------------------------------- typed

function TypedItem({ item, response, setResponse, checked, onEnter }: { item: Item; response: Response; setResponse: (r: Response) => void; checked: GradeResult | null; onEnter: () => void }) {
  const gaps = item.gaps?.length ?? 1;
  const values = Array.isArray(response) ? (response as string[]) : Array.from({ length: gaps }, () => "");
  const set = (i: number, v: string) => {
    const next = [...values];
    while (next.length < gaps) next.push("");
    next[i] = v;
    setResponse(next);
  };
  if (item.template && item.template.includes("___")) {
    const parts = item.template.split("___");
    return (
      <p className="templateLine" lang="grc">
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {i < parts.length - 1 && (
              <GreekInput size="inline" value={values[i] ?? ""} onChange={(v) => set(i, v)} onEnter={onEnter} disabled={!!checked} autoFocus={i === 0} label={parts.length > 2 ? `Gap ${i + 1} of ${parts.length - 1}` : "The missing word"} />
            )}
          </span>
        ))}
        {checked && checked.gaps && <span className="gapMarks">{checked.gaps.map((g, i) => <span key={i} className={g ? "ok" : "warnText"}><span aria-hidden="true">{g ? "✓" : "✗"}</span><span className="srOnly" lang="en">gap {i + 1} {g ? "right" : "wrong"}</span></span>)}</span>}
      </p>
    );
  }
  return (
    <div className="typedBlock">
      {Array.from({ length: gaps }).map((_, i) => (
        <GreekInput key={i} value={values[i] ?? ""} onChange={(v) => set(i, v)} onEnter={onEnter} disabled={!!checked} autoFocus={i === 0} placeholder={item.gaps?.[i]?.hint ?? "type Greek"} label={gaps > 1 ? `Answer ${i + 1} of ${gaps}${item.gaps?.[i]?.hint ? `: ${item.gaps[i].hint}` : ""}` : `Your answer in Greek${item.gaps?.[i]?.hint ? `: ${item.gaps[i].hint}` : ""}`} />
      ))}
    </div>
  );
}

// ------------------------------------------------------------------- parse

function ParseItem({ item, response, setResponse, checked }: { item: Item; response: Response; setResponse: (r: Response) => void; checked: GradeResult | null }) {
  const given = (response && typeof response === "object" && !Array.isArray(response) ? response : {}) as Record<string, string>;
  const answer = (item.answer ?? {}) as Record<string, string>;
  return (
    <div className="parseBlock">
      <p className="parseForm" lang="grc">{item.form}</p>
      {(item.groups ?? []).map((g) => (
        <div key={g.id} className="parseGroup">
          <span className="parseLabel" id={`parse-${item.id}-${g.id}`}>{g.label}</span>
          <div className="chips" role="group" aria-labelledby={`parse-${item.id}-${g.id}`}>
            {g.options.map((o) => {
              const on = given[g.id] === o.id;
              const state = checked ? (answer[g.id] === o.id ? "right" : on ? "wrong" : "") : "";
              return (
                <button key={o.id} type="button" className={`chip ${on ? "on" : ""} ${state}`} aria-pressed={on} disabled={!!checked} onClick={() => setResponse({ ...given, [g.id]: o.id })}>
                  {o.label}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ locate

function LocateItem({ item, response, setResponse, checked }: { item: Item; response: Response; setResponse: (r: Response) => void; checked: GradeResult | null }) {
  const toks = itemTokens(item);
  const picked = new Set(((response as number[] | null) ?? []).map(Number));
  const answer = new Set((item.answer as number[]) ?? []);
  return (
    <p className="locateLine" lang="grc" role="group" aria-label="Words of the sentence: pick the right ones">
      {toks.map((t, i) => {
        const on = picked.has(i);
        const state = checked ? (answer.has(i) ? "right" : on ? "wrong" : "") : "";
        return (
          <button key={i} type="button" className={`token ${on ? "on" : ""} ${state}`} disabled={!!checked} aria-pressed={on} onClick={() => {
            const next = new Set(picked);
            if (next.has(i)) next.delete(i);
            else next.add(i);
            setResponse([...next].sort((a, b) => a - b));
          }}>
            {t}
          </button>
        );
      })}
    </p>
  );
}

// ----------------------------------------------------------------- reorder

function ReorderItem({ item, response, setResponse, checked, seed }: { item: Item; response: Response; setResponse: (r: Response) => void; checked: GradeResult | null; seed: number }) {
  const toks = itemTokens(item);
  const order = useMemo(() => seededShuffle(toks.map((_, i) => i), seed + hashString(item.id) + 1), [item, toks.length, seed]); // eslint-disable-line react-hooks/exhaustive-deps
  const chosen = ((response as string[] | null) ?? []);
  const used = new Map<string, number>();
  for (const c of chosen) used.set(c, (used.get(c) ?? 0) + 1);
  const remaining = order.map((i) => toks[i]).filter((t) => {
    const n = used.get(t) ?? 0;
    if (n > 0) {
      used.set(t, n - 1);
      return false;
    }
    return true;
  });
  return (
    <div className="reorderBlock">
      <p className="reorderLine" lang="grc" role="group" aria-label="Your sentence (activate a word to take it back)">
        {chosen.length === 0 && <span className="muted" lang="en">tap the words below in order</span>}
        {chosen.map((t, i) => (
          <button key={`${t}-${i}`} type="button" className="token on" disabled={!!checked} onClick={() => setResponse(chosen.filter((_, j) => j !== i))}>{t}</button>
        ))}
      </p>
      <p className="reorderBank" lang="grc" role="group" aria-label="Word bank (activate the words in order)">
        {remaining.map((t, i) => (
          <button key={`${t}-${i}`} type="button" className="token" disabled={!!checked} onClick={() => setResponse([...chosen, t])}>{t}</button>
        ))}
      </p>
    </div>
  );
}

// ------------------------------------------------------------------- match

function MatchItem({ item, response, setResponse, checked, seed }: { item: Item; response: Response; setResponse: (r: Response) => void; checked: GradeResult | null; seed: number }) {
  const pairs = item.pairs ?? [];
  const rights = useMemo(() => seededShuffle(pairs.map((p) => p.right), seed + hashString(item.id) + 2), [item, seed]); // eslint-disable-line react-hooks/exhaustive-deps
  const given = (response && typeof response === "object" && !Array.isArray(response) ? response : {}) as Record<string, string>;
  const [left, setLeft] = useState<string | null>(null);
  const taken = new Set(Object.values(given));
  const greek = isGreek;
  return (
    <div className="matchBlock">
      <div className="matchCol" role="group" aria-label="Pick an item">
        {pairs.map((p) => {
          const state = checked ? (given[p.left] === p.right ? "right" : "wrong") : "";
          return (
            <button key={p.left} type="button" className={`token ${left === p.left ? "on" : ""} ${given[p.left] ? "paired" : ""} ${state}`} disabled={!!checked} aria-pressed={left === p.left} lang={greek(p.left) ? "grc" : "en"} onClick={() => setLeft(left === p.left ? null : p.left)}>
              {p.left}{given[p.left] ? ` → ${given[p.left]}` : ""}
            </button>
          );
        })}
      </div>
      <div className="matchCol" role="group" aria-label={left ? `Pick the match for ${left}` : "Matches (pick an item on the left first)"}>
        {rights.map((r) => (
          <button key={r} type="button" className={`token ${taken.has(r) ? "paired" : ""}`} disabled={!!checked || !left} lang={greek(r) ? "grc" : "en"} onClick={() => {
            if (!left) return;
            const next = { ...given };
            for (const k of Object.keys(next)) if (next[k] === r) delete next[k];
            next[left] = r;
            setResponse(next);
            setLeft(null);
          }}>
            {r}
          </button>
        ))}
      </div>
      {checked && !checked.correct && <p className="feedbackKey">{keyText(item)}</p>}
    </div>
  );
}

// -------------------------------------------------------------------- self

function SelfItem({ item, response, setResponse, mode }: { item: Item; response: Response; setResponse: (r: Response) => void; mode: Mode }) {
  const [revealed, setRevealed] = useState(false);
  const [draft, setDraft] = useState("");
  return (
    <div className="selfBlock">
      <textarea className="selfDraft" aria-label={item.type === "translate-en" ? "Your translation (optional)" : "Your Greek (optional)"} lang={item.type === "translate-en" ? "en" : "grc"} placeholder={item.type === "translate-en" ? "your translation (optional)" : "your Greek (optional)"} value={draft} onChange={(e) => setDraft(e.target.value)} rows={2} />
      {item.bank && <p className="muted" lang="grc">Word bank: {item.bank.join(" · ")}</p>}
      {!revealed ? (
        <button type="button" className="secondary" onClick={() => setRevealed(true)}>Show the model answer</button>
      ) : (
        <>
          <p className="modelAnswer">{item.model}</p>
          <p className="muted">{mode === "test" ? "Mark yourself honestly; it counts toward your score." : "Did you get the meaning?"}</p>
          <div className="selfMarks">
            <button type="button" className={`secondary ${response === false ? "on" : ""}`} aria-pressed={response === false} onClick={() => setResponse(false)}>Not quite</button>
            <button type="button" className={`primary ${response === true ? "on" : ""}`} aria-pressed={response === true} onClick={() => setResponse(true)}>I got it</button>
          </div>
        </>
      )}
    </div>
  );
}
