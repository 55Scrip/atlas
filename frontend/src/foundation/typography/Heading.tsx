import type { HTMLAttributes, ReactNode } from "react";
import { textColorToken, type TextColorToken } from "../tokenRefs";

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;

interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
  level: HeadingLevel;
  color?: TextColorToken;
}

const SIZE_VAR: Record<HeadingLevel, string> = {
  1: "var(--type-size-h1)",
  2: "var(--type-size-h2)",
  3: "var(--type-size-h3)",
  4: "var(--type-size-h4)",
  5: "var(--type-size-h5)",
  6: "var(--type-size-h6)",
};

/**
 * Renders the semantically-correct h1–h6 element for the given level.
 *
 * UX-012D describes six information-hierarchy font-size levels
 * conceptually but never assigns any of them a literal value ("the final
 * size table requires specification under UX-012B or UX-013"). Visual
 * Polish Sprint 1 is that specification, sourced from this sprint's
 * approved mockup reference (`frontend/src/tokens/global.css`'s own file
 * header) rather than a UX-012 citation — filling the gap the prior
 * commit's own comment named rather than leaving it to silent browser
 * defaults. Headings render in the display (serif) family, matching that
 * same reference; body text (`Text`) stays in the prose family, so
 * typography itself carries the primary/secondary distinction the
 * mockups establish, not weight or color alone.
 */
export function Heading({ children, level, color = "primary", style, ...rest }: HeadingProps) {
  const Component = `h${level}` as const;
  return (
    <Component
      {...rest}
      style={{
        fontFamily: "var(--type-family-display)",
        fontWeight: 400,
        fontSize: SIZE_VAR[level],
        lineHeight: "var(--type-heading-line-height)",
        letterSpacing: level === 1 ? "-0.01em" : undefined,
        margin: 0,
        color: textColorToken[color],
        ...style,
      }}
    >
      {children}
    </Component>
  );
}
