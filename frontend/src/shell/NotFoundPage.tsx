import { useTranslation } from "../i18n";

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <main>
      <h1>{t("shell.notFound.title")}</h1>
      <p>{t("shell.notFound.body")}</p>
    </main>
  );
}
