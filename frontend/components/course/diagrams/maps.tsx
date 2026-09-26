/** Schematic maps and plans: the Agora, the Long Walls, Piraeus, Attica in 431,
 * the Pnyx, and the kleroterion. Not to scale except where a bar says so. */

import { Arrow, Box, C, E, G, North, Path, Svg } from "./kit";

function Badge({ x, y, n }: { x: number; y: number; n: number }) {
  return (
    <g>
      <circle cx={x} cy={y} r={11} fill={C.accent} />
      <E x={x} y={y + 5.5} size={16} fill={C.card} weight={600}>{String(n)}</E>
    </g>
  );
}

// ------------------------------------------------------------- Agora (1.3)

export function AgoraPlan() {
  const legend: [string, string][] = [
    ["Ἡφαιστεῖον", "temple of Hephaestus"],
    ["στοὰ βασίλειος", "Royal Stoa"],
    ["βουλευτήριον", "council house"],
    ["θόλος", "round council hall"],
    ["στοὰ ποικίλη", "Painted Stoa"],
    ["δώδεκα θεοί", "altar of the Twelve Gods"],
    ["ἡλιαία", "law court"],
    ["νοτία στοά", "South Stoa"],
    ["ἀργυροκοπεῖον", "mint"],
  ];
  const b = { fill: C.card, stroke: C.strong };
  return (
    <Svg w={640} h={500}>
      {/* hill of Kolonos Agoraios */}
      <ellipse cx={52} cy={190} rx={48} ry={110} fill={C.cream} stroke={C.line} strokeWidth={1.5} />
      {/* the open square */}
      <path d="M142 72 H372 L392 380 H138 Z" fill={C.wash} stroke={C.sage} strokeWidth={1.5} strokeDasharray="6 5" strokeLinejoin="round" />
      {/* Panathenaic Way */}
      <path d="M120 16 L408 470" stroke={C.cream} strokeWidth={18} strokeLinecap="round" />
      <path d="M120 16 L408 470" stroke={C.strong} strokeWidth={1.5} strokeDasharray="2 6" strokeLinecap="round" />
      <g transform="rotate(57.6 290 250)">
        <G x={290} y={244} size={17} fill={C.muted}>ὁδὸς Παναθηναϊκή</G>
      </g>
      {/* buildings */}
      <rect x={22} y={170} width={64} height={30} rx={3} {...b} strokeWidth={1.5} />
      <rect x={98} y={100} width={30} height={42} rx={3} {...b} strokeWidth={1.5} />
      <rect x={92} y={220} width={40} height={54} rx={3} {...b} strokeWidth={1.5} />
      <circle cx={114} cy={308} r={18} {...b} strokeWidth={1.5} />
      <rect x={150} y={34} width={150} height={24} rx={3} {...b} strokeWidth={1.5} />
      <rect x={214} y={104} width={18} height={18} {...b} strokeWidth={1.5} />
      <rect x={116} y={350} width={56} height={52} rx={3} {...b} strokeWidth={1.5} />
      <rect x={186} y={398} width={150} height={24} rx={3} {...b} strokeWidth={1.5} />
      <rect x={346} y={392} width={44} height={36} rx={3} {...b} strokeWidth={1.5} />
      {[
        [54, 185],
        [113, 121],
        [112, 247],
        [114, 308],
        [225, 46],
        [248, 113],
        [144, 376],
        [261, 410],
        [368, 410],
      ].map(([x, y], i) => (
        <Badge key={i} x={x} y={y} n={i + 1} />
      ))}
      <G x={210} y={300} size={22} fill={C.accent} weight={600}>ἀγορά</G>
      <North x={380} y={30} />
      <E x={96} y={36} anchor="end">Dipylon ↖</E>
      <E x={400} y={494} anchor="end">Acropolis ↘</E>

      {/* legend */}
      {legend.map(([g, en], i) => {
        const y = 30 + i * 51;
        return (
          <g key={g}>
            <Badge x={428} y={y + 6} n={i + 1} />
            <G x={446} y={y + 12} size={18} anchor="start">{g}</G>
            <E x={446} y={y + 32} size={16} anchor="start">{en}</E>
          </g>
        );
      })}
    </Svg>
  );
}

