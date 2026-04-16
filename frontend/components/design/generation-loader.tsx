"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, CircleDashed, Server, Database, CloudCog, ShieldCheck, Zap } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n/i18n-context";
import { GenerationProgress } from "@/types/design";

type Props = {
  progress?: GenerationProgress | null;
};

const PHASE_INDEX: Record<string, number> = {
  queued: 0,
  context_parsed: 1,
  architecture_designed: 2,
  cost_estimated: 3,
  finalizing: 4,
  completed: 4,
};

export function GenerationLoader({ progress }: Props) {
  const [activeStep, setActiveStep] = useState(0);
  const [pseudoProgress, setPseudoProgress] = useState(6);
  const [startedAt] = useState<number>(() => Date.now());
  const { t } = useI18n();
  const hasRealtimeProgress = typeof progress?.progress_pct === "number" || Boolean(progress?.phase);

  const steps = [
    { label: t("detail.loader.analyzing"), icon: Server },
    { label: t("detail.loader.evaluating"), icon: CloudCog },
    { label: t("detail.loader.designing"), icon: Database },
    { label: t("detail.loader.calculating"), icon: Zap },
    { label: t("detail.loader.finalizing"), icon: ShieldCheck },
  ];

  useEffect(() => {
    if (progress?.phase && PHASE_INDEX[progress.phase] !== undefined) {
      setActiveStep(PHASE_INDEX[progress.phase]);
    }
    if (typeof progress?.progress_pct === "number") {
      setPseudoProgress(Math.max(progress.progress_pct, 5));
      return;
    }

    // Fallback pseudo-progress for labor-illusion behavior.
    const interval = setInterval(() => {
      setActiveStep((prev) => Math.min(prev + 1, steps.length - 1));
      setPseudoProgress((prev) => Math.min(prev + 3, 94));
    }, 4200);

    return () => clearInterval(interval);
  }, [steps.length, progress?.phase, progress?.progress_pct]);
  const elapsedSec = Math.max(1, Math.floor((Date.now() - startedAt) / 1000));
  const progressPct = Math.max(1, Math.min(99, pseudoProgress));
  const etaSec = Math.max(1, Math.floor((elapsedSec * (100 - progressPct)) / progressPct));
  const confidence = hasRealtimeProgress ? "high" : "medium";

  return (
    <Card className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl w-full max-w-2xl mx-auto mt-6">
      <div className="relative flex items-center justify-center w-24 h-24 mb-8">
        <div className="absolute inset-0 rounded-full border-t-2 border-l-2 border-emerald-500 animate-spin opacity-50" style={{ animationDuration: '3s' }} />
        <div className="absolute inset-2 rounded-full border-r-2 border-b-2 border-cyan-500 animate-spin opacity-40" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
        <div className="absolute inset-4 rounded-full border-t-2 border-brand animate-spin opacity-60" style={{ animationDuration: '1.5s' }} />
        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/10">
          <CloudCog className="w-6 h-6 text-white/80 animate-pulse" />
        </div>
      </div>

      <h3 className="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400 mb-2">
        {t("detail.loader.title")}
      </h3>
      <p className="text-sm text-white/40 mb-8 max-w-md">
        {t("detail.loader.desc")}
      </p>

      <div className="w-full space-y-4 text-left bg-white/[0.02] p-6 rounded-xl border border-white/5">
        <div className="mb-2">
          <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-700"
              style={{ width: `${Math.min(pseudoProgress, 100)}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-white/40">{Math.min(pseudoProgress, 100)}%</p>
          <p className="mt-1 text-[11px] text-white/35">
            {hasRealtimeProgress ? t("detail.loader.confidenceRealtime") : t("detail.loader.confidenceEstimated")}
          </p>
          <p className="mt-1 text-[11px] text-white/35">
            ETA ~ {etaSec}s • phase confidence: {confidence}
          </p>
        </div>
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isComplete = index < activeStep;
          const isActive = index === activeStep;
          const isPending = index > activeStep;

          return (
            <div 
              key={index} 
              className={`flex items-center gap-4 transition-all duration-500 ${isActive ? "opacity-100 translate-x-2" : isPending ? "opacity-30" : "opacity-70"}`}
            >
              <div className="flex-shrink-0">
                {isComplete ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                ) : isActive ? (
                  <CircleDashed className="w-5 h-5 text-cyan-400 animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border border-white/20" />
                )}
              </div>
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : isComplete ? "text-emerald-500" : "text-white/20"}`} />
                <span className={`text-sm font-medium ${isActive ? "text-white" : isComplete ? "text-white/70" : "text-white/40"}`}>
                  {step.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
