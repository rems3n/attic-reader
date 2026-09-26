/** Sentences: μέν … δέ, the genitive absolute, supplementary participles, moods,
 * purpose and fear, reported speech, sequence, conditions, result, negatives,
 * crasis and elision, a reading strategy. */

import type { ReactNode } from "react";
import { Arrow, Box, C, Curve, E, G, Gk, H, Person, Svg, layout } from "./kit";

// ------------------------------------------------------------- μέν … δέ (2.1)

export function MenDe() {
  const pans = [
    { x: 150, head: <>σὺ <H>μέν</H></>, clause: "τὴν ὑδρίαν φέρεις", en: "you carry the jar" },
    { x: 490, head: <>ἐγὼ <H>δέ</H></>, clause: "ὑφαίνω", en: "I weave" },
  ];
  return (
    <Svg w={640} h={400}>
      {/* stand */}
      <path d="M270 262 H370" stroke={C.strong} strokeWidth={2} strokeLinecap="round" />
      <line x1={320} y1={70} x2={320} y2={262} stroke={C.strong} strokeWidth={2} />
      <path d="M308 62 L320 44 L332 62 Z" fill={C.sage} stroke={C.accent} strokeWidth={1.5} strokeLinejoin="round" />
      <line x1={140} y1={64} x2={500} y2={64} stroke={C.accent} strokeWidth={3} strokeLinecap="round" />
      {pans.map((p) => (
        <g key={p.x}>
          <path d={`M${p.x - 10} 64 L${p.x - 100} 180 M${p.x + 10} 64 L${p.x + 100} 180`} stroke={C.strong} strokeWidth={1.5} />
          <path d={`M${p.x - 110} 180 Q${p.x} 222 ${p.x + 110} 180 Z`} fill={C.wash} stroke={C.accent} strokeWidth={1.5} strokeLinejoin="round" />
          <G x={p.x} y={162} size={27}>{p.head}</G>
          <G x={p.x} y={244} size={21}>{p.clause}</G>
          <E x={p.x} y={268}>{p.en}</E>
        </g>
      ))}
      <line x1={20} y1={292} x2={620} y2={292} stroke={C.line} strokeWidth={1.5} />
      <G x={320} y={326} size={22}>
        σὺ <H>μὲν</H> τὴν ὑδρίαν φέρεις, ἐγὼ <H>δὲ</H> ὑφαίνω.
      </G>
      <E x={320} y={352} fill={C.ink} italic>You carry the water jar, while I weave.</E>
      <E x={320} y={384}>
        also <Gk>πρῶτον μέν … ἔπειτα δέ</Gk> first … then
      </E>
    </Svg>
  );
}

// ------------------------------------------------------ genitive absolute

export function GenAbs() {
  const l1 = layout(["τῶν", "πολεμίων", "ἐλθόντων,"], 44, 26, 12, true);
  return (
    <Svg w={640} h={400}>
      <Box x={20} y={30} w={l1[2].x + l1[2].w + 4} h={62} fill={C.hl} stroke={C.accent} dash="6 5" />
      {l1.map((w) => (
        <G key={w.t} x={w.x} y={70} size={26} anchor="start" fill={w.t === "τῶν" ? C.ink : C.accent} weight={w.t === "τῶν" ? undefined : 600}>
          {w.t}
        </G>
      ))}
      <E x={l1[1].c} y={116} fill={C.ink}>noun</E>
      <E x={l1[2].c} y={116} fill={C.ink}>participle</E>
      <E x={(l1[1].c + l1[2].c) / 2} y={138}>both genitive</E>
      <E x={620} y={56} anchor="end" weight={600} fill={C.accent}>genitive absolute</E>
      <E x={620} y={78} anchor="end">set apart from</E>
      <E x={620} y={98} anchor="end">the main clause</E>

      <Box x={20} y={160} w={600} h={62} />
      <G x={44} y={200} size={26} anchor="start">οἱ γεωργοὶ εἰς τὴν πόλιν ἔφυγον.</G>
      <E x={604} y={244} anchor="end">main clause</E>

      <E x={20} y={290} anchor="start" fill={C.ink} weight={600}>The participle can mean:</E>
      {["when", "since", "although"].map((t, i) => (
        <g key={t}>
          <Box x={250 + i * 124} y={268} w={112} h={36} r={18} fill={C.wash} stroke={C.sage} />
          <E x={306 + i * 124} y={292} fill={C.accent} weight={600}>{t}</E>
        </g>
      ))}
      <E x={320} y={362} fill={C.ink} italic>When the enemy came, the farmers fled into the city.</E>
    </Svg>
  );
}

