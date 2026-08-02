import type { ButtonHTMLAttributes } from "react";
import { textColorToken } from "../tokenRefs";
import styles from "./Button.module.css";

type ButtonVariant = "primary" | "tertiary";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * UX-012D §3 Canonical Attribution & Action Text Mapping resolves
   * exactly two Action tiers to a token: Primary Action -> color.text.primary,
   * Inline/Section Action -> color.text.tertiary. UX-012B's own distinct
   * "Secondary Action" was explicitly left unresolved by that mapping
   * ("a separate, footer-scoped concept") — there is deliberately no
   * "secondary" variant here.
   */
  variant?: ButtonVariant;
}

/**
 * UX-012B's own Primary Action definition: "Clearly the highest-emphasis
 * action control — defined surface or clear outline at primary text
 * color. Not a filled bright button." The primary variant therefore gets
 * an outline (the existing generic `color.border.standard` /
 * `width.border.standard` tokens — no button-specific border token
 * exists) and primary text color; no background fill. The tertiary
 * variant (Inline/Section Action) is unbordered, at tertiary text color.
 */
export function Button({ variant = "primary", className, style, ...rest }: ButtonProps) {
  return (
    <button
      {...rest}
      className={[styles.button, className].filter(Boolean).join(" ")}
      style={{
        color: textColorToken[variant],
        border:
          variant === "primary"
            ? "var(--width-border-standard) solid var(--color-border-standard)"
            : "none",
        ...style,
      }}
    />
  );
}
