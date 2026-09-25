"use client";

import { useState } from "react";

/**
 * A text input for polytonic Greek. Users have a Greek keyboard; the helper
 * row covers the marks that are awkward on some layouts. Input is stored as
 * typed and normalized only when graded.
 */
const HELPERS = ["ᾳ", "ῃ", "ῳ", "ᾷ", "ῇ", "ῷ", "ἀ", "ἁ", "ἐ", "ἑ", "ἠ", "ἡ", "ἰ", "ἱ", "ὀ", "ὁ", "ὐ", "ὑ", "ὠ", "ὡ", "ῥ", "·", ";"];

export default function GreekInput({ value, onChange, onEnter, placeholder, autoFocus, id, size = "normal", disabled }: { value: string; onChange: (v: string) => void; onEnter?: () => void; placeholder?: string; autoFocus?: boolean; id?: string; size?: "normal" | "inline"; disabled?: boolean }) {
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
        <button type="button" className="helperToggle" aria-expanded={helpers} onClick={() => setHelpers(!helpers)} title="Accented letters">
          ᾷ
        </button>
      )}
      {helpers && (
        <span className="helperRow" role="group" aria-label="Insert a letter">
          {HELPERS.map((h) => (
            <button key={h} type="button" className="helperKey" onClick={() => onChange(value + h)} lang="grc">
              {h}
            </button>
          ))}
        </span>
      )}
    </span>
  );
}