// ------------------------------------------------ supplementary participles

function Icon({ kind, x, y }: { kind: "unseen" | "chance" | "first" | "plain"; x: number; y: number }) {
  const st = { stroke: C.accent, strokeWidth: 2, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <g transform={`translate(${x} ${y})`}>
      <circle cx={0} cy={0} r={30} fill={C.wash} stroke={C.sage} strokeWidth={1.5} />
      {kind === "unseen" && (
        <>
          <path d="M-18 0 Q0 -16 18 0 Q0 16 -18 0 Z" {...st} />
          <circle cx={0} cy={0} r={5} fill={C.accent} />
          <line x1={-16} y1={14} x2={16} y2={-14} {...st} />
        </>
      )}
      {kind === "chance" && (
        <>
          <rect x={-15} y={-15} width={30} height={30} rx={5} fill={C.card} stroke={C.accent} strokeWidth={2} />
          {[[-7, -7], [7, 7], [0, 0], [7, -7], [-7, 7]].map(([a, b], i) => (
            <circle key={i} cx={a} cy={b} r={2.6} fill={C.accent} />
          ))}
        </>
      )}
      {kind === "first" && (
        <>
          <line x1={14} y1={-18} x2={14} y2={18} stroke={C.ink} strokeWidth={2} />
          <Arrow x1={-20} y1={-7} x2={12} y2={-7} sw={2} size={8} />
          <Arrow x1={-20} y1={8} x2={0} y2={8} sw={2} size={8} color={C.strong} />
        </>
      )}
      {kind === "plain" && (
        <>
          <circle cx={0} cy={0} r={9} fill={C.hl} stroke={C.accent} strokeWidth={2} />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => {
            const r = (a * Math.PI) / 180;
            return <line key={a} x1={Math.cos(r) * 14} y1={Math.sin(r) * 14} x2={Math.cos(r) * 21} y2={Math.sin(r) * 21} {...st} />;
          })}
        </>
      )}
    </g>
  );
}

export function Supplementary() {
  const cells = [
    { kind: "unseen" as const, verb: "λανθάνω", gloss: "escape notice", ex: "ἔλαθεν εἰσελθών.", en: "He came in unseen." },
    { kind: "chance" as const, verb: "τυγχάνω", gloss: "happen to", ex: "ἔτυχε παρών.", en: "He happened to be there." },
    { kind: "first" as const, verb: "φθάνω", gloss: "get there first", ex: "ἔφθη ἀφικόμενος.", en: "He arrived first." },
    { kind: "plain" as const, verb: "φαίνομαι", gloss: "be plainly", ex: "φαίνεται φεύγων.", en: "He is plainly running away." },
  ];
  return (
    <Svg w={640} h={400}>
      {cells.map((c, i) => {
        const x = 20 + (i % 2) * 306;
        const y = 12 + Math.floor(i / 2) * 192;
        return (
          <g key={c.verb}>
            <Box x={x} y={y} w={294} h={180} />
            <Icon kind={c.kind} x={x + 48} y={y + 52} />
            <G x={x + 94} y={y + 50} size={25} anchor="start" weight={600} fill={C.accent}>{c.verb}</G>
            <E x={x + 94} y={y + 74} anchor="start" fill={C.ink}>{c.gloss}</E>
            <G x={x + 20} y={y + 126} size={22} anchor="start">{c.ex}</G>
            <E x={x + 20} y={y + 156} anchor="start">{c.en}</E>
          </g>
        );
      })}
    </Svg>
  );
}

// ------------------------------------------------------------------ moods

