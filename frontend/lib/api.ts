const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? JSON.stringify(body);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await getError(response));
  return response.json() as Promise<T>;
}

export type TtsProvider = {
  id: string;
  name: string;
  quality: "neural" | "robotic" | string;
  available: boolean;
  enabled: boolean;
  note: string;
};

export type SentenceSpan = {
  index: number;
  text: string;
  start: number;
  end: number;
};

export type SentenceClip = SentenceSpan & {
  ipa: string;
  audio_base64: string | null;
  mime_type: string;
  duration_seconds: number | null;
};

export type BatchSynthesis = {
  provider: string;
  normalized_text: string;
  speed: number;
  sentences: SentenceClip[];
};

export type OcrReport = {
  width: number;
  height: number;
  scale: number;
  skew_degrees: number;
  deskewed: boolean;
  engine: string;
  mode?: "lines" | "page";
  lines?: number;
};

export async function runOcr(file: File): Promise<{ text: string; report: OcrReport | null }> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/api/ocr`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await getError(response));
  const body = await response.json();
  return { text: body.text, report: body.preprocess ?? null };
}

export function phonemize(text: string): Promise<{ normalized_text: string; ipa: string }> {
  return postJson("/api/phonemize", { text });
}

export async function segment(text: string): Promise<SentenceSpan[]> {
  const body = await postJson<{ sentences: SentenceSpan[] }>("/api/segment", { text });
  return body.sentences;
}

export async function getTtsStatus(): Promise<TtsProvider[]> {
  const response = await fetch(`${API_BASE}/api/tts/status`, { cache: "no-store" });
  if (!response.ok) throw new Error(await getError(response));
  const body = await response.json();
  return body.providers ?? [];
}

export async function synthesize(text: string, speed = 1): Promise<{ audio: Blob; provider: string }> {
  const response = await fetch(`${API_BASE}/api/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, speed }),
  });
  if (!response.ok) throw new Error(await getError(response));
  return {
    audio: await response.blob(),
    provider: response.headers.get("X-TTS-Provider") ?? "unknown",
  };
}

/** One clip per sentence. `speed` is a learner multiplier on the default pace. */
export function synthesizeBatch(text: string, speed = 1): Promise<BatchSynthesis> {
  return postJson("/api/synthesize/batch", { text, speed });
}

export type StreamStart = {
  type: "start";
  provider: string;
  normalized_text: string;
  speed: number;
  sentences: (SentenceSpan & { ipa: string })[];
};
export type WordTiming = { start: number; end: number; t0: number; t1: number };
export type StreamClip = {
  type: "clip";
  index: number;
  audio_base64: string | null;
  mime_type: string;
  duration_seconds: number | null;
  words?: WordTiming[] | null;
};
export type StreamEvent =
  | StreamStart
  | StreamClip
  | { type: "done"; elapsed_seconds: number }
  | { type: "error"; detail: string };

/**
 * Streamed synthesis: the server sends one NDJSON line per event, so the first
 * sentence is playable within seconds and long paragraphs never trip mobile
 * browsers' ~60 s request timeouts. Falls back to reading the whole body when
 * the browser cannot stream a response.
 */
export async function synthesizeStream(
  text: string,
  speed: number,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/synthesize/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, speed }),
    signal,
  });
  if (!response.ok) throw new Error(await getError(response));

  const decoder = new TextDecoder();
  let buffer = "";
  const handleChunk = (chunk: string, flush = false) => {
    buffer += chunk;
    const lines = buffer.split("\n");
    buffer = flush ? "" : (lines.pop() ?? "");
    for (const line of lines) {
      if (!line.trim()) continue;
      onEvent(JSON.parse(line) as StreamEvent);
    }
  };

  if (!response.body) {
    handleChunk(await response.text(), true);
    return;
  }
  const reader = response.body.getReader();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    handleChunk(decoder.decode(value, { stream: true }));
  }
  handleChunk(decoder.decode(), true);
}

/** Decode a base64 WAV into an object URL usable by a single <audio> element. */
export function base64ToObjectUrl(base64: string, mimeType = "audio/wav"): string {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return URL.createObjectURL(new Blob([bytes], { type: mimeType }));
}

export type LibraryCategory = { id: string; label: string };
export type LibraryItem = {
  id: string;
  category: string;
  level: "beginner" | "intermediate" | "advanced" | string;
  title: string;
  author: string;
  work: string;
  ref: string;
  blurb: string;
  dialect: string;
  sentence_count: number;
  estimated_seconds: number;
  ready_speeds: number[];
  source: { edition: string; urn: string; license: string; url: string };
};
export type LibraryIndex = {
  categories: LibraryCategory[];
  items: LibraryItem[];
  prerender: { state: string; rendered: number; total: number };
};

