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
export type StreamClip = {
  type: "clip";
  index: number;
  audio_base64: string | null;
  mime_type: string;
  duration_seconds: number | null;
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
