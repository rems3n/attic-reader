/**
 * Drawing kit for the course diagrams: one canvas, text in the two course
 * faces, boxes, arrows and a few recurring figures. Colours are the theme's
 * CSS variables only, so a diagram follows the page theme.
 */

import type { ReactNode } from "react";

export const C = {
  ink: "var(--ink)",
  muted: "var(--muted)",
  paper: "var(--paper)",
  card: "var(--card)",
  cream: "var(--cream)",
  line: "var(--line)",
  strong: "var(--line-strong)",
  accent: "var(--accent)",
  wash: "var(--accent-2)",
  sage: "var(--sage)",
  hl: "var(--hl)",
};

const SERIF = { fontFamily: "var(--serif)" };
const SANS = { fontFamily: "var(--sans)" };

type Anchor = "start" | "middle" | "end";

export function Svg({ w = 640, h = 400, children }: { w?: number; h?: number; children: ReactNode }) {
  return (
    <svg viewBox={`0 0 ${w} ${h}`} xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
      {children}
    </svg>
  );
}

/** Greek text (serif). */
export function G({ x, y, size = 22, anchor = "middle", fill = C.ink, weight, italic, children }: { x: number; y: number; size?: number; anchor?: Anchor; fill?: string; weight?: number; italic?: boolean; children: ReactNode }) {
  return (
    <text x={x} y={y} textAnchor={anchor} fontSize={size} fill={fill} fontWeight={weight} fontStyle={italic ? "italic" : undefined} style={SERIF} lang="grc">
      {children}
    </text>
  );
}

/** English label (sans). */
export function E({ x, y, size = 16, anchor = "middle", fill = C.muted, weight, italic, children }: { x: number; y: number; size?: number; anchor?: Anchor; fill?: string; weight?: number; italic?: boolean; children: ReactNode }) {
  return (
    <text x={x} y={y} textAnchor={anchor} fontSize={size} fill={fill} fontWeight={weight} fontStyle={italic ? "italic" : undefined} style={SANS}>
      {children}
    </text>
  );
}

/** Highlighted part of a Greek word (an ending, an augment). */
export function H({ children, fill = C.accent }: { children: ReactNode; fill?: string }) {
  return (
    <tspan fill={fill} fontWeight={600}>
      {children}
    </tspan>
  );
}

/** Dimmed part of a word. */
export function D({ children }: { children: ReactNode }) {
  return <tspan fill={C.muted}>{children}</tspan>;
}

export function Box({ x, y, w, h, r = 10, fill = C.card, stroke = C.strong, sw = 1.5, dash }: { x: number; y: number; w: number; h: number; r?: number; fill?: string; stroke?: string; sw?: number; dash?: string }) {
  return <rect x={x} y={y} width={w} height={h} rx={r} ry={r} fill={fill} stroke={stroke} strokeWidth={sw} strokeDasharray={dash} />;
}

function head(x: number, y: number, angle: number, size: number, color: string) {
  const bx = x - size * Math.cos(angle);
  const by = y - size * Math.sin(angle);
  const px = size * 0.5 * Math.sin(angle);
  const py = -size * 0.5 * Math.cos(angle);
  const pts = [
    [x, y],
    [bx + px, by + py],
    [bx - px, by - py],
  ]
    .map(([a, b]) => `${round(a)},${round(b)}`)
    .join(" ");
  return <polygon points={pts} fill={color} />;
}

function round(n: number) {
  return Math.round(n * 10) / 10;
}

