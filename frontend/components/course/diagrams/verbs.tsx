/** Verbs: contraction, voice, aspect, augment, narrative tenses, root aorists,
 * future, -μι verbs, ἵστημι, perfect, participles. */

import type { ReactNode } from "react";
import { Arrow, Box, C, Curve, E, G, Gk, H, Person, Segs, Svg } from "./kit";

// ------------------------------------------------------ contraction (2.4)

export function Contract() {
  const cols = [
    {
      x: 20,
      head: <>ποιέ-ω → ποι<H>ῶ</H></>,
      en: "-έω verbs",
      rows: [
        ["ε + ε → ει", <>ποιέ-ετε → ποι<H>εῖ</H>τε</>],
        ["ε + ο → ου", <>ποιέ-ομεν → ποι<H>οῦ</H>μεν</>],
        ["ε + ω → ω", <>ποιέ-ω → ποι<H>ῶ</H></>],
      ],
    },
    {
      x: 330,
      head: <>τιμά-ω → τιμ<H>ῶ</H></>,
      en: "-άω verbs",
      rows: [
        ["α + ε → ᾱ", <>τιμά-ετε → τιμ<H>ᾶ</H>τε</>],
        ["α + ει → ᾳ", <>τιμά-ει → τιμ<H>ᾷ</H></>],
        ["α + ο → ω", <>τιμά-ομεν → τιμ<H>ῶ</H>μεν</>],
      ],
    },
  ] as const;
  return (
    <Svg w={640} h={400}>
      {cols.map((c) => (
        <g key={c.en}>
          <Box x={c.x} y={16} w={290} h={78} fill={C.wash} stroke={C.sage} />
          <E x={c.x + 145} y={42} weight={600} fill={C.accent}>{c.en}</E>
          <G x={c.x + 145} y={78} size={26}>{c.head}</G>
          {c.rows.map(([rule, ex], i) => {
            const y = 110 + i * 94;
            return (
              <g key={rule}>
                <Box x={c.x} y={y} w={290} h={84} />
                <G x={c.x + 145} y={y + 32} size={21} fill={C.accent} weight={600}>{rule}</G>
                <G x={c.x + 145} y={y + 66} size={22}>{ex}</G>
              </g>
            );
          })}
        </g>
      ))}
    </Svg>
  );
}

// ------------------------------------------------------ middle voice (3.3)

export function MiddleVoice() {
  const rows = [
    ["I", "λύ", "ω", "λύ", "ομαι"],
    ["you", "λύ", "εις", "λύ", "ει / -ῃ"],
    ["he, she", "λύ", "ει", "λύ", "εται"],
    ["we", "λύ", "ομεν", "λυ", "όμεθα"],
    ["you (pl.)", "λύ", "ετε", "λύ", "εσθε"],
    ["they", "λύ", "ουσι(ν)", "λύ", "ονται"],
  ];
  return (
    <Svg w={640} h={400}>
      <E x={180} y={30} weight={600} fill={C.accent}>active</E>
      <E x={330} y={30} weight={600} fill={C.accent}>middle</E>
      {rows.map(([p, s1, e1, s2, e2], i) => {
        const y = 44 + i * 52;
        return (
          <g key={p}>
            <Box x={20} y={y} w={390} h={46} r={8} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            <E x={34} y={y + 29} anchor="start">{p}</E>
            <G x={180} y={y + 31} size={23}>{s1}<H>{e1}</H></G>
            <G x={330} y={y + 31} size={23}>{s2}<H>{e2}</H></G>
          </g>
        );
      })}
      {/* what the middle means */}
      <Box x={430} y={16} w={190} h={368} fill={C.cream} stroke={C.line} />
      <Person x={480} y={140} s={0.85} />
      <Person x={572} y={140} s={0.85} fill={C.card} />
      <Arrow x1={502} y1={100} x2={548} y2={100} />
      <G x={525} y={176} size={22}>λούει</G>
      <E x={525} y={200} fill={C.ink}>washes (someone)</E>
      <line x1={446} y1={222} x2={604} y2={222} stroke={C.line} strokeWidth={1.5} />
      <Person x={525} y={330} s={0.85} />
      <Curve x1={545} y1={290} cx={610} cy={250} x2={540} y2={256} />
      <G x={525} y={358} size={22} weight={600} fill={C.accent}>λούεται</G>
      <E x={525} y={378} size={16} fill={C.ink}>washes himself</E>
    </Svg>
  );
}

