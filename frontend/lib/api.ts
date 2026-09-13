const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? JSON.stringify(body);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

export type TtsProvider = {
  id: string;
  name: string;
  quality: "neural" | "robotic" | string;
  available: boolean;
  enabled: boolean;
  note: string;
};

export async function runOcr(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/api/ocr`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await getError(response));
  const body = await response.json();
  return body.text;
}

export async function phonemize(text: string): Promise<{ normalized_text: string; ipa: string }> {
  const response = await fetch(`${API_BASE}/api/phonemize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error(await getError(response));
  return response.json();
}

export async function getTtsStatus(): Promise<TtsProvider[]> {
  const response = await fetch(`${API_BASE}/api/tts/status`, { cache: "no-store" });
  if (!response.ok) throw new Error(await getError(response));
  const body = await response.json();
  return body.providers ?? [];
}

export async function synthesize(text: string): Promise<{ audio: Blob; provider: string }> {
  const response = await fetch(`${API_BASE}/api/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error(await getError(response));
  return {
    audio: await response.blob(),
    provider: response.headers.get("X-TTS-Provider") ?? "unknown",
  };
}
