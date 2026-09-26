/**
 * Our own grammar diagrams and maps (image records of kind "diagram" with
 * `svg: true` in the course image manifests), drawn as inline SVG in the
 * app's theme colours (CSS variables), so they match the light Reader theme
 * and scale on any screen. Released CC BY-SA 4.0 with the course.
 *
 * Each diagram is a component with no props; register it here under its
 * image id. A test checks that every `svg: true` record has a component.
 */

import type { ComponentType } from "react";

export const DIAGRAMS: Record<string, ComponentType> = {};
