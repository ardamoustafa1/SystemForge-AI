"use client";

import { ReactNode } from "react";
import { useI18n } from "@/i18n/i18n-context";

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  const { t } = useI18n();
  return (
    <div className="grid min-h-screen grid-cols-1 bg-background text-foreground lg:grid-cols-2">
      <div className="hidden border-r border-white/5 bg-[#0a0a0a] lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div>
          <p className="text-sm font-medium tracking-wide text-white/80">SystemForge AI</p>
          <h2 className="mt-6 text-3xl font-medium tracking-tight text-white/90">
            {t("auth.leftTitle")}
          </h2>
          <p className="mt-4 max-w-md text-sm text-white/50 font-light">
            {t("auth.leftDesc")}
          </p>
        </div>
        <p className="text-[11px] uppercase tracking-widest font-medium text-white/30">{t("landing.badge")}</p>
      </div>
      <div className="container-page flex items-center py-10">
        <div className="mx-auto w-full max-w-md rounded-2xl border border-white/5 bg-white/[0.02] p-8 shadow-2xl backdrop-blur-sm">
          <h1 className="text-2xl font-medium tracking-tight text-white/90">{title}</h1>
          <p className="mt-1.5 text-sm text-white/50 font-light">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
