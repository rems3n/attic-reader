/** Nouns, adjectives, pronouns: plural, third-declension stems, demonstratives,
 * comparison, numerals, the relative, attributive position, the dual. */

import type { ReactNode } from "react";
import { Arrow, Box, C, Chip, Curve, E, G, H, Person, Svg, tw } from "./kit";

// ------------------------------------------------------------- plural (2.2)

export function Plural() {
  const rows: [ReactNode, ReactNode, string][] = [
    [<>ὁ δοῦλ<H>ος</H></>, <>οἱ δοῦλ<H>οι</H></>, "slave"],
    [<>τὸ ἔργ<H>ον</H></>, <>τὰ ἔργ<H>α</H></>, "task"],
    [<>ἡ κόρ<H>η</H> · ἡ ὑδρί<H>α</H></>, <>αἱ κόρ<H>αι</H> · αἱ ὑδρί<H>αι</H></>, "girl · water jar"],
  ];
  return (
    <Svg w={640} h={400}>
      <E x={140} y={30} weight={600} fill={C.accent}>singular</E>
      <E x={460} y={30} weight={600} fill={C.accent}>plural</E>
      <Person x={140} y={140} s={1.15} />
      <Person x={400} y={140} s={1.15} />
      <Person x={460} y={140} s={1.15} />
      <Person x={520} y={140} s={1.15} />
      <Arrow x1={215} y1={100} x2={335} y2={100} />
      <G x={140} y={178} size={26}>ὁ δοῦλ<H>ος</H></G>
      <G x={460} y={178} size={26}>οἱ δοῦλ<H>οι</H></G>
      <line x1={20} y1={204} x2={620} y2={204} stroke={C.line} strokeWidth={1.5} />
      {rows.map(([sg, pl, en], i) => {
        const y = 222 + i * 48;
        return (
          <g key={en}>
            <Box x={20} y={y} w={600} h={40} r={8} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            <G x={140} y={y + 27} size={21}>{sg}</G>
            <Arrow x1={282} y1={y + 20} x2={318} y2={y + 20} sw={1.5} size={9} />
            <G x={460} y={y + 27} size={21}>{pl}</G>
          </g>
        );
      })}
      <E x={320} y={384}>
        genitive plural always <tspan fill={C.ink} style={{ fontFamily: "var(--serif)" }}>-ων</tspan>: τῶν δούλων, τῶν κορῶν
      </E>
    </Svg>
  );
}

// ----------------------------------------------------- third declension (3.1)

export function Decl3Stem() {
  const steps = [
    { grc: <>φύλαξ</>, en: "nominative", note: "hides the stem" },
    { grc: <>φύλακ<H>ος</H></>, en: "genitive", note: "shows it" },
    { grc: <>φυλακ-</>, en: "stem", note: "drop the -ος" },
  ];
  const sg: [ReactNode, string][] = [
    [<>φύλακ<H>ος</H></>, "gen."],
    [<>φύλακ<H>ι</H></>, "dat."],
    [<>φύλακ<H>α</H></>, "acc."],
  ];
  const pl: [ReactNode, string][] = [
    [<>φύλακ<H>ες</H></>, "nom."],
    [<>φυλάκ<H>ων</H></>, "gen."],
    [<>φύλαξ<H>ι(ν)</H></>, "dat."],
    [<>φύλακ<H>ας</H></>, "acc."],
  ];
  return (
    <Svg w={640} h={400}>
      {steps.map((s, i) => {
        const x = 20 + i * 212;
        return (
          <g key={s.en}>
            <Box x={x} y={20} w={176} h={104} fill={i === 2 ? C.wash : C.card} stroke={i === 2 ? C.sage : C.strong} />
            <G x={x + 88} y={62} size={28}>{s.grc}</G>
            <E x={x + 88} y={90} fill={C.ink} weight={600}>{s.en}</E>
            <E x={x + 88} y={112}>{s.note}</E>
            {i < 2 && <Arrow x1={x + 180} y1={72} x2={x + 208} y2={72} />}
          </g>
        );
      })}
      <E x={320} y={160}>the same endings on every consonant stem</E>
      <E x={42} y={211} weight={600} fill={C.accent}>sg.</E>
      <E x={42} y={301} weight={600} fill={C.accent}>pl.</E>
      {sg.map(([f, c], i) => (
        <g key={c}>
          <Chip x={74 + i * 138} y={184} w={130} h={44} size={21}>{f}</Chip>
          <E x={74 + i * 138 + 65} y={248}>{c}</E>
        </g>
      ))}
      {pl.map(([f, c], i) => (
        <g key={c}>
          <Chip x={74 + i * 138} y={274} w={130} h={44} size={21}>{f}</Chip>
          <E x={74 + i * 138 + 65} y={338}>{c}</E>
        </g>
      ))}
      <E x={320} y={380}>
        κ + σ is written ξ: <tspan style={{ fontFamily: "var(--serif)" }} fill={C.ink}>φύλαξ, φύλαξι</tspan>
      </E>
    </Svg>
  );
}