export function Moods() {
  const signs = [
    { name: "indicative", right: true, a: ["λύει", "he frees"], b: ["ἐστίν", "it is"] },
    { name: "subjunctive", right: false, a: ["λύωμεν", "let us free"], b: ["ἵνα λύῃ", "so that he may free"] },
    { name: "optative", right: true, a: ["εἴη", "may it be"], b: ["λύοι ἄν", "he would free"] },
    { name: "imperative", right: false, a: ["λῦε", "free!"], b: ["ἐλθέ", "come!"] },
  ];
  return (
    <Svg w={640} h={400}>
      <line x1={20} y1={214} x2={620} y2={214} stroke={C.strong} strokeWidth={1.5} />
      {signs.map((s, i) => {
        const cx = 88 + i * 155;
        const x0 = cx - 70;
        const board = s.right
          ? `M${x0} 70 H${x0 + 124} L${x0 + 142} 94 L${x0 + 124} 118 H${x0} Z`
          : `M${x0 + 16} 70 H${x0 + 140} V118 H${x0 + 16} L${x0 - 2} 94 Z`;
        return (
          <g key={s.name}>
            <line x1={cx} y1={60} x2={cx} y2={214} stroke={C.strong} strokeWidth={3} strokeLinecap="round" />
            <path d={board} fill={C.wash} stroke={C.sage} strokeWidth={1.5} strokeLinejoin="round" />
            <E x={cx + (s.right ? -2 : 6)} y={100} fill={C.accent} weight={600}>{s.name}</E>
            <G x={cx} y={256} size={25}>{s.a[0]}</G>
            <E x={cx} y={280} fill={C.ink}>{s.a[1]}</E>
            <G x={cx} y={324} size={21}>{s.b[0]}</G>
            <E x={cx} y={348}>{s.b[1]}</E>
          </g>
        );
      })}
      <E x={88} y={382} size={16}>fact</E>
      <E x={243} y={382} size={16}>will, purpose</E>
      <E x={398} y={382} size={16}>wish, possibility</E>
      <E x={553} y={382} size={16}>command</E>
    </Svg>
  );
}

// -------------------------------------------------------- purpose and fear

export function PurposeFear() {
  return (
    <Svg w={640} h={400}>
      <Box x={20} y={12} w={600} h={180} fill={C.card} stroke={C.line} />
      <Person x={70} y={150} s={0.95} />
      <Arrow x1={98} y1={104} x2={196} y2={104} sw={2.5} />
      {[30, 20, 10].map((r, i) => (
        <circle key={r} cx={214} cy={104} r={r} fill={i === 2 ? C.accent : i === 1 ? C.hl : C.card} stroke={C.accent} strokeWidth={1.5} />
      ))}
      <E x={270} y={46} anchor="start" weight={600} fill={C.accent}>purpose: <Gk fill={C.accent}>ἵνα, ὅπως</Gk> + subjunctive</E>
      <G x={270} y={98} size={22} anchor="start">τρέχει <H>ἵνα</H> τὸν κύνα <H>λάβῃ</H>.</G>
      <E x={270} y={126} anchor="start" fill={C.ink}>He runs so that he may catch the dog.</E>
      <E x={270} y={170} anchor="start">negative: <Gk>ἵνα μή</Gk></E>

      <Box x={20} y={208} w={600} h={180} fill={C.card} stroke={C.line} />
      <Person x={70} y={346} s={0.95} />
      <path d="M98 330 H236" stroke={C.strong} strokeWidth={2} strokeDasharray="4 6" strokeLinecap="round" />
      <path d="M150 336 C150 300 176 282 204 292 C226 270 256 290 248 314 C266 322 256 342 236 340 H164 C150 340 146 338 150 336 Z" fill={C.strong} stroke={C.muted} strokeWidth={1.5} opacity={0.75} />
      <E x={270} y={242} anchor="start" weight={600} fill={C.accent}>fear: <Gk fill={C.accent}>φοβοῦμαι μή</Gk> + subjunctive</E>
      <G x={270} y={294} size={22} anchor="start">φοβοῦμαι <H>μὴ</H> ὁ κύων <H>φύγῃ</H>.</G>
      <E x={270} y={322} anchor="start" fill={C.ink}>I am afraid that the dog may run away.</E>
      <E x={270} y={366} anchor="start">fear that … not: <Gk>μὴ οὐ</Gk></E>
    </Svg>
  );
}

