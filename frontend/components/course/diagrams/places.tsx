/** Place and time: prepositions, -θεν/-δε/-οι, expressions of time, πόθεν; ποῦ; ποῖ; */

import type { ReactNode } from "react";
import { Arrow, Box, C, Curve, E, G, Gk, H, House, Person, Svg } from "./kit";

// -------------------------------------------------------- prepositions (3.4)

export function Prepositions() {
  const cells: { x: number; y: number; prep: string; cs: string; grc: ReactNode; en: string }[] = [
    { x: 20, y: 246, prep: "πρός", cs: "+ accusative", grc: <>πρὸς τὴν ἀκρόπολιν</>, en: "towards the Acropolis" },
    { x: 326, y: 246, prep: "ἀπό", cs: "+ genitive", grc: <>ἀπὸ τῆς ἀκροπόλεως</>, en: "away from the Acropolis" },
    { x: 20, y: 344, prep: "ἐπί", cs: "+ genitive", grc: <>ἐπὶ τῆς ἀκροπόλεως</>, en: "on the Acropolis" },
    { x: 326, y: 344, prep: "μετά", cs: "+ genitive", grc: <>μετὰ τῶν παίδων</>, en: "with the children" },
  ];
  return (
    <Svg w={640} h={440}>
      {/* the hill */}
      <line x1={20} y1={214} x2={620} y2={214} stroke={C.strong} strokeWidth={1.5} />
      <path d="M200 214 C230 150 250 120 290 116 H370 C410 120 430 150 460 214 Z" fill={C.cream} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      <rect x={344} y={92} width={36} height={24} fill={C.card} stroke={C.strong} strokeWidth={1.5} />
      <path d="M340 92 L362 80 L384 92 Z" fill={C.card} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      {/* ἐπί: someone on top */}
      <Person x={310} y={116} s={0.55} />
      <G x={310} y={40} size={24} weight={600} fill={C.accent}>ἐπί</G>
      <Arrow x1={310} y1={48} x2={310} y2={66} sw={1.5} size={8} />
      {/* μετά + πρός: a man with two children walking towards it */}
      <Person x={44} y={214} s={0.75} />
      <Person x={76} y={214} s={0.5} />
      <Person x={100} y={214} s={0.5} />
      <path d="M28 222 v8 H116 v-8" fill="none" stroke={C.accent} strokeWidth={1.5} />
      <G x={72} y={120} size={24} weight={600} fill={C.accent}>μετά</G>
      <Arrow x1={124} y1={178} x2={206} y2={178} />
      <G x={160} y={160} size={24} weight={600} fill={C.accent}>πρός</G>
      {/* ἀπό */}
      <Arrow x1={462} y1={178} x2={600} y2={178} />
      <G x={530} y={160} size={24} weight={600} fill={C.accent}>ἀπό</G>

      {cells.map((c) => (
        <g key={c.prep}>
          <Box x={c.x} y={c.y} w={294} h={88} />
          <G x={c.x + 16} y={c.y + 30} size={22} anchor="start" weight={600} fill={C.accent}>{c.prep}</G>
          <E x={c.x + 278} y={c.y + 28} anchor="end">{c.cs}</E>
          <G x={c.x + 16} y={c.y + 58} size={20} anchor="start">{c.grc}</G>
          <E x={c.x + 16} y={c.y + 80} anchor="start" fill={C.ink}>{c.en}</E>
        </g>
      ))}
    </Svg>
  );
}

// ---------------------------------------------------- place adverbs (4.4)

