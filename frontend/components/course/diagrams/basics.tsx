/** Stage 0 and Unit 1: the alphabet, the cases, ἐν · εἰς · ἐκ. */

import { Arrow, Box, C, Curve, E, G, H, House, Svg } from "./kit";

const LETTERS: [string, string, string][] = [
  ["Α α", "ἄλφα", "a"],
  ["Β β", "βῆτα", "b"],
  ["Γ γ", "γάμμα", "g"],
  ["Δ δ", "δέλτα", "d"],
  ["Ε ε", "ἒ ψιλόν", "e"],
  ["Ζ ζ", "ζῆτα", "zd"],
  ["Η η", "ἦτα", "ɛː"],
  ["Θ θ", "θῆτα", "tʰ"],
  ["Ι ι", "ἰῶτα", "i"],
  ["Κ κ", "κάππα", "k"],
  ["Λ λ", "λάμβδα", "l"],
  ["Μ μ", "μῦ", "m"],
  ["Ν ν", "νῦ", "n"],
  ["Ξ ξ", "ξῖ", "ks"],
  ["Ο ο", "ὂ μικρόν", "o"],
  ["Π π", "πῖ", "p"],
  ["Ρ ρ", "ῥῶ", "r"],
  ["Σ σ ς", "σίγμα", "s"],
  ["Τ τ", "ταῦ", "t"],
  ["Υ υ", "ὖ ψιλόν", "y"],
  ["Φ φ", "φῖ", "pʰ"],
  ["Χ χ", "χῖ", "kʰ"],
  ["Ψ ψ", "ψῖ", "ps"],
  ["Ω ω", "ὦ μέγα", "ɔː"],
];

export function AlphabetChart() {
  const cw = 104;
  const ch = 146;
  const x0 = 8;
  const y0 = 8;
  return (
    <Svg w={640} h={600}>
      {LETTERS.map(([glyph, name, sound], i) => {
        const col = i % 6;
        const row = Math.floor(i / 6);
        const x = x0 + col * (cw + 0.8);
        const y = y0 + row * ch;
        return (
          <g key={name}>
            <Box x={x + 3} y={y + 3} w={cw - 6} h={ch - 10} r={10} fill={i % 2 ? C.card : C.wash} stroke={C.line} />
            <G x={x + cw / 2} y={y + 58} size={glyph.length > 3 ? 30 : 36}>{glyph}</G>
            <G x={x + cw / 2} y={y + 94} size={name.length > 5 ? 17 : 19} fill={C.accent}>{name}</G>
            <E x={x + cw / 2} y={y + 122} size={16}>/{sound}/</E>
          </g>
        );
      })}
    </Svg>
  );
}

export function CaseMap() {
  return (
    <Svg w={640} h={400}>
      {/* the sentence */}
      <E x={110} y={34} weight={600} fill={C.accent}>subject</E>
      <E x={320} y={34} weight={600} fill={C.accent}>verb</E>
      <E x={530} y={34} weight={600} fill={C.accent}>object</E>
      <Box x={20} y={48} w={180} h={62} fill={C.wash} stroke={C.sage} />
      <Box x={250} y={48} w={140} h={62} />
      <Box x={440} y={48} w={180} h={62} fill={C.wash} stroke={C.sage} />
      <G x={110} y={87} size={26}>ὁ Λάβρ<H>ος</H></G>
      <G x={320} y={87} size={26}>λαμβάνει</G>
      <G x={530} y={87} size={26}>τὸν ἄρτ<H>ον</H></G>
      <Arrow x1={202} y1={79} x2={246} y2={79} />
      <Arrow x1={392} y1={79} x2={436} y2={79} />
      <E x={110} y={134}>nominative -ος</E>
      <E x={530} y={134}>accusative -ον</E>

      {/* free word order */}
      <G x={320} y={186} size={22}>
        τὸν ἄρτ<H>ον</H> ὁ Λάβρ<H>ος</H> λαμβάνει.
      </G>
      <E x={320} y={212}>Any order: the endings tell you who does what.</E>

      {/* the four cases */}
      <line x1={20} y1={236} x2={620} y2={236} stroke={C.line} strokeWidth={1.5} />
      {[
        ["ὁ λίθ", "ος", "nominative", "subject"],
        ["τοῦ λίθ", "ου", "genitive", "“of”"],
        ["τῷ λίθ", "ῳ", "dative", "after ἐν"],
        ["τὸν λίθ", "ον", "accusative", "object"],
      ].map(([stem, end, name, use], i) => {
        const x = 20 + i * 152;
        return (
          <g key={name}>
            <Box x={x} y={254} w={144} h={128} />
            <G x={x + 72} y={298} size={23}>
              {stem}
              <H>{end}</H>
            </G>
            <E x={x + 72} y={332} fill={C.ink} weight={600}>{name}</E>
            <E x={x + 72} y={358}>{use}</E>
          </g>
        );
      })}
    </Svg>
  );
}

export function EnEisEk() {
  return (
    <Svg w={640} h={400}>
      <line x1={20} y1={270} x2={620} y2={270} stroke={C.strong} strokeWidth={1.5} />
      <House x={235} y={270} w={170} h={170} />
      {/* ἐν: rest inside */}
      <circle cx={320} cy={185} r={9} fill={C.accent} />
      {/* εἰς: into */}
      <Curve x1={40} y1={150} cx={200} cy={130} x2={300} y2={228} />
      {/* ἐκ: out of */}
      <Curve x1={340} y1={228} cx={440} cy={130} x2={600} y2={150} />

      <G x={80} y={116} size={26} weight={600} fill={C.accent}>εἰς</G>
      <G x={320} y={80} size={26} weight={600} fill={C.accent}>ἐν</G>
      <G x={560} y={116} size={26} weight={600} fill={C.accent}>ἐκ</G>

      {[
        { x: 110, grc: <>εἰς τὴν οἰκί<H>αν</H></>, en: "into the house", cs: "+ accusative" },
        { x: 320, grc: <>ἐν τῇ οἰκί<H>ᾳ</H></>, en: "in the house", cs: "+ dative" },
        { x: 530, grc: <>ἐκ τῆς οἰκί<H>ας</H></>, en: "out of the house", cs: "+ genitive" },
      ].map((c) => (
        <g key={c.en}>
          <G x={c.x} y={312} size={22}>{c.grc}</G>
          <E x={c.x} y={340} fill={C.ink}>{c.en}</E>
          <E x={c.x} y={366}>{c.cs}</E>
        </g>
      ))}
    </Svg>
  );
}
