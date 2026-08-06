import { Component, type ErrorInfo, type ReactNode } from "react";
import { LanguageContext, type LanguageContextValue } from "../i18n/LanguageContext";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * A class component, so the language can't be read via `useTranslation`
 * (a hook) — `static contextType` is React's own class-component
 * equivalent, reading from the same `LanguageContext` every functional
 * component uses. `LanguageProvider` always wraps this boundary (see
 * `main.tsx`), so `this.context` is never actually null at runtime.
 */
export class ErrorBoundary extends Component<Props, State> {
  static override contextType = LanguageContext;
  declare context: LanguageContextValue;

  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Atlas application shell caught an error:", error, info.componentStack);
  }

  override render() {
    if (this.state.error) {
      return (
        <div role="alert">
          <h1>{this.context.t("shell.error.title")}</h1>
          <p>{this.state.error.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
