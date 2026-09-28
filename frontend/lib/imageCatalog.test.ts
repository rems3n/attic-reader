import { describe, expect, it } from "vitest";
import { catalogCsv, matchesSearch, type CatalogImage } from "./imageCatalog";

const image: CatalogImage = {
  id: "kyon", kind: "dictionary", file: "course/illustrations/kyon.webp", alt_grc: "ὁ κύων", alt_en: "A dog",
  credit: "Attic Reader", license: "Original AI illustration", source_url: null, status: "completed", medium: "illustration",
  words: ["κύων"], collection: { id: "manifest", label: "Opening" }, vocabulary: [{ id: "κυων", lemma: "κύων", definition: "dog" }],
  usages: [{ source: "lessons", id: "1.1", title: "Ariston's family", location: "story[1].image", context: "ὁ Λάβρος τρέχει", href: "/learn/lesson/1.1" }],
  provenance: null, candidate: null, pipeline_status: "ready",
};
describe("image catalog", () => {
  it("finds unaccented Greek, English, and the actual lesson context", () => {
    for (const query of ["κυων", "ΚΎΩΝ", "dog", "λαβροσ", "1.1 family"]) expect(matchesSearch(image, query)).toBe(true);
    expect(matchesSearch(image, "horse")).toBe(false);
  });
  it("exports the selected records with context and safe quoted cells", () => {
    const csv = catalogCsv([{ ...image, alt_en: '=A1,"test"' }]);
    expect(csv).toContain('"\'=A1,""test"""');
    expect(csv).toContain("ὁ Λάβρος τρέχει");
    expect(csv).toContain("κύων: dog");
  });
});
