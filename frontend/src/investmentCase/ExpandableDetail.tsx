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
}: {
  summaryLabel: string;
  children: ReactNode;
}) {
  return (
    <details>
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
