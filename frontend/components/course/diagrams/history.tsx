/** History track maps: the retreat from Syracuse (hist.3), Aegospotami
 * (hist.4) and the march up-country to Cunaxa (hist.7). Schematic, not to
 * scale; places where Thucydides and Xenophon put them. */

import { C, E, G, North, Path, Svg } from "./kit";

function Dot({ x, y, r = 5, fill = C.accent }: { x: number; y: number; r?: number; fill?: string }) {
  return <circle cx={x} cy={y} r={r} fill={fill} stroke={C.card} strokeWidth={1.5} />;
}

const LAND = { fill: C.cream, stroke: C.strong, strokeWidth: 1.5, strokeLinejoin: "round" as const };
const RIVER = { fill: "none", stroke: C.sage, strokeWidth: 3, strokeLinecap: "round" as const };

// ------------------------------------------------------- Syracuse, 413 BC

export function SicilyRetreat() {
  return (
    <Svg w={640} h={420}>
      <rect x={0} y={0} width={640} height={420} fill={C.wash} />
      {/* south-east Sicily: land to the west, the sea to the east and south */}
      <path d="M0 0 H470 C455 60 470 96 452 140 C440 168 470 186 462 214 C452 250 420 262 424 300 C428 340 380 372 330 420 H0 Z" {...LAND} />
      {/* the Great Harbour and Ortygia */}
      <path d="M452 140 C420 150 404 176 420 206 C434 220 454 214 462 214" fill={C.wash} stroke={C.strong} strokeWidth={1.5} />
      <ellipse cx={478} cy={178} rx={14} ry={22} {...LAND} />
      <Dot x={470} y={124} />
      <G x={492} y={112} size={18} anchor="start">Συράκουσαι</G>
      <G x={436} y={184} size={13} fill={C.muted}>ὁ μέγας λιμήν</G>
      <G x={330} y={96} size={15} fill={C.muted}>Ἐπιπολαί</G>
      {/* rivers crossed on the way south */}
      <path d="M240 246 C300 256 370 268 424 276" {...RIVER} />
      <path d="M216 296 C290 310 350 316 412 320" {...RIVER} />
      <path d="M190 350 C260 358 320 364 380 372" {...RIVER} />
      <G x={234} y={250} size={14} anchor="end" fill={C.muted}>Κακύπαρις</G>
      <G x={210} y={300} size={14} anchor="end" fill={C.muted}>Ἐρινεός</G>
      <G x={184} y={355} size={16} anchor="end" weight={600}>Ἀσίναρος</G>
      {/* the retreat: west towards the hills, back, then south */}
      <Path pts={[[430, 190], [330, 200], [250, 190], [210, 214]]} dash="7 6" color={C.accent} noHead />
      <Path pts={[[210, 214], [280, 236], [356, 262], [396, 300], [360, 342], [322, 366]]} color={C.accent} />
      <G x={150} y={180} size={14} fill={C.muted}>Ἀκραῖον λέπας</G>
      <E x={150} y={198} size={13}>blocked in the pass</E>
      <E x={330} y={392} size={13} anchor="middle" fill={C.ink}>Nicias's army cut down at the river</E>
      <North x={600} y={40} />
      {/* inset: where this is */}
      <g transform="translate(24 24)">
        <rect x={0} y={0} width={120} height={92} fill={C.card} stroke={C.line} strokeWidth={1.5} rx={6} />
        <path d="M14 22 L106 30 L82 80 Z" {...LAND} />
        <rect x={80} y={56} width={16} height={16} fill="none" stroke={C.accent} strokeWidth={2} />
        <G x={52} y={50} size={13}>Σικελία</G>
      </g>
    </Svg>
  );
}

// ----------------------------------------------------- Aegospotami, 405 BC

