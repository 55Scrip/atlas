import type { HTMLAttributes, ReactNode } from "react";
import { textColorToken, type TextColorToken } from "../tokenRefs";

interface LabelProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  color?: TextColorToken;
}

/**
 * Compact uppercase section label (Visual Fidelity Pass, Figma
 * `atlas-investment-case-v3` / `atlas-portfolio-redesign`): the small
 * letter-spaced caption that carries section hierarchy in the approved
 * designs ("EXECUTIVE SUMMARY", "ATLAS VIEW", "FINANCIALS (USD)")
 * instead of a large card heading. Typography-as-hierarchy, not a
 * Surface boundary.
 */
export function Label({ children, color = "tertiary", style, ...rest }: LabelProps) {
  return (
    <p
      {...rest}
      style={{
        fontFamily: "var(--type-family-metadata)",
        fontSize: "11px",
        fontWeight: 600,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: textColorToken[color],
        margin: 0,
        ...style,
      }}
    >
      {children}
    </p>
  );
}