// ---------------------------------------------------------- reported speech

export function Indirect() {
  const rows: { key: string; label: ReactNode; sub: ReactNode; grc: ReactNode; en: string }[] = [
    { key: "hoti", label: <><Gk fill={C.accent}>ὅτι</Gk> + indicative</>, sub: <>after <Gk fill={C.muted}>λέγω</Gk>: saying</>, grc: <>λέγει <H>ὅτι</H> ὁ κύων <H>φεύγει</H>.</>, en: "He says that the dog is running away." },
    { key: "inf", label: "accusative + infinitive", sub: <>after <Gk fill={C.muted}>φημί, οἴομαι</Gk></>, grc: <>φησὶ <H>τὸν κύνα φεύγειν</H>.</>, en: "He says the dog is running away." },
    { key: "ptc", label: "participle", sub: <>after <Gk fill={C.muted}>ὁρῶ, ἀκούω, οἶδα</Gk></>, grc: <>ὁρᾷ <H>τὸν κύνα φεύγοντα</H>.</>, en: "He sees the dog running away." },
  ];
  return (
    <Svg w={640} h={400}>
      <path d="M200 14 H440 Q460 14 460 34 V66 Q460 86 440 86 H346 L322 104 L324 86 H200 Q180 86 180 66 V34 Q180 14 200 14 Z" fill={C.wash} stroke={C.sage} strokeWidth={1.5} strokeLinejoin="round" />
      <G x={320} y={50} size={24}>«ὁ κύων φεύγει.»</G>
      <E x={320} y={74} fill={C.ink}>The dog is running away.</E>
      {rows.map((r, i) => {
        const y = 122 + i * 92;
        return (
          <g key={r.key}>
            <Box x={20} y={y} w={600} h={82} />
            <E x={36} y={y + 30} anchor="start" weight={600} fill={C.accent}>{r.label}</E>
            <E x={36} y={y + 56} anchor="start">{r.sub}</E>
            <G x={290} y={y + 36} size={22} anchor="start">{r.grc}</G>
            <E x={290} y={y + 62} anchor="start" fill={C.ink} size={16}>{r.en}</E>
          </g>
        );
      })}
    </Svg>
  );
}

// ------------------------------------------------------ sequence of moods

export function Sequence() {
  const rows = [
    { label: "primary", sub: "present, future", verb: "ἔρχεται", en1: "he comes", dep: <>ἵνα <H>ἴδῃ</H></>, mood: "subjunctive", en2: "so that he may see" },
    { label: "secondary", sub: "past: imperfect, aorist", verb: "ἦλθεν", en1: "he came", dep: <>ἵνα <H>ἴδοι</H></>, mood: "optative", en2: "so that he might see" },
  ];
  return (
    <Svg w={640} h={400}>
      <E x={140} y={34} weight={600} fill={C.accent}>main verb</E>
      <E x={470} y={34} weight={600} fill={C.accent}>dependent clause</E>
      {rows.map((r, i) => {
        const y = 52 + i * 150;
        return (
          <g key={r.label}>
            <Box x={20} y={y} w={240} h={128} fill={C.card} />
            <E x={140} y={y + 28} fill={C.ink} weight={600}>{r.label}</E>
            <E x={140} y={y + 50}>{r.sub}</E>
            <G x={140} y={y + 90} size={26}>{r.verb}</G>
            <E x={140} y={y + 116} fill={C.ink}>{r.en1}</E>
            <Arrow x1={266} y1={y + 64} x2={334} y2={y + 64} sw={2.5} />
            <Box x={340} y={y} w={280} h={128} fill={C.wash} stroke={C.sage} />
            <E x={480} y={y + 28} fill={C.accent} weight={600}>+ {r.mood}</E>
            <G x={480} y={y + 90} size={26}>{r.dep}</G>
            <E x={480} y={y + 116} fill={C.ink}>{r.en2}</E>
          </g>
        );
      })}
      <E x={320} y={372}>after a past verb the subjunctive may also stay, for vividness</E>
    </Svg>
  );
}

