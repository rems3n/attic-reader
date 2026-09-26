import Link from "next/link";

export type Crumb = { label: React.ReactNode; href?: string; lang?: string };

/**
 * Breadcrumbs for every sub-page: "Course › Unit 3 › Lesson 3.2",
 * "Vocab › λόγος". The last crumb is the current page (aria-current).
 */
export default function Crumbs({ items, className = "" }: { items: Crumb[]; className?: string }) {
  const last = items.length - 1;
  return (
    <nav aria-label="Breadcrumb" className={`crumbs ${className}`}>
      <ol>
        {items.map((c, i) => (
          <li key={i}>
            {c.href && i < last ? (
              <Link href={c.href} lang={c.lang}>
                {c.label}
              </Link>
            ) : (
              <span lang={c.lang} aria-current={i === last ? "page" : undefined}>
                {c.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
