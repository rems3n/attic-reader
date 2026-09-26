import Link from "next/link";

/** Secondary links and the sources the app is built on. */
export default function SiteFooter() {
  return (
    <footer className="siteFooter">
      <div className="footerInner">
        <nav aria-label="More">
          <ul className="footerLinks">
            <li><Link href="/course">Course</Link></li>
            <li><Link href="/course/placement">Placement test</Link></li>
            <li><Link href="/course/review">Review quiz</Link></li>
            <li><Link href="/">Reader</Link></li>
            <li><Link href="/vocab">Vocabulary</Link></li>
            <li><Link href="/grammar">Grammar</Link></li>
            <li><Link href="/course/credits">Image credits</Link></li>
          </ul>
        </nav>
        <p className="footerNote">
          Vocabulary from the <a href="https://dcc.dickinson.edu/greek-core-list" target="_blank" rel="noreferrer">DCC Greek Core List</a> (CC BY-SA).
          Greek texts from the <a href="https://github.com/PerseusDL/canonical-greekLit" target="_blank" rel="noreferrer">Perseus Digital Library</a> (CC BY-SA).
          Pictures: see <Link href="/course/credits">credits</Link>. Pronunciation: reconstructed Classical Attic, never Modern Greek.
        </p>
      </div>
    </footer>
  );
}