export async function getLibrary(): Promise<LibraryIndex> {
  const response = await fetch(`${API_BASE}/api/library`, { cache: "no-store" });
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

export async function getLibraryItem(id: string): Promise<LibraryItem & { text: string; sentences: string[] }> {
  const response = await fetch(`${API_BASE}/api/library/${encodeURIComponent(id)}`);
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

// ---------------------------------------------------------------------------
// Vocabulary, grammar, word audio, progress sync
// ---------------------------------------------------------------------------

export type Facet = { id: string | number; label: string; count: number; ranks?: string };
export type VocabItem = {
  id: string;
  rank: number;
  lemma: string;
  headword: string;
  short: string;
  kind: string;
  subclass: string;
  pos: string;
  group: string;
  tier: number;
  level: string;
  topics: string[];
  tags: string[];
  cognates: { derivatives?: string[]; cognates?: string[] } | null;
  readings: string[];
};
export type VocabIndex = {
  attribution: string;
  attribution_url: string;
  facets: { topics: Facet[]; tags: Facet[]; groups: Facet[]; kinds: Facet[]; pos: Facet[]; tiers: Facet[]; readings: Facet[] };
  items: VocabItem[];
};
export type NounTable = {
  kind: "noun";
  lemma: string;
  gender: string;
  declension?: string;
  note?: string;
  cells: { case: string; number: string; forms: string[] }[];
};
export type AdjTable = {
  kind: "adjective" | "pronoun" | "article";
  lemma: string;
  genders: string[];
  note?: string;
  cells: { case: string; number: string; forms: Record<string, string[]> }[];
  comparison?: { comparative: string[]; superlative: string[]; regular: boolean } | null;
  adverb?: string[];
};
export type VerbCell = { tag: string; forms: string[] };
export type VerbTable = { tense: string; voice: string; mood: string; cells: VerbCell[]; note?: string };
export type VerbForms = {
  kind: "verb";
  lemma: string;
  class: string;
  principal_parts: { slot: string; forms: string[] }[];
  notes: string[];
  systems: { id: string; label: string; tables: VerbTable[] }[];
};
export type Forms = NounTable | AdjTable | VerbForms;
export type Example = {
  reading: string;
  title: string;
  author: string;
  category: string;
  sentence: number;
  text: string;
  form: string;
};
export type VocabEntry = VocabItem & {
  definition: string;
  dcc_headword: string | null;
  notes: string | null;
  morph: Record<string, unknown>;
  ipa: string;
  dcc_url: string;
  forms: Forms | null;
  examples: Example[];
};

export async function getVocab(): Promise<VocabIndex> {
  const response = await fetch(`${API_BASE}/api/vocab`);
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

export async function getVocabEntry(id: string): Promise<VocabEntry> {
  const response = await fetch(`${API_BASE}/api/vocab/${encodeURIComponent(id)}`);
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

export type GrammarSection = { id: string; title: string; blurb: string; items: { id: string; title: string; lemma: string }[] };
export type GrammarItem = {
  id: string;
  section: string;
  title: string;
  lemma: string;
  kind: string;
  explanation: string;
  examples: { greek: string; english: string }[];
  table: Forms | null;
};

export async function getGrammar(): Promise<{ sections: GrammarSection[] }> {
  const response = await fetch(`${API_BASE}/api/grammar`);
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

export async function getGrammarItem(id: string): Promise<GrammarItem> {
  const response = await fetch(`${API_BASE}/api/grammar/${encodeURIComponent(id)}`);
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

const speakCache = new Map<string, string>();

/** Audio for a single word or phrase, as an object URL (cached per page). */
export async function speak(text: string, speed = 0.75): Promise<string> {
  const key = `${speed}|${text}`;
  const hit = speakCache.get(key);
  if (hit) return hit;
  const response = await fetch(`${API_BASE}/api/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, speed }),
  });
  if (!response.ok) throw new Error(await getError(response));
  const url = URL.createObjectURL(await response.blob());
  speakCache.set(key, url);
  return url;
}

export async function pushProgress(code: string, document: unknown): Promise<{ saved_at: number; bytes: number }> {
  const response = await fetch(`${API_BASE}/api/progress/${encodeURIComponent(code)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(document),
  });
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

export async function pullProgress<T>(code: string): Promise<{ saved_at: number; document: T } | null> {
  const response = await fetch(`${API_BASE}/api/progress/${encodeURIComponent(code)}`, { cache: "no-store" });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}
