"use client";

import { useEffect, useRef } from "react";

/** True when the user asked the OS for less motion. */
export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

/** "smooth" unless reduced motion is on. */
export function scrollBehavior(): ScrollBehavior {
  return prefersReducedMotion() ? "auto" : "smooth";
}

/** Move keyboard focus to the page's <main> (the skip link's target). */
export function focusMain(): void {
  const main = document.querySelector<HTMLElement>("main");
  if (!main) return;
  if (!main.hasAttribute("tabindex")) main.setAttribute("tabindex", "-1");
  main.focus({ preventScroll: true });
  main.scrollIntoView({ block: "start", behavior: scrollBehavior() });
}

/**
 * Focus an element when it mounts (a result heading, a new step): screen
 * readers read it, keyboard users continue from there. The element needs
 * tabIndex={-1} unless it is focusable already.
 */
export function useFocusOnMount<T extends HTMLElement>(active = true) {
  const ref = useRef<T | null>(null);
  useEffect(() => {
    if (active) ref.current?.focus({ preventScroll: false });
  }, [active]);
  return ref;
}
