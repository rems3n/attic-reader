"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE } from "../lib/offline";

/**
 * Registers public/sw.js (production builds only), asks it to keep each page
 * the learner opens (client-side navigations never reach its navigation
 * handler), and shows a slim notice under the nav while the device is offline.
 */
export default function ServiceWorker() {
  const [offline, setOffline] = useState(false);
  const pathname = usePathname();

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
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    const sw = navigator.serviceWorker;
    const keep = () => {
      if (navigator.onLine) sw.controller?.postMessage({ type: "cache-page", url: window.location.pathname + window.location.search });
    };
    keep();
    // First visit: the worker takes control only after this page loaded.
    sw.addEventListener("controllerchange", keep);
    return () => sw.removeEventListener("controllerchange", keep);
  }, [pathname]);

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
