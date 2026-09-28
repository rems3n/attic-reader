import type { ImageRecord } from "./course";

export type CatalogImage = ImageRecord & {
  status: "completed" | "remaining";
  medium: "illustration" | "photo" | "diagram" | "pending";
  words: string[];
  collection: { id: string; label: string };
  vocabulary: { id: string; lemma: string; definition: string }[];
  usages: { source: string; id: string; title: string; location: string; context: string; href: string | null }[];
  provenance: { prompt: string; review: string; generator: string; sha256: string } | null;
  candidate: { file: string; credit: string; license: string; source_url: string | null } | null;
  pipeline_status: string;
};
export type ImageCatalog = { images: CatalogImage[]; summary: {
  total: number; completed: number; remaining: number; illustrations: number;
  photos: number; diagrams: number; unique_raster_files: number; candidates: number;
} };
export const KIND_LABELS: Record<string, string> = { dictionary: "Vocabulary", story: "Story scenes", culture: "Culture", diagram: "Diagrams" };
export const MEDIUM_LABELS = { illustration: "AI illustration", photo: "Photograph", diagram: "Diagram", pending: "Image needed" };
export function searchText(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/ς/g, "σ");
}
export function matchesSearch(image: CatalogImage, query: string): boolean {
  const haystack = searchText([image.id, image.alt_grc, image.alt_en, image.collection.label,
    ...(image.words ?? []), ...image.vocabulary.flatMap(w => [w.lemma, w.definition]),
    ...image.usages.flatMap(u => [u.id, u.title, u.context])].join(" "));
  return searchText(query).trim().split(/\s+/).every(term => haystack.includes(term));
}
export async function getImageCatalog(): Promise<ImageCatalog> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${base}/api/course/image-catalog`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Image catalog could not load (${response.status}). Please retry.`);
  return response.json();
}
export function catalogCsv(images: CatalogImage[]): string {
  const cell = (value: string) => {
    const safe = /^[=+@\-\t\r]/.test(value) ? "'" + value : value;
    return '"' + safe.replace(/"/g, '""') + '"';
  };
  const rows = [["Image ID", "Status", "Type", "Medium", "Collection", "Greek", "English purpose", "Vocabulary", "Lesson context", "File", "Credit", "License"],
    ...images.map(i => [i.id, i.status, i.kind, i.medium, i.collection.label, i.alt_grc, i.alt_en,
      i.vocabulary.map(w => `${w.lemma}: ${w.definition}`).join("; "),
      i.usages.map(u => `${u.id} ${u.title} (${u.location}): ${u.context}`).join("; "), i.file ?? "", i.credit, i.license])];
  return "\uFEFF" + rows.map(r => r.map(cell).join(",")).join("\r\n");
}
