"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { focusMain } from "../lib/a11y";

type Tab = { href: string; label: string; match: (p: string) => boolean; icon: React.ReactNode };

const ICON = { width: 24, height: 24, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true, focusable: false };

const LINKS: Tab[] = [
  {
    href: "/course",
    label: "Course",
    match: (p) => p.startsWith("/course"),
    // a temple front: the course
    icon: <svg {...ICON}><path d="M3 9.5 12 4l9 5.5H3Z" /><path d="M5.5 9.5v9M10 9.5v9M14 9.5v9M18.5 9.5v9M3.5 19.5h17" /></svg>,
  },
  {
    href: "/",
    label: "Read",
    match: (p) => p === "/",
    // headphones: read aloud
    icon: <svg {...ICON}><path d="M4 15v-2.5a8 8 0 0 1 16 0V15" /><rect x="3.5" y="14" width="4" height="6.5" rx="1.6" /><rect x="16.5" y="14" width="4" height="6.5" rx="1.6" /></svg>,
  },
  {
    href: "/vocab",
    label: "Vocab",
    match: (p) => p.startsWith("/vocab"),
    // a stack of flash cards
    icon: <svg {...ICON}><rect x="7.5" y="3.5" width="12" height="15" rx="2" /><path d="M4.5 7v11.5a2 2 0 0 0 2 2h9" /></svg>,
  },
  {
    href: "/grammar",
    label: "Grammar",
    match: (p) => p.startsWith("/grammar"),
    // a paradigm table
    icon: <svg {...ICON}><rect x="3.5" y="4.5" width="17" height="15" rx="2" /><path d="M3.5 9.5h17M3.5 14.5h17M9.5 4.5v15" /></svg>,
  },
];

/**
 * Site header and primary navigation. Desktop: one sticky bar with the brand
 * and the four sections. Phones (≤ 640 px): the brand stays at the top and the
 * sections become a fixed bottom tab bar (icons + labels) within thumb reach;
 * globals.css keeps the Reader's player bar, the flash-card grade bar and
 * page content clear of it (--tabbar-h).
 */
export default function AppNav() {
  const pathname = usePathname() ?? "/";
  return (
    <>
      <a
        className="skipLink"
        href="#main"
        onClick={(e) => {
          e.preventDefault();
          focusMain();
        }}
      >
        Skip to content
      </a>
      <header className="nav">
        <div className="navInner">
          <Link href="/" className="navBrand" aria-label="Attic Reader, home">
            Attic Reader
          </Link>
          <nav className="navTabs tabBar" aria-label="Main">
            <ul className="navList">
              {LINKS.map((l) => {
                const on = l.match(pathname);
                return (
                  <li key={l.href}>
                    <Link href={l.href} className={`navLink ${on ? "on" : ""}`} aria-current={on ? "page" : undefined}>
                      <span className="navIcon">{l.icon}</span>
                      <span className="navLabel">{l.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </header>
    </>
  );
}
