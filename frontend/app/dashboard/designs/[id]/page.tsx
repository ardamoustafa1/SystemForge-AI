"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { CalendarDays, FileDown, FileOutput, FolderArchive, Link2, RefreshCw, Trash2, CloudCog } from "lucide-react";

import { api, apiBlob } from "@/lib/api";
import { WsClient } from "@/lib/ws-client";
import { DesignArtifactGrid } from "@/components/design/design-artifact-grid";
import { DesignRecord, GenerationProgress, DesignReview, DesignComment } from "@/types/design";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useI18n } from "@/i18n/i18n-context";
import { RealtimeMessagingPanel } from "@/components/realtime/realtime-messaging-panel";
import { GenerationLoader } from "@/components/design/generation-loader";

export default function DesignDetailPage() {
  const { t, language } = useI18n();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
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
  const [diffExplain, setDiffExplain] = useState<string | null>(null);
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress | null>(null);
  const [review, setReview] = useState<DesignReview | null>(null);
  const [comments, setComments] = useState<DesignComment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [exportJobs, setExportJobs] = useState<{ id: string; format: "pdf" | "markdown"; status: string }[]>([]);
  const [timeline, setTimeline] = useState<{ type: string; at: string; summary: string; note?: string }[]>([]);
  const executiveMode = searchParams.get("view") === "executive";
  const runExportJob = async (format: "pdf" | "markdown") => {
    const started = await api<{ job_id: string; status: string }>(`/designs/${id}/export-jobs?format=${format}`, {
      method: "POST",
    });
    setExportJobs((prev) => [{ id: started.job_id, format, status: "queued" }, ...prev].slice(0, 8));
    for (let i = 0; i < 60; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const status = await api<{ status: "queued" | "running" | "completed" | "failed"; error?: string }>(
        `/designs/export-jobs/${started.job_id}`,
      );
      setExportJobs((prev) => prev.map((j) => (j.id === started.job_id ? { ...j, status: status.status } : j)));
      if (status.status === "completed") {
        if (format === "pdf") {
          const blob = await apiBlob(`/designs/export-jobs/${started.job_id}/download`);
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${data?.title.replace(/[^\w\s-]/g, "").slice(0, 60) || "design"}-systemforge.pdf`;
          a.click();
          URL.revokeObjectURL(url);
        } else {
          const blob = await apiBlob(`/designs/export-jobs/${started.job_id}/download`);
          const markdown = await blob.text();
          await navigator.clipboard.writeText(markdown);
        }
        return;
      }
      if (status.status === "failed") {
        throw new Error(status.error || "Export job failed");
      }
    }
    throw new Error("Export timeout");
  };


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
    api<DesignReview>(`/designs/${id}/review`).then(setReview).catch(() => setReview(null));
    api<DesignComment[]>(`/designs/${id}/comments`).then(setComments).catch(() => setComments([]));
    api<{ items: { type: string; at: string; summary: string; note?: string }[] }>(`/designs/${id}/timeline`)
      .then((r) => setTimeline(r.items))
      .catch(() => setTimeline([]));
  }, [id, data?.updated_at]);

  useEffect(() => {
    if (!id) return;
    try {
      const raw = localStorage.getItem(`export_jobs_${id}`);
      if (!raw) return;
      const parsed = JSON.parse(raw) as { id: string; format: "pdf" | "markdown"; status: string }[];
      if (Array.isArray(parsed)) setExportJobs(parsed);
    } catch {
      // ignore storage parse issues
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    localStorage.setItem(`export_jobs_${id}`, JSON.stringify(exportJobs.slice(0, 8)));
  }, [id, exportJobs]);

  useEffect(() => {
    if (data?.status === "generating") {
      const timer = setInterval(async () => {
        try {
          const res = await api<DesignRecord>(`/designs/${id}`);
          if (res.status !== "generating") {
            setData(res);
            setNotes(res.notes ?? "");
            clearInterval(timer);
          }
        } catch {
          // ignore
        }
      }, 2000);
      return () => clearInterval(timer);
    }
  }, [data?.status, id]);

  useEffect(() => {
    if (data?.status !== "generating" || !id) return;
    const ws = new WebSocket(WsClient.buildDefaultUrl());
    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          v: 1,
          event_id: crypto.randomUUID(),
          type: "session.hello",
          ts_ms: Date.now(),
          payload: { protocol_version: 1 },
        }),
      );
    };
    ws.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data) as { type?: string; payload?: GenerationProgress };
        if (!parsed?.payload || parsed.payload.design_id !== id) return;
        if (parsed.type === "design.progress" || parsed.type === "design.updated") {
          setGenerationProgress(parsed.payload);
          if (parsed.payload.status && parsed.payload.status !== "generating") {
            void load();
          }
        }
      } catch {
        // ignore malformed events
      }
    };
    return () => ws.close();
  }, [data?.status, id]);

  useEffect(() => {
    if (!id || data?.status === "generating") return;
    api<
      { id: number; created_at: string; model_name: string; scale_stance: string; generation_ms: number }[]
    >(`/designs/${id}/versions`)
      .then(setVersions)
      .catch(() => setVersions([]));
  }, [id, data?.updated_at, data?.status]);

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

      <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <CalendarDays className="h-4 w-4" />
            {t("detail.createdAt")} {new Date(data.created_at).toLocaleString()}
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <div className="min-w-[140px]">
              <Label className="text-xs text-muted">{t("detail.scaleStance")}</Label>
              <select
                className="mt-1.5 h-9 w-full min-w-[160px] rounded-lg border border-white/10 bg-white/[0.02] text-white/80 px-2 text-sm appearance-none"
                value={scaleStance}
                onChange={(e) => setScaleStance(e.target.value as typeof scaleStance)}
              >
                <option value="balanced" className="bg-[#0a0a0a]">{t("detail.stanceBalanced")}</option>
                <option value="conservative" className="bg-[#0a0a0a]">{t("detail.stanceConservative")}</option>
                <option value="aggressive" className="bg-[#0a0a0a]">{t("detail.stanceAggressive")}</option>
              </select>
            </div>
            <Button
              variant="outline"
              className="h-9 rounded-lg border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 font-medium px-4"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("export");
                try {
                  await runExportJob("markdown");
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
              className="h-9 rounded-lg border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 font-medium px-4"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("export");
                try {
                  await runExportJob("pdf");
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <FileDown className="mr-2 h-4 w-4" />
              {t("detail.downloadPdf")}
            </Button>
            <Button
              variant="outline"
              className="h-9 rounded-lg border-emerald-500/20 bg-emerald-500/[0.06] text-emerald-400/90 hover:text-emerald-300 hover:bg-emerald-500/10 font-semibold px-4"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("export");
                try {
                  const blob = await apiBlob(`/designs/${id}/export/scaffold`);
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${data.title.replace(/[^\w\s-]/g, "").slice(0, 60) || "project"}-scaffold.zip`;
                  a.click();
                  URL.revokeObjectURL(url);
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <FolderArchive className="mr-2 h-4 w-4" />
              {t("detail.downloadScaffold")}
            </Button>
            <Button
              variant="outline"
              className="h-9 rounded-lg border-cyan-500/20 bg-cyan-500/[0.06] text-cyan-400/90 hover:text-cyan-300 hover:bg-cyan-500/10 font-semibold px-4"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("export");
                try {
                  const blob = await apiBlob(`/designs/${id}/export/terraform`);
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${data.title.replace(/[^\w\s-]/g, "").slice(0, 60) || "project"}-terraform.zip`;
                  a.click();
                  URL.revokeObjectURL(url);
                } finally {
                  setIsBusy(null);
                }
              }}
            >
              <CloudCog className="mr-2 h-4 w-4" />
              {t("detail.exportTerraform")}
            </Button>
            {data.share_enabled && data.share_url ? (
              <Button
                type="button"
                variant="outline"
                className="h-9 rounded-lg border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 font-medium px-4"
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
                className="h-9 rounded-lg border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 font-medium px-4"
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
                className="h-9 rounded-lg border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 font-medium px-4"
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
              className="h-9 rounded-lg border-white/5 bg-[#0a0a0a] text-white/60 hover:text-white/90 hover:bg-white/5 font-medium px-4"
              disabled={isBusy !== null}
              onClick={async () => {
                setIsBusy("regenerate");
                setActionError("");
                setActionMessage("");
                try {
                  const res = await api<{ status: string; message: string }>(`/designs/${id}/regenerate`, {
                    method: "POST",
                    body: JSON.stringify({ scale_stance: scaleStance, output_language: language }),
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
              className="h-9 rounded-lg border-red-500/10 bg-red-500/[0.02] text-red-500/60 hover:text-red-400 hover:bg-red-500/10 font-medium px-4"
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
        {exportJobs.length > 0 ? (
          <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-3">
            <p className="text-xs text-white/50 mb-2">{t("detail.exportJobs")}</p>
            <div className="space-y-1">
              {exportJobs.map((job) => (
                <p key={job.id} className="text-xs text-white/60">
                  {job.format.toUpperCase()} • {job.id.slice(0, 8)} • {job.status}
                </p>
              ))}
            </div>
          </div>
        ) : null}
      </Card>

      <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl p-5">
        <h3 className="text-sm font-semibold text-white/90 mb-3">{t("detail.reviewPanel")}</h3>
        <div className="flex flex-wrap items-end gap-2">
          <select
            className="h-9 rounded-lg border border-white/10 bg-white/[0.02] px-3 text-sm text-white/80"
            value={review?.review_status ?? "draft"}
            onChange={(e) => setReview((prev) => (prev ? { ...prev, review_status: e.target.value as DesignReview["review_status"] } : prev))}
          >
            <option value="draft" className="bg-[#0a0a0a]">draft</option>
            <option value="in_review" className="bg-[#0a0a0a]">in_review</option>
            <option value="approved" className="bg-[#0a0a0a]">approved</option>
            <option value="changes_requested" className="bg-[#0a0a0a]">changes_requested</option>
          </select>
          <input
            className="h-9 w-full max-w-sm rounded-lg border border-white/10 bg-white/[0.02] px-3 text-sm text-white"
            placeholder={t("detail.reviewNotePlaceholder")}
            value={review?.review_decision_note ?? ""}
            onChange={(e) => setReview((prev) => (prev ? { ...prev, review_decision_note: e.target.value } : prev))}
          />
          <Button
            variant="outline"
            onClick={async () => {
              const next = await api<DesignReview>(`/designs/${id}/review`, {
                method: "PATCH",
                body: JSON.stringify({
                  review_status: review?.review_status ?? "draft",
                  review_owner_user_id: review?.review_owner_user_id ?? null,
                  review_decision_note: review?.review_decision_note ?? "",
                }),
              });
              setReview(next);
            }}
          >
            {t("common.save")}
          </Button>
        </div>
        <div className="mt-4 space-y-2">
          {comments.map((c) => (
            <p key={c.id} className="text-xs text-white/70 rounded-lg border border-white/10 bg-black/20 p-2">
              <span className="text-white/40">{c.author_name ?? "User"}:</span> {c.content}
            </p>
          ))}
          <div className="flex gap-2">
            <input
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="h-9 flex-1 rounded-lg border border-white/10 bg-white/[0.02] px-3 text-sm text-white"
              placeholder={t("detail.commentPlaceholder")}
            />
            <Button
              variant="outline"
              onClick={async () => {
                if (!newComment.trim()) return;
                const added = await api<DesignComment>(`/designs/${id}/comments`, {
                  method: "POST",
                  body: JSON.stringify({ content: newComment }),
                });
                setComments((prev) => [...prev, added]);
                setNewComment("");
              }}
            >
              {t("detail.addComment")}
            </Button>
          </div>
        </div>
      </Card>

      {data.status === "generating" ? (
        <GenerationLoader progress={generationProgress} />
      ) : !data.output ? (
        <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl p-6">
          <p className="text-sm text-white/60">{t("detail.loadFailed")}</p>
        </Card>
      ) : executiveMode ? (
        <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl p-6">
          <h3 className="text-lg font-semibold text-white/90">Executive / Share Mode</h3>
          <p className="mt-3 text-sm text-white/60">{data.output.executive_summary}</p>
          <div className="mt-4 grid gap-2">
            {data.output.tradeoff_decisions.slice(0, 5).map((d) => (
              <p key={d} className="text-xs text-white/60">- {d}</p>
            ))}
          </div>
        </Card>
      ) : (
        <DesignArtifactGrid
          data={data as DesignRecord & { output: NonNullable<DesignRecord["output"]> }}
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
              const explain = await api<{ technical_explanation: string }>(
                `/designs/${id}/versions/explain?a=${compareA}&b=${compareB}`,
              );
              setDiffExplain(explain.technical_explanation);
            } catch {
              setDiffText(null);
              setDiffExplain(null);
            }
          }}
          notes={notes}
          setNotes={setNotes}
          notesSaveState={notesSaveState}
          onSyncArchitecture={async (newMermaid: string) => {
            await api(`/designs/${id}/architecture`, {
              method: "PATCH",
              body: JSON.stringify({ mermaid: newMermaid }),
            });
            await load(); // Refresh the data to show updated cost and diagram
          }}
        />
      )}
      {diffExplain ? (
        <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl p-5">
          <h3 className="text-sm font-semibold text-white/90 mb-2">Architecture Copilot Diff Explain</h3>
          <p className="text-sm text-white/60">{diffExplain}</p>
        </Card>
      ) : null}
      <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl p-5">
        <h3 className="text-sm font-semibold text-white/90 mb-3">Decision Timeline</h3>
        <div className="space-y-2">
          {timeline.map((entry, idx) => (
            <p key={`${entry.type}-${entry.at}-${idx}`} className="text-xs text-white/60">
              {new Date(entry.at).toLocaleString()} • {entry.type} • {entry.summary}
            </p>
          ))}
        </div>
      </Card>

      {data.discussion_conversation_id != null && data.discussion_conversation_id > 0 ? (
        <RealtimeMessagingPanel conversationId={data.discussion_conversation_id} />
      ) : null}
    </div>
  );
}
