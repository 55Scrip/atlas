import type { HTMLAttributes, ReactNode } from "react";

interface ContainerProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

/**
 * Horizontal centering wrapper.
 *
 * UX-012D §2 names a "maximum editorial column width" and "maximum
 * analytical column width" conceptually; UX-012A gives the only figure
 * for either ("approximately 560–640px") but immediately qualifies it as
 * unconfirmed ("this should be confirmed through rendering"). No
 * maxWidth is applied here — doing so would treat an explicitly
 * unconfirmed approximation as a canonical value. Container performs
 * structural centering only, pending that governed value.
 */
export function Container({ children, style, ...rest }: ContainerProps) {
  return (
    <div
      {...rest}
      style={{ width: "100%", marginInline: "auto", boxSizing: "border-box", ...style }}
    >
      {children}
    </div>
  );
}
