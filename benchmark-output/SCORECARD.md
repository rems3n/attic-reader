# Voice benchmark scorecard — 2026-09-12

First session in which neural WAVs were actually produced. 45 WAVs in this folder
(15 cases × Kokoro/bm_george, Kokoro/im_nicola, MMS-grc). `listening_sheet.html`
embeds all of them for phone listening.

Evidence sources
- Kokoro per-token predicted durations (`pred_dur`, 1 unit ≈ 12.5 ms).
- Phone recognition of every WAV with `facebook/wav2vec2-lv-60-espeak-cv-ft`
  (`phone_recognition.json`). Caveat: English-centric recogniser — it has no
  aspirated-stop labels and is unreliable on /y/. Treat as evidence, not proof.
- Nobody has *listened* yet. Final acceptance is still the user's ear.

## Provider decision

| Provider | Naturalness | Classical fidelity | Verdict |
|---|---|---|---|
| MMS `facebook/mms-tts-grc` | (unheard) | **FAIL** | Rejected. Recogniser hears Modern Greek on every case: β→ð/v, δ→ð, γ→ɣ, θ→θ, φ→f, χ→x, αυ/ευ→af/ef, η/υ/ει→i, no /h/. Not fixable from our side — the model's training data was read in Modern pronunciation. Also CC-BY-NC. |
| Kokoro raw phonemes | needs listening | **PASS (provisional)** | Primary backend. See contrast table. |

## Kokoro contrast table (bm_george unless noted)

| Contrast | Evidence | Status |
|---|---|---|
| β γ δ = /b g d/ | recogniser: `b i o s d i k aɪ o s ɡ e n o s` | PASS |
| θ φ χ aspirated | `ʰ` token gets its own ~25 ms segment; recogniser can't label aspiration | PASS on duration; confirm by ear |
| η ω long | ɔː = 8 units vs o = 5 (1.6×); recogniser hears `oː`/`eː` | PASS |
| υ = /y/ | English voices: mixed (i / u / y). im_nicola & ff_siwis: consistent `y` | PARTIAL on English voices; PASS on im_nicola |
| rough breathing /h/ | `h` present in every rough-breathing word, all English/Italian voices | PASS |
| αι οι αυ ευ | `aɪ oɪ aʊ eu` all recognised | PASS |
| γγ γκ γχ | rendered; recogniser hears `n g`/`n k` | PASS (ŋ vs n not resolvable by recogniser) |
| geminates | ll = 8 vs l = 4; pp = 9 vs p = 5; recogniser hears `a l l o s` | PASS |
| ζ = /zd/ | `b a d i z d e` | PASS |
| iota subscript ɛːi̯/ɔːi̯ | English voices insert **linking-R** ("t e r i", "d oː r i") | ISSUE — voice-dependent |
| long vowel + vowel-initial word | English voices insert linking-R (καλὴ ἐστίν → "kale-r-istin"), both British and American | ISSUE — voice-dependent |
| stress mark ˈ | normal English-style stress duration, no pathology | OK; judge prosody by ear |
| sentence coherence (Xenophon) | full clause rendered in 7.3 s, all words recovered | PASS |

## Voice sweep (8 voices on the sensitive cases)

- `im_nicola` (Italian M): /y/ consistent, /h/ present, no linking-R, pure vowels. **Top candidate.**
- `bm_george` (British M): everything except linking-R and shaky /y/. Fallback.
- `am_michael`, `am_adam`, `af_heart`, `af_bella` (American): same linking-R problem; /y/ shaky.
- `ff_siwis` (French F): perfect /y/ but renders /h/ as French /ʁ/. **Disqualified.**
- `bm_lewis`: comparable to bm_george.
- Raw voice-sweep WAVs are in `voices/`.

## Bug fixed this session

ASCII `g` (U+0067) is not in Kokoro's 114-symbol vocab; IPA `ɡ` (U+0261) is.
Every γ was being silently deleted by the model before this session. Fixed in
`prepare_kokoro_phonemes` (provider mapping layer, canonical G2P untouched) and
guarded by `unknown_kokoro_symbols()` + two new tests.

## Things tried and rejected

- Glottal stop `ʔ` between words to block linking-R → model renders it as tʃ/dʒ.
- Doubling long vowels (`ɛɛ`) instead of `ɛː` → no consistent improvement.

## Next actions

1. **User listens** to `listening_sheet.html`: im_nicola vs bm_george. This is the
   acceptance gate.
2. If im_nicola is acceptable, set `KOKORO_VOICE=im_nicola` (and consider
   `KOKORO_LANG_CODE=i` only if it changes nothing — we bypass G2P anyway).
3. If linking-R is audible and bothersome on the chosen voice, options in order:
   a. insert a short silence (~40 ms) at word boundaries after ɛː/ɔː/ɔːi̯ in
      learner mode (provider layer; not tested yet),
   b. try `ω → oː` in the provider mapping only (no merger: ου is already uː),
   c. try a `,` token at those boundaries.
4. Benchmark a female voice for the Italian path (`if_sara`) once the male voice
   is judged.
