import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { DIAGRAMS } from "../components/course/diagrams";

type Rec = { id: string; kind: string; svg?: boolean; license?: string; file?: string | null };

const IMAGES = join(__dirname, "..", "..", "backend", "app", "course_data", "images");

function records(): Rec[] {
  return readdirSync(IMAGES)
    .filter((f) => /^manifest.*\.json$/.test(f))
    .flatMap((f) => (JSON.parse(readFileSync(join(IMAGES, f), "utf8")).images ?? []) as Rec[]);
}

describe("course diagrams", () => {
  const all = records();
  const svgIds = all.filter((r) => r.svg).map((r) => r.id);
  const byId = new Map(all.map((r) => [r.id, r]));

  it("every svg record has a registered component", () => {
    expect(svgIds.length).toBeGreaterThan(0);
    expect(svgIds.filter((id) => !DIAGRAMS[id])).toEqual([]);
  });

  it("every registered component has a diagram record marked svg", () => {
    const orphans = Object.keys(DIAGRAMS).filter((id) => {
      const r = byId.get(id);
      return !r || r.kind !== "diagram" || !r.svg;
    });
    expect(orphans).toEqual([]);
  });

  it("svg records carry the course licence and no file", () => {
    for (const id of svgIds) {
      const r = byId.get(id)!;
      expect(r.license, id).toBe("CC BY-SA 4.0");
      expect(r.file ?? null, id).toBeNull();
    }
  });

  it.each(Object.keys(DIAGRAMS))("%s renders a themed <svg> with a viewBox", (id) => {
    const html = renderToStaticMarkup(createElement(DIAGRAMS[id]));
    expect(html.startsWith("<svg")).toBe(true);
    expect(html).toMatch(/viewBox="0 0 \d+ \d+"/);
    expect(html).not.toMatch(/<(image|script|foreignObject)\b/);
    expect(html).not.toMatch(/NaN|undefined/);
    // colours come from the theme: no hard-coded hex or rgb values
    expect(html).not.toMatch(/#[0-9a-fA-F]{3,6}\b|rgb\(/);
  });
});
