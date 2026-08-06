import { useTranslation } from "../i18n";

export function LoadingBoundary() {
  const { t } = useTranslation();

  return (
    <p role="status" aria-live="polite">
      {t("common.loading")}
    </p>
  );
}
