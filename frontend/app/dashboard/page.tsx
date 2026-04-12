"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Activity, Clock3, Search, ShieldCheck } from "lucide-react";

import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useI18n } from "@/i18n/i18n-context";

type DesignSummary = { id: number; title: string; project_type: string; created_at: string; status: string };
type DesignListResponse = { items: DesignSummary[]; total: number; page: number; page_size: number };

export default function DashboardPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<DesignSummary[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    api<DesignListResponse>(`/designs${q ? `?q=${encodeURIComponent(q)}` : ""}`)
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load dashboard data"))
      .finally(() => setLoading(false));
  }, [q]);

  const stats = [
    { label: "Total Designs", value: items.length.toString(), icon: Activity },
    { label: "Recent Activity", value: items.length > 0 ? "Active" : "No activity", icon: Clock3 },
    { label: "Quality Posture", value: "Scorecards enabled", icon: ShieldCheck },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("dashboard.title")}
        subtitle={t("dashboard.subtitle")}
        actions={
          <Link href="/dashboard/new">
            <Button>{t("common.createNewDesign")}</Button>
          </Link>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((item) => (
          <Card key={item.label} className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted">{item.label}</p>
                <p className="mt-1 text-lg font-semibold">{item.value}</p>
              </div>
              <item.icon className="h-4 w-4 text-muted" />
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-4">
        <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("dashboard.searchPlaceholder")}
              className="pl-9"
            />
          </div>
          <Button variant="outline" disabled title="Filter support is planned">
            Status Filter (Soon)
          </Button>
          <Button variant="outline" disabled title="Filter support is planned">
            Project Type (Soon)
          </Button>
        </div>
      </Card>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">{t("dashboard.recentDesigns")}</h2>
          <Link href="/dashboard/designs">
            <Badge className="bg-transparent text-muted hover:text-foreground">{t("dashboard.viewFullHistory")}</Badge>
          </Link>
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
      ) : items.length === 0 ? (
        <Card className="p-10 text-center">
          <h3 className="text-lg font-semibold">{t("dashboard.noDesignsTitle")}</h3>
          <p className="mx-auto mt-2 max-w-lg text-sm text-muted">
            {t("dashboard.noDesignsDesc")}
          </p>
          <Link href="/dashboard/new" className="mt-5 inline-block">
            <Button>{t("dashboard.createFirst")}</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid gap-3">
          {items.map((d) => (
            <Link key={d.id} href={`/dashboard/designs/${d.id}`}>
              <Card className="p-4 transition hover:border-zinc-500 hover:bg-zinc-900/20">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="font-medium">{d.title}</div>
                    <div className="text-sm text-muted">{d.project_type}</div>
                  </div>
                  <Badge className="w-fit bg-transparent text-muted">
                    {new Date(d.created_at).toLocaleDateString()}
                  </Badge>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
      </section>
    </div>
  );
}