export function PlaceAdverbs() {
  const table: [string, string, string, string][] = [
    ["home", "οἴκαδε", "οἴκοι", "οἴκοθεν"],
    ["Athens", "Ἀθήναζε", "Ἀθήνησι", "Ἀθήνηθεν"],
    ["question", "ποῖ;", "ποῦ;", "πόθεν;"],
  ];
  const cols = [250, 400, 550];
  return (
    <Svg w={640} h={420}>
      <line x1={20} y1={200} x2={620} y2={200} stroke={C.strong} strokeWidth={1.5} />
      <House x={250} y={200} w={140} h={126} />
      <circle cx={320} cy={138} r={9} fill={C.accent} />
      <Curve x1={40} y1={110} cx={190} cy={80} x2={302} y2={168} />
      <Curve x1={338} y1={168} cx={450} cy={80} x2={600} y2={110} />
      <G x={100} y={70} size={26} weight={600} fill={C.accent}>οἴκα<H>δε</H></G>
      <E x={100} y={94} fill={C.ink}>homeward, to home</E>
      <G x={320} y={30} size={26} weight={600} fill={C.accent}>οἴκ<H>οι</H></G>
      <E x={320} y={54} fill={C.ink}>at home</E>
      <G x={540} y={70} size={26} weight={600} fill={C.accent}>οἴκο<H>θεν</H></G>
      <E x={540} y={94} fill={C.ink}>from home</E>

      <E x={cols[0]} y={236} weight={600} fill={C.accent}>
        to: <Gk fill={C.accent}>-δε, -ζε</Gk>
      </E>
      <E x={cols[1]} y={236} weight={600} fill={C.accent}>
        at: <Gk fill={C.accent}>-οι, -σι</Gk>
      </E>
      <E x={cols[2]} y={236} weight={600} fill={C.accent}>
        from: <Gk fill={C.accent}>-θεν</Gk>
      </E>
      {table.map((r, i) => {
        const y = 250 + i * 54;
        return (
          <g key={r[0]}>
            <Box x={20} y={y} w={600} h={46} r={8} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            <E x={36} y={y + 29} anchor="start">{r[0]}</E>
            {cols.map((x, j) => (
              <G key={j} x={x} y={y + 31} size={22}>{r[j + 1]}</G>
            ))}
          </g>
        );
      })}
    </Svg>
  );
}

// -------------------------------------------------- expressions of time (4.4, 6.2)

export function TimeCases() {
  const days = ["πρώτη", "δευτέρα", "τρίτη", "τετάρτη"];
  const dw = 110;
  const nw = 40;
  const x0 = 40;
  const dx = (i: number) => x0 + i * (dw + nw);
  const y = 70;
  const h = 48;
  return (
    <Svg w={640} h={400}>
      {days.map((d, i) => (
        <g key={d}>
          <rect x={dx(i)} y={y} width={dw} height={h} rx={6} fill={C.card} stroke={C.strong} strokeWidth={1.5} />
          <G x={dx(i) + dw / 2} y={y - 14} size={18} fill={C.muted}>{d}</G>
          {i < 3 && (
            <g>
              <rect x={dx(i) + dw} y={y} width={nw} height={h} fill={i === 2 ? C.accent : C.muted} opacity={i === 2 ? 1 : 0.55} />
              <circle cx={dx(i) + dw + nw / 2} cy={y + h / 2} r={8} fill={C.card} />
              <circle cx={dx(i) + dw + nw / 2 + 4} cy={y + h / 2 - 3} r={7} fill={i === 2 ? C.accent : C.muted} opacity={i === 2 ? 1 : 0.9} />
            </g>
          )}
        </g>
      ))}
      {/* the dot: day 3 */}
      <circle cx={dx(2) + dw / 2} cy={y + h / 2} r={10} fill={C.accent} />
      {/* the bar: days 1–3 */}
      <path d={`M${dx(0)} ${y + h + 18} v14 M${dx(0)} ${y + h + 25} H${dx(2) + dw} M${dx(2) + dw} ${y + h + 18} v14`} stroke={C.accent} strokeWidth={3} strokeLinecap="round" />

      {[
        { icon: "dot", grc: "τῇ τρίτῃ ἡμέρᾳ", en: "on the third day", cs: "dative: when?" },
        { icon: "bar", grc: "τρεῖς ἡμέρας", en: "for three days", cs: "accusative: how long?" },
        { icon: "night", grc: "νυκτός", en: "by night, within the night", cs: "genitive: within what time?" },
      ].map((r, i) => {
        const ry = 176 + i * 74;
        return (
          <g key={r.icon}>
            <Box x={20} y={ry} w={600} h={64} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            {r.icon === "dot" && <circle cx={56} cy={ry + 32} r={10} fill={C.accent} />}
            {r.icon === "bar" && <path d={`M36 ${ry + 24} v16 M36 ${ry + 32} H76 M76 ${ry + 24} v16`} stroke={C.accent} strokeWidth={3} strokeLinecap="round" />}
            {r.icon === "night" && <rect x={44} y={ry + 16} width={24} height={32} rx={3} fill={C.accent} />}
            <G x={96} y={ry + 30} size={22} anchor="start">{r.grc}</G>
            <E x={96} y={ry + 53} anchor="start" fill={C.ink}>{r.en}</E>
            <E x={604} y={ry + 38} anchor="end" weight={600} fill={C.accent}>{r.cs}</E>
          </g>
        );
      })}
    </Svg>
  );
}

