import type { ReactNode } from "react";
import styles from "./VisuallyHidden.module.css";

interface VisuallyHiddenProps {
  children: ReactNode;
}

/** Renders content for assistive technology only — see VisuallyHidden.module.css. */
export function VisuallyHidden({ children }: VisuallyHiddenProps) {
  return <span className={styles.visuallyHidden}>{children}</span>;
}
