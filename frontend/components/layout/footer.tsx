"use client";

import Link from "next/link";
import { useI18n } from "@/i18n/i18n-context";

export function Footer() {
  const { t } = useI18n();
  return (
    <footer className="border-t border-border/80 py-10">
      <div className="container-page flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium">SystemForge AI</p>
          <p className="mt-1 text-sm text-muted">{t("footer.tagline")}</p>
        </div>
        <div className="flex items-center gap-5 text-sm text-muted">
          <Link href="/features" className="hover:text-foreground">
            {t("nav.features")}
          </Link>
          <Link href="/use-cases" className="hover:text-foreground">
            {t("nav.useCases")}
          </Link>
          <Link href="/auth/sign-up" className="hover:text-foreground">
            {t("common.getStarted")}
          </Link>
        </div>
      </div>
    </footer>
  );
}