// ------------------------------------------------------------- aspect (5.1)

function wave(x1: number, x2: number, y: number, amp = 12, step = 24) {
  let d = `M${x1} ${y}`;
  for (let x = x1; x < x2; x += step) d += ` q${step / 4} ${-amp} ${step / 2} 0 t${step / 2} 0`;
  return d;
}

export function Aspect() {
  return (
    <Svg w={640} h={400}>
      <E x={20} y={40} anchor="start" weight={600} fill={C.accent}>present stem: going on, repeated</E>
      <G x={20} y={104} size={28} anchor="start">λαμβάνειν</G>
      <path d={wave(220, 604, 94)} fill="none" stroke={C.accent} strokeWidth={2.5} strokeLinecap="round" />
      <E x={20} y={140} anchor="start">to be taking, to take (again and again)</E>

      <line x1={20} y1={172} x2={620} y2={172} stroke={C.line} strokeWidth={1.5} />

      <E x={20} y={210} anchor="start" weight={600} fill={C.accent}>aorist stem: one complete act</E>
      <G x={20} y={274} size={28} anchor="start">λαβεῖν</G>
      <line x1={220} y1={264} x2={604} y2={264} stroke={C.line} strokeWidth={1.5} strokeDasharray="4 6" />
      <circle cx={412} cy={264} r={11} fill={C.accent} />
      <E x={20} y={310} anchor="start">to take (grab), once</E>

      <line x1={20} y1={336} x2={620} y2={336} stroke={C.line} strokeWidth={1.5} />
      <E x={320} y={370} fill={C.ink}>
        participles too: <Gk>λαμβάνων</Gk> taking · <Gk>λαβών</Gk> having taken
      </E>
      <E x={320} y={394}>aspect is about how, not when</E>
    </Svg>
  );
}

// ------------------------------------------------------------ augment (5.2)

export function Augment() {
  const rows: { title: string; items: { from: string; parts: { t: string; kind?: "pre" | "aug" | "stem" }[]; note?: string }[] }[] = [
    {
      title: "before a consonant: ἐ- is added",
      items: [
        { from: "λύω", parts: [{ t: "ἔ", kind: "aug" }, { t: "λυσα" }] },
        { from: "λαμβάνω", parts: [{ t: "ἔ", kind: "aug" }, { t: "λαβον" }] },
      ],
    },
    {
      title: "before a vowel: the vowel lengthens",
      items: [
        { from: "ἀκούω", parts: [{ t: "ἤ", kind: "aug" }, { t: "κουσα" }], note: "α → η" },
        { from: "ὁρμάω", parts: [{ t: "ὥ", kind: "aug" }, { t: "ρμησα" }], note: "ο → ω" },
      ],
    },
    {
      title: "compound verb: after the prefix",
      items: [
        { from: "εἰσ-έρχομαι", parts: [{ t: "εἰσ", kind: "pre" }, { t: "ῆ", kind: "aug" }, { t: "λθον" }] },
        { from: "ἀπο-πέμπω", parts: [{ t: "ἀπ", kind: "pre" }, { t: "έ", kind: "aug" }, { t: "πεμψα" }] },
      ],
    },
  ];
  return (
    <Svg w={640} h={400}>
      {rows.map((r, i) => {
        const y = 12 + i * 130;
        return (
          <g key={r.title}>
            <E x={20} y={y + 22} anchor="start" weight={600} fill={C.accent}>{r.title}</E>
            {r.items.map((it, j) => {
              const x = 20 + j * 310;
              return (
                <g key={it.from}>
                  <G x={x + 8} y={y + 70} size={21} anchor="start" fill={C.muted}>{it.from}</G>
                  <Segs x={x + 8} y={y + 80} parts={it.parts} size={22} h={40} />
                  {it.note && <E x={x + 290} y={y + 106} anchor="end">{it.note}</E>}
                </g>
              );
            })}
          </g>
        );
      })}
    </Svg>
  );
}

