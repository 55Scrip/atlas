import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import { spaceToken, type SpaceToken } from "../tokenRefs";

interface StackProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Omit for no gap. Only `"inter-section"` is canonical — see tokenRefs.ts. */
  gap?: SpaceToken;
  align?: CSSProperties["alignItems"];
}

/** Vertical flex composition primitive. */
export function Stack({ children, gap, align, style, ...rest }: StackProps) {
  return (
    <div
      {...rest}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: gap ? spaceToken[gap] : undefined,
        alignItems: align,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
