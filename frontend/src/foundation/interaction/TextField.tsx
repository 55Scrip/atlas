import type { InputHTMLAttributes } from "react";
import styles from "./TextField.module.css";

type TextFieldProps = InputHTMLAttributes<HTMLInputElement>;

/**
 * Atlas UX Freeze v1 — "Search field" is a named, frozen component (the
 * Component Freeze, §7), but no styled input control existed anywhere in
 * Foundation before this: Discover's search used a bare `<input>` with no
 * width, no Design System typography, and no dark-theme styling at all —
 * the exact placeholder-clipping defect the freeze's own fidelity review
 * found. This is the first real implementation of that frozen component,
 * following Button.tsx's own token/composition conventions so any future
 * page that needs a text input reuses this rather than another bare
 * `<input>`.
 */
export function TextField({ className, ...rest }: TextFieldProps) {
  return <input {...rest} className={[styles.field, className].filter(Boolean).join(" ")} />;
}
