"use client";

import { useState } from "react";

/**
 * A text input for polytonic Greek. Users have a Greek keyboard; the helper
 * row covers the marks that are awkward on some layouts. Input is stored as
 * typed and normalized only when graded.
 */
const HELPERS = ["ᾳ", "ῃ", "ῳ", "ᾷ", "ῇ", "ῷ", "ἀ", "ἁ", "ἐ", "ἑ", "ἠ", "ἡ", "ἰ", "ἱ", "ὀ", "ὁ", "ὐ", "ὑ", "ὠ", "ὡ", "ῥ", "·", ";"];

export default function GreekInput({ value, onChange, onEnter, placeholder, autoFocus, id, size = "normal", disabled, label = "Your answer in Greek" }: { value: string; onChange: (v: string) => void; onEnter?: () => void; placeholder?: string; autoFocus?: boolean; id?: string; size?: "normal" | "inline"; disabled?: boolean; /** accessible name of the input */ label?: string }) {
  const [helpers, setHelpers] = useState(false);
  return (
    <span className={`greekInputWrap ${size}`}>
      <input
        id={id}
        className={`greekAnswer ${size}`}
        lang="grc"
        type="text"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
        autoComplete="off"
        value={value}
        placeholder={placeholder}
        aria-label={label}
        autoFocus={autoFocus}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && onEnter) {
            e.preventDefault();
            onEnter();
          }
        }}
      />
      {size === "normal" && (
        <button type="button" className="helperToggle" aria-expanded={helpers} onClick={() => setHelpers(!helpers)} title="Accented letters" aria-label="Accented letters">
          <span aria-hidden="true" lang="grc">ᾷ</span>
        </button>
      )}
      {helpers && (
        <span className="helperRow" role="group" aria-label="Insert a letter">
          {HELPERS.map((h) => (
            <button key={h} type="button" className="helperKey" onClick={() => onChange(value + h)} lang="grc" aria-label={`Insert ${h}`}>
              {h}
            </button>
          ))}
        </span>
      )}
    </span>
  );
}