// -------------------------------------------------------------- conditions

export function Conditions() {
  const g = (t: string) => <Gk fill={C.ink}>{t}</Gk>;
  const rungs: { name: string; p: ReactNode; a: ReactNode }[] = [
    { name: "past contrary to fact", p: <>{g("εἰ")} + aorist</>, a: <>{g("ἄν")} + aorist</> },
    { name: "present contrary to fact", p: <>{g("εἰ")} + imperfect</>, a: <>{g("ἄν")} + imperfect</> },
    { name: "future less vivid", p: <>{g("εἰ")} + optative</>, a: <>{g("ἄν")} + optative</> },
    { name: "future more vivid", p: <>{g("ἐάν")} + subjunctive</>, a: <>future indicative</> },
    { name: "general", p: <>{g("ἐάν")} + subj. / {g("εἰ")} + opt.</>, a: <>present / imperfect</> },
    { name: "simple", p: <>{g("εἰ")} + indicative</>, a: <>indicative</> },
  ];
  const top = 64;
  const step = 68;
  return (
    <Svg w={640} h={500}>
      <E x={352} y={30} weight={600} fill={C.accent}>if … (protasis)</E>
      <E x={530} y={30} weight={600} fill={C.accent}>then … (apodosis)</E>
      <line x1={26} y1={top - 16} x2={26} y2={top + step * 6 - 6} stroke={C.sage} strokeWidth={4} strokeLinecap="round" />
      <line x1={614} y1={top - 16} x2={614} y2={top + step * 6 - 6} stroke={C.sage} strokeWidth={4} strokeLinecap="round" />
      {rungs.map((r, i) => {
        const y = top + i * step;
        return (
          <g key={r.name}>
            <line x1={26} y1={y + step - 6} x2={614} y2={y + step - 6} stroke={C.sage} strokeWidth={4} strokeLinecap="round" />
            <E x={44} y={y + 34} anchor="start" fill={C.ink} weight={600}>{r.name}</E>
            <E x={352} y={y + 34} fill={C.muted}>{r.p}</E>
            <E x={530} y={y + 34} fill={C.muted}>{r.a}</E>
          </g>
        );
      })}
      <Arrow x1={10} y1={top + step * 6} x2={10} y2={top} color={C.strong} sw={1.5} size={9} />
      <E x={320} y={490}>
        higher rungs: further from fact · <Gk>ἐάν</Gk> = <Gk>εἰ + ἄν</Gk> (also <Gk>ἤν, ἄν</Gk>)
      </E>
    </Svg>
  );
}

// -------------------------------------------------------------------- result

export function Result() {
  const rows = [
    {
      title: <>natural result: <Gk fill={C.accent}>ὥστε</Gk> + infinitive</>,
      cause: "οὕτω σοφός ἐστιν",
      res: <><H>ὥστε</H> πάντα <H>γιγνώσκειν</H></>,
      en: "He is so wise as to know everything.",
      neg: "μή",
      dash: "7 6",
    },
    {
      title: <>actual result: <Gk fill={C.accent}>ὥστε</Gk> + indicative</>,
      cause: "οὕτω ταχέως ἔδραμεν",
      res: <><H>ὥστε</H> πρῶτος <H>ἀφίκετο</H></>,
      en: "He ran so fast that he (actually) arrived first.",
      neg: "οὐ",
      dash: undefined,
    },
  ];
  return (
    <Svg w={640} h={400}>
      {rows.map((r, i) => {
        const y = 14 + i * 192;
        return (
          <g key={i}>
            <E x={20} y={y + 20} anchor="start" weight={600} fill={C.accent}>{r.title}</E>
            <Box x={20} y={y + 36} w={264} h={62} />
            <G x={152} y={y + 75} size={22}>{r.cause}</G>
            <Arrow x1={290} y1={y + 67} x2={338} y2={y + 67} sw={2.5} dash={r.dash} />
            <Box x={344} y={y + 36} w={276} h={62} fill={C.wash} stroke={C.accent} dash={r.dash} />
            <G x={482} y={y + 74} size={20}>{r.res}</G>
            <E x={20} y={y + 128} anchor="start" fill={C.ink} italic>{r.en}</E>
            <E x={20} y={y + 154} anchor="start">
              {i === 0 ? "a tendency: what would follow" : "a fact: what did follow"} · negative <Gk>{r.neg}</Gk>
            </E>
          </g>
        );
      })}
    </Svg>
  );
}

