import Link from "next/link";

/** Secondary links and the sources the app is built on. */
export default function SiteFooter() {
  return (
    <footer className="siteFooter">
      <div className="footerInner">
        <nav aria-label="More">
          <ul className="footerLinks">
            <li><Link href="/learn">Learn</Link></li>
            <li><Link href="/learn/placement">Placement test</Link></li>
            <li><Link href="/practice/review">Review quiz</Link></li>
            <li><Link href="/library">Library</Link></li>
            <li><Link href="/words">Words</Link></li>
            <li><Link href="/grammar">Grammar</Link></li>
            <li><Link href="/learn/credits">Image credits</Link></li>
          </ul>
        </nav>
        <p className="footerNote">
          Vocabulary from the <a href="https://dcc.dickinson.edu/greek-core-list" target="_blank" rel="noreferrer">DCC Greek Core List</a> (CC BY-SA).
          Greek texts from the <a href="https://github.com/PerseusDL/canonical-greekLit" target="_blank" rel="noreferrer">Perseus Digital Library</a> (CC BY-SA).
          Pictures: see <Link href="/learn/credits">credits</Link>. Pronunciation: reconstructed Classical Attic, never Modern Greek.
        </p>
      </div>
    </footer>
  );
}
