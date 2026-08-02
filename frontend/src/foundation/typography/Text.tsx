import type { HTMLAttributes, ReactNode } from "react";
import { textColorToken, type TextColorToken } from "../tokenRefs";

interface TextProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  color?: TextColorToken;
  as?: "span" | "p" | "label";
}

/**
 * Body-scale text.
 *
 * UX-012A's own six-level type-size scale has never been given literal
 * px values for any level ("the specific pixel values [...] depend on
 * the final font family choice [...] requires specification under
 * UX-012B or UX-013"). Only the body-text minimum (15px) and its line
 * height (1.65) are evidenced (UX-012A §15) — Text renders at that one
 * evidenced scale. There is no `size` prop because no other size is
 * evidenced; adding one would mean inventing values for the missing
 * levels.
 */
export function Text({ children, color = "primary", as = "span", style, ...rest }: TextProps) {
  const Component = as;
  return (
    <Component
      {...rest}
      style={{
        fontFamily: "var(--type-family-prose)",
        fontSize: "var(--type-body-min-size)",
        lineHeight: "var(--type-body-line-height)",
        color: textColorToken[color],
        ...style,
      }}
    >
      {children}
    </Component>
  );
}
