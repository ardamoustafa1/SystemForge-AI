"use client";

import Link from "next/link";
import { useI18n } from "@/i18n/i18n-context";

export function Footer() {
  const { t } = useI18n();
  return (
    <footer className="border-t border-white/[0.02] py-12">
      <div className="container-page flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-white/80">SystemForge AI</p>
          <p className="mt-2 text-sm text-white/40 font-light">{t("footer.tagline")}</p>
        </div>
        <div className="flex items-center gap-6 text-sm text-white/40 font-medium">
          <Link href="#features" className="hover:text-white/80 transition-colors">
            {t("nav.features")}
          </Link>
          <Link href="#use-cases" className="hover:text-white/80 transition-colors">
            {t("nav.useCases")}
          </Link>
          <Link href="/auth/sign-up" className="hover:text-white/80 transition-colors">
            {t("common.getStarted")}
          </Link>
        </div>
      </div>
    </footer>
  );
}
