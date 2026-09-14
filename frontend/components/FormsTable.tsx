"use client";

import type { AdjTable, Forms, NounTable, VerbForms, VerbTable } from "../lib/api";

const CASE_LABEL: Record<string, string> = { nom: "nom.", gen: "gen.", dat: "dat.", acc: "acc.", voc: "voc." };
const GENDER_LABEL: Record<string, string> = { m: "masc.", f: "fem.", n: "neut.", mf: "masc./fem.", "1st person": "", "2nd person": "" };
const PERSON_LABEL: Record<string, string> = { "1sg": "1 sg.", "2sg": "2 sg.", "3sg": "3 sg.", "1pl": "1 pl.", "2pl": "2 pl.", "3pl": "3 pl.", inf: "inf.", m: "masc.", f: "fem.", n: "neut.", mg: "gen." };

type Props = { forms: Forms; play?: (text: string) => void; compact?: boolean };

function Cell({ forms, play }: { forms: string[]; play?: (t: string) => void }) {
  if (!forms || forms.length === 0) return <span className="formEmpty">—</span>;
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

function NounView({ t, play }: { t: NounTable; play?: (s: string) => void }) {
  const cases = ["nom", "gen", "dat", "acc", "voc"];
  const get = (c: string, n: string) => t.cells.find((x) => x.case === c && x.number === n)?.forms ?? [];
  return (
    <div className="tableWrap">
      <table className="formsTable">
        <thead>
          <tr>
            <th />
            <th>singular</th>
            <th>plural</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c}>
              <th>{CASE_LABEL[c]}</th>
              <td><Cell forms={get(c, "sg")} play={play} /></td>
              <td><Cell forms={get(c, "pl")} play={play} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      {t.note && <p className="tableNote">{t.note}</p>}
    </div>
  );
}

function AdjView({ t, play }: { t: AdjTable; play?: (s: string) => void }) {
  const cases = ["nom", "gen", "dat", "acc", "voc"];
  const numbers = ["sg", "pl"].filter((n) => t.cells.some((c) => c.number === n && Object.values(c.forms).some((f) => f.length)));
  const get = (c: string, n: string, g: string) => t.cells.find((x) => x.case === c && x.number === n)?.forms[g] ?? [];
  return (
    <div className="tableWrap">
      {numbers.map((n) => (
        <table className="formsTable" key={n}>
          <thead>
            <tr>
              <th>{n === "sg" ? "singular" : "plural"}</th>
              {t.genders.map((g) => (
                <th key={g}>{GENDER_LABEL[g] ?? g}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cases
              .filter((c) => t.genders.some((g) => get(c, n, g).length))
              .map((c) => (
                <tr key={c}>
                  <th>{CASE_LABEL[c]}</th>
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

function FiniteGrid({ table, play }: { table: VerbTable; play?: (s: string) => void }) {
  const tags = ["1sg", "2sg", "3sg", "1pl", "2pl", "3pl"];
  const by = Object.fromEntries(table.cells.map((c) => [c.tag, c.forms]));
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

function VerbView({ t, play, compact }: { t: VerbForms; play?: (s: string) => void; compact?: boolean }) {
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
                  <FiniteGrid key={i} table={tb} play={play} />
                ))}
              </div>
            ))}
          </details>
        );
      })}
    </div>
  );
}

export default function FormsTable({ forms, play, compact }: Props) {
  if (forms.kind === "verb") return <VerbView t={forms} play={play} compact={compact} />;
  if (forms.kind === "noun") return <NounView t={forms} play={play} />;
  return <AdjView t={forms} play={play} />;
}
