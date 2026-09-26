"use client";

import type { ImageRecord } from "../../lib/course";
import { DIAGRAMS } from "./diagrams";

type Size = "panel" | "tile" | "thumb";

/**
 * A course picture. Until the Creative Commons image pass lands, every image
 * in the manifest is a placeholder: a cream panel with its Greek caption.
 * Real images render from /course/pics with their credit on the badge.
 */
export default function Picture({ image, size = "panel", caption = true, className = "" }: { image: ImageRecord | null | undefined; size?: Size; caption?: boolean; className?: string }) {
  if (!image) return null;
  const Diagram = image.kind === "diagram" ? DIAGRAMS[image.id] : undefined;
  if (Diagram) {
    return (
      <figure className={`pic pic-${size} diagram ${className}`}>
        <div className="diagramBody" role="img" aria-label={image.alt_en}>
          <Diagram />
        </div>
        {caption && size === "panel" && (
          <figcaption>
            <span lang="grc">{image.alt_grc}</span>
            <a className="picBadge" href="/learn/credits" title={image.credit}>{image.license === "placeholder" ? "CC BY-SA" : image.license}</a>
          </figcaption>
        )}
      </figure>
    );
  }
  const placeholder = image.license === "placeholder" || !image.file;
  return (
    <figure className={`pic pic-${size} ${className}`}>
      {placeholder ? (
        <div className="picPlaceholder" role="img" aria-label={image.alt_en}>
          <svg viewBox="0 0 64 48" width="100%" height="100%" aria-hidden="true">
            <rect x="0" y="0" width="64" height="48" fill="var(--cream)"></rect>
            <path d="M6 40h52M14 40V22M22 40V22M12 22h12M40 40V22M48 40V22M38 22h12M10 22l22-12 22 12" fill="none" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"></path>
          </svg>
          {size !== "thumb" && <span className="picLabel" lang="grc">{image.alt_grc}</span>}
        </div>
      ) : (
        <img src={`/${image.file}`} alt={image.alt_en} loading="lazy" />
      )}
      {caption && size === "panel" && (
        <figcaption>
          <span lang="grc">{image.alt_grc}</span>
          {placeholder ? <span className="picBadge">image coming · CC</span> : <a className="picBadge" href="/learn/credits" title={image.credit}>{image.license}</a>}
        </figcaption>
      )}
    </figure>
  );
}

export function imageById(images: ImageRecord[] | Map<string, ImageRecord>, id: string | null | undefined): ImageRecord | null {
  if (!id) return null;
  if (images instanceof Map) return images.get(id) ?? null;
  return images.find((i) => i.id === id) ?? null;
}
