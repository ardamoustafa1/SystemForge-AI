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
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load design history"))
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

      <Card className="p-4">
        <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("history.searchPlaceholder")}
              className="pl-9"
            />
          </div>
          <Button variant="outline" disabled title="Filter support is planned">
            Status Filter (Soon)
          </Button>
          <Button
            variant="outline"
            onClick={() => setSortBy((current) => (current === "recent" ? "title" : "recent"))}
          >
            <ArrowUpDown className="mr-2 h-4 w-4" />
            {sortBy === "recent" ? "Sort: Recent" : "Sort: Title"}
          </Button>
        </div>
      </Card>

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
              <Card className="p-4 transition hover:border-zinc-500 hover:bg-zinc-900/20">
                <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-center">
                  <div>
                    <h3 className="font-medium">{design.title}</h3>
                    <p className="mt-1 text-sm text-muted">{design.project_type}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <Badge className="bg-transparent text-muted">
                      <CalendarDays className="mr-1 h-3 w-3" />
                      {new Date(design.created_at).toLocaleDateString()}
                    </Badge>
                    <Badge className="bg-transparent text-muted">Updated {new Date(design.updated_at).toLocaleDateString()}</Badge>
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
