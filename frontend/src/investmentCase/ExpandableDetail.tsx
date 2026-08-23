import type { ReactNode } from "react";

/**
 * Progressive disclosure primitive (Figma-fidelity pass): a native
 * `<details>`/`<summary>` element, styled with existing tokens only --
 * no new design language, no new client-side expand/collapse state to
 * manage, and correct keyboard/screen-reader behavior for free (a
 * `<summary>` is a real, focusable, `Enter`/`Space`-activated disclosure
 * widget in every browser). Used everywhere the approved design shows
 * an "Expand" affordance: each Company Health Assessment card, and the
 * Detailed Financials / Sources & Methodology section.
 */
export function ExpandableDetail({
  summaryLabel,
  children,
  onToggle,
}: {
  summaryLabel: string;
  children: ReactNode;
  /** Fires once, the first time the detail is opened -- used by
   * callers that lazily fetch content only when an investor actually
   * asks to see it, never eagerly for every row on a list (Atlas
   * Intelligence Sprint 3, Deliverable 5/8). Optional; every existing
   * caller is unaffected. */
  onToggle?: (open: boolean) => void;
}) {
  return (
    <details onToggle={onToggle ? (event) => onToggle(event.currentTarget.open) : undefined}>
      <summary
        style={{
          cursor: "pointer",
          fontFamily: "var(--type-family-metadata)",
          fontSize: "var(--type-body-min-size)",
          color: "var(--color-text-secondary)",
          userSelect: "none",
        }}
      >
        {summaryLabel}
      </summary>
      <div style={{ marginTop: "var(--space-metadata)" }}>{children}</div>
    </details>
  );
}
