"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Activity, Clock3, Search, ShieldCheck, DollarSign, AlertTriangle } from "lucide-react";

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
type OpsSummary = {
  total_designs: number;
  generating_count: number;
  approved_count: number;
  review_pending_count: number;
  avg_generation_ms: number;
  monthly_cost_min_total: number;
  monthly_cost_max_total: number;
  risk_drift_count: number;
};

export default function DashboardPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<DesignSummary[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [ops, setOps] = useState<OpsSummary | null>(null);

  useEffect(() => {
    setLoading(true);
    setError("");
    api<DesignListResponse>(`/designs${q ? `?q=${encodeURIComponent(q)}` : ""}`)
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load dashboard data"))
      .finally(() => setLoading(false));
    api<OpsSummary>("/dashboard/ops-summary").then(setOps).catch(() => setOps(null));
  }, [q]);

  const stats = [
    { label: t("dashboard.totalDesigns"), value: String(ops?.total_designs ?? items.length), icon: Activity },
    { label: t("dashboard.reviewPending"), value: String(ops?.review_pending_count ?? 0), icon: Clock3 },
    { label: t("dashboard.approvedDesigns"), value: String(ops?.approved_count ?? 0), icon: ShieldCheck },
    {
      label: t("dashboard.monthlyCostRange"),
      value: ops ? `$${ops.monthly_cost_min_total.toLocaleString()} - $${ops.monthly_cost_max_total.toLocaleString()}` : "—",
      icon: DollarSign,
    },
    { label: t("dashboard.riskDrift"), value: String(ops?.risk_drift_count ?? 0), icon: AlertTriangle },
  ];

  return (
    <div className="space-y-8 animate-in fade-in zoom-in-[0.98] duration-500 pb-20">
      <PageHeader
        title={t("dashboard.title")}
        subtitle={t("dashboard.subtitle")}
        actions={
          <Link href="/dashboard/new">
            <Button className="bg-white text-black hover:bg-white/90 font-medium">
              {t("common.createNewDesign")}
            </Button>
          </Link>
        }
      />

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
        {stats.map((item) => (
          <Card key={item.label} className="group relative overflow-hidden rounded-2xl border border-white/5 bg-[#0a0a0a] p-6 transition-all hover:bg-white/[0.02] hover:border-white/10 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.5)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-medium uppercase tracking-wider text-white/40">{item.label}</p>
                <p className="mt-3 text-2xl font-medium text-white/90">{item.value}</p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.03] ring-1 ring-white/5 transition-all group-hover:bg-white/[0.06] group-hover:ring-white/10">
                <item.icon className="h-4 w-4 text-white/50 group-hover:text-white transition-colors" strokeWidth={1.5} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mt-8 pt-8 border-t border-white/5">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("dashboard.searchPlaceholder")}
            className="pl-11 h-12 bg-[#0a0a0a] border-white/5 text-white/90 placeholder:text-white/30 rounded-xl focus-visible:ring-1 focus-visible:ring-white/20 focus-visible:border-white/20"
          />
        </div>
        <div className="flex gap-3">
          <Button variant="outline" disabled className="h-12 border-white/5 bg-[#0a0a0a] text-white/40 rounded-xl font-medium">
            {t("dashboard.statusFilter")}
          </Button>
          <Button variant="outline" disabled className="h-12 border-white/5 bg-[#0a0a0a] text-white/40 rounded-xl font-medium hidden sm:flex">
            {t("dashboard.projectTypeFilter")}
          </Button>
        </div>
      </div>

      <section className="space-y-4">
        <div className="flex items-center justify-between pb-2">
          <h2 className="text-base font-medium tracking-wide text-white/90">{t("dashboard.recentDesigns")}</h2>
          <Link href="/dashboard/designs">
            <Badge className="bg-transparent text-white/40 hover:text-white transition-colors cursor-pointer border border-transparent hover:border-white/10 px-3 py-1 font-medium">
              {t("dashboard.viewFullHistory")}
            </Badge>
          </Link>
        </div>

      {error ? (
        <Card className="rounded-2xl border-red-500/10 bg-red-500/[0.02] p-8 text-center">
          <p className="text-sm text-red-400">{error}</p>
          <Button className="mt-4 bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/20" variant="outline" onClick={() => window.location.reload()}>
            {t("common.retry")}
          </Button>
        </Card>
      ) : loading ? (
        <div className="grid gap-3">
          <Skeleton className="h-[88px] w-full rounded-2xl bg-white/[0.02] border border-white/5" />
          <Skeleton className="h-[88px] w-full rounded-2xl bg-white/[0.02] border border-white/5" />
          <Skeleton className="h-[88px] w-full rounded-2xl bg-white/[0.02] border border-white/5" />
        </div>
      ) : items.length === 0 ? (
        <Card className="rounded-2xl border border-dashed border-white/10 bg-white/[0.01] p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white/[0.03] ring-1 ring-white/5 mb-4">
            <Activity className="h-5 w-5 text-white/40" />
          </div>
          <h3 className="text-lg font-medium text-white/90">{t("dashboard.noDesignsTitle")}</h3>
          <p className="mx-auto mt-2 max-w-sm text-sm text-white/40 font-light">
            {t("dashboard.noDesignsDesc")}
          </p>
          <Link href="/dashboard/new" className="mt-6 inline-block">
            <Button className="bg-white text-black hover:bg-white/90 font-medium">{t("dashboard.createFirst")}</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid gap-3">
          {items.map((d) => (
            <Link key={d.id} href={`/dashboard/designs/${d.id}`}>
              <Card className="group flex flex-col gap-3 rounded-2xl border border-white/5 bg-[#0a0a0a] p-6 sm:flex-row sm:items-center sm:justify-between transition-all duration-300 hover:bg-white/[0.03] hover:border-white/10 hover:shadow-[0_0_30px_-5px_rgba(255,255,255,0.03)] cursor-pointer">
                <div>
                  <div className="text-base font-medium text-white/90 group-hover:text-white transition-colors">{d.title}</div>
                  <div className="mt-1.5 text-[13px] text-white/40 font-light">{d.project_type}</div>
                </div>
                <div className="flex items-center gap-6 justify-between sm:justify-end">
                  <span className="text-[11px] font-medium tracking-widest text-white/30 uppercase">
                    {new Date(d.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/5 bg-transparent transition-colors group-hover:bg-white/10 group-hover:border-white/20">
                     <span className="text-white/40 group-hover:text-white opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0">→</span>
                  </div>
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