// ------------------------------------------------ οὗτος · ἐκεῖνος (3.2 picture)

export function HoutosEkeinos() {
  return (
    <Svg w={640} h={400}>
      {/* far ground */}
      <path d="M300 236 Q450 214 620 228" fill="none" stroke={C.line} strokeWidth={1.5} />
      <line x1={20} y1={300} x2={620} y2={300} stroke={C.strong} strokeWidth={1.5} />
      {/* speaker */}
      <Person x={100} y={300} s={1.3} fill={C.cream} stroke={C.strong} />
      {/* near man */}
      <Person x={220} y={300} s={1.25} />
      {/* far man */}
      <Person x={530} y={224} s={0.62} />
      {/* pointing */}
      <Arrow x1={122} y1={236} x2={196} y2={236} color={C.accent} />
      <Arrow x1={126} y1={222} x2={505} y2={190} color={C.accent} dash="6 6" />
      <G x={220} y={120} size={30} weight={600} fill={C.accent}>οὗτος</G>
      <E x={220} y={146} fill={C.ink}>this man, here</E>
      <G x={530} y={100} size={30} weight={600} fill={C.accent}>ἐκεῖνος</G>
      <E x={530} y={126} fill={C.ink}>that man, over there</E>
      <G x={100} y={340} size={21}>ἐγώ</G>
      <G x={220} y={340} size={21}>οὗτος ὁ παῖς</G>
      <G x={530} y={340} size={21}>ἐκεῖνος ὁ νεανίας</G>
      <E x={220} y={366}>near</E>
      <E x={530} y={366}>far</E>
    </Svg>
  );
}

// ------------------------------------------- demonstratives (3.2, 6.2 grammar)

export function Demonstratives() {
  const zones = [
    { x: 190, grc: "ὅδε", en: "this, here by me", s: 1 },
    { x: 360, grc: "οὗτος", en: "this, near; just said", s: 0.82 },
    { x: 540, grc: "ἐκεῖνος", en: "that, over there", s: 0.6 },
  ];
  const Group = ({ x, y, dem, noun, before }: { x: number; y: number; dem: string; noun: string; before: boolean }) => {
    const size = 24;
    const dw = tw(dem, size) + 24;
    const nw = tw(noun, size) + 28;
    const gap = 14;
    const total = dw + gap + nw;
    const x0 = x - total / 2;
    const dx = before ? x0 : x0 + nw + gap;
    const nx = before ? x0 + dw + gap : x0;
    return (
      <g>
        <Box x={nx} y={y} w={nw} h={46} fill={C.wash} stroke={C.sage} />
        <G x={nx + nw / 2} y={y + 31} size={size}>{noun}</G>
        <G x={dx + dw / 2} y={y + 31} size={size} weight={600} fill={C.accent}>{dem}</G>
      </g>
    );
  };
  return (
    <Svg w={640} h={400}>
      <line x1={20} y1={150} x2={620} y2={150} stroke={C.strong} strokeWidth={1.5} />
      <Person x={70} y={150} s={1.15} fill={C.cream} stroke={C.strong} />
      <E x={70} y={176}>speaker</E>
      {zones.map((z) => (
        <g key={z.grc}>
          <Person x={z.x} y={150} s={z.s} />
          <G x={z.x} y={36} size={26} weight={600} fill={C.accent}>{z.grc}</G>
          <E x={z.x} y={176} fill={C.ink}>{z.en}</E>
        </g>
      ))}
      <Arrow x1={110} y1={200} x2={600} y2={200} color={C.strong} sw={1.5} size={9} />
      <E x={600} y={222} anchor="end">further from the speaker</E>

      <line x1={20} y1={242} x2={620} y2={242} stroke={C.line} strokeWidth={1.5} />
      <Group x={170} y={262} dem="οὗτος" noun="ὁ παῖς" before />
      <Group x={470} y={262} dem="οὗτος" noun="ὁ παῖς" before={false} />
      <Group x={320} y={318} dem="ἐκεῖνος" noun="ὁ ἀνήρ" before />
      <E x={320} y={390}>article + noun stay together; the demonstrative stands outside</E>
    </Svg>
  );
}

