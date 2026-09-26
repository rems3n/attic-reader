"use client";

import { useState } from "react";
import type { AdjTable, Forms, NounTable, VerbForms, VerbTable } from "../lib/api";

// The engine returns dual forms in a separate `dual` block of each table
// (cells with number "du"; verb cells tagged 2du/3du). They stay hidden
// unless the reader turns them on.
type NounCell = NounTable["cells"][number];
type AdjCell = AdjTable["cells"][number];
type VerbCellT = VerbTable["cells"][number];
type WithDual<T, C> = T & { dual?: C[] };

const CASE_LABEL: Record<string, string> = { nom: "nom.", gen: "gen.", dat: "dat.", acc: "acc.", voc: "voc." };
const GENDER_LABEL: Record<string, string> = { m: "masc.", f: "fem.", n: "neut.", mf: "masc./fem.", "1st person": "", "2nd person": "" };
const PERSON_LABEL: Record<string, string> = {
  "1sg": "1 sg.", "2sg": "2 sg.", "3sg": "3 sg.", "1pl": "1 pl.", "2pl": "2 pl.", "3pl": "3 pl.", "2du": "2 du.", "3du": "3 du.",
  inf: "inf.", m: "masc.", f: "fem.", n: "neut.", mg: "gen.", tos: "-τός", teos: "-τέος",
};

type Props = { forms: Forms; play?: (text: string) => void; compact?: boolean };

function Cell({ forms, play }: { forms: string[]; play?: (t: string) => void }) {
  if (!forms || forms.length === 0) return <span className="formEmpty"><span aria-hidden="true">—</span><span className="srOnly">none</span></span>;
  return (
    <span className="formCell">
      {forms.map((f, i) => (
        <button key={i} type="button" className="formButton" onClick={() => play?.(f)} title="Play">
          {f}
        </button>
      ))}
    </span>
  );
}

function DualToggle({ on, set }: { on: boolean; set: (v: boolean) => void }) {
  return (
    <label className="tableNote dualToggle">
      <input type="checkbox" checked={on} onChange={(e) => set(e.target.checked)} /> show dual
    </label>
  );
}

function NounView({ t, play, dual }: { t: WithDual<NounTable, NounCell>; play?: (s: string) => void; dual: boolean }) {
  const cases = ["nom", "gen", "dat", "acc", "voc"];
  const cells = [...t.cells, ...(dual ? t.dual ?? [] : [])];
  const get = (c: string, n: string) => cells.find((x) => x.case === c && x.number === n)?.forms ?? [];
  const showDual = dual && (t.dual ?? []).some((c) => c.forms.length);
  return (
    <div className="tableWrap">
      <table className="formsTable">
        <thead>
          <tr>
            <th><span className="srOnly">case</span></th>
            <th scope="col">singular</th>
            <th scope="col">plural</th>
            {showDual && <th scope="col">dual</th>}
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c}>
              <th scope="row">{CASE_LABEL[c]}</th>
              <td><Cell forms={get(c, "sg")} play={play} /></td>
              <td><Cell forms={get(c, "pl")} play={play} /></td>
              {showDual && <td><Cell forms={get(c, "du")} play={play} /></td>}
            </tr>
          ))}
        </tbody>
      </table>
      {t.note && <p className="tableNote">{t.note}</p>}
    </div>
  );
}

