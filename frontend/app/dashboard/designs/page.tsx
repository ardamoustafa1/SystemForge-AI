"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpDown, CalendarDays, Search } from "lucide-react";

import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useI18n } from "@/i18n/i18n-context";

type DesignSummary = {
  id: number;
  title: string;
  project_type: string;
  status: string;
  created_at: string;
  updated_at: string;
};
type DesignListResponse = { items: DesignSummary[]; total: number; page: number; page_size: number };

export default function DesignsHistoryPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<DesignSummary[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState<"recent" | "title">("recent");

  useEffect(() => {
    setLoading(true);
    setError("");
    api<DesignListResponse>(`/designs${query ? `?q=${encodeURIComponent(query)}` : ""}`)
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : t("history.loadFailed")))
      .finally(() => setLoading(false));
  }, [query]);

  const sortedItems = useMemo(() => {
    const copy = [...items];
    if (sortBy === "title") {
      return copy.sort((a, b) => a.title.localeCompare(b.title));
    }
    return copy.sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at));
  }, [items, sortBy]);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("history.title")}
        subtitle={t("history.subtitle")}
        actions={
          <Link href="/dashboard/new">
            <Button>{t("common.createNewDesign")}</Button>
          </Link>
        }
      />

      <div className="flex flex-col sm:flex-row gap-4 mt-8 pt-8 border-t border-white/5">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("history.searchPlaceholder")}
            className="pl-11 h-12 bg-[#0a0a0a] border-white/5 text-white/90 placeholder:text-white/30 rounded-xl focus-visible:ring-1 focus-visible:ring-white/20 focus-visible:border-white/20"
          />
        </div>
        <div className="flex gap-3">
          <Button variant="outline" disabled className="h-12 border-white/5 bg-[#0a0a0a] text-white/40 rounded-xl font-medium">
            {t("history.statusFilterSoon")}
          </Button>
          <Button
            variant="outline"
            className="h-12 border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 rounded-xl font-medium"
            onClick={() => setSortBy((current) => (current === "recent" ? "title" : "recent"))}
          >
            <ArrowUpDown className="mr-2 h-4 w-4" />
            {sortBy === "recent" ? t("history.sortRecent") : t("history.sortTitle")}
          </Button>
        </div>
      </div>

      {error ? (
        <Card className="p-6">
          <p className="text-sm text-red-300">{error}</p>
          <Button className="mt-3" variant="outline" onClick={() => window.location.reload()}>
            {t("common.retry")}
          </Button>
        </Card>
      ) : loading ? (
        <div className="grid gap-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : sortedItems.length === 0 ? (
        <Card className="p-10 text-center">
          <h3 className="text-lg font-semibold">{t("history.emptyTitle")}</h3>
          <p className="mx-auto mt-2 max-w-lg text-sm text-muted">
            {t("history.emptyDesc")}
          </p>
          <Link href="/dashboard/new" className="mt-5 inline-block">
            <Button>{t("dashboard.createFirst")}</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid gap-3">
          {sortedItems.map((design) => (
            <Link key={design.id} href={`/dashboard/designs/${design.id}`}>
              <Card className="group flex flex-col gap-3 rounded-2xl border border-white/5 bg-[#0a0a0a] p-6 sm:flex-row sm:items-center sm:justify-between transition-all duration-300 hover:bg-white/[0.03] hover:border-white/10 hover:shadow-[0_0_30px_-5px_rgba(255,255,255,0.03)] cursor-pointer">
                <div>
                  <h3 className="text-base font-medium text-white/90 group-hover:text-white transition-colors">{design.title}</h3>
                  <p className="mt-1 text-[13px] text-white/40 font-light">{design.project_type}</p>
                </div>
                <div className="flex flex-wrap items-center gap-4 justify-between sm:justify-end">
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-medium tracking-widest text-white/30 uppercase flex items-center">
                      <CalendarDays className="mr-1.5 h-3.5 w-3.5" />
                      {new Date(design.created_at).toLocaleDateString()}
                    </span>
                    <span className="text-white/10">•</span>
                    <span className="text-[11px] font-medium tracking-widest text-white/30 uppercase">
                      {t("history.updatedLabel")} {new Date(design.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/5 bg-transparent transition-colors group-hover:bg-white/10 group-hover:border-white/20 ml-2 hidden sm:flex">
                     <span className="text-white/40 group-hover:text-white opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0">→</span>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
