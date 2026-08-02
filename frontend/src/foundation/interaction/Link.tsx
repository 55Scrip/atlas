import type { AnchorHTMLAttributes } from "react";
import styles from "./Link.module.css";

type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement>;

/**
 * Inline navigation-style action. UX-012D §3 Canonical Attribution &
 * Action Text Mapping: Inline Action's own named examples explicitly
 * include navigation-style links ("View source →") -> color.text.tertiary.
 *
 * No min touch-target size is applied here (unlike Button): UX-012A §15
 * states touch targets "may extend beyond the visible element boundary
 * through transparent padding," which for an inline text link depends on
 * its surrounding layout context — not something this generic primitive
 * can apply without assuming a context it doesn't have.
 */
export function Link({ className, ...rest }: LinkProps) {
  return <a {...rest} className={[styles.link, className].filter(Boolean).join(" ")} />;
}