function AdjView({ t, play, dual }: { t: WithDual<AdjTable, AdjCell>; play?: (s: string) => void; dual: boolean }) {
  const cases = ["nom", "gen", "dat", "acc", "voc"];
  const cells = [...t.cells, ...(dual ? t.dual ?? [] : [])];
  const numbers = ["sg", "pl", "du"].filter((n) => cells.some((c) => c.number === n && Object.values(c.forms).some((f) => f.length)));
  const get = (c: string, n: string, g: string) => cells.find((x) => x.case === c && x.number === n)?.forms[g] ?? [];
  return (
    <div className="tableWrap">
      {numbers.map((n) => (
        <table className="formsTable" key={n}>
          <thead>
            <tr>
              <th>{n === "sg" ? "singular" : n === "pl" ? "plural" : "dual"}</th>
              {t.genders.map((g) => (
                <th key={g} scope="col">{GENDER_LABEL[g] || <span className="srOnly">{g}</span>}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cases
              .filter((c) => t.genders.some((g) => get(c, n, g).length))
              .map((c) => (
                <tr key={c}>
                  <th scope="row">{CASE_LABEL[c]}</th>
                  {t.genders.map((g) => (
                    <td key={g}><Cell forms={get(c, n, g)} play={play} /></td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      ))}
      {t.comparison && (
        <p className="tableNote">
          Comparative <b>{t.comparison.comparative.join(", ")}</b>; superlative <b>{t.comparison.superlative.join(", ")}</b>
          {t.comparison.regular ? "" : " (irregular)"}.
        </p>
      )}
      {t.adverb && t.adverb.length > 0 && <p className="tableNote">Adverb <b>{t.adverb.join(", ")}</b>.</p>}
      {t.note && <p className="tableNote">{t.note}</p>}
    </div>
  );
}

function FiniteGrid({ table, play, dual }: { table: WithDual<VerbTable, VerbCellT>; play?: (s: string) => void; dual: boolean }) {
  const tags = ["1sg", "2sg", "3sg", "1pl", "2pl", "3pl", ...(dual ? ["2du", "3du"] : [])];
  const by = Object.fromEntries([...table.cells, ...(dual ? table.dual ?? [] : [])].map((c) => [c.tag, c.forms]));
  const finite = tags.some((t) => by[t]);
  return (
    <div className="moodBlock">
      <h5>{table.mood}{table.note && <span className="moodNote"> · {table.note}</span>}</h5>
      {finite ? (
        <div className="personGrid">
          {tags.map((t) =>
            by[t] ? (
              <div key={t} className="personRow">
                <span className="personLabel">{PERSON_LABEL[t]}</span>
                <Cell forms={by[t]} play={play} />
              </div>
            ) : null,
          )}
        </div>
      ) : (
        <div className="personGrid">
          {table.cells.map((c) => (
            <div key={c.tag} className="personRow">
              <span className="personLabel">{PERSON_LABEL[c.tag] ?? c.tag}</span>
              <Cell forms={c.forms} play={play} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function VerbView({ t, play, compact, dual }: { t: VerbForms; play?: (s: string) => void; compact?: boolean; dual: boolean }) {
  return (
    <div className="verbForms">
      {t.principal_parts.length > 0 && (
        <p className="principalParts">
          {t.principal_parts.map((p) => (
            <span key={p.slot} className="ppart">
              <span className="ppslot">{p.slot}</span> <Cell forms={p.forms} play={play} />
            </span>
          ))}
        </p>
      )}
      {t.notes.filter(Boolean).map((n, i) => (
        <p key={i} className="tableNote">{n}</p>
      ))}
      {t.systems.map((s, si) => {
        const groups = new Map<string, VerbTable[]>();
        for (const tb of s.tables) {
          const key = `${tb.tense} · ${tb.voice}`;
          groups.set(key, [...(groups.get(key) ?? []), tb]);
        }
        return (
          <details key={s.id} className="verbSystem" open={!compact && si === 0}>
            <summary>{s.label}</summary>
            {[...groups.entries()].map(([key, tables]) => (
              <div key={key} className="tenseVoice">
                <h4>{key}</h4>
                {tables.map((tb, i) => (
                  <FiniteGrid key={i} table={tb} play={play} dual={dual} />
                ))}
              </div>
            ))}
          </details>
        );
      })}
    </div>
  );
}

function hasDual(forms: Forms): boolean {
  if (forms.kind === "verb") return forms.systems.some((s) => s.tables.some((tb) => ((tb as WithDual<VerbTable, VerbCellT>).dual ?? []).length > 0));
  return ((forms as { dual?: unknown[] }).dual ?? []).length > 0;
}

export default function FormsTable({ forms, play, compact }: Props) {
  const [dual, setDual] = useState(false);
  const toggle = hasDual(forms) ? <DualToggle on={dual} set={setDual} /> : null;
  let view;
  if (forms.kind === "verb") view = <VerbView t={forms} play={play} compact={compact} dual={dual} />;
  else if (forms.kind === "noun") view = <NounView t={forms} play={play} dual={dual} />;
  else view = <AdjView t={forms} play={play} dual={dual} />;
  return (
    <>
      {toggle}
      {view}
    </>
  );
}
