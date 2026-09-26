"use client";

import Link from "next/link";
import Crumbs from "../../../components/Crumbs";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import ExerciseRunner, { type Outcome } from "../../../components/course/ExerciseRunner";
import { getCourse, getCourseImages, getCourseItems, getCourseSkill, getDrill } from "../../../lib/api";
import { scoreOf, updateSkill, weakSkills, type CourseIndex, type ImageRecord, type Item } from "../../../lib/course";
import { lastDoneLesson } from "../../../lib/courseState";
import { addError, bumpActivity, loadProgress, saveProgress, strictAccentsFor, type CourseProgress, type Progress } from "../../../lib/progress";
import { deckRefs, dismissCards, markDeckAnswer, mistakeDeck, originLabel, pickDeckItems, type DeckCard, type DeckItem } from "../../../lib/skills";
import styles from "../skills/skills.module.css";

const SESSION = 10;
const DECK_SESSION = 12;

type Mode = { kind: "weak" } | { kind: "skills"; skills: string[] } | { kind: "mistakes" };

export default function ReviewPage() {
  return (
    <Suspense fallback={<main className="shell"><p className="muted">Loading…</p></main>}>
      <Review />
    </Suspense>
  );
}

/**
 * Three kinds of practice on one screen:
 * - default: a quiz generated from the learner's weakest skills;
 * - `?skills=a,b`: generated items for those skills (Practise on /course/skills);
 * - `?mode=mistakes`: the items the learner got wrong, rebuilt from the error
 *   log; an item leaves the deck after two right answers in a row.
 */
