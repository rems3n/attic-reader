"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/course", label: "Course", match: (p: string) => p.startsWith("/course") },
  { href: "/", label: "Read", match: (p: string) => p === "/" },
  { href: "/vocab", label: "Vocab", match: (p: string) => p.startsWith("/vocab") },
  { href: "/grammar", label: "Grammar", match: (p: string) => p.startsWith("/grammar") },
];

export default function AppNav() {
  const pathname = usePathname() ?? "/";
  return (
    <nav className="nav" aria-label="Sections">
      <div className="navInner">
        <span className="navBrand">Attic Reader</span>
        <div className="navLinks">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className={`navLink ${l.match(pathname) ? "on" : ""}`}>
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