/** A straight arrow from (x1,y1) to (x2,y2); `both` puts a head on each end. */
export function Arrow({ x1, y1, x2, y2, color = C.accent, sw = 2, size = 11, dash, both }: { x1: number; y1: number; x2: number; y2: number; color?: string; sw?: number; size?: number; dash?: string; both?: boolean }) {
  const a = Math.atan2(y2 - y1, x2 - x1);
  const ex = x2 - (size * 0.8) * Math.cos(a);
  const ey = y2 - (size * 0.8) * Math.sin(a);
  const sx = both ? x1 + size * 0.8 * Math.cos(a) : x1;
  const sy = both ? y1 + size * 0.8 * Math.sin(a) : y1;
  return (
    <g>
      <line x1={round(sx)} y1={round(sy)} x2={round(ex)} y2={round(ey)} stroke={color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={dash} />
      {head(x2, y2, a, size, color)}
      {both && head(x1, y1, a + Math.PI, size, color)}
    </g>
  );
}

/** A quadratic curved arrow from (x1,y1) through control (cx,cy) to (x2,y2). */
export function Curve({ x1, y1, cx, cy, x2, y2, color = C.accent, sw = 2, size = 11, dash, noHead }: { x1: number; y1: number; cx: number; cy: number; x2: number; y2: number; color?: string; sw?: number; size?: number; dash?: string; noHead?: boolean }) {
  const a = Math.atan2(y2 - cy, x2 - cx);
  const ex = noHead ? x2 : x2 - size * 0.8 * Math.cos(a);
  const ey = noHead ? y2 : y2 - size * 0.8 * Math.sin(a);
  return (
    <g>
      <path d={`M${x1} ${y1} Q${cx} ${cy} ${round(ex)} ${round(ey)}`} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={dash} />
      {!noHead && head(x2, y2, a, size, color)}
    </g>
  );
}

/** A polyline arrow through the given points. */
export function Path({ pts, color = C.accent, sw = 2, size = 11, dash, noHead }: { pts: [number, number][]; color?: string; sw?: number; size?: number; dash?: string; noHead?: boolean }) {
  const n = pts.length;
  const [px, py] = pts[n - 2];
  const [x2, y2] = pts[n - 1];
  const a = Math.atan2(y2 - py, x2 - px);
  const last: [number, number] = noHead ? [x2, y2] : [x2 - size * 0.8 * Math.cos(a), y2 - size * 0.8 * Math.sin(a)];
  const all = [...pts.slice(0, -1), last];
  return (
    <g>
      <polyline points={all.map(([a1, b1]) => `${round(a1)},${round(b1)}`).join(" ")} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={dash} />
      {!noHead && head(x2, y2, a, size, color)}
    </g>
  );
}

/** A little standing figure (head + body), feet at (x, y). */
export function Person({ x, y, s = 1, fill = C.sage, stroke = C.accent }: { x: number; y: number; s?: number; fill?: string; stroke?: string }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <circle cx={0} cy={-62} r={11} fill={fill} stroke={stroke} strokeWidth={1.5 / s} />
      <path d="M-16 0 L-12 -36 Q0 -48 12 -36 L16 0 Z" fill={fill} stroke={stroke} strokeWidth={1.5 / s} strokeLinejoin="round" />
    </g>
  );
}

/** A small house with a door, ground line at y. */
export function House({ x, y, w = 150, h = 110 }: { x: number; y: number; w?: number; h?: number }) {
  const roof = h * 0.42;
  const wall = h - roof;
  const dw = w * 0.2;
  return (
    <g>
      <path d={`M${x - 8} ${y - wall} L${x + w / 2} ${y - h} L${x + w + 8} ${y - wall} Z`} fill={C.cream} stroke={C.strong} strokeWidth={1.5} strokeLinejoin="round" />
      <rect x={x} y={y - wall} width={w} height={wall} fill={C.card} stroke={C.strong} strokeWidth={1.5} />
      <rect x={x + w / 2 - dw / 2} y={y - wall * 0.62} width={dw} height={wall * 0.62} rx={3} fill={C.cream} stroke={C.strong} strokeWidth={1.5} />
    </g>
  );
}

/** A compass mark "N" with an arrow pointing up. */
export function North({ x, y }: { x: number; y: number }) {
  return (
    <g>
      <Arrow x1={x} y1={y + 26} x2={x} y2={y - 4} color={C.muted} sw={1.5} size={9} />
      <E x={x} y={y + 46} size={16} fill={C.muted} weight={600}>N</E>
    </g>
  );
}

/** A row of text chips: rounded boxes with centred Greek text. */
export function Chip({ x, y, w, h = 40, fill = C.card, stroke = C.strong, children, size = 20, dash }: { x: number; y: number; w: number; h?: number; fill?: string; stroke?: string; children: ReactNode; size?: number; dash?: string }) {
  return (
    <g>
      <Box x={x} y={y} w={w} h={h} r={9} fill={fill} stroke={stroke} dash={dash} />
      <G x={x + w / 2} y={y + h / 2 + size * 0.35} size={size}>
        {children}
      </G>
    </g>
  );
}

/** Rough rendered width of a Greek string in the serif face (for boxes around words). */
export function tw(text: string, size: number) {
  return [...text.normalize("NFC")].reduce((w, ch) => w + (ch === " " ? 0.28 : /[Α-ΩἈ-Ὧ]/.test(ch) ? 0.68 : /[ιίὶἰἱῖ]/.test(ch) ? 0.3 : 0.54), 0) * size;
}
