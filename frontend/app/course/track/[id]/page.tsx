"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { SpeakButton, useSpeaker } from "../../../../components/Speak";
import Crumbs from "../../../../components/Crumbs";
import { PageError, PageLoading } from "../../../../components/PageState";
import { getCourse, getTrack } from "../../../../lib/api";
import type { CourseIndex, TrackDetail } from "../../../../lib/course";
import { findLesson, formatWait, trackGate, trackLessonStatus, trackState } from "../../../../lib/courseState";
import { loadProgress, saveProgress, type Progress } from "../../../../lib/progress";

const LADDER = ["Adapted", "Adapted", "Adapted", "Lightly adapted", "Lightly adapted", "Lightly adapted", "Original"];

/** A track: its seven lessons on the ladder adapted → original, the gate,
 * and the track word list. */
export default function TrackPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(params.id);
  const [track, setTrack] = useState<TrackDetail | null>(null);
  const [course, setCourse] = useState<CourseIndex | null>(null);
  const [progress, setProgress] = useState<Progress>(() => loadProgress());
  const [error, setError] = useState("");
  const [showWords, setShowWords] = useState(false);
  const [now] = useState(() => Date.now());
  const { play, busy } = useSpeaker();

  useEffect(() => {
    getTrack(id).then(setTrack).catch((e) => setError(e instanceof Error ? e.message : "Could not load the track"));
    getCourse().then(setCourse).catch(() => setCourse(null));
  }, [id]);
  useEffect(() => saveProgress(progress), [progress]);

  const baseCrumbs = [{ label: "Course", href: "/course" }, { label: "Tracks", href: "/course#tracks" }];
  if (error) return <PageError message={error} crumbs={baseCrumbs} back={{ href: "/course#tracks", label: "All tracks" }} />;
  if (!track || !course) return <PageLoading label="Loading the track…" crumbs={baseCrumbs} />;

  const cp = progress.course;
  const ts = trackState(cp, track);
  const gate = trackGate(course, cp, track, now);
  const chosen = cp.track === track.id;
  const title = (lid: string) => findLesson(course, lid);
  const requiresMet = (lid?: string) => !lid || ["done", "skipped"].includes(cp.lessons[lid]?.status ?? "");

  return (
    <main className="shell trackPage">
      <Crumbs items={[...baseCrumbs, { label: track.title_grc, lang: "grc" }]} />
      <section className="hero">
        <p className="eyebrow">TRACK · {ts.done} OF {ts.total || track.lessons.length} DONE</p>
        <h1 lang="grc">{track.title_grc}</h1>
        <p className="lede">{track.title_en}. {track.blurb}</p>
        <div className="actions">
          <button type="button" className={chosen ? "secondary" : ts.next ? "secondary" : "primary"} aria-pressed={chosen} onClick={() => setProgress({ ...progress, course: { ...cp, track: chosen ? undefined : track.id } })}>
            {chosen ? "Your track ✓ · unset" : "Make this my track"}
          </button>
          {ts.next && <Link href={`/course/lesson/${ts.next}`} className="primary buttonLike">{cp.lessons[ts.next]?.status === "in-progress" ? "Resume" : "Open"} lesson {ts.next.split(".")[1]} →</Link>}
        </div>
        {ts.state === "locked" && <p className="muted small">The first three lessons open when you finish lesson {track.side_after}; the rest after {track.full_after}.</p>}
        {ts.state === "side" && <p className="muted small">Lessons 1–3 are open as side readings. Lessons 4–7 open after lesson {track.full_after}.</p>}
      </section>

      <ol className="trackLadder">
        {track.lessons.map((l, i) => {
          const st = l.available ? trackLessonStatus(cp, track, l.id) : "locked";
          const open = l.available && st !== "locked";
          const src = l.source ?? title(l.id)?.source;
          const body = (
            <>
              <span className={`dot ${st} ${!l.available ? "planned" : ""}`} aria-hidden="true" />
              <span className="ladderText">
                <span className="ladderTop">
                  <span className="unitLabel">{i + 1} · {LADDER[i] ?? "Original"}{l.side ? " · side reading" : ""}</span>
                  {st === "done" && <span className="unitLabel doneMark">DONE ✓</span>}
                </span>
                <span className="ladderTitle" lang="grc">{l.available ? l.title_grc : "—"}</span>
                <span className="unitSub">
                  {l.available ? l.title_en : "Planned"}
                  {src?.author ? ` · ${src.author}, ${src.work ?? ""} ${src.ref ?? ""}`.trimEnd() : ""}
                </span>
                {!open && l.available && <span className="muted small">{requiresMet(l.requires) ? `Opens when lesson ${i} of this track is done` : `Opens after lesson ${l.requires}`}</span>}
              </span>
            </>
          );
          return <li key={l.id} className={`ladderItem ${open ? "open" : "locked"}`}>{open ? <Link href={`/course/lesson/${l.id}`}>{body}<span className="tileGo" aria-hidden="true">›</span></Link> : <div>{body}</div>}</li>;
        })}
        <li className={`ladderItem gate ${gate.state === "open" || gate.state === "passed" ? "open" : "locked"}`}>
          {gate.state === "open" || gate.state === "passed" ? (
            <Link href={`/course/test/${track.gate}`}>
              <span className={`dot ${gate.state === "passed" ? "done" : "open"}`} aria-hidden="true" />
              <span className="ladderText">
                <span className="unitLabel">8 · TRACK GATE{gate.state === "passed" ? " · PASSED ✓" : ""}</span>
                <span className="ladderTitle">An unseen original passage</span>
                <span className="unitSub">{gate.state === "passed" ? "Retake any time" : "Questions, parsing and translation · no feedback until the end"}</span>
              </span>
            </Link>
          ) : (
            <div>
              <span className="dot locked" aria-hidden="true" />
              <span className="ladderText">
                <span className="unitLabel">8 · TRACK GATE</span>
                <span className="ladderTitle">An unseen original passage</span>
                <span className="muted small">{!track.gate_available ? "Planned" : gate.state === "waiting" ? `Opens in ${formatWait((gate.availableAt ?? now) - now)}` : "Finish the track's lessons to unlock it"}</span>
              </span>
            </div>
          )}
        </li>
      </ol>

      {track.texts.length > 0 && (
        <section className="card">
          <div className="sectionHead"><div><h2>Texts</h2><p>Every lesson reads a real passage, simplified at first and then as written.</p></div></div>
          <ul className="trackTexts">
            {track.texts.map((t) => (
              <li key={t.lesson}><span className="muted">{t.lesson.split(".")[1]}</span> {t.author}, <em>{t.work}</em> {t.ref}{t.title ? ` · ${t.title}` : ""}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="card">
        <div className="sectionHead">
          <div>
            <h2>Track words</h2>
            <p>{track.words.length ? `${track.words.length} words this track teaches on top of the core list.` : "The track's word list appears as its lessons are written."}</p>
          </div>
          {track.words.length > 0 && <button type="button" className="linkButton" aria-expanded={showWords} aria-controls="track-words" onClick={() => setShowWords((s) => !s)}>{showWords ? "Hide" : "Show"}<span className="srOnly"> the track words</span></button>}
        </div>
        {track.words.length > 0 && (
          <p><Link href={`/vocab?words=${track.words.map((w) => w.id).join(",")}&from=${encodeURIComponent(`${track.title_en} track`)}`} className="secondary buttonLike">Study the track words</Link></p>
        )}
        {showWords && (
          <ul className="trackWords" id="track-words">
            {track.words.map((w) => (
              <li key={w.id}>
                <SpeakButton text={w.lemma} play={play} busy={busy} small />
                <Link href={`/vocab/${w.id}`} lang="grc" className="trackWordLemma">{w.headword}</Link>
                <span className="muted">{w.short}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