// ------------------------------------------------------------------ negatives

export function Negatives() {
  const mh = [
    { k: "command", grc: "μὴ φεῦγε.", en: "Don’t run away!" },
    { k: "wish", grc: "μὴ γένοιτο.", en: "May it not happen!" },
    { k: "condition", grc: "εἰ μὴ ἔρχεται …", en: "if he is not coming …" },
    { k: "purpose", grc: "ἵνα μὴ ἴδῃ", en: "so that he may not see" },
  ];
  return (
    <Svg w={640} h={400}>
      <Box x={20} y={14} w={236} h={372} fill={C.cream} stroke={C.line} />
      <circle cx={138} cy={72} r={40} fill={C.card} stroke={C.accent} strokeWidth={1.5} />
      <G x={138} y={84} size={34} weight={600} fill={C.accent}>οὐ</G>
      <E x={138} y={140} fill={C.ink} weight={600}>facts, statements</E>
      <G x={138} y={194} size={23}>οὐ λέγει.</G>
      <E x={138} y={218}>He does not speak.</E>
      <G x={138} y={266} size={23}>οὐκ ἔστιν.</G>
      <E x={138} y={290}>It is not.</E>
      <E x={138} y={338}>
        <Gk>οὐκ</Gk> before a vowel,
      </E>
      <E x={138} y={360}>
        <Gk>οὐχ</Gk> before rough breathing
      </E>

      <Box x={270} y={14} w={350} h={372} fill={C.wash} stroke={C.sage} />
      <circle cx={445} cy={72} r={40} fill={C.card} stroke={C.accent} strokeWidth={1.5} />
      <G x={445} y={84} size={34} weight={600} fill={C.accent}>μή</G>
      <E x={445} y={140} fill={C.ink} weight={600}>will, wish, condition, purpose</E>
      {mh.map((m, i) => {
        const y = 164 + i * 54;
        return (
          <g key={m.k}>
            <E x={290} y={y + 26} anchor="start" fill={C.accent} weight={600}>{m.k}</E>
            <G x={396} y={y + 20} size={21} anchor="start">{m.grc}</G>
            <E x={396} y={y + 42} anchor="start" size={16}>{m.en}</E>
          </g>
        );
      })}
    </Svg>
  );
}

// ------------------------------------------------------ crasis and elision

export function CrasisElision() {
  const dim = (t: string) => <tspan fill={C.strong}>{t}</tspan>;
  return (
    <Svg w={640} h={400}>
      <E x={20} y={34} anchor="start" weight={600} fill={C.accent}>crasis: two words fuse</E>
      <E x={620} y={34} anchor="end">the coronis ( ᾿ ) marks the join</E>
      <G x={150} y={96} size={27}>κα<H>ὶ ἐ</H>γώ</G>
      <Arrow x1={266} y1={88} x2={350} y2={88} />
      <G x={470} y={96} size={27}>κ<H>ἀ</H>γώ</G>
      <G x={150} y={164} size={27}>τ<H>ὸ ὄ</H>νομα</G>
      <Arrow x1={266} y1={156} x2={350} y2={156} />
      <G x={470} y={164} size={27}>τ<H>οὔ</H>νομα</G>

      <line x1={20} y1={200} x2={620} y2={200} stroke={C.line} strokeWidth={1.5} />
      <E x={20} y={236} anchor="start" weight={600} fill={C.accent}>elision: a final short vowel drops</E>
      <E x={620} y={236} anchor="end">an apostrophe takes its place</E>
      <G x={150} y={298} size={27}>ἀλλ{dim("ὰ")} ἐγώ</G>
      <Arrow x1={266} y1={290} x2={350} y2={290} />
      <G x={470} y={298} size={27}>ἀλλ<H>’</H> ἐγώ</G>
      <G x={150} y={366} size={27}>ἐπ{dim("ὶ")} αὐτόν</G>
      <Arrow x1={266} y1={358} x2={350} y2={358} />
      <G x={470} y={366} size={27}>ἐπ<H>’</H> αὐτόν</G>
    </Svg>
  );
}

