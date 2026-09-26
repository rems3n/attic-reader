import Link from "next/link";
import { streakDays, type Progress } from "../lib/progress";
import { wordCounts } from "../lib/dashboard";
export default function SessionSummary({
  title = "Session complete",
  reviewed,
  correct,
  before,
  progress,
  minutes,
  wordsMet,
  children,
}: {
  title?: string;
  reviewed: number;
  correct?: number;
  before?: Progress;
  progress?: Progress;
  minutes?: number;
  wordsMet?: number;
  children?: React.ReactNode;
}) {
  const learned =
    progress && before
      ? Math.max(0, wordCounts(progress).known - wordCounts(before).known)
      : 0;
  const moved =
    progress && before
      ? Object.entries(progress.course.skills).filter(
          ([id, s]) => s.ewma > (before.course.skills[id]?.ewma ?? 0),
        ).length
      : 0;
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
            {reviewed > 0 && ` (${Math.round((correct / reviewed) * 100)}%)`}
          </>
        )}
      </p>
      {(wordsMet != null || before) && (
        <p>
          {wordsMet != null && <>{wordsMet} lesson words · </>}
          {learned} newly known words · {moved} skills with improved accuracy
        </p>
      )}
      {minutes != null && (
        <p>
          {Math.round(minutes * 10) / 10} minutes this session
          {progress && <> · {streakDays(progress.course)}-day course streak</>}
        </p>
      )}
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