// ---------------------------------------------------- narrative tenses (5.3)

export function Timeline() {
  const y = 190;
  const dots = [
    { x: 100, grc: "ἦλθε", en: "came", up: true },
    { x: 404, grc: "ἤκουσεν", en: "heard", up: true },
    { x: 470, grc: "ἐγένετο", en: "became (a tree)", up: false },
    { x: 580, grc: "ἔκλαυσεν", en: "wept", up: true },
  ];
  return (
    <Svg w={640} h={400}>
      <Arrow x1={20} y1={y} x2={624} y2={y} color={C.strong} sw={1.5} size={10} />
      <Box x={140} y={y - 26} w={330} h={52} r={26} fill={C.wash} stroke={C.sage} />
      <G x={255} y={y + 8} size={22}>ἔφευγεν · ἐδίωκεν</G>
      <E x={305} y={y + 62} fill={C.ink} weight={600}>imperfect: the background</E>
      <E x={305} y={y + 84}>she was fleeing, he was chasing</E>
      {dots.map((d) => (
        <g key={d.grc}>
          <circle cx={d.x} cy={y} r={10} fill={C.accent} stroke={C.card} strokeWidth={2} />
          {d.up ? (
            <>
              <line x1={d.x} y1={y - 14} x2={d.x} y2={y - 58} stroke={C.accent} strokeWidth={1.5} />
              <G x={d.x} y={y - 92} size={22} weight={600} fill={C.accent}>{d.grc}</G>
              <E x={d.x} y={y - 68} fill={C.ink}>{d.en}</E>
            </>
          ) : (
            <>
              <line x1={d.x} y1={y + 14} x2={d.x} y2={y + 108} stroke={C.accent} strokeWidth={1.5} />
              <G x={d.x} y={y + 134} size={22} weight={600} fill={C.accent}>{d.grc}</G>
              <E x={d.x} y={y + 156} fill={C.ink}>{d.en}</E>
            </>
          )}
        </g>
      ))}
      <E x={20} y={40} anchor="start" weight={600} fill={C.accent}>aorist: the events</E>
      <line x1={20} y1={y + 176} x2={620} y2={y + 176} stroke={C.line} strokeWidth={1.5} />
      <E x={320} y={y + 202} fill={C.ink}>
        <Gk>ἔφευγε</Gk> was fleeing · <Gk>ἔφυγε</Gk> fled, got away
      </E>
    </Svg>
  );
}

// --------------------------------------------------------- root aorist (6.3)

