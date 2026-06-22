"use client";

import { ReactNode } from "react";
import { AuthProvider } from "@/features/auth/auth-context";
import { I18nProvider } from "@/i18n/i18n-context";
import { ThemeSync } from "@/components/theme-sync";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <I18nProvider>
      <AuthProvider>
        <ThemeSync />
        {children}
      </AuthProvider>
    </I18nProvider>
  );
}