export function Hellespont() {
  return (
    <Svg w={640} h={420}>
      <rect x={0} y={0} width={640} height={420} fill={C.wash} />
      {/* Europe: the Chersonese, north-west of the strait */}
      <path d="M0 0 H560 C540 60 500 90 462 120 C400 170 330 214 262 262 C200 306 130 352 0 372 Z" {...LAND} />
      {/* Asia, south-east */}
      <path d="M640 60 C600 110 548 150 500 184 C430 232 360 280 300 318 C240 356 170 390 120 420 H640 Z" {...LAND} />
      <G x={120} y={120} size={20} fill={C.muted}>Χερρόνησος</G>
      <E x={120} y={142} size={13}>Europe</E>
      <G x={540} y={330} size={20} fill={C.muted}>Ἀσία</G>
      <g transform="rotate(-33 380 236)">
        <G x={380} y={236} size={18} fill={C.accent} italic>Ἑλλήσποντος</G>
      </g>
      <G x={600} y={40} size={14} fill={C.muted} anchor="end">Προποντίς ↗</G>
      <G x={40} y={404} size={14} fill={C.muted} anchor="start">↙ τὸ Αἰγαῖον</G>
      {/* places */}
      <Dot x={420} y={140} />
      <G x={410} y={128} size={16} anchor="end" weight={600}>Αἰγὸς ποταμοί</G>
      <E x={410} y={110} size={12} anchor="end">the Athenian ships on the beach</E>
      <Dot x={482} y={190} />
      <G x={494} y={210} size={16} anchor="start">Λάμψακος</G>
      <E x={494} y={228} size={12} anchor="start">Lysander's fleet</E>
      <Dot x={300} y={232} />
      <G x={288} y={224} size={15} anchor="end">Σηστός</G>
      {/* Lysander crosses; the few ships escape */}
      <Path pts={[[476, 186], [448, 164], [428, 148]]} color={C.ink} size={12} />
      <E x={466} y={150} size={12} anchor="start" fill={C.ink}>≈ 15 stades</E>
      <Path pts={[[412, 150], [340, 206], [250, 276], [150, 340]]} dash="7 6" color={C.accent} />
      <E x={210} y={276} size={13} anchor="end" fill={C.ink}>the Paralos → Athens</E>
      <E x={210} y={294} size={13} anchor="end">Konon → Cyprus</E>
      <North x={600} y={96} />
    </Svg>
  );
}

// --------------------------------------------------- up-country to Cunaxa

export function AnabasisMap() {
  const stops: [number, number, string, "start" | "end" | "middle", number][] = [
    [70, 142, "Σάρδεις", "middle", -14],
    [146, 170, "Κελαιναί", "middle", -14],
    [220, 176, "Ἰκόνιον", "middle", -14],
    [282, 234, "Ταρσοί", "middle", 24],
    [338, 238, "Ἰσσοί", "middle", 24],
    [412, 176, "Θάψακος", "end", -12],
  ];
  const route: [number, number][] = [[70, 142], [146, 170], [220, 176], [282, 234], [338, 238], [360, 214], [412, 176], [446, 196], [482, 242], [522, 284], [556, 306]];
  return (
    <Svg w={640} h={420}>
      <rect x={0} y={0} width={640} height={420} fill={C.cream} />
      {/* seas */}
      <path d="M0 230 C60 222 120 250 180 262 C240 270 290 262 330 272 C352 300 336 360 300 420 H0 Z" fill={C.wash} stroke={C.strong} strokeWidth={1.5} />
      <path d="M0 0 H300 C250 30 170 40 90 30 C50 26 20 40 0 50 Z" fill={C.wash} stroke={C.strong} strokeWidth={1.5} />
      <path d="M560 420 C580 380 610 360 640 350 V420 Z" fill={C.wash} stroke={C.strong} strokeWidth={1.5} />
      <G x={140} y={330} size={15} fill={C.muted} italic>ἡ θάλαττα</G>
      <G x={150} y={24} size={13} fill={C.muted} italic>ὁ Εὔξεινος πόντος</G>
      {/* rivers */}
      <path d="M430 60 C420 110 410 150 414 176 C430 220 470 256 520 300 C548 326 570 360 590 400" {...RIVER} />
      <path d="M540 40 C560 110 580 170 596 230 C606 280 610 340 612 400" {...RIVER} />
      <G x={446} y={112} size={14} fill={C.muted} anchor="start">Εὐφράτης</G>
      <G x={586} y={150} size={14} fill={C.muted} anchor="end">Τίγρης</G>
      {/* the march */}
      <Path pts={route} color={C.accent} />
      {stops.map(([x, y, g, a, dy]) => (
        <g key={g}>
          <Dot x={x} y={y} r={4.5} />
          <G x={x} y={y + dy} size={14} anchor={a}>{g}</G>
        </g>
      ))}
      <circle cx={556} cy={306} r={9} fill={C.card} stroke={C.accent} strokeWidth={2.5} />
      <G x={556} y={286} size={17} weight={600}>Κούναξα</G>
      <Dot x={566} y={360} r={4.5} fill={C.ink} />
      <G x={556} y={378} size={14} anchor="end">Βαβυλών</G>
      <E x={24} y={390} size={13} anchor="start" fill={C.ink}>Spring–September 401 BC: Cyrus marches from Sardis</E>
      <E x={24} y={408} size={13} anchor="start">Xenophon counts 93 day-marches from Ephesus to the battle</E>
      <North x={600} y={40} />
    </Svg>
  );
}