function Stick({ x, y, pose }: { x: number; y: number; pose: "walk" | "think" | "stand" }) {
  const st = { stroke: C.accent, strokeWidth: 3, strokeLinecap: "round" as const, fill: "none" };
  return (
    <g transform={`translate(${x} ${y})`}>
      <circle cx={0} cy={-104} r={13} fill={C.sage} stroke={C.accent} strokeWidth={2} />
      <line x1={0} y1={-90} x2={0} y2={-44} {...st} />
      {pose === "walk" && (
        <>
          <path d="M0 -44 L-20 0 M0 -44 L22 -4 L32 -2" {...st} />
          <path d="M0 -80 L-18 -58 M0 -80 L20 -64" {...st} />
          <Arrow x1={30} y1={-64} x2={70} y2={-64} sw={2} size={10} />
        </>
      )}
      {pose === "think" && (
        <>
          <path d="M0 -44 L-10 0 M0 -44 L10 0" {...st} />
          <path d="M0 -80 L-20 -58 M0 -80 L14 -96 L10 -110" {...st} />
          <circle cx={0} cy={-150} r={14} fill={C.hl} stroke={C.accent} strokeWidth={2} />
          <rect x={-6} y={-138} width={12} height={9} rx={2} fill={C.cream} stroke={C.accent} strokeWidth={1.5} />
          <path d="M-24 -166 l-8 -6 M24 -166 l8 -6 M0 -172 v-10 M-26 -148 h-10 M26 -148 h10" stroke={C.accent} strokeWidth={2} strokeLinecap="round" />
        </>
      )}
      {pose === "stand" && (
        <>
          <path d="M0 -44 L-5 0 M0 -44 L5 0" {...st} />
          <path d="M0 -80 L-8 -46 M0 -80 L8 -46" {...st} />
          <line x1={-30} y1={4} x2={30} y2={4} stroke={C.strong} strokeWidth={2} strokeLinecap="round" />
        </>
      )}
    </g>
  );
}

export function RootAorist() {
  const figs = [
    { x: 110, pose: "walk" as const, grc: "ἔβην", en: "I went", from: "βαίνω" },
    { x: 320, pose: "think" as const, grc: "ἔγνων", en: "I got to know", from: "γιγνώσκω" },
    { x: 530, pose: "stand" as const, grc: "ἔστην", en: "I stood", from: "ἵστημι" },
  ];
  const ends = ["ν", "ς", "", "μεν", "τε", "σαν"];
  const who = ["I", "you", "he, she", "we", "you (pl.)", "they"];
  return (
    <Svg w={640} h={400}>
      {figs.map((f) => (
        <g key={f.grc}>
          <Stick x={f.x} y={196} pose={f.pose} />
          <G x={f.x} y={234} size={27} weight={600} fill={C.accent}>{f.grc}</G>
          <E x={f.x} y={258} fill={C.ink}>{f.en} <Gk fill={C.muted}>({f.from})</Gk></E>
        </g>
      ))}
      <line x1={20} y1={280} x2={620} y2={280} stroke={C.line} strokeWidth={1.5} />
      {ends.map((e, i) => {
        const x = 20 + i * 101;
        return (
          <g key={i}>
            <Box x={x} y={296} w={95} h={46} r={8} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            <G x={x + 47.5} y={327} size={22}>ἔβη<H>{e}</H></G>
            <E x={x + 47.5} y={366}>{who[i]}</E>
          </g>
        );
      })}
      <E x={320} y={392}>endings straight onto the long stem: -ν -ς – -μεν -τε -σαν</E>
    </Svg>
  );
}

// ------------------------------------------------------------ future (Unit 7+)

