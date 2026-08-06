/**
 * Single source of truth mapping Foundation Component props to their
 * canonical UX-012D token names (frontend/src/tokens/tokens.css). Every
 * component imports from here rather than writing its own var(--...)
 * string, so a token reference exists in exactly one place.
 *
 * Only tokens with an actual canonical name in UX-012D §3 are represented
 * — the key sets below are deliberately short because most categories
 * (color primitives, radius, spacing beyond inter-section) have no
 * resolved value yet. Do not add a key here without a corresponding
 * token already declared in tokens.css.
 */

export const textColorToken = {
  primary: "var(--color-text-primary)",
  secondary: "var(--color-text-secondary)",
  tertiary: "var(--color-text-tertiary)",
} as const;
export type TextColorToken = keyof typeof textColorToken;

export const surfaceToken = {
  background: "var(--surface-background)",
  primary: "var(--surface-primary)",
  elevated: "var(--surface-elevated)",
  panel: "var(--surface-panel)",
} as const;
export type SurfaceToken = keyof typeof surfaceToken;

export const borderToken = {
  hairline: { color: "var(--color-border-hairline)", width: "var(--width-border-hairline)" },
  standard: { color: "var(--color-border-standard)", width: "var(--width-border-standard)" },
} as const;
export type BorderToken = keyof typeof borderToken;

/**
 * UX-012D §2 names six conceptual spacing levels; Visual Polish Sprint 1
 * (frontend/src/tokens/global.css) gives all six a value, sourced from
 * this sprint's approved mockup reference rather than a UX-012 citation
 * (none exists). `"inter-section"` remains the only one with its own
 * UX-012D naming-convention worked example (§4); the rest are named to
 * match UX-012D §2's own conceptual labels.
 */
export const spaceToken = {
  "workspace-margin": "var(--space-workspace-margin)",
  "inter-section": "var(--space-inter-section)",
  "intra-section": "var(--space-intra-section)",
  "card-padding": "var(--space-card-padding)",
  row: "var(--space-row)",
  metadata: "var(--space-metadata)",
} as const;
export type SpaceToken = keyof typeof spaceToken;
