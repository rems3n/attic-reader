"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import PageHeader from "../../../components/PageHeader";
import Picture from "../../../components/course/Picture";
import { catalogCsv, getImageCatalog, KIND_LABELS, matchesSearch, MEDIUM_LABELS, type CatalogImage, type ImageCatalog } from "../../../lib/imageCatalog";
import styles from "./page.module.css";

const PAGE_SIZE = 24;
function Preview({ image, candidate = false }: { image: CatalogImage; candidate?: boolean }) {
  const [failed, setFailed] = useState(false);
  const file = candidate ? image.candidate?.file : image.file;
  if (!candidate && image.medium === "diagram") return <Picture image={image} caption={false} />;
  if (failed) return <div className={styles.pending}>Image could not load.<br />{file}</div>;
  if (file && (candidate || image.status === "completed")) return <img src={`/${file}`} alt={candidate ? `Unreviewed candidate for ${image.alt_en}` : image.alt_en} loading="lazy" onError={() => setFailed(true)} />;
  return <div className={styles.pending}><span aria-hidden="true">◇</span><strong>Image needed</strong><span lang="grc">{image.alt_grc}</span></div>;
}

export default function ImageDashboard() {
  const [catalog, setCatalog] = useState<ImageCatalog | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [kind, setKind] = useState("all");
  const [collection, setCollection] = useState("all");
  const [medium, setMedium] = useState("all");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<CatalogImage | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  function load() {
    setError("");
    getImageCatalog().then(setCatalog).catch(e => setError(e instanceof Error ? e.message : "Could not load images."));
  }
  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (selected && !dialog.current?.open) dialog.current?.showModal();
    else if (!selected && dialog.current?.open) dialog.current.close();
  }, [selected]);
  const collections = useMemo(() => [...new Map((catalog?.images ?? []).map(i => [i.collection.id, i.collection])).values()]
    .sort((a, b) => a.label.localeCompare(b.label, undefined, { numeric: true })), [catalog]);
  const filtered = useMemo(() => (catalog?.images ?? []).filter(i =>
    (status === "all" || (status === "candidates" ? !!i.candidate : i.status === status)) &&
    (kind === "all" || i.kind === kind) && (collection === "all" || i.collection.id === collection) &&
    (medium === "all" || i.medium === medium) && matchesSearch(i, query))
    .sort((a, b) => a.status.localeCompare(b.status) || a.id.localeCompare(b.id, undefined, { numeric: true })),
    [catalog, status, kind, collection, medium, query]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pages);
  const shown = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  function reset() { setQuery(""); setStatus("all"); setKind("all"); setCollection("all"); setMedium("all"); setPage(1); }
  function goToPage(value: number) {
    setPage(value);
    document.getElementById("image-results")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function exportList() {
    const url = URL.createObjectURL(new Blob([catalogCsv(filtered)], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "attic-reader-images.csv"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const counts = catalog?.summary;
  return <main className={`shell ${styles.dashboard}`}>
    <PageHeader eyebrow="ADMIN · IMAGE LIBRARY" title="Every picture, in context" action={<Link href="/settings">Back to settings</Link>}>
      Browse course artwork, see what it teaches, and find the images still needed.
    </PageHeader>
    {error ? <div className="card" role="alert"><p>{error}</p><button onClick={load}>Retry loading</button></div> : !catalog ? <p role="status">Loading the image library…</p> : <>
      <section className={styles.stats} aria-label="Image totals">
        {[["all", "All images", counts!.total], ["completed", "Completed", counts!.completed], ["remaining", "Still needed", counts!.remaining], ["candidates", "Candidates to review", counts!.candidates]].map(([value, label, count]) =>
          <button key={value} className={status === value ? styles.activeStat : ""} aria-pressed={status === value} onClick={() => { reset(); setStatus(String(value)); }}><strong>{count}</strong><span>{label}</span></button>)}
      </section>
      <p className={styles.inventoryNote}>{counts!.illustrations} illustrated entries · {counts!.photos} photographic entries · {counts!.diagrams} diagrams. Some entries share artwork ({counts!.unique_raster_files} distinct image files).</p>
      <section className={styles.filters} aria-label="Filter images">
        <label className={styles.search}>Search Greek, English, image ID, or lesson
          <input type="search" value={query} placeholder="Try κύων, dog, daytime, or 2.1" onChange={e => { setQuery(e.target.value); setPage(1); }} />
        </label>
        <label>Status<select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}><option value="all">All statuses</option><option value="completed">Completed</option><option value="remaining">Still needed</option><option value="candidates">Candidates to review</option></select></label>
        <label>Purpose<select value={kind} onChange={e => { setKind(e.target.value); setPage(1); }}><option value="all">All purposes</option>{Object.entries(KIND_LABELS).map(([key, value]) => <option key={key} value={key}>{value}</option>)}</select></label>
        <label>Collection<select value={collection} onChange={e => { setCollection(e.target.value); setPage(1); }}><option value="all">All collections</option>{collections.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}</select></label>
        <label>Artwork<select value={medium} onChange={e => { setMedium(e.target.value); setPage(1); }}><option value="all">All artwork</option>{Object.entries(MEDIUM_LABELS).map(([key, value]) => <option key={key} value={key}>{value}</option>)}</select></label>
      </section>
      <div id="image-results" className={styles.resultBar}><p role="status" aria-live="polite">{filtered.length} matching images{filtered.length > PAGE_SIZE && ` · Page ${currentPage} of ${pages}`}</p><div><button onClick={reset}>Clear filters</button><button onClick={exportList} disabled={!filtered.length}>Export current list</button></div></div>
      {!filtered.length ? <section className="card"><h2>No matching images</h2><p>Try another word or clear the filters.</p></section> : <div className={styles.grid}>
        {shown.map(image => <article className={styles.imageCard} key={image.id}>
          <button className={styles.preview} onClick={() => setSelected(image)} aria-label={`View details: ${image.id}`}><Preview image={image} /></button>
          <div className={styles.cardBody}><div className={styles.badges}><span className={image.status === "completed" ? styles.completed : styles.needed}>{image.status === "completed" ? "Completed" : "Still needed"}</span><span>{KIND_LABELS[image.kind]}</span></div>
            <h2 lang="grc">{image.alt_grc}</h2><p className={styles.description}>{image.alt_en}</p>
            {!!image.vocabulary.length && <p className={styles.words}>{image.vocabulary.map(w => `${w.lemma} — ${w.definition}`).join(" · ")}</p>}
            <p className={styles.meta}>{image.collection.label} · {MEDIUM_LABELS[image.medium]}</p>
            <button className={styles.detailsButton} onClick={() => setSelected(image)}>Context & details <span aria-hidden="true">↗</span></button>
          </div>
        </article>)}
      </div>}
      {pages > 1 && <nav className={styles.pagination} aria-label="Image pages"><button disabled={currentPage === 1} onClick={() => goToPage(currentPage - 1)}>Previous</button><span>Page {currentPage} of {pages}</span><button disabled={currentPage === pages} onClick={() => goToPage(currentPage + 1)}>Next</button></nav>}
    </>}
    <dialog ref={dialog} className={styles.dialog} aria-labelledby="image-detail-title" onClose={() => setSelected(null)} onClick={e => { if (e.target === e.currentTarget) dialog.current?.close(); }}>
      {selected && <div className={styles.detailBody}>
        <div className={styles.detailHeading}><div><p className="eyebrow">{selected.id}</p><h2 id="image-detail-title" lang="grc">{selected.alt_grc}</h2></div><button autoFocus onClick={() => dialog.current?.close()} aria-label="Close image details">Close</button></div>
        <div className={styles.detailPreview}><Preview key={selected.id} image={selected} /></div>
        <h3>Intended word or scene</h3><p>{selected.alt_en}</p>
        {selected.vocabulary.length > 0 && <ul>{selected.vocabulary.map(w => <li key={w.id}><span lang="grc">{w.lemma}</span> — {w.definition}</li>)}</ul>}
        {!!selected.words?.length && <p><strong>Associated Greek:</strong> <span lang="grc">{selected.words.join(" · ")}</span></p>}
        <p><strong>Status:</strong> {selected.status === "completed" ? `Completed · ${MEDIUM_LABELS[selected.medium]}` : "Still needed"}</p>
        <h3>Where it appears ({selected.usages.length})</h3>
        {!selected.usages.length ? <p>Planned in the image collection; no direct lesson reference yet.</p> : <ul className={styles.usageList}>{selected.usages.map((usage, n) => <li key={n}>
          {usage.href ? <Link href={usage.href}>{usage.id} · {usage.title}</Link> : <strong>{usage.id} · {usage.title}</strong>}
          <span className={styles.location}>{usage.source} · {usage.location}</span>{usage.context && <p lang="grc">{usage.context}</p>}
        </li>)}</ul>}
        {selected.status === "completed" && <><h3>Source & credit</h3><p>{selected.credit}</p><p>{selected.license}</p><div className={styles.links}>{selected.file && <a href={`/${selected.file}`} target="_blank" rel="noreferrer">Open full image</a>}{selected.source_url && <a href={selected.source_url} target="_blank" rel="noreferrer">Original source</a>}</div></>}
        {selected.provenance && <details><summary>Generation prompt & review</summary><p>{selected.provenance.generator}</p><p className={styles.prompt}>{selected.provenance.prompt}</p><p><strong>Review:</strong> {selected.provenance.review}</p></details>}
        {selected.candidate && <details className={styles.candidate}><summary>View unreviewed candidate</summary><p>This downloaded image has not been approved for this word or scene. It may depict a different subject and does not count as completed.</p><Preview key={`${selected.id}-candidate`} image={selected} candidate /><p>{selected.candidate.credit}</p><p>{selected.candidate.license}</p>{selected.candidate.source_url && <a href={selected.candidate.source_url} target="_blank" rel="noreferrer">Candidate source</a>}</details>}
      </div>}
    </dialog>
  </main>;
}