// -------------------------------------------------------- Long Walls (4.1)

export function LongWalls() {
  return (
    <Svg w={640} h={440}>
      <rect x={0} y={0} width={640} height={440} fill={C.card} />
      <path
        d="M0 0 H640 V440 H610 C560 424 500 400 440 386 C390 374 340 364 300 352 C270 340 250 322 214 312 C204 308 198 300 194 296 C196 320 180 346 150 354 C116 360 84 346 72 322 C62 300 58 276 40 264 L0 256 Z"
        fill={C.cream}
        stroke={C.strong}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      {/* Athens: circuit and Acropolis */}
      <circle cx={462} cy={118} r={56} fill={C.card} stroke={C.accent} strokeWidth={2.5} />
      <ellipse cx={470} cy={132} rx={16} ry={9} fill={C.sage} stroke={C.accent} strokeWidth={1.5} />
      {/* Piraeus circuit round the peninsula */}
      <path d="M84 300 C96 272 150 268 180 284 C198 300 190 334 160 344 C128 352 92 336 84 300 Z" fill="none" stroke={C.accent} strokeWidth={2.5} />
      {/* the Long Walls: two to Piraeus, one to Phaleron */}
      <path d="M414 146 L172 280" stroke={C.accent} strokeWidth={3} strokeLinecap="round" />
      <path d="M424 164 L188 296" stroke={C.accent} strokeWidth={3} strokeLinecap="round" />
      <path d="M440 170 L300 350" stroke={C.accent} strokeWidth={3} strokeLinecap="round" />
      <circle cx={300} cy={352} r={6} fill={C.accent} />

      <G x={462} y={48} size={24} weight={600}>Ἀθῆναι</G>
      <E x={500} y={134} anchor="start">Acropolis</E>
      <G x={96} y={252} size={22} weight={600}>Πειραιεύς</G>
      <G x={318} y={390} size={20}>Φάληρον</G>
      <g transform="rotate(-29 282 196)">
        <G x={282} y={196} size={22} fill={C.accent} weight={600}>τὰ μακρὰ τείχη</G>
      </g>
      <E x={380} y={290} anchor="start" fill={C.ink}>Phaleric wall</E>
      <E x={130} y={414} italic>the sea (Saronic Gulf)</E>
      <North x={40} y={30} />
      {/* scale: Athens–Piraeus ≈ 7 km ≈ 385 units */}
      <path d="M494 414 H604 M494 408 v12 M604 408 v12" stroke={C.ink} strokeWidth={1.5} />
      <E x={549} y={402}>2 km</E>
    </Svg>
  );
}

// ------------------------------------------------------------- Piraeus (4.2)