// --------------------------------------------------------- comparison (6.1)

function Kylix({ x, y, s, level }: { x: number; y: number; s: number; level: 0 | 1 | 2 }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} strokeWidth={1.5 / s} stroke={C.accent} strokeLinejoin="round">
      <path d="M-26 0 Q0 -12 26 0 Z" fill={C.cream} />
      <rect x={-5} y={-26} width={10} height={20} fill={C.cream} />
      <path d="M-70 -56 C-62 -22 62 -22 70 -56 Z" fill={level === 2 ? C.sage : level === 1 ? C.hl : C.cream} />
      <path d="M-70 -54 C-90 -58 -92 -40 -64 -42" fill="none" />
      <path d="M70 -54 C90 -58 92 -40 64 -42" fill="none" />
      {level >= 1 && <path d="M-60 -46 C-40 -34 40 -34 60 -46" fill="none" />}
      {level === 2 &&
        [-40, -20, 0, 20, 40].map((d) => <circle key={d} cx={d} cy={-40 + Math.abs(d) * 0.1} r={2.6} fill={C.card} stroke="none" />)}
    </g>
  );
}

export function Comparison() {
  const cups = [
    { x: 110, s: 0.7, h: 30, grc: "καλός", en: "beautiful" },
    { x: 320, s: 0.9, h: 60, grc: "καλλίων", en: "more beautiful" },
    { x: 530, s: 1.1, h: 90, grc: "κάλλιστος", en: "most beautiful" },
  ] as const;
  return (
    <Svg w={640} h={400}>
      {cups.map((c, i) => (
        <g key={c.grc}>
          <Box x={c.x - 90} y={196 - c.h} w={180} h={c.h} r={6} fill={C.cream} stroke={C.strong} />
          <Kylix x={c.x} y={196 - c.h} s={c.s} level={i as 0 | 1 | 2} />
          <G x={c.x} y={232} size={26} weight={i ? 600 : undefined} fill={i ? C.accent : C.ink}>{c.grc}</G>
          <E x={c.x} y={256} fill={C.ink}>{c.en}</E>
        </g>
      ))}
      <line x1={20} y1={276} x2={620} y2={276} stroke={C.line} strokeWidth={1.5} />
      <E x={20} y={302} anchor="start" weight={600} fill={C.accent}>‘than’ = ἤ + the same case</E>
      <G x={40} y={332} size={21} anchor="start">ἡ κύλιξ καλλίων ἐστὶν <H>ἢ ἡ ὑδρία</H>.</G>
      <E x={20} y={362} anchor="start" weight={600} fill={C.accent}>or the genitive alone</E>
      <G x={40} y={392} size={21} anchor="start">ἡ κύλιξ καλλίων ἐστὶ <H>τῆς ὑδρίας</H>.</G>
    </Svg>
  );
}

// ------------------------------------------------------------ numbers (4.4)

function Ship({ x, y, n }: { x: number; y: number; n: number }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      {[-30, -18, -6, 6, 18, 30].map((d) => (
        <line key={d} x1={d} y1={-6} x2={d - 7} y2={12} stroke={C.strong} strokeWidth={1.5} strokeLinecap="round" />
      ))}
      <path d="M-50 -22 Q-46 -2 -32 0 L38 0 L54 -2 L44 -8 L48 -22 Z" fill={C.cream} stroke={C.accent} strokeWidth={1.5} strokeLinejoin="round" />
      <line x1={0} y1={-22} x2={0} y2={-76} stroke={C.accent} strokeWidth={1.5} />
      <rect x={-20} y={-72} width={40} height={40} rx={4} fill={C.card} stroke={C.accent} strokeWidth={1.5} />
      <E x={0} y={-45} size={20} fill={C.ink} weight={600}>{String(n)}</E>
    </g>
  );
}

