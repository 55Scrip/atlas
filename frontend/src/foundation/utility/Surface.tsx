import type { HTMLAttributes, ReactNode } from "react";
import { borderToken, surfaceToken, type SurfaceToken } from "../tokenRefs";

interface SurfaceProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  tier?: SurfaceToken;
  /** Applies the standard border token. UX-012D names no surface-specific border. */
  bordered?: boolean;
}

/** Generic container applying one of the four Surface Hierarchy tiers. */
export function Surface({ children, tier = "primary", bordered = false, style, ...rest }: SurfaceProps) {
  const border = bordered ? borderToken.standard : undefined;
  return (
    <div
      {...rest}
      style={{
        background: surfaceToken[tier],
        border: border ? `${border.width} solid ${border.color}` : undefined,
        boxSizing: "border-box",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
