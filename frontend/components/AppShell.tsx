"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { focusMain } from "../lib/a11y";
import Crumbs from "./Crumbs";
import Tour from "./Tour";
import QuickTimer from "./QuickTimer";
import SiteFooter from "./SiteFooter";

const sections = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/learn", label: "Learn", icon: "learn" },
  { href: "/library", label: "Library", icon: "book" },
  { href: "/practice", label: "Practice", icon: "cards" },
  { href: "/grammar", label: "Grammar", icon: "table" },
  { href: "/progress", label: "Progress", icon: "chart" },
];
const secondary = [
  { href: "/help", label: "Help", icon: "help" },
  { href: "/settings", label: "Settings", icon: "settings" },
];
function Icon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    home: (
      <>
        <path d="m3 10 9-7 9 7v10H3Z" />
        <path d="M9 20v-7h6v7" />
      </>
    ),
    learn: (
      <>
        <path d="m3 8 9-5 9 5H3ZM5 9v10m5-10v10m4-10v10m5-10v10M3 21h18" />
      </>
    ),
    book: (
      <>
        <path d="M12 5v16M12 5C9 3 5 3 2 4v15c3-1 7-1 10 2 3-3 7-3 10-2V4c-3-1-7-1-10 1Z" />
      </>
    ),
    cards: (
      <>
        <rect x="8" y="3" width="12" height="15" rx="2" />
        <path d="M4 7v12a2 2 0 0 0 2 2h10" />
      </>
    ),
    table: (
      <>
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M3 10h18M10 4v16M3 15h18" />
      </>
    ),
    chart: (
      <>
        <path d="M4 3v18h17M8 17v-5m5 5V8m5 9V4" />
      </>
    ),
    help: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M9 9a3 3 0 1 1 4 3c-1 .5-1 1-1 2M12 17h.01" />
      </>
    ),
    settings: (
      <>
        <path d="M4 6h16M4 12h16M4 18h16" />
        <circle cx="8" cy="6" r="2" />
        <circle cx="16" cy="12" r="2" />
        <circle cx="10" cy="18" r="2" />
      </>
    ),
    more: (
      <>
        <circle cx="5" cy="12" r="1" />
        <circle cx="12" cy="12" r="1" />
        <circle cx="19" cy="12" r="1" />
      </>
    ),
  };
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
export default function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname() ?? "/";
  const [account, setAccount] = useState(false);
  const sheet = useRef<HTMLDialogElement>(null);
  const more = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    setAccount(false);
    sheet.current?.close();
  }, [path]);
  const active = (href: string) =>
    href === "/"
      ? path === "/"
      : path.startsWith(href) ||
        (href === "/practice" && path.startsWith("/words"));
  const links = (items: typeof sections) =>
    items.map((s) => (
      <Link
        key={s.href}
        href={s.href}
        onClick={() => sheet.current?.close()}
        className={`shellLink ${active(s.href) ? "on" : ""}`}
        aria-current={active(s.href) ? "page" : undefined}
      >
        <Icon name={s.icon} />
        <span>{s.label}</span>
      </Link>
    ));
  const segment = path.split("/").filter(Boolean);
  const label = (s: string) =>
    ({
      learn: "Learn",
      library: "Library",
      practice: "Practice",
      words: "Words",
      progress: "Progress",
      start: "Get started",
    })[s] ?? s.replace(/-/g, " ").replace(/^./, (c) => c.toUpperCase());
  const crumbs = segment.length
    ? [
        { label: "Home", href: "/" },
        ...segment.map((s, i) => ({
          label: label(s),
          href: i === 0 ? `/${s}` : undefined,
        })),
      ]
    : [{ label: "Home" }];
  const help =
    path.startsWith("/words") || path.startsWith("/practice")
      ? "practice"
      : path.startsWith("/library")
        ? "reading"
        : path.startsWith("/learn")
          ? "lessons"
          : "overview";
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
      <aside className="sidebar">
        <Link href="/" className="shellBrand">
          Attic Reader<span>Classical Greek</span>
        </Link>
        <nav aria-label="Main" className="sideLinks">
          {links(sections)}
          {path.startsWith("/learn") && (
            <div className="shellSubnav">
              <Link href="/learn#units">Units</Link>
              <Link href="/learn#tracks">Tracks</Link>
              <Link href="/learn/placement">Placement</Link>
            </div>
          )}
          {(path.startsWith("/practice") || path.startsWith("/words")) && (
            <div className="shellSubnav">
              <Link href="/practice/review">Review</Link>
              <Link href="/words">Words</Link>
              <Link href="/progress">Skills and drills</Link>
            </div>
          )}
        </nav>
        <nav aria-label="Support" className="sideSupport">
          {links(secondary)}
        </nav>
        <p className="sidebarNote">
          Guest mode
          <br />
          <span>Progress saved on this device</span>
        </p>
      </aside>
      <div className="shellBody">
        <header className="shellTopbar">
          <Crumbs items={crumbs} />
          <div className="shellUtilities">
            <Link aria-label="Help for this page" href={`/help#${help}`}>
              Help
            </Link>
            <div className="accountWrap">
              <button
                type="button"
                className="secondary"
                aria-expanded={account}
                aria-controls="account-menu"
                onClick={() => setAccount(!account)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") setAccount(false);
                }}
              >
                Guest
              </button>
              {account && (
                <div id="account-menu" className="accountMenu">
                  <p>Progress stays on this device.</p>
                  <Link href="/settings">Settings and backup</Link>
                </div>
              )}
            </div>
          </div>
        </header>
        <QuickTimer />
        <div id="main" tabIndex={-1}>
          <Tour />
          {children}
        </div>
        <SiteFooter />
      </div>
      <nav className="mobileTabs tabBar" aria-label="Main mobile">
        {links(sections.slice(0, 4))}
        <button
          type="button"
          ref={more}
          className={`shellLink ${[...sections.slice(4), ...secondary].some((s) => active(s.href)) ? "on" : ""}`}
          aria-haspopup="dialog"
          onClick={() => sheet.current?.showModal()}
        >
          <Icon name="more" />
          <span>More</span>
        </button>
      </nav>
      <dialog
        className="moreSheet"
        ref={sheet}
        aria-labelledby="more-title"
        onClose={() => more.current?.focus()}
        onClick={(e) => {
          if (e.target === sheet.current) sheet.current.close();
        }}
      >
        <div className="sectionHead">
          <h2 id="more-title">More</h2>
          <button
            type="button"
            className="secondary"
            onClick={() => sheet.current?.close()}
          >
            Close
          </button>
        </div>
        <nav aria-label="More pages">
          {links([...sections.slice(4), ...secondary])}
        </nav>
      </dialog>
    </>
  );
}
