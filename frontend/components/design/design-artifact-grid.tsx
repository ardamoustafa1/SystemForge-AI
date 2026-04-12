"use client";

import { useState } from "react";
import { ClipboardList } from "lucide-react";

import { DesignRecord } from "@/types/design";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MermaidViewer } from "@/components/design/mermaid-viewer";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
export type VersionRow = {
  id: number;
  created_at: string;
  model_name: string;
  scale_stance: string;
  generation_ms: number;
};

type Props = {
  data: DesignRecord;
  t: (key: string) => string;
  /** Dashboard-only: regeneration snapshots & diff */
  versions?: VersionRow[];
  designId?: number;
  compareA?: number | "";
  compareB?: number | "";
  setCompareA?: (v: number | "") => void;
  setCompareB?: (v: number | "") => void;
  diffText?: string | null;
  onCompare?: () => void;
  /** Notes editor (dashboard only) */
  notes?: string;
  setNotes?: (v: string) => void;
  notesSaveState?: "idle" | "saving" | "saved" | "error";
};

export function DesignArtifactGrid({
  data,
  t,
  versions,
  designId,
  compareA,
  compareB,
  setCompareA,
  setCompareB,
  diffText,
  onCompare,
  notes,
  setNotes,
  notesSaveState,
}: Props) {
  const [showRawDiagram, setShowRawDiagram] = useState(false);
  const score = data.output.architecture_scorecard;
  const scoreItems = [
    [t("detail.score.scalability"), score.scalability],
    [t("detail.score.reliability"), score.reliability],
    [t("detail.score.security"), score.security],
    [t("detail.score.maintainability"), score.maintainability],
    [t("detail.score.costEfficiency"), score.cost_efficiency],
    [t("detail.score.simplicity"), score.simplicity],
  ] as const;

  const showVersions = versions !== undefined && designId !== undefined;
  const showNotes = notes !== undefined && setNotes !== undefined;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-6">
        <Card className="p-5">
          <h2 className="text-lg font-medium">{t("detail.executiveSummary")}</h2>
          <p className="mt-2 text-sm text-muted">{data.output.executive_summary}</p>
        </Card>

        {(data.output.consistency_warnings?.length ?? 0) > 0 ? (
          <Card className="border-amber-500/35 p-5">
            <h2 className="text-lg font-medium text-amber-200">{t("detail.consistencyWarnings")}</h2>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
              {data.output.consistency_warnings!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {(data.output.assumptions?.length ?? 0) > 0 ? (
          <Card className="p-5">
            <h2 className="text-lg font-medium">{t("detail.assumptions")}</h2>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
              {data.output.assumptions!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {(data.output.architecture_decisions?.length ?? 0) > 0 ? (
          <Card className="p-5">
            <h2 className="text-lg font-medium">{t("detail.architectureDecisions")}</h2>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
              {data.output.architecture_decisions!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {(data.output.open_questions?.length ?? 0) > 0 ? (
          <Card className="p-5">
            <h2 className="text-lg font-medium">{t("detail.openQuestions")}</h2>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
              {data.output.open_questions!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        <Card className="p-5">
          <h2 className="text-lg font-medium">{t("detail.highLevelArchitecture")}</h2>
          <p className="mt-2 text-sm text-muted">{data.output.high_level_architecture}</p>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-medium">{t("detail.functionalRequirements")}</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
            {data.output.functional_requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-medium">{t("detail.nonFunctionalRequirements")}</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
            {data.output.non_functional_requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-medium">{t("detail.tradeOffDecisions")}</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
            {data.output.tradeoff_decisions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-medium">{t("detail.architectureDiagram")}</h2>
            <Button variant="ghost" aria-pressed={showRawDiagram} onClick={() => setShowRawDiagram((p) => !p)}>
              {showRawDiagram ? t("detail.showRendered") : t("detail.showRawMermaid")}
            </Button>
          </div>
          {showRawDiagram ? (
            <pre className="mt-3 overflow-x-auto rounded-md border border-border bg-black/30 p-4 text-xs text-muted">
              {data.output.suggested_mermaid_diagram}
            </pre>
          ) : (
            <div className="mt-3">
              <MermaidViewer code={data.output.suggested_mermaid_diagram} />
            </div>
          )}
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2">
            <ClipboardList className="h-4 w-4 text-muted" />
            <h2 className="text-lg font-medium">{t("detail.implementationChecklist")}</h2>
          </div>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            {data.output.engineering_checklist.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-0.5">-</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card>

        {showVersions && versions && designId !== undefined && setCompareA && setCompareB && onCompare ? (
          <Card className="p-5">
            <h2 className="text-lg font-medium">{t("detail.versionHistory")}</h2>
            {versions.length === 0 ? (
              <p className="mt-2 text-sm text-muted">{t("detail.noVersions")}</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm text-muted">
                {versions.map((v) => (
                  <li key={v.id} className="rounded border border-border/60 px-3 py-2">
                    <span className="text-foreground">#{v.id}</span> · {new Date(v.created_at).toLocaleString()} · {v.model_name} ·{" "}
                    {v.scale_stance}
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-4 flex flex-wrap items-end gap-2">
              <div>
                <Label className="text-xs">{t("detail.versionId")} A</Label>
                <select
                  className="mt-1 h-9 rounded-md border border-border bg-transparent px-2 text-sm"
                  value={compareA}
                  onChange={(e) => setCompareA(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="">—</option>
                  {versions.map((v) => (
                    <option key={`a-${v.id}`} value={v.id}>
                      #{v.id}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label className="text-xs">{t("detail.versionId")} B</Label>
                <select
                  className="mt-1 h-9 rounded-md border border-border bg-transparent px-2 text-sm"
                  value={compareB}
                  onChange={(e) => setCompareB(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="">—</option>
                  {versions.map((v) => (
                    <option key={`b-${v.id}`} value={v.id}>
                      #{v.id}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={compareA === "" || compareB === "" || compareA === compareB}
                onClick={onCompare}
              >
                {t("detail.compareRun")}
              </Button>
            </div>
            {diffText ? (
              <pre className="mt-3 max-h-64 overflow-auto rounded-md border border-border bg-black/40 p-3 text-xs text-muted">{diffText}</pre>
            ) : null}
          </Card>
        ) : null}

        {showNotes ? (
          <Card className="p-5">
            <h2 className="text-lg font-medium">{t("detail.notes")}</h2>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-3 min-h-28"
              placeholder={t("detail.notesPlaceholder")}
            />
            <p className="mt-2 text-xs text-muted">
              {notesSaveState === "saving" && t("detail.notesSaving")}
              {notesSaveState === "saved" && t("detail.notesSaved")}
              {notesSaveState === "error" && t("detail.notesError")}
              {notesSaveState === "idle" && t("detail.notesAutosaved")}
            </p>
          </Card>
        ) : null}
      </div>

      <div className="space-y-6">
        <Card className="p-5">
          <h2 className="text-lg font-medium">{t("detail.architectureScorecard")}</h2>
          <div className="mt-4 space-y-2">
            {scoreItems.map(([label, value]) => (
              <div key={label} className="grid grid-cols-[1fr_auto] items-center gap-3 text-sm">
                <span className="text-muted">{label}</span>
                <span className="font-medium">{value}/10</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="font-medium">{t("detail.riskAnalysis")}</h3>
          <div className="mt-3 space-y-3 text-sm text-muted">
            <p>
              <span className="text-foreground">{t("detail.biggestRisk")}:</span> {score.biggest_risk}
            </p>
            <p>
              <span className="text-foreground">{t("detail.biggestBottleneck")}:</span> {score.biggest_bottleneck}
            </p>
            <p>
              <span className="text-foreground">{t("detail.firstOptimization")}:</span> {score.first_optimization}
            </p>
            <p>
              <span className="text-foreground">{t("detail.avoidOverengineering")}:</span> {score.avoid_overengineering}
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
