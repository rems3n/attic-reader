"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
export default function QuickTimer() {
  const path = usePathname();
  const [left, setLeft] = useState<number | null>(null);
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("quick") !== "1") {
      setLeft(null);
      return;
    }
    const end = Date.now() + 300000;
    setLeft(300);
    const id = window.setInterval(
      () => setLeft(Math.max(0, Math.ceil((end - Date.now()) / 1000))),
      1000,
    );
    return () => clearInterval(id);
  }, [path]);
  if (left == null) return null;
  return (
    <div className="quickTimer">
      <span>
        {left > 0
          ? `Quick session · ${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")} remaining`
          : "Five minutes complete. Finish this answer whenever you are ready."}
      </span>
      {left === 0 && <Link href="/practice">Finish session</Link>}
    </div>
  );
}
