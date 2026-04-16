"use client";

import { useI18n } from "@/i18n/i18n-context";
import { Globe } from "lucide-react";

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();
  return (
    <div className="relative inline-flex items-center group">
      <Globe className="absolute left-2.5 h-3.5 w-3.5 text-white/40 group-hover:text-white/80 transition-colors pointer-events-none" />
      <select
        aria-label={t("lang.label")}
        value={language}
        onChange={(e) => setLanguage(e.target.value as "en" | "tr" | "de")}
        className="h-8 w-24 appearance-none rounded-full border border-white/5 bg-white/[0.02] pl-8 pr-8 py-1 text-[11px] font-medium tracking-widest text-white/50 transition-all hover:bg-white/[0.05] hover:border-white/10 hover:text-white/90 focus:outline-none focus:ring-1 focus:ring-white/10 cursor-pointer uppercase"
      >
        <option value="en" className="bg-[#0a0a0a] text-white py-1">EN</option>
        <option value="tr" className="bg-[#0a0a0a] text-white py-1">TR</option>
        <option value="de" className="bg-[#0a0a0a] text-white py-1">DE</option>
      </select>
      <div className="pointer-events-none absolute right-3 text-white/40 group-hover:text-white/80 transition-colors">
        <svg width="9" height="5" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
    </div>
  );
}
