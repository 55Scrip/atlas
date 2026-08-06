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
 * color. Not a filled bright button." The primary variant therefore
 * stays an outline (never a solid fill) at primary text color — the
 * citation this component has always followed. Visual Polish Sprint 1
 * (per this sprint's approved mockup reference,
 * `frontend/src/tokens/global.css`'s own file header) gives that outline
 * an accent tint rather than the neutral border — accent color
 * communicating "this is the primary action," compatible with "clear
 * outline," not a departure from it — plus real padding and radius so
 * the control reads as a considered button rather than a bare
 * `<button>`. The tertiary variant (Inline/Section Action) stays
 * unbordered, at tertiary text color, unchanged.
 */
export function Button({ variant = "primary", className, style, ...rest }: ButtonProps) {
  return (
    <button
      {...rest}
      className={[styles.button, styles[variant], className].filter(Boolean).join(" ")}
      style={{
        color: textColorToken[variant],
        ...style,
      }}
    />
  );
}