function Review() {
  const search = useSearchParams();
  const skillsParam = search.get("skills") ?? "";
  const mode: Mode = useMemo(() => {
    if (search.get("mode") === "mistakes") return { kind: "mistakes" };
    const list = skillsParam.split(",").map((s) => s.trim()).filter(Boolean);
    return list.length ? { kind: "skills", skills: list } : { kind: "weak" };
  }, [search, skillsParam]);

  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [items, setItems] = useState<DeckItem[] | null>(null);
  const [missing, setMissing] = useState<DeckCard[]>([]);
  const [error, setError] = useState("");
  const [done, setDone] = useState<{ score: number } | null>(null);
  const [round, setRound] = useState(0);
  const keyOf = useRef(new Map<string, string>()); // session item id → deck key
  const scopeRef = useRef<string>("0.4");
  const deckAtStart = useRef(0); // deck size when the round was built

  useEffect(() => {
    getCourse().then(setCourse).catch((e) => setError(e instanceof Error ? e.message : "Could not load the course"));
    getCourseImages().then(setImages).catch(() => setImages([]));
  }, []);
  useEffect(() => saveProgress(progress), [progress]);

  const deck = useMemo(() => mistakeDeck(progress.course.errors), [progress.course.errors]);

  // build the round
  useEffect(() => {
    if (!course) return;
    let cancelled = false;
    const fail = (e: unknown) => !cancelled && setError(e instanceof Error ? e.message : "Could not build the quiz");
    const seed = (Date.now() + round) % 100000;
    const cp = progress.course;
    const scope = lastDoneLesson(course, cp) ?? "0.4";
    scopeRef.current = scope;
    setItems(null);
    setMissing([]);
    deckAtStart.current = mistakeDeck(cp.errors).length;

    if (mode.kind === "weak") {
      const weak = weakSkills(cp.skills, 6).filter((s) => /^(noun|art|verb|adj)\./.test(s));
      if (!weak.length) {
        setItems([]);
        return;
      }
      getDrill(weak, scope, SESSION, seed).then((its) => !cancelled && setItems(tagDrill(its, seed))).catch(fail);
    } else if (mode.kind === "skills") {
      // the learner's own scope first; if it has no words for the skill yet,
      // the lessons that teach it
      (async () => {
        const tried = new Set<string>();
        const scopes = [scope];
        for (let i = 0; i < scopes.length && i < 6; i += 1) {
          const sc = scopes[i];
          if (tried.has(sc)) continue;
          tried.add(sc);
          const its = await getDrill(mode.skills, sc, SESSION, seed);
          if (its.length) {
            scopeRef.current = sc;
            return its;
          }
          if (i === 0) {
            const details = await Promise.all(mode.skills.map((s) => getCourseSkill(s).catch(() => null)));
            for (const d of details) for (const l of d?.lessons ?? []) scopes.push(l.id);
          }
        }
        return [];
      })().then((its) => !cancelled && setItems(tagDrill(its, seed))).catch(fail);
    } else {
      const cards = mistakeDeck(cp.errors).slice(0, DECK_SESSION);
      if (!cards.length) {
        setItems([]);
        return;
      }
      getCourseItems(deckRefs(cards), scope, seed)
        .then((res) => {
          if (cancelled) return;
          const picked = pickDeckItems(cards, res.items);
          keyOf.current = picked.keyOf;
          const lost = new Set(res.missing);
          setMissing(cards.filter((c) => lost.has(c.key)));
          setItems(picked.items.map((it) => withAccents(it, cards.find((c) => c.key === picked.keyOf.get(it.id)), progress)));
        })
        .catch(fail);
    }
    return () => {
      cancelled = true;
    };
    // the round is built once per mode/round, not on every progress change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [course, round, mode]);

  function record(o: Outcome) {
    const now = Date.now();
    const item = o.item as DeckItem;
    setProgress((p) => {
      let c: CourseProgress = { ...p.course, skills: { ...p.course.skills } };
      for (const s of item.skills) c.skills[s] = updateSkill(c.skills[s], o.result.correct, now);
      const answer = JSON.stringify(o.response).slice(0, 120);
      if (mode.kind === "mistakes") {
        const key = keyOf.current.get(item.id);
        const card = key ? mistakeDeck(c.errors).find((x) => x.key === key) : undefined;
        if (key && card) {
          c = { ...c, errors: markDeckAnswer(c.errors, key, o.result.correct, now) };
          if (!o.result.correct) c = addError(c, { item: card.item, lesson: card.lesson, answer, at: now, ...(card.skills ? { skills: card.skills } : {}) });
        }
      } else if (!o.result.correct) {
        // drill ids (drill1…) repeat every round: log a unique id with its skills and scope
        c = addError(c, { item: item.id, lesson: scopeRef.current, answer, at: now, skills: item.skills });
      }
      c = bumpActivity(c, 1, 0.5, now);
      return { ...p, course: c };
    });
  }

  function dismissMissing() {
    const keys = missing.map((m) => m.key);
    setProgress((p) => ({ ...p, course: { ...p.course, errors: dismissCards(p.course.errors, keys, Date.now()) } }));
    setMissing([]);
  }

  const skillLabel = (id: string) => course?.skills.find((s) => s.id === id)?.label ?? id;
  const title = mode.kind === "mistakes" ? "MISTAKES" : mode.kind === "skills" ? "PRACTISE" : "REVIEW QUIZ";

  if (error) return <main className="shell"><p className="error">{error}</p></main>;
  return (
    <main className="shell lessonShell">
      <Crumbs items={[{ label: "Course", href: "/course" }, ...(mode.kind !== "weak" ? [{ label: "Skills", href: "/course/skills" }] : []), { label: mode.kind === "mistakes" ? "Mistakes" : "Review" }]} />
      <section className="card">
        <p className="eyebrow">{title}</p>
        {mode.kind === "skills" ? (
          <h1 className={styles.reviewTitle}>{mode.skills.map(skillLabel).join(" · ")}</h1>
        ) : (
          <h1 className={styles.reviewTitle}>{mode.kind === "mistakes" ? "Mistakes deck" : "Review quiz"}</h1>
        )}
        {mode.kind === "mistakes" && done === null && (
          <p className={styles.reviewLede}>
            {deck.length === 0 ? "No mistakes waiting." : `${deck.length} in the deck${deck.length > DECK_SESSION ? `, ${DECK_SESSION} this round` : ""}.`} An item leaves the deck when you get it right twice in a row.
          </p>
        )}
        {missing.length > 0 && done === null && (
          <div className={styles.missing}>
            <p>{missing.length} older {missing.length === 1 ? "mistake" : "mistakes"} can no longer be rebuilt (the exercise changed).</p>
            <button type="button" className="secondary" onClick={dismissMissing}>Remove {missing.length === 1 ? "it" : "them"}</button>
          </div>
        )}

        {items === null && <p className="muted">Building your {mode.kind === "mistakes" ? "deck" : "quiz"}…</p>}
        {items && items.length === 0 && (
          <p className="muted">
            {mode.kind === "mistakes" ? "Nothing to redo: every mistake has been answered right twice in a row." : mode.kind === "skills" ? "No items can be generated for this skill yet: it is practised inside the lessons." : "Nothing to review yet: finish a lesson with form exercises first."}
          </p>
        )}
        {items && items.length > 0 && done === null && (
          <ExerciseRunner
            key={round}
            items={items as Item[]}
            images={images}
            mode="practice"
            accents={false}
            onOutcome={record}
            onDone={(outs) => setDone({ score: scoreOf(outs.map((o) => o.result)) })}
            seed={round}
            title={mode.kind === "mistakes" ? "Mistakes" : mode.kind === "skills" ? "Practise" : "Review"}
            renderAbove={mode.kind === "mistakes" ? (it) => <DeckItemHead item={it as DeckItem} card={deck.find((c) => c.key === keyOf.current.get(it.id))} /> : undefined}
          />
        )}
        {done !== null && (
          <div className="stepDone">
            <p className="resultBig">{Math.round(done.score * 100)} %</p>
            {mode.kind === "mistakes" && (
              <p className="muted">{deckAtStart.current > deck.length ? `${deckAtStart.current - deck.length} left the deck. ` : ""}{deck.length ? `${deck.length} still in the deck.` : "The deck is empty."}</p>
            )}
            <div className="stepNav">
              {(mode.kind !== "mistakes" || deck.length > 0) && (
                <button type="button" className="primary" onClick={() => { setDone(null); setItems(null); setRound(round + 1); }}>Another round</button>
              )}
              <Link href={mode.kind === "weak" ? "/course" : "/course/skills"} className="secondary buttonLike">{mode.kind === "weak" ? "Course home" : "Skills"}</Link>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

/** Drill ids (drill1…) repeat every round; make them unique per round. */
function tagDrill(items: Item[], seed: number): DeckItem[] {
  return items.map((it, n) => ({ ...it, id: `review-${seed}:g${n + 1}` }));
}

/** Typed answers follow the accent policy of the lesson the mistake came from. */
function withAccents(item: DeckItem, card: DeckCard | undefined, p: Progress): DeckItem {
  if (item.strict_accents != null) return item;
  const lesson = item.origin?.scope ?? card?.lesson ?? "";
  return { ...item, strict_accents: strictAccentsFor(p.settings, lesson) };
}

function DeckItemHead({ item, card }: { item: DeckItem; card?: DeckCard }) {
  const ctx = item.context;
  return (
    <div className={styles.deckHead}>
      <p className={styles.deckOrigin}>
        {originLabel(item)}
        {card && card.misses > 1 ? ` · missed ${card.misses}×` : ""}
        {card && card.right > 0 ? ` · ${card.right} right in a row` : ""}
      </p>
      {ctx && (
        <details className={styles.deckContext}>
          <summary>{ctx.kind === "story" ? "The story" : "The passage"}{ctx.title ? <> · <span lang="grc">{ctx.title}</span></> : null}</summary>
          <p lang="grc">{ctx.text}</p>
          {ctx.glosses && Object.keys(ctx.glosses).length > 0 && (
            <p className={styles.deckGlosses}>{Object.entries(ctx.glosses).map(([w, g]) => <span key={w}><span lang="grc">{w}</span> {g}</span>)}</p>
          )}
        </details>
      )}
    </div>
  );
}