export function PiraeusPlan() {
  const grid = [];
  for (let x = 270; x <= 450; x += 26) grid.push(<line key={`v${x}`} x1={x} y1={96} x2={x} y2={236} stroke={C.strong} strokeWidth={1.5} />);
  for (let y = 96; y <= 236; y += 22) grid.push(<line key={`h${y}`} x1={270} y1={y} x2={452} y2={y} stroke={C.strong} strokeWidth={1.5} />);
  return (
    <Svg w={640} h={440}>
      <rect x={0} y={0} width={640} height={440} fill={C.card} />
      {/* land */}
      <path
        d="M0 0 H640 V110 L596 150 L566 196 L546 252 L486 282 L420 302 L360 318 L300 332 L252 362 L200 392 L120 394 L60 372 L30 332 L40 292 L20 250 L0 242 Z"
        fill={C.cream}
        stroke={C.strong}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      {grid}
      {/* Kantharos */}
      <path d="M22 254 C60 226 100 186 170 182 C232 180 264 212 248 250 C234 282 170 292 110 292 C80 292 56 291 38 294" fill={C.card} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      {/* Zea */}
      <path d="M314 329 C292 300 294 256 330 250 C366 246 374 290 346 323" fill={C.card} stroke={C.strong} strokeWidth={1.5} />
      {/* Munichia */}
      <path d="M494 279 C478 256 486 226 510 222 C534 220 540 250 514 270" fill={C.card} stroke={C.strong} strokeWidth={1.5} />
      {/* harbour moles */}
      {[
        [22, 254, 30, 262],
        [38, 294, 44, 284],
        [314, 329, 318, 318],
        [346, 323, 342, 312],
        [494, 279, 494, 268],
        [514, 270, 508, 262],
      ].map(([a, b, c, d], i) => (
        <line key={i} x1={a} y1={b} x2={c} y2={d} stroke={C.accent} strokeWidth={4} strokeLinecap="round" />
      ))}
      {/* the emporion on the east shore of Kantharos */}
      <path d="M224 190 C256 208 262 244 238 270" fill="none" stroke={C.sage} strokeWidth={10} strokeLinecap="round" />
      {/* Long Walls to Athens */}
      <path d="M330 92 L420 0 M350 96 L444 0" stroke={C.accent} strokeWidth={3} strokeLinecap="round" />
      <E x={452} y={30} anchor="start" fill={C.ink}>to Athens ↗</E>
      <E x={452} y={52} anchor="start">Long Walls</E>

      <G x={140} y={238} size={22} weight={600}>Κάνθαρος</G>
      <E x={140} y={262}>trade harbour</E>
      <G x={214} y={160} size={20} fill={C.accent} weight={600} anchor="end">ἐμπόριον</G>
      <Path pts={[[200, 166], [226, 190]]} sw={1.5} size={8} />
      <G x={332} y={292} size={20} weight={600}>Ζέα</G>
      <G x={512} y={210} size={20} weight={600}>Μουνιχία</G>
      <E x={420} y={368} fill={C.ink}>Zea and Munichia: war harbours</E>
      <E x={420} y={390}>shipsheds for the triremes</E>
      <G x={130} y={350} size={20} fill={C.muted}>Ἀκτή</G>
      <E x={360} y={86} fill={C.ink} anchor="start">street grid</E>
      <North x={40} y={30} />
    </Svg>
  );
}

// -------------------------------------------------- Attica at war (431 BC)

