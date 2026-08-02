import type { HTMLAttributes, ReactNode } from "react";
import { textColorToken, type TextColorToken } from "../tokenRefs";

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;

interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
  level: HeadingLevel;
  color?: TextColorToken;
}

/**
 * Renders the semantically-correct h1–h6 element for the given level.
 *
 * UX-012D describes six information-hierarchy font-size levels
 * conceptually but never assigns any of them a literal value anywhere in
 * the corpus (UX-012A: "the final size table requires specification
 * under UX-012B or UX-013"). No font-size or font-weight is set here —
 * only semantic structure plus the same family/color tokens Text uses.
 * Browser default heading sizing applies until that governed scale
 * exists; this is not an omission, it is the honest state of the
 * evidence.
 */
export function Heading({ children, level, color = "primary", style, ...rest }: HeadingProps) {
  const Component = `h${level}` as const;
  return (
    <Component
      {...rest}
      style={{ fontFamily: "var(--type-family-prose)", color: textColorToken[color], ...style }}
    >
      {children}
    </Component>
  );
}
