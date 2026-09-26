/** Politics track: Cleisthenes' tribes and the working parts of the
 * democracy. Schematic, not to scale. */

import { Arrow, Box, C, E, G, Svg } from "./kit";

// --------------------------------------------------------- tribes (pol.1)

const ATTICA = "M44 70 L150 38 L262 30 L318 88 L330 170 L292 250 L252 318 L214 392 L182 330 L136 282 L70 238 L34 150 Z";
const INLAND = "M104 96 L236 74 L286 128 L280 196 L238 262 L196 214 L118 190 Z";

export function TribesMap() {
  const regions: [string, string, string][] = [
    [C.hl, "ἄστυ", "the city and its plain"],
    [C.wash, "παραλία", "the coast"],
    [C.cream, "μεσόγειος", "the inland"],
  ];
  return (
    <Svg w={640} h={420}>
      <defs>
        <clipPath id="attica-clip"><path d={ATTICA} /></clipPath>
      </defs>
      {/* coast = the whole land, then inland and city on top */}
      <path d={ATTICA} fill={C.wash} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      <g clipPath="url(#attica-clip)">
        <path d={INLAND} fill={C.cream} stroke={C.line} strokeWidth={1.5} strokeLinejoin="round" />
        <ellipse cx={128} cy={214} rx={58} ry={44} fill={C.hl} stroke={C.sage} strokeWidth={1.5} />
      </g>
      <circle cx={128} cy={206} r={5} fill={C.accent} />
      <G x={128} y={236} size={16}>Ἀθῆναι</G>
      <G x={216} y={150} size={16} fill={C.muted}>μεσόγειος</G>
      <G x={240} y={336} size={16} fill={C.muted} anchor="start">παραλία</G>
      <G x={226} y={396} size={14} fill={C.muted} anchor="start">Σούνιον</G>

      {/* one tribe = a third from each region */}
      <G x={480} y={46} size={22} weight={600} fill={C.accent}>μία φυλή</G>
      <E x={480} y={68} size={14}>one tribe = three “thirds”</E>
      {regions.map(([fill, g, en], i) => {
        const y = 92 + i * 70;
        return (
          <g key={g}>
            <Box x={384} y={y} w={192} h={56} fill={fill} stroke={C.strong} />
            <G x={480} y={y + 25} size={18}>τριττὺς ἐκ τ{i === 0 ? "οῦ ἄστεως" : i === 1 ? "ῆς παραλίας" : "ῆς μεσογείου"}</G>
            <E x={480} y={y + 45} size={13}>{en}</E>
          </g>
        );
      })}
      <Arrow x1={340} y1={200} x2={378} y2={200} color={C.strong} />
      <G x={480} y={332} size={18}>δέκα φυλαί · τριάκοντα τριττύες</G>
      <E x={480} y={356} size={14}>10 tribes · 30 thirds · about 139 demes</E>
      <E x={480} y={380} size={14}>so no tribe belongs to one district:</E>
      <E x={480} y={398} size={14}>city, shore and hill men vote together</E>
    </Svg>
  );
}

// ---------------------------------------------------- the democracy (pol.3)

export function Constitution() {
  const bodies: { x: number; g: string; en: string; sub: string }[] = [
    { x: 20, g: "ἐκκλησία", en: "Assembly · Pnyx", sub: "every citizen · votes" },
    { x: 180, g: "βουλή", en: "Council of 500", sub: "50 a tribe · by lot" },
    { x: 340, g: "δικαστήρια", en: "law courts", sub: "6,000 jurors · by lot" },
    { x: 500, g: "ἄρχοντες", en: "officials", sub: "by lot · generals elected" },
  ];
  return (
    <Svg w={640} h={420}>
      <G x={320} y={36} size={22} weight={600} fill={C.accent}>ὁ δῆμος</G>
      <E x={320} y={58} size={14}>the citizens: adult men with an Athenian father and mother (jurors over 30)</E>
      {bodies.map((b) => (
        <g key={b.g}>
          <Arrow x1={320} y1={70} x2={b.x + 60} y2={128} color={C.strong} sw={1.5} />
          <Box x={b.x} y={134} w={120} h={92} fill={C.card} />
          <G x={b.x + 60} y={166} size={19} weight={600}>{b.g}</G>
          <E x={b.x + 60} y={190} size={13} fill={C.ink}>{b.en}</E>
          <E x={b.x + 60} y={210} size={12}>{b.sub}</E>
        </g>
      ))}
      {/* Council prepares business for the Assembly */}
      <Arrow x1={180} y1={250} x2={142} y2={250} />
      <G x={96} y={278} size={15} anchor="start">προβούλευμα</G>
      <E x={96} y={296} size={12} anchor="start">the Council drafts the agenda</E>
      {/* Assembly decides */}
      <Arrow x1={80} y1={226} x2={80} y2={330} />
      <G x={80} y={352} size={16}>ψήφισμα</G>
      <E x={80} y={370} size={12}>decrees · war and peace</E>
      <E x={80} y={386} size={12}>elects the ten generals</E>
      {/* courts judge */}
      <Arrow x1={400} y1={226} x2={400} y2={330} />
      <G x={400} y={352} size={16}>δίκη · γραφή</G>
      <E x={400} y={370} size={12}>private suits · public charges</E>
      {/* officials accountable */}
      <path d="M560 226 C 560 300, 470 300, 452 238" fill="none" stroke={C.accent} strokeWidth={2} strokeDasharray="6 5" />
      <Arrow x1={458} y1={250} x2={452} y2={236} />
      <G x={560} y={352} size={16}>εὔθυναι</G>
      <E x={560} y={370} size={12}>every official's accounts</E>
      <E x={560} y={386} size={12}>are checked at year's end</E>
      <E x={320} y={414} size={12} italic>Athens in the later 5th and 4th centuries BC, simplified</E>
    </Svg>
  );
}