export function WarMap() {
  const athens = { x: 410, y: 300 };
  const piraeus = { x: 342, y: 352 };
  const acharnae = { x: 402, y: 158 };
  const eleusis = { x: 184, y: 272 };
  const mountain = (x: number, y: number, s = 1) => <path key={`${x}-${y}`} d={`M${x - 14 * s} ${y} L${x} ${y - 16 * s} L${x + 14 * s} ${y}`} fill="none" stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />;
  return (
    <Svg w={640} h={480}>
      <rect x={0} y={0} width={640} height={480} fill={C.card} />
      <path
        d="M0 0 H640 V480 H540 C510 440 480 410 452 392 C420 376 396 372 376 370 C360 372 348 380 330 374 C316 368 318 356 326 348 C300 330 272 318 250 302 C230 290 210 282 186 278 C160 280 140 292 110 300 C80 306 40 306 0 312 Z"
        fill={C.cream}
        stroke={C.strong}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      {/* Salamis */}
      <path d="M168 342 C196 324 246 326 276 348 C296 364 268 396 228 390 C196 386 156 368 168 342 Z" fill={C.cream} stroke={C.strong} strokeWidth={1.5} />
      <G x={222} y={366} size={18} fill={C.muted}>Σαλαμίς</G>
      {/* mountains */}
      {[mountain(300, 88), mountain(330, 74), mountain(362, 86), mountain(392, 72)]}
      <G x={346} y={110} size={18} fill={C.muted}>Πάρνης</G>
      {[mountain(292, 222, 0.8), mountain(306, 246, 0.8), mountain(320, 270, 0.8)]}
      {[mountain(486, 318, 0.8), mountain(500, 342, 0.8)]}
      <G x={522} y={350} size={18} fill={C.muted} anchor="start">Ὑμηττός</G>

      {/* Long Walls */}
      <path d={`M${athens.x - 4} ${athens.y + 6} L${piraeus.x + 6} ${piraeus.y - 6} M${athens.x + 2} ${athens.y + 10} L${piraeus.x + 12} ${piraeus.y + 2} M${athens.x + 4} ${athens.y + 12} L376 368`} stroke={C.accent} strokeWidth={2.5} strokeLinecap="round" />
      <circle cx={athens.x} cy={athens.y} r={15} fill={C.card} stroke={C.accent} strokeWidth={2.5} />
      <circle cx={piraeus.x} cy={piraeus.y} r={8} fill={C.card} stroke={C.accent} strokeWidth={2.5} />

      {/* the invasion route */}
      <Path
        pts={[
          [4, 292],
          [70, 290],
          [eleusis.x - 12, eleusis.y - 4],
          [eleusis.x + 22, eleusis.y - 24],
          [256, 196],
          [300, 176],
          [acharnae.x - 18, acharnae.y + 2],
        ]}
        color={C.ink}
        sw={2.5}
        dash="8 6"
        size={12}
      />
      {[eleusis, acharnae].map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={7} fill={C.accent} stroke={C.card} strokeWidth={2} />
      ))}
      {/* 11 km */}
      <line x1={acharnae.x + 2} y1={acharnae.y + 12} x2={athens.x} y2={athens.y - 18} stroke={C.muted} strokeWidth={1.5} strokeDasharray="2 5" />
      <E x={acharnae.x + 12} y={232} anchor="start">≈ 11 km</E>

      <G x={athens.x + 22} y={athens.y + 6} size={22} weight={600} anchor="start">Ἀθῆναι</G>
      <G x={piraeus.x - 12} y={piraeus.y + 36} size={20} weight={600} anchor="end">Πειραιεύς</G>
      <G x={acharnae.x + 14} y={acharnae.y + 6} size={22} weight={600} anchor="start">Ἀχαρναί</G>
      <G x={eleusis.x + 18} y={eleusis.y + 42} size={20} weight={600}>Ἐλευσίς</G>
      <E x={14} y={272} anchor="start" fill={C.ink}>← Isthmus</E>
      <G x={150} y={196} size={20} fill={C.ink}>Λακεδαιμόνιοι</G>
      <E x={150} y={218}>Archidamus, 431 BC</E>
      <E x={130} y={440} italic>Saronic Gulf</E>
      <North x={600} y={24} />
      {/* legend */}
      <Box x={440} y={410} w={190} h={60} r={8} fill={C.card} stroke={C.line} />
      <path d="M452 428 H486" stroke={C.ink} strokeWidth={2.5} strokeDasharray="8 6" />
      <E x={494} y={434} anchor="start" fill={C.ink}>Spartan army</E>
      <path d="M452 454 H486" stroke={C.accent} strokeWidth={2.5} />
      <E x={494} y={460} anchor="start" fill={C.ink}>Long Walls</E>
    </Svg>
  );
}

// ------------------------------------------------------------------- Pnyx

export function PnyxPlan() {
  const cx = 404;
  const cy = 146;
  const pt = (r: number, deg: number) => [cx + r * Math.cos((deg * Math.PI) / 180), cy + r * Math.sin((deg * Math.PI) / 180)];
  const [ax, ay] = pt(250, 72);
  const [bx, by] = pt(250, 196);
  const dots = [];
  for (let r = 70; r <= 230; r += 22) {
    const n = Math.floor((r * (116 * Math.PI)) / 180 / 17);
    for (let k = 0; k <= n; k++) {
      const deg = 76 + (116 * k) / n;
      const [x, y] = pt(r, deg);
      dots.push(<circle key={`${r}-${k}`} cx={x} cy={y} r={3.6} fill={C.sage} />);
    }
  }
  return (
    <Svg w={640} h={440}>
      {/* the auditorium on the hillside */}
      <path d={`M${cx} ${cy} L${ax} ${ay} A250 250 0 0 1 ${bx} ${by} Z`} fill={C.wash} stroke={C.sage} strokeWidth={1.5} strokeLinejoin="round" />
      {dots}
      {/* the bema */}
      <rect x={cx - 16} y={cy - 16} width={32} height={32} rx={4} fill={C.accent} />
      <rect x={cx - 10} y={cy - 26} width={20} height={10} rx={2} fill={C.sage} stroke={C.accent} strokeWidth={1.5} />
      <G x={cx + 30} y={cy + 8} size={24} weight={600} anchor="start">τὸ βῆμα</G>
      <E x={cx + 30} y={cy + 32} anchor="start" fill={C.ink}>the speaker’s platform</E>
      {/* view to the Agora */}
      <Arrow x1={cx + 6} y1={cy - 34} x2={cx + 110} y2={cy - 120} color={C.accent} dash="6 5" />
      <G x={cx + 104} y={24} size={22} weight={600} anchor="start">ἡ ἀγορά</G>
      <E x={cx + 104} y={46} anchor="start">north-east, below</E>
      <E x={620} y={220} anchor="end" fill={C.ink}>Acropolis →</E>
      <G x={150} y={394} size={22} weight={600}>ἡ ἐκκλησία</G>
      <E x={150} y={418}>citizens seated on the slope</E>
      <E x={620} y={404} anchor="end" fill={C.ink}>about 6,000 at a meeting</E>
      <E x={620} y={426} anchor="end">5th-century layout</E>
      <North x={40} y={30} />
    </Svg>
  );
}

