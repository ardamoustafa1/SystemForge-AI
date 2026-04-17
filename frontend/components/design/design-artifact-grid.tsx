"use client";

import { useState } from "react";
import { ClipboardList, Trello, Kanban } from "lucide-react";

import { DesignOutput, DesignRecord } from "@/types/design";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArchitectureCanvas } from "@/components/design/architecture-canvas";
import { api } from "@/lib/api";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CostAnalysisResult, CostCalibration } from "@/types/design";
export type VersionRow = {
  id: number;
  created_at: string;
  model_name: string;
  scale_stance: string;
  generation_ms: number;
};

type Props = {
  data: DesignRecord & { output: DesignOutput };
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
  onSyncArchitecture?: (mermaid: string) => Promise<void>;
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
  onSyncArchitecture,
}: Props) {
  // showRawDiagram state removed — ArchitectureCanvas handles its own toggle
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
  const [trafficMultiplier, setTrafficMultiplier] = useState(1);
  const [dataMultiplier, setDataMultiplier] = useState(1);
  const [reliability, setReliability] = useState<"lean" | "balanced" | "critical">("balanced");
  const [costScenario, setCostScenario] = useState<CostAnalysisResult | null>(null);
  const [costBusy, setCostBusy] = useState(false);
  const [calibration, setCalibration] = useState<CostCalibration | null>(null);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-6">
        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-white/90">{t("detail.executiveSummary")}</h2>
          <p className="mt-3 text-sm text-white/50 leading-relaxed">{data.output.executive_summary}</p>
        </Card>

        {(data.output.consistency_warnings?.length ?? 0) > 0 ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-amber-500/20 bg-amber-500/[0.02] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-amber-200">{t("detail.consistencyWarnings")}</h2>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-amber-200/70">
              {data.output.consistency_warnings!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {(data.output.assumptions?.length ?? 0) > 0 ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-white/90">{t("detail.assumptions")}</h2>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-white/50 leading-relaxed">
              {data.output.assumptions!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {(data.output.architecture_decisions?.length ?? 0) > 0 ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-white/90">{t("detail.architectureDecisions")}</h2>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-white/50 leading-relaxed">
              {data.output.architecture_decisions!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        {(data.output.open_questions?.length ?? 0) > 0 ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-white/90">{t("detail.openQuestions")}</h2>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-white/50 leading-relaxed">
              {data.output.open_questions!.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
        ) : null}

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-white/90">{t("detail.highLevelArchitecture")}</h2>
          <p className="mt-3 text-sm text-white/50 leading-relaxed">{data.output.high_level_architecture}</p>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-cyan-500/10 bg-cyan-500/[0.03] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-cyan-200">{t("detail.runtimeTopology")}</h2>
          <p className="mt-3 text-sm text-white/60 leading-relaxed">{data.output.runtime_topology.architecture_style}</p>
          <div className="mt-5 grid gap-5 md:grid-cols-3">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.deployableUnits")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.runtime_topology.deployable_units.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.runtimePaths")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.runtime_topology.primary_runtime_paths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.statefulComponents")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.runtime_topology.stateful_components.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-indigo-500/10 bg-indigo-500/[0.03] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-indigo-200">{t("detail.dataFlows")}</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.requestResponseFlow")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.data_flows.request_response_flow.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.asyncEventFlow")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.data_flows.asynchronous_event_flow.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.persistenceFlow")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.data_flows.persistence_flow.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.failureRecoveryFlow")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.data_flows.failure_recovery_flow.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        {(data.output.websocket_architecture.connection_lifecycle.length > 0 ||
          data.output.websocket_architecture.fanout_strategy.length > 0) ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-violet-500/10 bg-violet-500/[0.03] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-violet-200">{t("detail.websocketArchitecture")}</h2>
            <p className="mt-3 text-sm text-white/60 leading-relaxed">{data.output.websocket_architecture.pubsub_backplane}</p>
            <p className="mt-2 text-sm text-white/50 leading-relaxed">{data.output.websocket_architecture.sticky_session_strategy}</p>
            <div className="mt-5 grid gap-5 md:grid-cols-3">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketConnectionLifecycle")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.connection_lifecycle.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketFanout")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.fanout_strategy.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketScaling")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.scaling_strategy.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-5 grid gap-5 md:grid-cols-2">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketChannelPartitioning")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.channel_partitioning.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketShardStrategy")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.shard_strategy.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketTopicDesign")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.topic_design.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.websocketPartitionKeys")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.websocket_architecture.partition_keys.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        ) : null}

        {(data.output.video_streaming_architecture.streaming_protocols.length > 0 ||
          data.output.video_streaming_architecture.cdn_strategy.length > 0) ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-sky-500/10 bg-sky-500/[0.03] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-sky-200">{t("detail.videoStreamingArchitecture")}</h2>
            <div className="mt-5 grid gap-5 md:grid-cols-2">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.videoProtocols")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.video_streaming_architecture.streaming_protocols.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.videoIngestPackaging")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.video_streaming_architecture.ingest_and_packaging.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.videoCdnStrategy")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.video_streaming_architecture.cdn_strategy.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.videoAdaptiveBitrate")}</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                  {data.output.video_streaming_architecture.adaptive_bitrate_strategy.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        ) : null}

        <Card className="p-6 sm:p-8 rounded-2xl border-fuchsia-500/10 bg-fuchsia-500/[0.03] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-fuchsia-200">{t("detail.databaseArchitecture")}</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.databasePrimaryEntities")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.database_architecture.primary_entities.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.databaseSchemaDesign")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.database_architecture.schema_design.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.databaseIndexingStrategy")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.database_architecture.indexing_strategy.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.databasePartitioningStrategy")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.database_architecture.partitioning_strategy.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-orange-500/10 bg-orange-500/[0.03] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-orange-200">{t("detail.observabilityArchitecture")}</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.observabilityLogging")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.observability_architecture.logging_strategy.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.observabilityTracing")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.observability_architecture.tracing_strategy.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.observabilityMetrics")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.observability_architecture.metrics_strategy.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.observabilityAlerting")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {[...data.output.observability_architecture.alerting_strategy, ...data.output.observability_architecture.sli_slo_targets].map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-emerald-500/10 bg-emerald-500/[0.03] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-emerald-200">{t("detail.aiServingQueueing")}</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.aiGuardrails")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.ai_architecture.request_guardrails.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.aiInferenceOrchestration")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.ai_architecture.inference_orchestration.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.aiQueueBackpressure")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.ai_architecture.queue_and_backpressure.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.aiProviderRecovery")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {[...data.output.ai_architecture.model_provider_strategy, ...data.output.ai_architecture.fallback_and_recovery].map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-rose-500/10 bg-rose-500/[0.03] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-rose-200">{t("detail.securityBlueprint")}</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.securityAuthFlow")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.security_architecture.auth_flow.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.securitySessionRefresh")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.security_architecture.session_and_refresh_flow.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.securityAbuseProtection")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {data.output.security_architecture.abuse_protection.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40">{t("detail.securitySecretsAudit")}</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-white/55">
                {[...data.output.security_architecture.secrets_and_key_management, ...data.output.security_architecture.audit_and_compliance].map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-white/90">{t("detail.functionalRequirements")}</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-white/50 leading-relaxed">
            {data.output.functional_requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-white/90">{t("detail.nonFunctionalRequirements")}</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-white/50 leading-relaxed">
            {data.output.non_functional_requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-white/90">{t("detail.tradeOffDecisions")}</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-white/50 leading-relaxed">
            {data.output.tradeoff_decisions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <ArchitectureCanvas mermaidCode={data.output.suggested_mermaid_diagram} t={t} onSync={onSyncArchitecture} />
        </Card>

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.03] ring-1 ring-white/5">
                 <ClipboardList className="h-4 w-4 text-white/60" />
              </div>
              <h2 className="text-lg font-medium text-white/90">{t("detail.implementationChecklist")}</h2>
            </div>
            {designId !== undefined ? (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 rounded-lg border-white/5 bg-[#0a0a0a] hover:bg-white/5 text-white/60 hover:text-white/90 font-medium"
                  onClick={() => {
                    const a = document.createElement("a");
                    a.href = `/api/designs/${designId}/export/tasks-csv?provider=jira`;
                    a.download = `tasks-jira.csv`;
                    a.click();
                  }}
                >
                  <Trello className="mr-2 w-3 h-3" />
                  {t("detail.exportJira")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 rounded-lg border-indigo-500/20 bg-indigo-500/[0.05] hover:bg-indigo-500/10 text-indigo-400 font-medium"
                  onClick={() => {
                    const a = document.createElement("a");
                    a.href = `/api/designs/${designId}/export/tasks-csv?provider=linear`;
                    a.download = `tasks-linear.csv`;
                    a.click();
                  }}
                >
                  <Kanban className="mr-2 w-3 h-3" />
                  {t("detail.exportLinear")}
                </Button>
              </div>
            ) : null}
          </div>
          <ul className="mt-6 space-y-3 text-sm text-white/50">
            {data.output.engineering_checklist.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-0.5 text-white/20">—</span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </Card>

        {showVersions && versions && designId !== undefined && setCompareA && setCompareB && onCompare ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-white/90">{t("detail.versionHistory")}</h2>
            {versions.length === 0 ? (
              <p className="mt-4 text-sm text-white/50">{t("detail.noVersions")}</p>
            ) : (
              <ul className="mt-4 space-y-2 text-sm text-white/50">
                {versions.map((v) => (
                  <li key={v.id} className="rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 font-medium">
                    <span className="text-white/90">#{v.id}</span> <span className="text-white/20 px-2">•</span> {new Date(v.created_at).toLocaleString()} <span className="text-white/20 px-2">•</span> {v.model_name} <span className="text-white/20 px-2">•</span>{" "}
                    {v.scale_stance}
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-6 flex flex-wrap items-end gap-3 p-4 rounded-xl border border-white/5 bg-black/20">
              <div className="flex-1">
                <Label className="text-xs text-white/60">{t("detail.versionId")} A</Label>
                <select
                  className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-white/[0.02] text-white/80 px-3 text-sm appearance-none focus-visible:ring-1 focus-visible:ring-white/20"
                  value={compareA}
                  onChange={(e) => setCompareA(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="" className="bg-[#0a0a0a]">—</option>
                  {versions.map((v) => (
                    <option key={`a-${v.id}`} value={v.id} className="bg-[#0a0a0a]">
                      #{v.id}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <Label className="text-xs text-white/60">{t("detail.versionId")} B</Label>
                <select
                  className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-white/[0.02] text-white/80 px-3 text-sm appearance-none focus-visible:ring-1 focus-visible:ring-white/20"
                  value={compareB}
                  onChange={(e) => setCompareB(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="" className="bg-[#0a0a0a]">—</option>
                  {versions.map((v) => (
                    <option key={`b-${v.id}`} value={v.id} className="bg-[#0a0a0a]">
                      #{v.id}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                type="button"
                variant="outline"
                className="h-10 rounded-lg border-white/5 bg-white/[0.05] text-white hover:text-white hover:bg-white/10 px-6 font-medium"
                disabled={compareA === "" || compareB === "" || compareA === compareB}
                onClick={onCompare}
              >
                {t("detail.compareRun")}
              </Button>
            </div>
            {diffText ? (
              <pre className="mt-4 max-h-64 overflow-auto rounded-xl border border-white/5 bg-black/50 p-4 text-xs text-white/60 whitespace-pre-wrap">{diffText}</pre>
            ) : null}
          </Card>
        ) : null}

        {showNotes ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
            <h2 className="text-lg font-medium text-white/90">{t("detail.notes")}</h2>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-4 min-h-32 bg-white/[0.02] border-white/10 text-white placeholder:text-white/30 focus-visible:ring-1 focus-visible:ring-white/20 p-4"
              placeholder={t("detail.notesPlaceholder")}
            />
            <p className="mt-3 text-xs text-white/40 font-medium">
              {notesSaveState === "saving" && t("detail.notesSaving")}
              {notesSaveState === "saved" && <span className="text-emerald-400/80">{t("detail.notesSaved")}</span>}
              {notesSaveState === "error" && <span className="text-red-400">{t("detail.notesError")}</span>}
              {notesSaveState === "idle" && t("detail.notesAutosaved")}
            </p>
          </Card>
        ) : null}
      </div>

      <div className="space-y-6">
        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h2 className="text-lg font-medium text-white/90">{t("detail.architectureScorecard")}</h2>
          <div className="mt-6 space-y-3">
            {scoreItems.map(([label, value]) => (
              <div key={label} className="grid grid-cols-[1fr_auto] items-center gap-3 text-sm p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <span className="text-white/60 font-medium">{label}</span>
                <span className="font-semibold text-white/90">{value}/10</span>
              </div>
            ))}
          </div>
        </Card>

        {data.output.estimated_cloud_cost ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-emerald-500/10 bg-gradient-to-br from-[#0a0a0a] to-emerald-950/10 shadow-xl relative overflow-hidden">
            <h3 className="text-lg font-medium text-emerald-400/90 tracking-tight">{t("detail.estimatedCloudCost")}</h3>
            <div className="mt-4 mb-6">
              <span className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                ${data.output.estimated_cloud_cost.monthly_usd_min.toLocaleString()} - ${data.output.estimated_cloud_cost.monthly_usd_max.toLocaleString()}
              </span>
              <span className="text-emerald-400/50 ml-2 text-sm font-medium">{t("detail.perMonth")}</span>
            </div>
            
            <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-400/50 mb-3">{t("detail.topCostDrivers")}</h4>
            <div className="space-y-2">
              {data.output.estimated_cloud_cost.cost_breakdown.map((item, i) => (
                <div key={i} className="flex items-start gap-3 bg-emerald-900/10 p-3 rounded-lg border border-emerald-500/10 text-sm text-emerald-100/80">
                  <span className="text-emerald-500/40 shrink-0 font-mono font-bold">{i + 1}.</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {designId !== undefined ? (
          <Card className="p-6 sm:p-8 rounded-2xl border-cyan-500/10 bg-gradient-to-br from-[#0a0a0a] to-cyan-950/10 shadow-xl relative overflow-hidden">
            <h3 className="text-lg font-medium text-cyan-300/90">{t("detail.costWhatIfTitle")}</h3>
            <div className="mt-4 grid grid-cols-1 gap-3">
              <Label className="text-xs text-white/60">{t("detail.costTrafficMultiplier")} ({trafficMultiplier.toFixed(1)}x)</Label>
              <input type="range" min={0.5} max={5} step={0.1} value={trafficMultiplier} onChange={(e) => setTrafficMultiplier(Number(e.target.value))} />
              <Label className="text-xs text-white/60">{t("detail.costDataMultiplier")} ({dataMultiplier.toFixed(1)}x)</Label>
              <input type="range" min={0.5} max={5} step={0.1} value={dataMultiplier} onChange={(e) => setDataMultiplier(Number(e.target.value))} />
              <Label className="text-xs text-white/60">{t("detail.costReliabilityProfile")}</Label>
              <select
                className="h-9 rounded-lg border border-white/10 bg-white/[0.02] text-white/80 px-3 text-sm"
                value={reliability}
                onChange={(e) => setReliability(e.target.value as typeof reliability)}
              >
                <option value="lean" className="bg-[#0a0a0a]">{t("detail.costProfileLean")}</option>
                <option value="balanced" className="bg-[#0a0a0a]">{t("detail.costProfileBalanced")}</option>
                <option value="critical" className="bg-[#0a0a0a]">{t("detail.costProfileCritical")}</option>
              </select>
              <Button
                variant="outline"
                className="mt-2"
                disabled={costBusy}
                onClick={async () => {
                  setCostBusy(true);
                  try {
                    const res = await api<CostAnalysisResult>(`/designs/${designId}/cost-analysis`, {
                      method: "POST",
                      body: JSON.stringify({
                        traffic_multiplier: trafficMultiplier,
                        data_multiplier: dataMultiplier,
                        reliability_profile: reliability,
                      }),
                    });
                    setCostScenario(res);
                  } finally {
                    setCostBusy(false);
                  }
                }}
              >
                {costBusy ? t("detail.costAnalyzing") : t("detail.costRunScenario")}
              </Button>
            </div>
            {costScenario ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-black/30 p-4 text-sm text-white/70">
                <p className="font-semibold text-cyan-200">
                  ${costScenario.monthly_usd_min.toLocaleString()} - ${costScenario.monthly_usd_max.toLocaleString()} / month
                </p>
                <p className="mt-1 text-white/50">
                  ${costScenario.yearly_usd_min.toLocaleString()} - ${costScenario.yearly_usd_max.toLocaleString()} / {t("detail.costPerYear")} • {t("detail.costConfidence")} {costScenario.confidence}
                </p>
              </div>
            ) : null}

              {designId !== undefined ? (
                <div className="mt-5 border-t border-white/10 pt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 rounded-lg border-emerald-500/20 bg-emerald-500/[0.05] text-emerald-300 hover:bg-emerald-500/10"
                    onClick={async () => {
                      const res = await api<CostCalibration>(`/designs/${designId}/cost-calibration`);
                      setCalibration(res);
                    }}
                  >
                    {t("detail.calibrateWithLiveSignals")}
                  </Button>
                  {calibration ? (
                    <div className="mt-2 text-xs text-emerald-200/80 space-y-1">
                      <p>
                        {t("detail.calibratedRange")}: ${calibration.calibrated_monthly_usd_min.toLocaleString()} - $
                        {calibration.calibrated_monthly_usd_max.toLocaleString()}
                      </p>
                      <p>
                        {t("detail.calibrationConfidence")}: {calibration.confidence} ({calibration.calibration_factor}x)
                      </p>
                    </div>
                  ) : null}
                </div>
              ) : null}
          </Card>
        ) : null}

        <Card className="p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl relative overflow-hidden">
          <h3 className="text-lg font-medium text-white/90">{t("detail.riskAnalysis")}</h3>
          <div className="mt-6 space-y-5 text-sm text-white/50 leading-relaxed">
            <p className="bg-white/[0.02] p-4 rounded-xl border border-white/5">
              <span className="text-white/90 block font-medium mb-1.5">{t("detail.biggestRisk")}:</span> {score.biggest_risk}
            </p>
            <p className="bg-white/[0.02] p-4 rounded-xl border border-white/5">
              <span className="text-white/90 block font-medium mb-1.5">{t("detail.biggestBottleneck")}:</span> {score.biggest_bottleneck}
            </p>
            <p className="bg-white/[0.02] p-4 rounded-xl border border-white/5">
              <span className="text-white/90 block font-medium mb-1.5">{t("detail.firstOptimization")}:</span> {score.first_optimization}
            </p>
            <p className="bg-white/[0.02] p-4 rounded-xl border border-white/5">
              <span className="text-white/90 block font-medium mb-1.5">{t("detail.avoidOverengineering")}:</span> {score.avoid_overengineering}
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
