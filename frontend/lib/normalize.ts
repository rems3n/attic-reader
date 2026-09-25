/**
 * Answer normalization for typed Greek, mirroring backend/app/course/normalize.py.
 * Tested against lib/normalize.fixtures.json, which the backend generates.
 *
 * lenient (default until Unit 4): accents, macrons, breves, iota subscript and
 * the smooth breathing are ignored; the rough breathing is kept (ὁ ≠ ὀ);
 * final sigma unified; case, spacing, surrounding punctuation ignored.
 * strict: accents, iota subscript and both breathings count; grave = acute.
 */

const ACUTE = "́";
const GRAVE = "̀";
const CIRCUMFLEX = "͂";
const MACRON = "̄";
const BREVE = "̆";
const IOTA_SUB = "ͅ";
const DIAERESIS = "̈";
const SMOOTH = "̓";

const PUNCT = /[.,;·!?:«»"“”‘’'()[\]{}—–\-…]+/g;
const GREEK = /[Ͱ-Ͽἀ-῿]/;

export function expandMovable(answer: string): string[] {
  if (!answer.includes("(ν)")) return [answer];
  return [answer.replace("(ν)", "ν"), answer.replace("(ν)", "")];
}

export function normalizeAnswer(text: string, accents = false): string {
  const s = (text || "").toLowerCase().normalize("NFD");
  let out = "";
  for (const ch of s) {
    if (ch === MACRON || ch === BREVE || ch === DIAERESIS) continue;
    if (ch === ACUTE || ch === GRAVE || ch === CIRCUMFLEX) {
      if (accents) out += ch === GRAVE ? ACUTE : ch;
      continue;
    }
    if ((ch === IOTA_SUB || ch === SMOOTH) && !accents) continue;
    out += ch;
  }
  out = out.replace(/ς/g, "σ").replace(PUNCT, " ").replace(/\s+/g, " ").trim();
  return out.normalize("NFC");
}

export function answersMatch(given: string, accepted: string[], accents = false): boolean {
  const key = normalizeAnswer(given, accents);
  if (!key) return false;
  for (const answer of accepted) {
    for (const variant of expandMovable(answer)) {
      if (normalizeAnswer(variant, accents) === key) return true;
    }
  }
  return false;
}

/** Greek word tokens of a sentence: punctuation stripped, elision mark kept. */
export function tokens(text: string): string[] {
  const strip = /^[.,;·!?:«»"“”()[\]{}—–…]+|[.,;·!?:«»"“”()[\]{}—–…]+$/g;
  return text
    .split(/\s+/)
    .map((raw) => raw.replace(strip, ""))
    .filter((tok) => tok && GREEK.test(tok));
}