export function Future() {
  return (
    <Svg w={640} h={400}>
      <Segs
        x={170}
        y={22}
        anchor="middle"
        size={28}
        h={52}
        parts={[{ t: "λύ" }, { t: "σ", kind: "aug" }, { t: "ω", kind: "end" }]}
      />
      <G x={300} y={58} size={28} anchor="start">= λύσω</G>
      <E x={460} y={42} anchor="start" fill={C.ink}>stem + <Gk>σ</Gk> +</E>
      <E x={460} y={64} anchor="start" fill={C.ink}>present endings</E>
      <G x={320} y={112} size={20} fill={C.muted}>λύσω, λύσεις, λύσει, λύσομεν, λύσετε, λύσουσι(ν)</G>

      {[
        { rule: "π β φ + σ → ψ", ex: "πέμπω → πέμψω" },
        { rule: "κ γ χ + σ → ξ", ex: "ἄγω → ἄξω" },
        { rule: "τ δ θ + σ → σ", ex: "πείθω → πείσω" },
      ].map((r, i) => {
        const x = 20 + i * 204;
        return (
          <g key={r.rule}>
            <Box x={x} y={134} w={192} h={84} />
            <G x={x + 96} y={166} size={20} fill={C.accent} weight={600}>{r.rule}</G>
            <G x={x + 96} y={200} size={20}>{r.ex}</G>
          </g>
        );
      })}

      <Box x={20} y={234} w={295} h={150} fill={C.wash} stroke={C.sage} />
      <E x={167} y={262} weight={600} fill={C.accent}>liquid and contract futures</E>
      <E x={167} y={284}>no <Gk>σ</Gk>; contracted like <Gk>ποιῶ</Gk></E>
      <G x={167} y={322} size={22}>μένω → μεν<H>ῶ</H>, μεν<H>εῖ</H>ς</G>
      <G x={167} y={358} size={22}>καλέω → καλ<H>ῶ</H>, καλ<H>εῖ</H>ς</G>

      <Box x={325} y={234} w={295} h={150} fill={C.wash} stroke={C.sage} />
      <E x={472} y={262} weight={600} fill={C.accent}><Gk fill={C.accent}>εἰμί</Gk>: middle endings</E>
      <E x={472} y={284}>I shall be</E>
      <G x={472} y={322} size={21}>ἔσ<H>ομαι</H>, ἔσ<H>ῃ</H>, ἔσ<H>ται</H></G>
      <G x={472} y={358} size={19}>ἐσ<H>όμεθα</H>, ἔσ<H>εσθε</H>, ἔσ<H>ονται</H></G>
    </Svg>
  );
}

// ---------------------------------------------------------- -μι verbs (Unit 7+)

export function MiVerbs() {
  const rows = [
    { red: "δι-", sg: ["δί", "δω", "μι"], pl: ["δί", "δο", "μεν"], en: "give" },
    { red: "τι-", sg: ["τί", "θη", "μι"], pl: ["τί", "θε", "μεν"], en: "put" },
    { red: "ἱ-", sg: ["ἵ", "στη", "μι"], pl: ["ἵ", "στα", "μεν"], en: "set up" },
  ];
  const cols = [
    { x: 90, t: "doubling" },
    { x: 280, t: "singular: long vowel" },
    { x: 500, t: "plural: short vowel" },
  ];
  return (
    <Svg w={640} h={400}>
      {cols.map((c) => (
        <E key={c.t} x={c.x} y={34} weight={600} fill={C.accent}>{c.t}</E>
      ))}
      {rows.map((r, i) => {
        const y = 52 + i * 94;
        return (
          <g key={r.en}>
            <Box x={20} y={y} w={600} h={84} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            <G x={90} y={y + 44} size={28} fill={C.muted}>{r.red}</G>
            <E x={90} y={y + 70}>{r.en}</E>
            <G x={280} y={y + 52} size={30}>
              {r.sg[0]}-<H>{r.sg[1]}</H>-{r.sg[2]}
            </G>
            <G x={500} y={y + 52} size={30}>
              {r.pl[0]}-<H fill={C.ink}>{r.pl[1]}</H>-{r.pl[2]}
            </G>
          </g>
        );
      })}
      <E x={320} y={344} fill={C.ink}>
        <Gk>δίδωμι · δίδομεν</Gk>, <Gk>τίθημι · τίθεμεν</Gk>, <Gk>ἵστημι · ἵσταμεν</Gk>
      </E>
      <E x={320} y={374}>
        endings straight onto the stem: <Gk>-μι -ς -σι · -μεν -τε -ασι</Gk>
      </E>
    </Svg>
  );
}

// ------------------------------------------------------------ ἵστημι (6.3+)

