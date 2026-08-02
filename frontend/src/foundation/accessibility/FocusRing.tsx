import { cloneElement, type ReactElement } from "react";
import styles from "./focus-ring.module.css";

interface FocusRingProps {
  /** The single focusable element to apply the canonical focus ring to. */
  children: ReactElement<{ className?: string }>;
}

/**
 * Applies the canonical Atlas focus ring (see focus-ring.module.css) to an
 * arbitrary focusable child, by cloning it rather than wrapping it in an
 * extra DOM node — the child itself must remain the actual focus target.
 *
 * Button and Link already apply this same rule directly via CSS Modules'
 * `composes`; use FocusRing for any other focusable element that isn't
 * one of those two.
 */
export function FocusRing({ children }: FocusRingProps) {
  return cloneElement(children, {
    className: [children.props.className, styles.focusRing].filter(Boolean).join(" "),
  });
}
