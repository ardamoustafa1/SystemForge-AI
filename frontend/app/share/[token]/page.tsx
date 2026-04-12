"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CalendarDays, FileDown, FileOutput, Home } from "lucide-react";

import { apiBlobPublic, apiPublic } from "@/lib/api";
import { DesignArtifactGrid } from "@/components/design/design-artifact-grid";
import type { DesignRecord } from "@/types/design";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useI18n } from "@/i18n/i18n-context";

export default function SharedDesignPage() {
  const { t } = useI18n();
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [data, setData] = useState<DesignRecord | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        setError("");
        const res = await apiPublic<Omit<DesignRecord, "notes"> & { notes?: string }>(`/public/share/${token}`);
        if (cancelled) return;
        setData({
          ...res,
          notes: "",
          discussion_conversation_id: null,
        } as DesignRecord);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t("sharePage.loadFailed"));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, t]);

  if (error) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <Card className="p-6">
          <p className="text-sm text-red-300">{error}</p>
          <Link
            href="/"
            className={cn(
              "mt-4 inline-flex h-10 items-center justify-center rounded-md border border-border bg-transparent px-4 text-sm font-medium hover:bg-zinc-900",
            )}
          >
            {t("sharePage.backHome")}
          </Link>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 p-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link
          href="/"
          className={cn(
            "inline-flex h-9 items-center justify-center rounded-md px-3 text-sm font-medium hover:bg-zinc-900",
          )}
        >
          <Home className="mr-2 h-4 w-4" />
          {t("sharePage.backHome")}
        </Link>
      </div>

      <PageHeader
        title={data.title}
        subtitle={t("sharePage.subtitle")}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="bg-transparent text-muted">{data.project_type}</Badge>
            <Badge className="bg-transparent text-muted">{t("sharePage.readOnly")}</Badge>
          </div>
        }
      />

      <Card className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <CalendarDays className="h-4 w-4" />
            {t("detail.createdAt")} {new Date(data.created_at).toLocaleString()}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  const ex = await apiPublic<{ content: string }>(`/public/share/${token}/export?format=markdown`);
                  await navigator.clipboard.writeText(ex.content);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <FileOutput className="mr-2 h-4 w-4" />
              {t("detail.copyExport")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  const blob = await apiBlobPublic(`/public/share/${token}/export?format=pdf`);
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${data.title.replace(/[^\w\s-]/g, "").slice(0, 60) || "design"}-systemforge.pdf`;
                  a.click();
                  URL.revokeObjectURL(url);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <FileDown className="mr-2 h-4 w-4" />
              {t("detail.downloadPdf")}
            </Button>
          </div>
        </div>
      </Card>

      <DesignArtifactGrid data={data} t={t} />
    </div>
  );
}