export function Histemi() {
  return (
    <Svg w={640} h={400}>
      <Box x={20} y={16} w={290} h={368} fill={C.cream} stroke={C.line} />
      <Box x={330} y={16} w={290} h={368} fill={C.wash} stroke={C.sage} />
      <E x={165} y={46} weight={600} fill={C.accent}>transitive: sets something up</E>
      <E x={475} y={46} weight={600} fill={C.accent}>intransitive: stands</E>

      {/* hand placing a statue */}
      <rect x={140} y={214} width={80} height={36} rx={4} fill={C.card} stroke={C.strong} strokeWidth={1.5} />
      <Person x={180} y={214} s={0.95} fill={C.card} stroke={C.strong} />
      <Person x={76} y={250} s={1.05} />
      <path d="M88 214 L128 198 L162 196" fill="none" stroke={C.accent} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
      <Arrow x1={180} y1={92} x2={180} y2={132} />
      <line x1={40} y1={252} x2={290} y2={252} stroke={C.strong} strokeWidth={1.5} />
      <G x={165} y={292} size={26} weight={600} fill={C.accent}>ἔστησα</G>
      <G x={165} y={322} size={21}>τὸ ἄγαλμα</G>
      <E x={165} y={350} fill={C.ink}>I set up the statue</E>
      <G x={165} y={374} size={18} fill={C.muted}>ἵστημι</G>

      {/* standing figure */}
      <Person x={475} y={214} s={1.2} />
      <line x1={430} y1={216} x2={520} y2={216} stroke={C.strong} strokeWidth={2} strokeLinecap="round" />
      <G x={420} y={292} size={26} weight={600} fill={C.accent}>ἔστην</G>
      <E x={420} y={316} fill={C.ink}>I stood</E>
      <G x={540} y={292} size={26} weight={600} fill={C.accent}>ἕστηκα</G>
      <E x={540} y={316} fill={C.ink}>I stand</E>
      <E x={475} y={350}>took my stand · am standing</E>
      <G x={475} y={374} size={18} fill={C.muted}>ἵσταμαι</G>
    </Svg>
  );
}

// ------------------------------------------------------------- perfect (Unit 8+)

function Door({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <rect x={x - 16} y={y - 44} width={32} height={44} rx={3} fill={C.cream} stroke={C.accent} strokeWidth={1.5} />
      <line x1={x} y1={y - 44} x2={x} y2={y} stroke={C.accent} strokeWidth={1.5} />
      <circle cx={x - 5} cy={y - 20} r={2} fill={C.accent} />
      <circle cx={x + 5} cy={y - 20} r={2} fill={C.accent} />
    </g>
  );
}

export function Perfect() {
  const now = 470;
  const rows = [
    { y: 92, label: "present", grc: "κλείει", en: "is shutting" },
    { y: 202, label: "aorist", grc: "ἔκλεισε", en: "shut" },
    { y: 312, label: "perfect", grc: "κέκλεικε", en: "has shut: it is still shut" },
  ];
  return (
    <Svg w={640} h={400}>
      <line x1={now} y1={30} x2={now} y2={350} stroke={C.strong} strokeWidth={1.5} strokeDasharray="5 5" />
      <G x={now} y={24} size={20} fill={C.muted}>νῦν</G>
      {rows.map((r, i) => (
        <g key={r.label}>
          <line x1={250} y1={r.y} x2={620} y2={r.y} stroke={C.line} strokeWidth={1.5} />
          <E x={20} y={r.y - 12} anchor="start" weight={600} fill={C.accent}>{r.label}</E>
          <G x={20} y={r.y + 20} size={25} anchor="start">{r.grc}</G>
          <E x={20} y={r.y + 44} anchor="start" fill={C.ink}>{r.en}</E>
          {i === 0 && <path d={wave(410, 530, r.y, 10, 20)} fill="none" stroke={C.accent} strokeWidth={2.5} strokeLinecap="round" />}
          {i === 1 && <circle cx={330} cy={r.y} r={10} fill={C.accent} />}
          {i === 2 && (
            <>
              <rect x={330} y={r.y - 8} width={now - 330} height={16} rx={8} fill={C.hl} stroke={C.sage} strokeWidth={1.5} />
              <circle cx={330} cy={r.y} r={10} fill={C.accent} />
              <Door x={now + 50} y={r.y + 20} />
            </>
          )}
        </g>
      ))}
      <E x={320} y={384}>the perfect: a finished act whose result still holds</E>
    </Svg>
  );
}

