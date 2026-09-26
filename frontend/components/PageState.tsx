import Link from "next/link";
import Crumbs, { type Crumb } from "./Crumbs";

/**
 * Loading and error states for a whole page. The skeleton reserves roughly
 * the space of a page header and a card so the page does not jump when the
 * data arrives.
 */
export function PageLoading({ label, crumbs }: { label: string; crumbs?: Crumb[] }) {
  return (
    <main className="shell" aria-busy="true">
      {crumbs && <Crumbs items={crumbs} />}
      <p className="loadingLine" role="status">{label}</p>
      <div className="skeleton skTitle" aria-hidden="true" />
      <div className="skeleton skLine" aria-hidden="true" />
      <div className="skeleton skCard" aria-hidden="true" />
    </main>
  );
}

export function PageError({ message, crumbs, back }: { message: string; crumbs?: Crumb[]; back?: { href: string; label: string } }) {
  return (
    <main className="shell">
      {crumbs && <Crumbs items={crumbs} />}
      <h1 className="pageTitle">Something went wrong</h1>
      <p className="error" role="alert">{message}</p>
      {back && (
        <p className="stepNav start">
          <Link href={back.href} className="secondary buttonLike">{back.label}</Link>
        </p>
      )}
    </main>
  );
}
