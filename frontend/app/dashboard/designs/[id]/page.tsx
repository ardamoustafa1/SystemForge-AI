"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CalendarDays, FileDown, FileOutput, Link2, RefreshCw, Trash2 } from "lucide-react";

import { api, apiBlob } from "@/lib/api";
import { DesignArtifactGrid } from "@/components/design/design-artifact-grid";
import { DesignRecord } from "@/types/design";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useI18n } from "@/i18n/i18n-context";
import { RealtimeMessagingPanel } from "@/components/realtime/realtime-messaging-panel";

export default function DesignDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<DesignRecord | null>(null);
  const [error, setError] = useState("");
  const [notes, setNotes] = useState("");
  const [notesSaveState, setNotesSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [isBusy, setIsBusy] = useState<"export" | "regenerate" | "delete" | "share" | null>(null);
  const [actionMessage, setActionMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [scaleStance, setScaleStance] = useState<"balanced" | "conservative" | "aggressive">("balanced");
  const [versions, setVersions] = useState<
    { id: number; created_at: string; model_name: string; scale_stance: string; generation_ms: number }[]
  >([]);
  const [compareA, setCompareA] = useState<number | "">("");
  const [compareB, setCompareB] = useState<number | "">("");
  const [diffText, setDiffText] = useState<string | null>(null);

  const id = Number(params.id);

  const load = async () => {
    try {
      setError("");
      const res = await api<DesignRecord>(`/designs/${id}`);
      setData(res);
      setNotes(res.notes ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("detail.loadFailed"));
    }
  };

  useEffect(() => {
    if (id) load();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    api<
      { id: number; created_at: string; model_name: string; scale_stance: string; generation_ms: number }[]
    >(`/designs/${id}/versions`)
      .then(setVersions)
      .catch(() => setVersions([]));
  }, [id, data?.updated_at]);

  useEffect(() => {
    if (!data) return;
    const timer = setTimeout(async () => {
      if (notes === data.notes) return;
      setNotesSaveState("saving");
      try {
        const res = await api<{ notes: string }>(`/designs/${id}/notes`, {
          method: "PATCH",
          body: JSON.stringify({ notes }),
        });
        setData((prev) => (prev ? { ...prev, notes: res.notes } : prev));
        setNotesSaveState("saved");
      } catch {
        setNotesSaveState("error");
      }
    }, 700);
    return () => clearTimeout(timer);
  }, [notes, data, id]);

  if (error) {
    return (
      <Card className="p-6">
        <p className="text-sm text-red-300">{error}</p>
        <Button className="mt-3" variant="outline" onClick={load}>
          {t("common.retry")}
        </Button>
      </Card>
    );
  }
  if (!data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-56 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.title}
        subtitle={t("detail.subtitle")}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="bg-transparent text-muted">{data.project_type}</Badge>
            <Badge className="bg-transparent text-muted">{data.status}</Badge>
          </div>
        }
      />

      <Card className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <CalendarDays className="h-4 w-4" />
            {t("detail.createdAt")} {new Date(data.created_at).toLocaleString()}
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <div className="min-w-[140px]">
              <Label className="text-xs text-muted">{t("detail.scaleStance")}</Label>
              <select
                className="mt-1 h-9 w-full rounded-md border border-border bg-transparent px-2 text-sm"
                value={scaleStance}
                onChange={(e) => setScaleStance(e.target.value as typeof scaleStance)}
              >
                <option value="balanced">{t("detail.stanceBalanced")}</option>
                <option value="conservative">{t("detail.stanceConservative")}</option>
                <option value="aggressive">{t("detail.stanceAggressive")}</option>
              </select>
            </div>
            <Button
              variant="outline"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("export");
                try {
                  const ex = await api<{ content: string }>(`/designs/${id}/export?format=markdown`);
                  await navigator.clipboard.writeText(ex.content);
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <FileOutput className="mr-2 h-4 w-4" />
              {isBusy === "export" ? t("detail.exporting") : t("detail.copyExport")}
            </Button>
            <Button
              variant="outline"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("export");
                try {
                  const blob = await apiBlob(`/designs/${id}/export?format=pdf`);
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${data.title.replace(/[^\w\s-]/g, "").slice(0, 60) || "design"}-systemforge.pdf`;
                  a.click();
                  URL.revokeObjectURL(url);
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <FileDown className="mr-2 h-4 w-4" />
              {t("detail.downloadPdf")}
            </Button>
            {data.share_enabled && data.share_url ? (
              <Button
                type="button"
                variant="outline"
                disabled={isBusy !== null}
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(data.share_url!);
                    setActionMessage(t("detail.shareCopied"));
                  } catch {
                    setActionError(t("detail.shareCopyFailed"));
                  }
                }}
              >
                <Link2 className="mr-2 h-4 w-4" />
                {t("detail.shareCopy")}
              </Button>
            ) : (
              <Button
                type="button"
                variant="outline"
                disabled={isBusy !== null}
                onClick={async () => {
                  setIsBusy("share");
                  setActionError("");
                  try {
                    await api(`/designs/${id}/share`, { method: "POST" });
                    await load();
                    setActionMessage(t("detail.shareEnabled"));
                  } catch (e) {
                    setActionError(e instanceof Error ? e.message : t("detail.shareEnableFailed"));
                  } finally {
                    setIsBusy(null);
                  }
                }}
              >
                <Link2 className="mr-2 h-4 w-4" />
                {t("detail.shareEnable")}
              </Button>
            )}
            {data.share_enabled ? (
              <Button
                type="button"
                variant="outline"
                disabled={isBusy !== null}
                onClick={async () => {
                  setIsBusy("share");
                  setActionError("");
                  try {
                    await api(`/designs/${id}/share`, { method: "DELETE" });
                    await load();
                    setActionMessage(t("detail.shareDisabled"));
                  } catch (e) {
                    setActionError(e instanceof Error ? e.message : t("detail.shareDisableFailed"));
                  } finally {
                    setIsBusy(null);
                  }
                }}
              >
                {t("detail.shareDisable")}
              </Button>
            ) : null}
            <Button
              variant="outline"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("regenerate");
                setActionError("");
                setActionMessage("");
                try {
                  const res = await api<{ status: string; message: string }>(`/designs/${id}/regenerate`, {
                    method: "POST",
                    body: JSON.stringify({ scale_stance: scaleStance }),
                  });
                  await load();
                  setActionMessage(res.message || t("detail.regenerateSuccess"));
                } catch (e) {
                  setActionError(e instanceof Error ? e.message : t("detail.regenerateFailed"));
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {isBusy === "regenerate" ? t("detail.regenerating") : t("detail.regenerate")}
            </Button>
            <Button
              variant="outline"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("delete");
                try {
                  await api(`/designs/${id}`, { method: "DELETE" });
                  router.push("/dashboard");
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {t("common.delete")}
            </Button>
          </div>
        </div>
        {actionError ? <p className="mt-3 text-sm text-red-300">{actionError}</p> : null}
        {actionMessage ? <p className="mt-3 text-sm text-emerald-300">{actionMessage}</p> : null}
      </Card>

      <DesignArtifactGrid
        data={data}
        t={t}
        versions={versions}
        designId={id}
        compareA={compareA}
        compareB={compareB}
        setCompareA={setCompareA}
        setCompareB={setCompareB}
        diffText={diffText}
        onCompare={async () => {
          if (compareA === "" || compareB === "") return;
          try {
            const r = await api<{ diff_markdown: string }>(
              `/designs/${id}/versions/compare?a=${compareA}&b=${compareB}`,
            );
            setDiffText(r.diff_markdown);
          } catch {
            setDiffText(null);
          }
        }}
        notes={notes}
        setNotes={setNotes}
        notesSaveState={notesSaveState}
      />

      {data.discussion_conversation_id != null && data.discussion_conversation_id > 0 ? (
        <RealtimeMessagingPanel conversationId={data.discussion_conversation_id} />
      ) : null}
    </div>
  );
}