// ------------------------------------------------------ πόθεν; ποῦ; ποῖ; (6.2)

export function PothenPoi() {
  const athens = { x: 196, y: 176 };
  const piraeus = { x: 152, y: 226 };
  const miletus = { x: 528, y: 292 };
  return (
    <Svg w={640} h={400}>
      <rect x={0} y={0} width={640} height={400} fill={C.card} />
      {/* Greece: Attica */}
      <path d="M0 0 H300 L286 50 L262 96 L244 150 L262 196 L256 250 L236 300 L220 262 L196 230 L160 222 L128 232 L96 252 L50 244 L0 256 Z" fill={C.cream} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      {/* Euboea */}
      <path d="M300 30 C330 60 352 110 360 150 C350 150 334 120 314 86 C300 64 292 44 300 30 Z" fill={C.cream} stroke={C.strong} strokeWidth={1.5} />
      {/* Asia Minor */}
      <path d="M640 0 V400 H572 L548 350 L566 318 L530 300 L546 266 L516 240 L534 200 L506 170 L528 130 L500 96 L520 50 L500 0 Z" fill={C.cream} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      {/* the Cyclades */}
      {[[330, 250, 14, 9], [372, 292, 12, 8], [410, 238, 10, 7], [396, 340, 13, 8], [450, 300, 11, 7], [312, 318, 9, 6], [468, 214, 9, 6]].map(([x, y, rx, ry], i) => (
        <ellipse key={i} cx={x} cy={y} rx={rx} ry={ry} fill={C.cream} stroke={C.strong} strokeWidth={1.5} />
      ))}
      <G x={400} y={386} size={18} fill={C.muted} italic>τὸ Αἰγαῖον πέλαγος</G>

      {/* the route */}
      <Curve x1={miletus.x - 12} y1={miletus.y - 4} cx={360} cy={170} x2={athens.x + 12} y2={athens.y + 2} dash="7 6" />
      <Arrow x1={athens.x - 6} y1={athens.y + 8} x2={piraeus.x + 10} y2={piraeus.y - 6} />
      {[athens, piraeus, miletus].map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={7} fill={C.accent} stroke={C.card} strokeWidth={2} />
      ))}

      <G x={560} y={34} size={28} weight={600} fill={C.accent} anchor="end">πόθεν;</G>
      <G x={622} y={76} size={20} anchor="end">ἐκ Μιλήτου</G>
      <E x={622} y={100} anchor="end">from where? from Miletus</E>
      <line x1={560} y1={108} x2={536} y2={278} stroke={C.accent} strokeWidth={1.5} strokeDasharray="3 4" />

      <G x={180} y={40} size={28} weight={600} fill={C.accent}>ποῦ;</G>
      <G x={180} y={76} size={20}>Ἀθήνησι</G>
      <E x={180} y={100}>where? at Athens</E>
      <line x1={190} y1={108} x2={196} y2={164} stroke={C.accent} strokeWidth={1.5} strokeDasharray="3 4" />

      <G x={110} y={306} size={28} weight={600} fill={C.accent}>ποῖ;</G>
      <G x={110} y={340} size={20}>εἰς Πειραιᾶ</G>
      <E x={110} y={364}>to where? to Piraeus</E>
      <line x1={120} y1={284} x2={146} y2={236} stroke={C.accent} strokeWidth={1.5} strokeDasharray="3 4" />
    </Svg>
  );
}