export function Numbers() {
  const words = ["εἷς", "δύο", "τρεῖς", "τέτταρες", "πέντε", "ἕξ", "ἑπτά", "ὀκτώ", "ἐννέα", "δέκα"];
  return (
    <Svg w={640} h={400}>
      {words.map((w, i) => {
        const col = i % 5;
        const row = Math.floor(i / 5);
        const x = 68 + col * 126;
        const y = 104 + row * 146;
        return (
          <g key={w}>
            <path d={`M${x - 58} ${y + 16} q14 -6 29 0 t29 0 t29 0 t29 0`} fill="none" stroke={C.sage} strokeWidth={1.5} />
            <Ship x={x} y={y} n={i + 1} />
            <G x={x} y={y + 46} size={23} fill={i < 4 ? C.accent : C.ink} weight={i < 4 ? 600 : undefined}>{w}</G>
          </g>
        );
      })}
      <E x={320} y={384}>
        1–4 agree with their noun: <tspan style={{ fontFamily: "var(--serif)" }} fill={C.ink}>μία ναῦς · τρεῖς νῆες · δέκα νῆες</tspan>
      </E>
    </Svg>
  );
}

// ------------------------------------------------------------ relative (5.4)

export function Relative() {
  const y = 176;
  return (
    <Svg w={640} h={400}>
      <Box x={24} y={y - 34} w={134} h={50} fill={C.wash} stroke={C.sage} />
      <G x={91} y={y} size={25}>ὁ ἰατρός,</G>
      <Box x={180} y={y - 34} w={50} h={50} fill={C.hl} stroke={C.accent} />
      <G x={205} y={y} size={25} weight={600} fill={C.accent}>ὃν</G>
      <G x={300} y={y} size={25}>ὁ Σύρος</G>
      <G x={440} y={y} size={25}>ἐκάλεσεν,</G>
      <G x={570} y={y} size={25}>ἀφίκετο.</G>

      {/* gender and number from the antecedent */}
      <Curve x1={205} y1={y - 40} cx={150} cy={40} x2={96} y2={y - 40} />
      <E x={160} y={50} fill={C.ink} weight={600}>masculine singular</E>
      <E x={160} y={72}>like its antecedent</E>

      {/* case from its own clause */}
      <Curve x1={205} y1={y + 20} cx={320} cy={y + 80} x2={432} y2={y + 20} />
      <E x={440} y={y + 60} anchor="start" fill={C.ink} weight={600}>accusative</E>
      <E x={440} y={y + 82} anchor="start">object of ἐκάλεσεν</E>

      {/* bracket under the relative clause */}
      <path d={`M180 ${y + 104} v10 H500 v-10`} fill="none" stroke={C.strong} strokeWidth={1.5} />
      <E x={340} y={y + 138}>relative clause</E>
      <E x={320} y={y + 196} fill={C.ink} italic>The doctor whom Syros called arrived.</E>
    </Svg>
  );
}

// ------------------------------------------------------ position (Unit 7+)

function Phrase({ x, y, parts, frame, size = 25 }: { x: number; y: number; parts: { t: string; adj?: boolean }[]; frame: [number, number]; size?: number }) {
  const gap = 12;
  const widths = parts.map((p) => tw(p.t, size));
  const total = widths.reduce((a, b) => a + b, 0) + gap * (parts.length - 1);
  let cx = x - total / 2;
  const xs = widths.map((w) => {
    const s = cx;
    cx += w + gap;
    return s;
  });
  const fx = xs[frame[0]] - 10;
  const fw = xs[frame[1]] + widths[frame[1]] - xs[frame[0]] + 20;
  return (
    <g>
      <Box x={fx} y={y - size - 6} w={fw} h={size + 22} fill={C.wash} stroke={C.sage} />
      {parts.map((p, i) => (
        <G key={i} x={xs[i]} y={y} size={size} anchor="start" fill={p.adj ? C.accent : C.ink} weight={p.adj ? 600 : undefined}>
          {p.t}
        </G>
      ))}
    </g>
  );
}