// ------------------------------------------------------------- kleroterion

export function Kleroterion() {
  const cols = 5;
  const rows = 11;
  const white = new Set([2, 7]);
  const filled = (r: number, c: number) => (r * 7 + c * 3) % 5 !== 0;
  return (
    <Svg w={640} h={470}>
      {/* stone */}
      <path d="M170 30 H470 V412 H170 Z" fill={C.cream} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      {/* slot rows */}
      {Array.from({ length: rows }, (_, r) => {
        const y = 66 + r * 30;
        return (
          <g key={r}>
            {white.has(r) && <rect x={244} y={y - 5} width={214} height={24} rx={6} fill={C.hl} stroke={C.accent} strokeWidth={1.5} />}
            {Array.from({ length: cols }, (_, c) => (
              <rect key={c} x={254 + c * 40} y={y} width={32} height={14} rx={2} fill={filled(r, c) ? C.card : C.cream} stroke={filled(r, c) ? C.accent : C.strong} strokeWidth={1.5} />
            ))}
          </g>
        );
      })}
      {/* the tube and its funnel */}
      <path d="M190 44 L204 60 V396 H222 V60 L236 44" fill="none" stroke={C.accent} strokeWidth={2} strokeLinejoin="round" />
      {Array.from({ length: rows }, (_, r) => (
        <circle key={r} cx={213} cy={73 + r * 30} r={8} fill={white.has(r) ? C.card : C.ink} stroke={C.ink} strokeWidth={1.5} />
      ))}

      {/* labels */}
      <G x={24} y={120} size={24} weight={600} anchor="start">κύβοι</G>
      <E x={24} y={144} anchor="start" fill={C.ink}>black and white</E>
      <E x={24} y={164} anchor="start" fill={C.ink}>balls, fed in</E>
      <E x={24} y={184} anchor="start" fill={C.ink}>at the top</E>
      <Arrow x1={130} y1={104} x2={196} y2={56} sw={1.5} size={9} />

      <G x={486} y={200} size={24} weight={600} anchor="start">πινάκια</G>
      <E x={486} y={224} anchor="start" fill={C.ink}>jurors’ name</E>
      <E x={486} y={244} anchor="start" fill={C.ink}>tickets, one</E>
      <E x={486} y={264} anchor="start" fill={C.ink}>in each slot</E>
      <Arrow x1={484} y1={188} x2={446} y2={160} sw={1.5} size={9} />

      <E x={24} y={300} anchor="start" fill={C.accent} weight={600}>white ball:</E>
      <E x={24} y={320} anchor="start" fill={C.ink}>the row</E>
      <E x={24} y={340} anchor="start" fill={C.ink}>serves today</E>
      <Arrow x1={120} y1={292} x2={198} y2={283} sw={1.5} size={9} />
      <E x={320} y={446} fill={C.ink}>a black ball sends its row home</E>
    </Svg>
  );
}
