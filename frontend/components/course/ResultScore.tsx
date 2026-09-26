"use client";

import { useFocusOnMount } from "../../lib/a11y";

/**
 * The big score at the end of a quiz, test or placement. It takes focus when
 * it appears, so screen readers announce the result and keyboard users
 * continue from it (the Check / Submit button they were on is gone).
 */
export default function ResultScore({ children, lang }: { children: React.ReactNode; lang?: string }) {
  const ref = useFocusOnMount<HTMLParagraphElement>();
  return (
    <p className="resultBig" ref={ref} tabIndex={-1} lang={lang}>
      {children}
    </p>
  );
}