// ------------------------------------------------------------ reading strategy

function Badge({ x, y, n }: { x: number; y: number; n: number }) {
  return (
    <g>
      <circle cx={x} cy={y} r={14} fill={C.accent} />
      <E x={x} y={y + 6} size={16} fill={C.card} weight={600}>{String(n)}</E>
    </g>
  );
}

export function ReadingStrategy() {
  const size = 24;
  const l1 = layout(["ὁ Σύρος,", "τὰς ὑδρίας φέρων,"], 40, size, 26);
  const l2 = layout(["τὸν κύνα", "ὁρᾷ,", "ὃς ἐκ τῆς οἰκίας φεύγει."], 40, size, 26);
  const y1 = 110;
  const y2 = 240;
  return (
    <Svg w={640} h={400}>
      {/* line 1 */}
      <Box x={l1[1].x - 10} y={y1 - 34} w={l1[1].w + 20} h={48} fill={C.cream} stroke={C.strong} dash="6 5" />
      <E x={l1[1].c} y={y1 + 38}>participle phrase</E>
      <Badge x={l1[0].c} y={y1 - 52} n={2} />
      {l1.map((w) => (
        <G key={w.t} x={w.x} y={y1} size={size} anchor="start" fill={w === l1[0] ? C.ink : C.muted}>{w.t}</G>
      ))}
      <line x1={l1[0].x} y1={y1 + 10} x2={l1[0].x + l1[0].w - 10} y2={y1 + 10} stroke={C.accent} strokeWidth={2.5} />

      {/* line 2 */}
      <Box x={l2[2].x - 10} y={y2 - 34} w={l2[2].w + 20} h={48} fill={C.cream} stroke={C.strong} dash="6 5" />
      <E x={l2[2].c} y={y2 + 38}>relative clause</E>
      <Badge x={l2[0].c} y={y2 - 52} n={3} />
      <Badge x={l2[1].c} y={y2 - 52} n={1} />
      <Box x={l2[1].x - 8} y={y2 - 32} w={l2[1].w + 10} h={44} fill={C.hl} stroke={C.accent} />
      {l2.map((w, i) => (
        <G key={w.t} x={w.x} y={y2} size={size} anchor="start" fill={i === 2 ? C.muted : C.ink} weight={i === 1 ? 600 : undefined}>{w.t}</G>
      ))}
      <line x1={l2[0].x} y1={y2 + 10} x2={l2[0].x + l2[0].w} y2={y2 + 10} stroke={C.accent} strokeWidth={2.5} />
      <Curve x1={l2[1].c} y1={y2 - 70} cx={l2[1].c - 40} cy={150} x2={l1[0].c + 30} y2={y1 + 16} color={C.sage} sw={1.5} size={9} />

      {/* legend */}
      <line x1={20} y1={306} x2={620} y2={306} stroke={C.line} strokeWidth={1.5} />
      <Badge x={40} y={334} n={1} />
      <E x={62} y={340} anchor="start" fill={C.ink}>verb</E>
      <Badge x={140} y={334} n={2} />
      <E x={162} y={340} anchor="start" fill={C.ink}>subject</E>
      <Badge x={262} y={334} n={3} />
      <E x={284} y={340} anchor="start" fill={C.ink}>object</E>
      <Box x={370} y={318} w={36} h={30} r={6} fill={C.cream} stroke={C.strong} dash="6 5" />
      <E x={416} y={340} anchor="start" fill={C.ink}>bracket, read later</E>
      <E x={320} y={384} italic>Syros, carrying the jars, sees the dog, which is running from the house.</E>
    </Svg>
  );
}