// --------------------------------------------------------------- voice (Unit 8+)

function Dog({ x, y, s = 1 }: { x: number; y: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} stroke={C.accent} strokeWidth={1.5 / s} strokeLinejoin="round" strokeLinecap="round">
      <path d="M-30 -10 L-32 0 M-18 -10 L-18 0 M14 -10 L14 0 M26 -10 L28 0" fill="none" />
      <path d="M-34 -30 Q-44 -44 -40 -50" fill="none" />
      <ellipse cx={-2} cy={-22} rx={34} ry={14} fill={C.cream} />
      <circle cx={36} cy={-40} r={13} fill={C.cream} />
      <ellipse cx={50} cy={-36} rx={9} ry={6} fill={C.cream} />
      <path d="M28 -50 Q18 -44 24 -30 Q32 -38 34 -50 Z" fill={C.sage} />
      <circle cx={40} cy={-42} r={1.8} fill={C.ink} stroke="none" />
    </g>
  );
}

export function Voice() {
  const rows: { label: string; pic: ReactNode; grc: ReactNode; en: string }[] = [
    {
      label: "active",
      pic: (
        <>
          <Person x={60} y={110} s={0.9} />
          <Arrow x1={88} y1={80} x2={146} y2={80} />
          <Dog x={196} y={110} />
        </>
      ),
      grc: <>ὁ Λύσις τὸν κύνα λού<H>ει</H></>,
      en: "Lysis washes the dog.",
    },
    {
      label: "middle",
      pic: (
        <>
          <Person x={110} y={236} s={0.9} />
          <Curve x1={130} y1={196} cx={200} cy={160} x2={126} y2={168} />
        </>
      ),
      grc: <>ὁ Λύσις λού<H>εται</H></>,
      en: "Lysis washes (himself).",
    },
    {
      label: "passive",
      pic: (
        <>
          <Person x={60} y={362} s={0.9} fill={C.card} stroke={C.strong} />
          <Arrow x1={88} y1={332} x2={146} y2={332} dash="5 5" color={C.strong} />
          <Dog x={196} y={362} />
        </>
      ),
      grc: <>ὁ κύων λού<H>εται</H> ὑπὸ τοῦ Λύσιδος</>,
      en: "The dog is washed by Lysis.",
    },
  ];
  return (
    <Svg w={640} h={400}>
      {rows.map((r, i) => {
        const y = 12 + i * 126;
        return (
          <g key={r.label}>
            <Box x={20} y={y} w={600} h={116} fill={i === 1 ? C.wash : C.card} stroke={i === 1 ? C.sage : C.line} />
            {r.pic}
            <E x={262} y={y + 34} anchor="start" weight={600} fill={C.accent}>{r.label}</E>
            <G x={262} y={y + 70} size={20} anchor="start">{r.grc}</G>
            <E x={262} y={y + 98} anchor="start" fill={C.ink}>{r.en}</E>
          </g>
        );
      })}
    </Svg>
  );
}

// ---------------------------------------------------- participle map (Unit 7+)

