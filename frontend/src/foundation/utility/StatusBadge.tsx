import type { HTMLAttributes } from "react";

export type StatusTone = "positive" | "caution" | "critical" | "neutral";

interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  label: string;
  tone?: StatusTone;
  /** Editorial Design Sprint P3 -- `"outline"` (default, unchanged) is
   * the existing thin-border chip every current caller already renders.
   * `"strong"` is additive: a filled, higher-contrast treatment for the
   * one badge a page wants read before anything else is (Recommendation
   * on Investment Case's own new summary bar, "Current view" on
   * Portfolio/Watchlist) -- same four tones, same enum-to-tone maps in
   * `status/statusTone.ts`, purely a heavier rendering for the single
   * PRIMARY signal on a page, never a new categorical meaning. */
  weight?: "outline" | "strong";
}

const toneColor: Record<StatusTone, string> = {
  positive: "var(--color-semantic-green)",
  caution: "var(--color-semantic-amber)",
  critical: "var(--color-semantic-red)",
  neutral: "var(--color-text-tertiary)",
};

const toneSoftBackground: Record<StatusTone, string> = {
  positive: "var(--global-color-green-soft)",
  caution: "var(--global-color-amber-soft)",
  critical: "var(--global-color-red-soft)",
  neutral: "var(--surface-elevated)",
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
export function StatusBadge({ label, tone = "neutral", weight = "outline", style, ...rest }: StatusBadgeProps) {
  const color = toneColor[tone];
  const isStrong = weight === "strong";
  return (
    <span
      {...rest}
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: isStrong ? "0.3rem var(--space-row)" : "0.125rem var(--space-metadata)",
        borderRadius: "var(--radius-chip)",
        border: `var(--width-border-hairline) solid ${color}`,
        background: isStrong ? toneSoftBackground[tone] : "transparent",
        color,
        fontFamily: "var(--type-family-metadata)",
        fontSize: isStrong ? "var(--type-size-h5)" : "var(--type-body-min-size)",
        fontWeight: isStrong ? 600 : 400,
        lineHeight: "var(--type-body-line-height)",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {label}
    </span>
  );
}

/**
 * Visual Fidelity Pass -- the approved Figma tables (Holdings Fit/Risk/
 * Action columns) render most categorical values as plain colored text,
 * reserving the bordered chip (`StatusBadge` above) for the one column
 * that actually shows a chip (Conviction). Same tone set, same enum-to-
 * tone maps in `status/statusTone.ts` -- purely a lighter rendering, no
 * new categorical meaning.
 */
export function StatusText({ label, tone = "neutral", style, ...rest }: StatusBadgeProps) {
  return (
    <span
      {...rest}
      style={{
        color: toneColor[tone],
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
