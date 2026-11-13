"use client";
import Link from "next/link";
import { useLayoutEffect, useState } from "react";
import Logo from "./Logo";

const SPEEDS = [0.5, 0.6, 0.75, 1];
const IMG = "/course/illustrations";

function Arrow() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14" />
      <path d="M13 6l6 6-6 6" />
    </svg>
  );
}

/** Marketing home for visitors who have not started yet. Hides the app shell. */
export default function Landing() {
  const [speed, setSpeed] = useState(0.75);
  useLayoutEffect(() => {
    document.body.classList.add("landingMode");
    return () => document.body.classList.remove("landingMode");
  }, []);
  const cta = (
    <>
      <Link href="/start" className="lpBtn lpBtnPrimary">
        Try it <Arrow />
      </Link>
      <Link href="/account" className="lpBtn lpBtnGhost">
        Sign up
      </Link>
    </>
  );
  return (
    <main className="lp">
      <header className="lpHero">
        <img className="lpBg lpKb" src={`${IMG}/polis.webp`} alt="" />
        <div className="lpShade" aria-hidden="true" />
        <div className="lpFade" aria-hidden="true" />
        <nav aria-label="Home page" className="lpNav lpWrap">
          <span className="lpBrand">
            <Logo size={40} />
            <span>Attic Academy</span>
          </span>
          <div className="lpNavLinks">
            <a href="#why">Why it is different</a>
            <a href="#journey">The course</a>
            <a href="#reading">Voice and reading</a>
          </div>
          <div className="lpNavCta">
            <Link href="/account" className="lpBtn lpBtnGhost lpBtnSmall">
              Sign up
            </Link>
            <Link href="/start" className="lpBtn lpBtnPrimary lpBtnSmall">
              Try it
            </Link>
          </div>
        </nav>
        <div className="lpHeroBody lpWrap">
          <div className="lpHeroCopy">
            <p className="lpEyebrow lpIn">Classical Greek · from the alphabet to original texts</p>
            <h1 className="lpIn lpIn2">
              Read Ancient Greek.
              <br />
              Hear it the way Athens did.
            </h1>
            <p className="lpLede lpIn lpIn3">
              A story-driven course, a library of Greek authors and a voice that
              reads every word aloud in reconstructed Classical Attic, the
              pronunciation of about 400 BC.
            </p>
            <div className="lpActions lpIn lpIn4">{cta}</div>
            <p className="lpSmall lpIn lpIn4">
              80 lessons · 524 core words · 4 reading tracks. No account needed to try it.
            </p>
          </div>
          <div className="lpDrift">
            <div className="lpPlayer lpIn lpIn3" style={{ ["--dur" as string]: `${(3 / speed).toFixed(2)}s` }}>
              <div className="lpPlayerHead">
                <span className="lpTag">Lesson 1.1 · listening</span>
                <div className="lpBars" aria-hidden="true">
                  {[0, 0.15, 0.3, 0.45, 0.6, 0.2, 0.5].map((d, i) => (
                    <span key={i} style={{ animationDelay: `${d}s` }} />
                  ))}
                </div>
              </div>
              <p className="lpGreek lpSentence" lang="grc">
                <span className="lpW lpW1">ὁ</span> <span className="lpW lpW2">Ἀρίστων</span>{" "}
                <span className="lpW lpW3">κεραμεύς</span> <span className="lpW lpW4">ἐστιν.</span>
              </p>
              <p className="lpMuted">Ariston is a potter. The word being spoken lights up as the voice reads.</p>
              <div className="lpPlayerFoot">
                <span className="lpPlay" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 4l14 8-14 8z" />
                  </svg>
                </span>
                <span className="lpMuted">Speed</span>
                <div role="group" aria-label="Demo playback speed" className="lpPills">
                  {SPEEDS.map((v) => (
                    <button key={v} type="button" aria-pressed={v === speed} className={v === speed ? "on" : ""} onClick={() => setSpeed(v)}>
                      {v}×
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section id="why" className="lpSection lpWrap">
        <div className="lpHead">
          <p className="lpEyebrow">Why it is different</p>
          <h2>Most Greek courses hand you tables. This one hands you a city.</h2>
        </div>
        <div className="lpCards">
          <article className="lpCard">
            <div className="lpCardImg">
              <img src={`${IMG}/verb-akouei.webp`} alt="A woman cups her hand to her ear, listening" loading="lazy" />
            </div>
            <div className="lpCardBody">
              <h3>It sounds like Classical Athens</h3>
              <p>Our own pronunciation rules drive a natural voice. Modern Greek sounds never creep in.</p>
            </div>
          </article>
          <article className="lpCard">
            <div className="lpCardImg">
              <img src={`${IMG}/panel-1-1-a.webp`} alt="Ariston and Chrysis outside their house in Athens, with their dog Labros" loading="lazy" />
            </div>
            <div className="lpCardBody">
              <h3>You learn from a story told in Greek</h3>
              <p>Follow a potter&rsquo;s family through Athens in 432 BC. New words arrive with pictures, not word lists.</p>
            </div>
          </article>
          <article className="lpCard">
            <div className="lpCardImg">
              <img src={`${IMG}/biblion.webp`} alt="A papyrus scroll unrolled on a table, the Acropolis behind it" loading="lazy" />
            </div>
            <div className="lpCardBody">
              <h3>It ends in the real authors</h3>
              <p>By the last units you are reading real Thucydides, Plato and Xenophon.</p>
            </div>
          </article>
        </div>
      </section>

      <section id="journey" className="lpLight">
        <div className="lpSection lpWrap">
          <div className="lpHead">
            <p className="lpEyebrow">The learning journey</p>
            <h2>
              <span lang="grc">Ἡ ὁδός</span>: the road from alpha to Plato
            </h2>
            <p className="lpLede">Three stages, twelve units, one continuous story. A placement test drops you in at the right unit.</p>
          </div>
          <div className="lpStages">
            <article>
              <span className="lpTag">Stage 0 · 4 lessons</span>
              <h3 lang="grc">Στοιχεῖα</h3>
              <p className="lpStrong">Letters and sounds</p>
              <p>The alphabet, breathings, accents and how Classical Attic sounded.</p>
            </article>
            <article>
              <span className="lpTag">Stage 1 · 6 units</span>
              <h3 lang="grc">Θεμέλια</h3>
              <p className="lpStrong">Foundations</p>
              <p>The agora, the household, the city, Piraeus, the gods and money.</p>
            </article>
            <article>
              <span className="lpTag">Stage 2 · 6 units</span>
              <h3 lang="grc">Γέφυρα</h3>
              <p className="lpStrong">The bridge</p>
              <p>The Dionysia, the Assembly, the war and the law court, ending in real authors.</p>
            </article>
          </div>
          <div className="lpTracks">
            <span className="lpStrong">Then choose a reading track:</span>
            {["Μυθολογία", "Φιλοσοφία", "Ἱστορία", "Πολιτεία"].map((t) => (
              <span key={t} lang="grc" className="lpTrack">
                {t}
              </span>
            ))}
            <span className="lpTracksNote">Mythology, philosophy, history, politics</span>
          </div>
        </div>
      </section>

      <section id="reading" className="lpSection lpWrap lpSplit">
        <div className="lpSplitCopy">
          <div className="lpHead">
            <p className="lpEyebrow">Voice and reading</p>
            <h2>Everything speaks. Every word explains itself.</h2>
          </div>
          <ul className="lpList">
            <li>
              <strong>Listen sentence by sentence.</strong> <span>The spoken word lights up, at the speed you choose.</span>
            </li>
            <li>
              <strong>Highlight a word to translate it.</strong> <span>Its dictionary meaning appears beside the text.</span>
            </li>
            <li>
              <strong>Read the library or your own page.</strong> <span>Pick a passage from Plato or Xenophon, or photograph any Greek page.</span>
            </li>
            <li>
              <strong>Practise what you met.</strong> <span>Spaced-repetition word decks, grammar tables and drills, all with audio.</span>
            </li>
          </ul>
        </div>
        <div className="lpDemo">
          <span className="lpTag">Xenophon, Anabasis 1.1</span>
          <p className="lpGreek" lang="grc">
            Δαρείου καὶ Παρυσάτιδος γίγνονται <span className="lpSel">παῖδες</span> δύο.
          </p>
          <div className="lpPop">
            <span className="lpGreek" lang="grc">
              παῖς, παιδός, ὁ / ἡ
            </span>
            <span>child; boy, girl; son, daughter</span>
          </div>
        </div>
      </section>

      <section className="lpClose">
        <img className="lpBg lpKb" src={`${IMG}/hodos.webp`} alt="" loading="lazy" />
        <div className="lpShade lpShadeDeep" aria-hidden="true" />
        <div className="lpCloseBody">
          <h2>What you will get out of it</h2>
          <ul className="lpOutcomes">
            <li>
              <span className="lpGreek" aria-hidden="true">α</span>
              <span>Pronounce Greek the Classical way.</span>
            </li>
            <li>
              <span className="lpGreek" aria-hidden="true">β</span>
              <span>Follow a story in Greek without translating word by word.</span>
            </li>
            <li>
              <span className="lpGreek" aria-hidden="true">γ</span>
              <span>Read real Plato, Thucydides and Xenophon.</span>
            </li>
          </ul>
          <div className="lpActions lpCenter">{cta}</div>
        </div>
      </section>

      <footer className="lpFooter">
        <div className="lpWrap lpFooterInner">
          <span className="lpBrand lpBrandSmall">Attic Academy</span>
          <p>
            Vocabulary from the{" "}
            <a href="https://dcc.dickinson.edu/greek-core-list" target="_blank" rel="noreferrer">
              DCC Greek Core List
            </a>{" "}
            (CC BY-SA). Greek texts from the{" "}
            <a href="https://github.com/PerseusDL/canonical-greekLit" target="_blank" rel="noreferrer">
              Perseus Digital Library
            </a>{" "}
            (CC BY-SA). Pictures: see <Link href="/learn/credits">credits</Link>. Pronunciation: reconstructed Classical Attic, never Modern Greek.
          </p>
        </div>
      </footer>
    </main>
  );
}
