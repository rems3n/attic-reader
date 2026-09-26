import Link from "next/link";
export default function SessionSummary({
  title = "Session complete",
  reviewed,
  correct,
  children,
}: {
  title?: string;
  reviewed: number;
  correct?: number;
  children?: React.ReactNode;
}) {
  return (
    <div className="sessionSummary" role="status">
      <p className="eyebrow">SESSION SUMMARY</p>
      <h2>{title}</h2>
      <p>
        <strong>{reviewed}</strong> items practised
        {correct != null && (
          <>
            {" "}
            · <strong>{correct}</strong> correct
          </>
        )}
      </p>
      {children}
      <p className="muted small">Your progress is saved on this device.</p>
      <div className="actions">
        <Link href="/" className="secondary buttonLike">
          Home
        </Link>
        <Link href="/practice" className="secondary buttonLike">
          Review and practice
        </Link>
      </div>
    </div>
  );
}
