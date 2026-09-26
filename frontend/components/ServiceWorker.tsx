"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "../lib/offline";

/**
 * Registers public/sw.js (production builds only) and shows a slim notice
 * under the nav while the device is offline.
 */
export default function ServiceWorker() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    // The worker learns the API origin from its URL (it cannot read the build env).
    const url = `/sw.js?api=${encodeURIComponent(API_BASE)}`;
    const register = () => {
      navigator.serviceWorker.register(url, { scope: "/", updateViaCache: "none" }).catch(() => undefined);
    };
    if (document.readyState === "complete") register();
    else {
      window.addEventListener("load", register, { once: true });
      return () => window.removeEventListener("load", register);
    }
  }, []);

  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  if (!offline) return null;
  return (
    <div
      role="status"
      className="offlineBanner"
      style={{
        background: "var(--cream, #eeebe3)",
        color: "var(--ink, #1c2024)",
        borderBottom: "1px solid var(--line, #dcd8ce)",
        fontSize: 14,
        lineHeight: 1.4,
        padding: "8px 14px",
        textAlign: "center",
      }}
    >
      <strong style={{ color: "var(--accent, #4e6136)", fontWeight: 600 }}>Offline.</strong>{" "}
      Lessons and audio you have already opened still work; reading photos (OCR) and new audio need a connection.
    </div>
  );
}
