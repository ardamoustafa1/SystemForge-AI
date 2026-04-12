"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { useI18n } from "@/i18n/i18n-context";

export function Navbar() {
  const { t } = useI18n();
  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/90 backdrop-blur">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="font-semibold tracking-tight text-foreground">
          SystemForge AI
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          <a href="#features" className="text-sm text-muted transition-colors hover:text-foreground">
            {t("nav.features")}
          </a>
          <a href="#use-cases" className="text-sm text-muted transition-colors hover:text-foreground">
            {t("nav.useCases")}
          </a>
          <a href="#comparison" className="text-sm text-muted transition-colors hover:text-foreground">
            {t("nav.comparison")}
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <Link href="/auth/sign-in">
            <Button variant="ghost">{t("common.signIn")}</Button>
          </Link>
          <Link href="/auth/sign-up">
            <Button>{t("common.getStarted")}</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
