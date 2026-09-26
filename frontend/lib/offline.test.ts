import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import type { Lesson } from "./course";
import { cleanSpeakText, lessonImageUrls, lessonWordTexts, shouldPrefetch, swCacheKey } from "./offline";

const SW_SOURCE = readFileSync(join(__dirname, "..", "public", "sw.js"), "utf8");

/** The copy of swCacheKey inside public/sw.js, evaluated as-is. */
function workerKeyFn(): typeof swCacheKey {
  const m = SW_SOURCE.match(/\/\/ <sw-key>[^\n]*\n([\s\S]*?)\/\/ <\/sw-key>/);
  if (!m) throw new Error("sw.js lost its <sw-key> markers");
  return new Function(`${m[1]}\nreturn swCacheKey;`)() as typeof swCacheKey;
}

describe("swCacheKey", () => {
  it("builds a GET URL on the API origin from text and speed", () => {
    expect(swCacheKey("https://api.example/", "speak", "λόγος", 0.75)).toBe(
      "https://api.example/__sw_speak?speed=0.75&text=%CE%BB%CF%8C%CE%B3%CE%BF%CF%82",
    );
  });

  it("normalises speed and trims text so equivalent bodies share a key", () => {
    expect(swCacheKey("http://x", "stream", " ὁ ἀνήρ. ", "0.750")).toBe(swCacheKey("http://x", "stream", "ὁ ἀνήρ.", 0.75));
    expect(swCacheKey("http://x", "speak", "a", 1)).toBe(swCacheKey("http://x", "speak", "a", "1"));
    expect(swCacheKey("http://x", "speak", "a", undefined)).toContain("speed=1&");
    expect(swCacheKey("http://x", "speak", "a", 0.6)).not.toBe(swCacheKey("http://x", "speak", "a", 0.75));
    expect(swCacheKey("http://x", "speak", "a", 1)).not.toBe(swCacheKey("http://x", "stream", "a", 1));
  });

  it("encodes characters that would break a query string", () => {
    const key = swCacheKey("http://x", "speak", "a&b=c #d", 1);
    expect(new URL(key).searchParams.get("text")).toBe("a&b=c #d");
  });

  it("is identical to the copy in public/sw.js", () => {
    const worker = workerKeyFn();
    const cases: [string, string, unknown, unknown][] = [
      ["https://backend-preview-production.up.railway.app", "speak", "ἀκούετε", 0.75],
      ["http://localhost:8000/", "stream", "  ὁ Ἀρίστων αὐτουργός ἐστιν. «χαῖρε», ἔφη.\n", 0.6],
      ["http://x", "speak", "a&b / c", "1"],
      ["http://x", "speak", null, "fast"],
      ["", "stream", "ᾠδή", 1.25],
    ];
    for (const c of cases) expect(worker(...c)).toBe(swCacheKey(...c));
  });
});

describe("cleanSpeakText", () => {
  it("matches what the ▶ button sends", () => {
    expect(cleanSpeakText("ἐστί(ν)")).toBe("ἐστίν");
    expect(cleanSpeakText("ὁ / ἡ")).toBe("ὁ");
    expect(cleanSpeakText(" λόγος ")).toBe("λόγος");
  });
});

const img = (id: string, file: string | null, license = "CC0") => ({ id, kind: "photo", file, alt_grc: "", alt_en: id, credit: "", license, source_url: null });

describe("lessonImageUrls", () => {
  it("collects every real picture once, skipping placeholders and diagrams", () => {
    const lesson = {
      cover: "cover",
      cover_image: img("cover", "course/pics/cover.webp"),
      story: [
        { image: "p1", sentences: [{ text: "x", glosses: [{ word: "ἀγρός", kind: "pic", value: "field" }] }] },
        { image_record: img("p2", "course/pics/p2.webp"), sentences: [] },
      ],
      vocab: [{ pic: "field" }, { pic: "ph" }, { pic: null }],
      grammar: { md: "", paradigms: [], diagram: "diag" },
      culture: { title: "", md: "", image: "p1" },
    } as unknown as Lesson;
    const images = [img("p1", "course/pics/p1.webp"), img("field", "/course/pics/field.webp"), img("ph", null, "placeholder"), img("diag", null)];
    expect(lessonImageUrls(lesson, images).sort()).toEqual(["/course/pics/cover.webp", "/course/pics/field.webp", "/course/pics/p1.webp", "/course/pics/p2.webp"]);
  });
});

describe("lessonWordTexts", () => {
  it("dedupes and cleans the lesson words", () => {
    const lesson = { vocab: [{ lemma: "ἐστί(ν)" }, { lemma: "ἐστί(ν)" }, { lemma: "ὁ" }] } as unknown as Lesson;
    expect(lessonWordTexts(lesson)).toEqual(["ἐστίν", "ὁ"]);
  });
});

describe("shouldPrefetch", () => {
  const sw = {};
  it("needs signal and a service worker", () => {
    expect(shouldPrefetch({ onLine: true, serviceWorker: sw })).toBe(true);
    expect(shouldPrefetch({ onLine: false, serviceWorker: sw })).toBe(false);
    expect(shouldPrefetch({ onLine: true })).toBe(false);
    expect(shouldPrefetch(undefined)).toBe(false);
  });
  it("respects data saver and very slow links", () => {
    expect(shouldPrefetch({ onLine: true, serviceWorker: sw, connection: { saveData: true } })).toBe(false);
    expect(shouldPrefetch({ onLine: true, serviceWorker: sw, connection: { effectiveType: "2g" } })).toBe(false);
    expect(shouldPrefetch({ onLine: true, serviceWorker: sw, connection: { effectiveType: "4g" } })).toBe(true);
  });
});
