"use client";

import Link from "next/link";
import { useI18n } from "@/i18n/i18n-context";

export default function NotFoundPage() {
  const { t } = useI18n();
  return (
    <div className="container-page py-10">
      <h1 className="text-2xl font-semibold">{t("common.pageNotFound")}</h1>
      <p className="mt-2 text-sm text-muted">{t("common.routeNotFound")}</p>
      <Link href="/" className="mt-4 inline-block text-sm text-brand">
        {t("common.backToHome")}
      </Link>
    </div>
  );
}
