import Link from "next/link";
export default function EmptyState({
  title,
  children,
  href,
  action,
}: {
  title: string;
  children: React.ReactNode;
  href: string;
  action: string;
}) {
  return (
    <div className="emptyState">
      <h2>{title}</h2>
      <p className="muted">{children}</p>
      <Link className="secondary buttonLike" href={href}>
        {action}
      </Link>
    </div>
  );
}
