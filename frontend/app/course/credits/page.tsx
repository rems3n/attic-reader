"use client";

import { useEffect, useMemo, useState } from "react";
import { getCourseImages } from "../../../lib/api";
import type { ImageRecord } from "../../../lib/course";
import Crumbs from "../../../components/Crumbs";
import { PageError, PageLoading } from "../../../components/PageState";

const KIND_LABEL: Record<string, string> = { dictionary: "Picture dictionary", story: "Story panels", culture: "Culture", diagram: "Diagrams" };

/** Every course image with its credit, licence and source. CC BY / CC BY-SA
 * pictures must be credited; CC0 pictures are credited anyway. */
export default function CreditsPage() {
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    getCourseImages().then((list) => { setImages(list); setLoaded(true); }).catch((e) => setError(e instanceof Error ? e.message : "Could not load the image list"));
  }, []);
  const groups = useMemo(() => {
    const out = new Map<string, ImageRecord[]>();
    for (const img of images) out.set(img.kind, [...(out.get(img.kind) ?? []), img]);
    return [...out.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [images]);
  const real = images.filter((i) => i.license !== "placeholder" && i.file);

  const crumbs = [{ label: "Course", href: "/course" }, { label: "Image credits" }];
  if (error) return <PageError message={error} crumbs={crumbs} back={{ href: "/course", label: "Back to the course" }} />;
  if (!loaded) return <PageLoading label="Loading the image list…" crumbs={crumbs} />;
  return (
    <main className="shell">
      <Crumbs items={crumbs} />
      <section className="hero">
        <p className="eyebrow">IMAGE CREDITS</p>
        <h1>Pictures in the course</h1>
        <p className="lede">All pictures are Creative Commons: CC0 and public-domain photographs from museum open-access programmes, CC BY / CC BY-SA photographs from Wikimedia Commons with their authors' names, and our own diagrams released CC BY-SA. {real.length} of {images.length} pictures are in place; the rest show a placeholder panel.</p>
      </section>
        {groups.map(([kind, list]) => (
          <section key={kind} className="card">
            <h2>{KIND_LABEL[kind] ?? kind} <span className="muted">· {list.length}</span></h2>
            <ul className="creditList">
              {list.map((img) => (
                <li key={img.id}>
                  {img.file && img.license !== "placeholder" ? <img src={`/${img.file}`} alt="" loading="lazy" /> : <span className="picPlaceholder" aria-hidden="true" />}
                  <div>
                    <span lang="grc">{img.alt_grc}</span> <span className="muted">· {img.alt_en}</span>
                    <br />
                    {img.license === "placeholder" ? <span className="muted small">image coming</span> : (
                      <>
                        <span className="small">{img.credit}</span>
                        <span className="creditLicense">{img.license}</span>
                        {img.source_url && <> <a href={img.source_url} target="_blank" rel="noreferrer" className="small">source</a></>}
                      </>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
    </main>
  );
}
