"use client";

import { useI18n } from "@/i18n/i18n-context";

export default function RootError({ reset }: { error: Error; reset: () => void }) {
  const { t } = useI18n();
  return (
    <div className="container-page py-10">
      <h2 className="text-xl font-semibold">{t("common.somethingWentWrong")}</h2>
      <p className="mt-2 text-sm text-muted">{t("common.recoverableUiError")}</p>
      <button onClick={reset} className="mt-4 rounded-md border border-border px-4 py-2 text-sm">
        {t("common.tryAgain")}
      </button>
    </div>
  );
}
