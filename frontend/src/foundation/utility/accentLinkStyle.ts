import type { CSSProperties } from "react";

/**
 * Product Sprint 10 (Navigation & Workflow Excellence, Deliverable 12
 * -- Cleanup): the identical inline style object was independently
 * declared in ten different files (every Tier 1 page's own secondary
 * navigation links -- Compare, Back to X, Open Y). One shared export,
 * consolidated here rather than re-declared per file.
 */
export const ACCENT_LINK_STYLE: CSSProperties = {
  color: "var(--global-color-accent)",
  textDecoration: "none",
  fontSize: "var(--type-body-min-size)",
};