export function ParticipleMap() {
  const col = [110, 290, 470];
  const head = ["active", "middle", "passive"];
  type Cell = { x: number; w: number; form: ReactNode; ends: string };
  const rows: { label: string; cells: Cell[] }[] = [
    {
      label: "present",
      cells: [
        { x: 0, w: 1, form: <>λύ<H>ων</H></>, ends: "-ων -ουσα -ον" },
        { x: 1, w: 2, form: <>λυό<H>μενος</H></>, ends: "-μενος -μένη -μενον" },
      ],
    },
    {
      label: "aorist",
      cells: [
        { x: 0, w: 1, form: <>λύσ<H>ας</H></>, ends: "-ας -ασα -αν" },
        { x: 1, w: 1, form: <>λυσά<H>μενος</H></>, ends: "-μενος -η -ον" },
        { x: 2, w: 1, form: <>λυθ<H>είς</H></>, ends: "-είς -εῖσα -έν" },
      ],
    },
    {
      label: "perfect",
      cells: [
        { x: 0, w: 1, form: <>λελυκ<H>ώς</H></>, ends: "-ώς -υῖα -ός" },
        { x: 1, w: 2, form: <>λελυ<H>μένος</H></>, ends: "-μένος -μένη -μένον" },
      ],
    },
  ];
  return (
    <Svg w={640} h={400}>
      {head.map((h, i) => (
        <E key={h} x={col[i] + 85} y={30} weight={600} fill={C.accent}>{h}</E>
      ))}
      {rows.map((r, i) => {
        const y = 44 + i * 112;
        return (
          <g key={r.label}>
            <E x={20} y={y + 56} anchor="start" fill={C.ink} weight={600}>{r.label}</E>
            {r.cells.map((c) => {
              const x = col[c.x];
              const w = c.w === 2 ? 350 : 170;
              return (
                <g key={c.x}>
                  <Box x={x} y={y} w={w} h={100} fill={c.w === 2 ? C.wash : C.card} stroke={c.w === 2 ? C.sage : C.strong} />
                  <G x={x + w / 2} y={y + 44} size={25}>{c.form}</G>
                  <G x={x + w / 2} y={y + 78} size={17} fill={C.muted}>{c.ends}</G>
                </g>
              );
            })}
          </g>
        );
      })}
      <E x={320} y={390}>
        middle and passive share a form except in the aorist
      </E>
    </Svg>
  );
}

// ------------------------------------------------------ participle use (4.1)

export function Participle() {
  return (
    <Svg w={640} h={400}>
      <Box x={20} y={16} w={290} h={368} fill={C.card} stroke={C.line} />
      <Box x={330} y={16} w={290} h={368} fill={C.card} stroke={C.line} />
      <E x={165} y={46} weight={600} fill={C.accent}>with the article: which one?</E>
      <E x={475} y={46} weight={600} fill={C.accent}>without: while …-ing</E>

      {/* three men, the walking one picked out */}
      <line x1={40} y1={196} x2={290} y2={196} stroke={C.strong} strokeWidth={1.5} />
      <Person x={75} y={196} s={0.95} fill={C.cream} stroke={C.strong} />
      <Person x={130} y={196} s={0.95} fill={C.cream} stroke={C.strong} />
      <Person x={220} y={196} s={0.95} />
      <Arrow x1={242} y1={150} x2={282} y2={150} sw={2} size={10} />
      <circle cx={220} cy={134} r={62} fill="none" stroke={C.accent} strokeWidth={1.5} strokeDasharray="5 5" />
      <G x={165} y={250} size={23}>ὁ ἀνὴρ <H>ὁ βαίνων</H></G>
      <E x={165} y={278} fill={C.ink}>the man who is walking</E>
      <E x={165} y={320}>attributive: picks out</E>
      <E x={165} y={342}>which person</E>

      {/* ongoing walk with a seeing inside it */}
      <path d={wave(350, 596, 150, 10, 22)} fill="none" stroke={C.accent} strokeWidth={2.5} strokeLinecap="round" />
      <circle cx={500} cy={150} r={10} fill={C.accent} stroke={C.card} strokeWidth={2} />
      <G x={390} y={118} size={20} fill={C.accent}>βαίνων</G>
      <G x={500} y={196} size={20} fill={C.accent} weight={600}>ὁρᾷ</G>
      <G x={475} y={250} size={23}><H>βαίνων</H> ὁρᾷ</G>
      <E x={475} y={278} fill={C.ink}>while walking, he sees</E>
      <E x={475} y={320}>circumstantial: the setting</E>
      <E x={475} y={342}>of the main verb</E>
    </Svg>
  );
}
