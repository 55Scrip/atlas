import type { HTMLAttributes, ReactNode } from "react";

interface ContainerProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

/**
 * Horizontal centering wrapper.
 *
 * UX-012D §2 names a "maximum editorial column width" conceptually;
 * UX-012A's own "approximately 560–640px" figure was explicitly flagged
 * unconfirmed. Visual Polish Sprint 1 confirms a value via its approved
 * mockup reference (`frontend/src/tokens/global.css`'s own file header),
 * widened from that editorial figure since every real page in this
 * application (Dashboard, Portfolio, History) is list-and-card dense
 * rather than long-form reading — the closest implementation per this
 * sprint's own "do not block on ambiguity" instruction. Horizontal page
 * padding uses the same workspace-margin token the mockups use.
 */
export function Container({ children, style, ...rest }: ContainerProps) {
  return (
    <div
      {...rest}
      style={{
        width: "100%",
        maxWidth: "var(--container-max-width)",
        marginInline: "auto",
        paddingInline: "var(--space-workspace-margin)",
        boxSizing: "border-box",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