export function Position() {
  return (
    <Svg w={640} h={400}>
      <E x={20} y={32} anchor="start" weight={600} fill={C.accent}>attributive: the adjective inside the article group</E>
      <Phrase x={165} y={96} parts={[{ t: "ὁ" }, { t: "ἀγαθὸς", adj: true }, { t: "ἀνήρ" }]} frame={[0, 2]} />
      <Phrase x={470} y={96} parts={[{ t: "ὁ" }, { t: "ἀνὴρ" }, { t: "ὁ" }, { t: "ἀγαθός", adj: true }]} frame={[0, 3]} />
      <E x={320} y={148} fill={C.ink} italic>“the good man”</E>

      <line x1={20} y1={180} x2={620} y2={180} stroke={C.line} strokeWidth={1.5} />
      <E x={20} y={216} anchor="start" weight={600} fill={C.accent}>predicate: the adjective outside it</E>
      <Phrase x={165} y={280} parts={[{ t: "ὁ" }, { t: "ἀνὴρ" }, { t: "ἀγαθός", adj: true }]} frame={[0, 1]} />
      <Phrase x={470} y={280} parts={[{ t: "ἀγαθὸς", adj: true }, { t: "ὁ" }, { t: "ἀνήρ" }]} frame={[1, 2]} />
      <E x={320} y={332} fill={C.ink} italic>“the man is good”</E>
      <E x={320} y={378}>(ἐστί is understood)</E>
    </Svg>
  );
}

// ---------------------------------------------------------------- dual

function Ox({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x} ${y})`} stroke={C.accent} strokeWidth={1.5} strokeLinejoin="round">
      <path d="M-22 -40 Q-44 -52 -40 -74" fill="none" />
      <path d="M22 -40 Q44 -52 40 -74" fill="none" />
      <path d="M-24 -44 Q0 -56 24 -44 L18 12 Q0 26 -18 12 Z" fill={C.cream} />
      <ellipse cx={0} cy={10} rx={14} ry={9} fill={C.hl} />
      <circle cx={-10} cy={-22} r={3} fill={C.ink} stroke="none" />
      <circle cx={10} cy={-22} r={3} fill={C.ink} stroke="none" />
    </g>
  );
}

export function Dual() {
  const rows = [
    { n: 1, label: "singular", grc: <>ὁ ἀδελφ<H>ός</H></>, sub: "" },
    { n: 2, label: "dual", grc: <>τὼ ἀδελφ<H>ώ</H></>, sub: "τοῖν ἀδελφοῖν" },
    { n: 3, label: "plural", grc: <>οἱ ἀδελφ<H>οί</H></>, sub: "" },
  ];
  return (
    <Svg w={640} h={400}>
      <Box x={20} y={20} w={220} h={360} fill={C.cream} stroke={C.line} />
      <Ox x={88} y={190} />
      <Ox x={172} y={190} />
      <rect x={42} y={130} width={176} height={12} rx={6} fill={C.sage} stroke={C.accent} strokeWidth={1.5} />
      <path d="M62 142 q26 34 52 0 M146 142 q26 34 52 0" fill="none" stroke={C.accent} strokeWidth={1.5} />
      <G x={130} y={264} size={25} weight={600} fill={C.accent}>τὼ βόε</G>
      <E x={130} y={290} fill={C.ink}>two oxen, a pair</E>
      <E x={130} y={330}>the dual: for two,</E>
      <E x={130} y={352}>often a natural pair</E>
      {rows.map((r, i) => {
        const y = 20 + i * 124;
        return (
          <g key={r.label}>
            <Box x={260} y={y} w={360} h={112} fill={i === 1 ? C.wash : C.card} stroke={i === 1 ? C.sage : C.strong} />
            {Array.from({ length: r.n }, (_, k) => (
              <Person key={k} x={296 + k * 30} y={y + 96} s={0.62} />
            ))}
            <E x={400} y={y + 30} anchor="start" weight={600} fill={C.accent}>{r.label}</E>
            <G x={400} y={y + 64} size={24} anchor="start">{r.grc}</G>
            {r.sub && (
              <G x={400} y={y + 96} size={19} anchor="start" fill={C.muted}>
                gen./dat. {r.sub}
              </G>
            )}
          </g>
        );
      })}
    </Svg>
  );
}
