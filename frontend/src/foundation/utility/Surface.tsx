import type { HTMLAttributes, ReactNode } from "react";
import { borderToken, surfaceToken, type SurfaceToken } from "../tokenRefs";

interface SurfaceProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  tier?: SurfaceToken;
  /** Applies the standard border token. UX-012D names no surface-specific border. */
  bordered?: boolean;
}

/**
 * Generic container applying one of the four Surface Hierarchy tiers.
 *
 * Visual Polish Sprint 1: `primary` — the tier every real page in this
 * application actually uses for its card-like sections — now carries
 * real card treatment (radius, padding, a soft hairline border, and a
 * restrained shadow), per this sprint's approved mockup reference
 * (`frontend/src/tokens/global.css`'s own file header). `background` is
 * left bare (it's meant to render as the page canvas itself, already set
 * on `<body>` in tokens.css, not a card); `elevated`/`panel` step up
 * through the same surface ladder with the same card treatment, for
 * whenever a page needs visual layering beyond the flat `primary` cards
 * every page uses today.
 */
export function Surface({ children, tier = "primary", bordered = false, style, ...rest }: SurfaceProps) {
  const isCard = tier !== "background";
  const border = bordered || isCard ? borderToken.hairline : undefined;
  return (
    <div
      {...rest}
      style={{
        background: surfaceToken[tier],
        border: border ? `${border.width} solid ${border.color}` : undefined,
        borderRadius: isCard ? "var(--radius-card)" : undefined,
        padding: isCard ? "var(--space-card-padding)" : undefined,
        boxShadow: isCard ? "var(--elevation-card-shadow)" : undefined,
        boxSizing: "border-box",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
