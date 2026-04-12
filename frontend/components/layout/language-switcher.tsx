"use client";

import { useI18n } from "@/i18n/i18n-context";

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();
  return (
    <label className="flex items-center gap-2 text-xs text-muted">
      <span className="hidden sm:inline">{t("lang.label")}</span>
      <select
        aria-label={t("lang.label")}
        value={language}
        onChange={(e) => setLanguage(e.target.value as "en" | "tr" | "de")}
        className="h-9 rounded-md border border-border bg-transparent px-2 py-1 text-xs"
      >
        <option value="en">English</option>
        <option value="tr">Turkce</option>
        <option value="de">Deutsch</option>
      </select>
    </label>
  );
}
