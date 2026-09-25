"use client";

import { Fragment, type ReactNode } from "react";

/**
 * A tiny renderer for the grammar and culture notes: paragraphs, **bold**,
 * *italic*, numbered/bulleted lists and pipe tables. No HTML passthrough.
 */
export default function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n\s*\n/);
  return (
    <div className="md">
      {blocks.map((block, i) => {
        const lines = block.split("\n").filter((l) => l.trim().length);
        if (!lines.length) return null;
        if (lines.every((l) => l.trim().startsWith("|"))) return <Table key={i} lines={lines} />;
        if (lines.every((l) => /^\s*(\d+\.|[-*])\s/.test(l))) {
          const ordered = /^\s*\d+\./.test(lines[0]);
          const items = lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*(\d+\.|[-*])\s/, ""))}</li>);
          return ordered ? <ol key={i}>{items}</ol> : <ul key={i}>{items}</ul>;
        }
        return <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}{inline(l)}</Fragment>)}</p>;
      })}
    </div>
  );
}

function Table({ lines }: { lines: string[] }) {
  const rows = lines.map((l) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
  const body = rows.filter((r) => !r.every((c) => /^:?-+:?$/.test(c)));
  const [head, ...rest] = body;
  return (
    <div className="tableWrap">
      <table className="mdTable">
        <thead><tr>{head.map((c, i) => <th key={i}>{inline(c)}</th>)}</tr></thead>
        <tbody>{rest.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{inline(c)}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

function inline(s: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(greekify(s.slice(last, m.index), k++));
    const t = m[0];
    if (t.startsWith("**")) out.push(<strong key={k++}>{greekify(t.slice(2, -2), 0)}</strong>);
    else out.push(<em key={k++}>{greekify(t.slice(1, -1), 0)}</em>);
    last = m.index + t.length;
  }
  if (last < s.length) out.push(greekify(s.slice(last), k++));
  return out;
}

/** Wrap runs of Greek in a lang="grc" span so the serif Greek font applies. */
function greekify(s: string, key: number): ReactNode {
  const parts = s.split(/([Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿\s·,;.’'()]*[Ͱ-Ͽἀ-῿]|[Ͱ-Ͽἀ-῿])/);
  if (parts.length === 1) return s;
  return <Fragment key={key}>{parts.map((p, i) => (i % 2 === 1 ? <span key={i} lang="grc" className="grc">{p}</span> : p))}</Fragment>;
}
