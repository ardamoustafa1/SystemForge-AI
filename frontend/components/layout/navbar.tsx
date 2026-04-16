"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { useI18n } from "@/i18n/i18n-context";

export function Navbar() {
  const { t } = useI18n();
  return (
    <header className="sticky top-0 z-30 border-b border-white/[0.05] bg-background/60 backdrop-blur-xl">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="font-medium tracking-tight text-white/90">
          SystemForge AI
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          <a href="#features" className="text-sm font-medium text-white/50 transition-colors hover:text-white/90">
            {t("nav.features")}
          </a>
          <a href="#use-cases" className="text-sm font-medium text-white/50 transition-colors hover:text-white/90">
            {t("nav.useCases")}
          </a>
          <a href="#comparison" className="text-sm font-medium text-white/50 transition-colors hover:text-white/90">
            {t("nav.comparison")}
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <Link href="/auth/sign-in">
            <Button variant="ghost" className="rounded-full text-white/70 hover:bg-white/[0.03] hover:text-white font-medium">
              {t("common.signIn")}
            </Button>
          </Link>
          <Link href="/auth/sign-up">
            <Button className="rounded-full bg-white text-black hover:bg-white/90 font-medium">
              {t("common.getStarted")}
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
