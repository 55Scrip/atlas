import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import { spaceToken, type SpaceToken } from "../tokenRefs";

interface InlineProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Omit for no gap. Only `"inter-section"` is canonical — see tokenRefs.ts. */
  gap?: SpaceToken;
  align?: CSSProperties["alignItems"];
  wrap?: boolean;
}

/** Horizontal flex composition primitive. */
export function Inline({ children, gap, align, wrap = false, style, ...rest }: InlineProps) {
  return (
    <div
      {...rest}
      style={{
        display: "flex",
        flexDirection: "row",
        flexWrap: wrap ? "wrap" : "nowrap",
        gap: gap ? spaceToken[gap] : undefined,
        alignItems: align,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
