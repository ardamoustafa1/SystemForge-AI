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
    <div className="grid min-h-screen grid-cols-1 bg-background lg:grid-cols-2">
      <div className="hidden border-r border-border lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div>
          <p className="text-sm font-medium text-brand">SystemForge AI</p>
          <h2 className="mt-6 text-3xl font-semibold tracking-tight">
            Production-grade system design workspace for serious engineering teams.
          </h2>
          <p className="mt-4 max-w-md text-sm text-muted">
            Structured architecture outputs, trade-offs, scorecards, and implementation roadmaps in one workflow.
          </p>
        </div>
        <p className="text-xs text-muted">{t("landing.badge")}</p>
      </div>
      <div className="container-page flex items-center py-10">
        <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-surface p-7 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-sm text-muted">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
}
