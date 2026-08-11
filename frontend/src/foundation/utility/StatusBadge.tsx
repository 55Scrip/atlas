import type { HTMLAttributes } from "react";

export type StatusTone = "positive" | "caution" | "critical" | "neutral";

interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  label: string;
  tone?: StatusTone;
}

const toneColor: Record<StatusTone, string> = {
  positive: "var(--color-semantic-green)",
  caution: "var(--color-semantic-amber)",
  critical: "var(--color-semantic-red)",
  neutral: "var(--color-text-tertiary)",
};

/**
 * Workspace Migration (Foundation extraction) — a single, reusable
 * presentational primitive for the short categorical labels that
 * recur across every workspace: Conviction, Analysis Coverage, Risk,
 * Valuation, Review Priority, and the Decision Support Engine's own
 * evidence-support state. `StatusBadge` knows nothing about any of
 * these domains — it only renders a label in one of four tones. The
 * enum-to-tone and enum-to-translation-key mappings that decide what
 * to pass in live in `frontend/src/status/statusTone.ts`, kept
 * deliberately separate so this component stays a pure Foundation
 * primitive, the same way `Text`'s `color` prop carries no knowledge
 * of what produced it.
 *
 * `tone` is a fixed four-value set (positive/caution/critical/neutral),
 * matching the only three semantic colors this design system actually
 * has (`--color-semantic-green/amber/red`) plus the existing tertiary
 * text color for the "nothing to signal" case — never a fifth,
 * invented hue.
 */
export function StatusBadge({ label, tone = "neutral", style, ...rest }: StatusBadgeProps) {
  const color = toneColor[tone];
  return (
    <span
      {...rest}
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "0.125rem var(--space-metadata)",
        borderRadius: "var(--radius-chip)",
        border: `var(--width-border-hairline) solid ${color}`,
        color,
        fontFamily: "var(--type-family-metadata)",
        fontSize: "var(--type-body-min-size)",
        lineHeight: "var(--type-body-line-height)",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {label}
    </span>
  );
}
