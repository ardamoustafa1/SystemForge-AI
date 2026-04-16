"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Sparkles, UploadCloud, FileText, X } from "lucide-react";

import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/page-header";
import { createDesignSchema } from "@/features/designs/schemas";
import { useI18n } from "@/i18n/i18n-context";

type FormData = z.infer<typeof createDesignSchema>;

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-red-400">{message}</p>;
}

export default function NewDesignPage() {
  const router = useRouter();
  const { t, language } = useI18n();
  const [error, setError] = useState("");
  const [wizardStep, setWizardStep] = useState(1);
  const form = useForm<FormData>({
    resolver: zodResolver(createDesignSchema),
    defaultValues: {
      project_title: "",
      project_type: "",
      problem_statement: "",
      expected_users: "",
      traffic_assumptions: "",
      preferred_stack: "",
      constraints: "",
      budget_sensitivity: "medium",
      deployment_scope: "single-region",
      data_sensitivity: "medium",
      real_time_required: false,
      mode: "product",
      scale_stance: "balanced",
      document_context: "",
    },
    mode: "onBlur",
  });

  const [fileName, setFileName] = useState("");
  const watched = form.watch();
  const qualityScore = useMemo(() => {
    let score = 0;
    if ((watched.project_title || "").trim().length >= 3) score += 15;
    if ((watched.problem_statement || "").trim().length >= 40) score += 20;
    if ((watched.traffic_assumptions || "").trim().length >= 5) score += 20;
    if ((watched.constraints || "").trim().length >= 5) score += 15;
    if ((watched.expected_users || "").trim().length >= 1) score += 10;
    if ((watched.preferred_stack || "").trim().length >= 3) score += 10;
    if ((watched.document_context || "").trim().length >= 20) score += 10;
    return Math.min(100, score);
  }, [watched]);
  const starterPresets: { id: string; title: string; values: Partial<FormData> }[] = [
    {
      id: "saas",
      title: t("newDesign.presetSaas"),
      values: {
        project_type: "B2B SaaS",
        expected_users: "50k MAU",
        traffic_assumptions: "read-heavy daytime spikes",
        budget_sensitivity: "medium",
        deployment_scope: "multi-region",
      },
    },
    {
      id: "realtime",
      title: t("newDesign.presetRealtime"),
      values: {
        project_type: "Realtime collaboration",
        expected_users: "10k concurrent",
        traffic_assumptions: "burst writes, low latency",
        real_time_required: true,
        deployment_scope: "global",
      },
    },
    {
      id: "regulated",
      title: t("newDesign.presetRegulated"),
      values: {
        project_type: "Fintech / regulated",
        data_sensitivity: "critical",
        constraints: "audit trails, encryption at rest, tenant isolation",
        budget_sensitivity: "high",
      },
    },
  ];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result;
      if (typeof text === "string") {
        form.setValue("document_context", text);
      }
    };
    reader.readAsText(file);
  };
  
  const clearFile = () => {
    setFileName("");
    form.setValue("document_context", "");
  };

  const onSubmit = form.handleSubmit(async (values) => {
    setError("");
    try {
      const { scale_stance, ...input } = values;
      const response = await api<{ id: number; title: string }>("/designs", {
        method: "POST",
        body: JSON.stringify({ input, scale_stance, output_language: language }),
      });
      router.push(`/dashboard/designs/${response.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("newDesign.generateFailed"));
    }
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("newDesign.title")}
        subtitle={t("newDesign.subtitle")}
      />

      <form className="grid gap-6 lg:grid-cols-12 pb-20" onSubmit={onSubmit}>
        <Card className="lg:col-span-8 p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl space-y-6">
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-white/60">Onboarding wizard step {wizardStep}/3</p>
              <p className="text-xs text-emerald-300">Input quality score: {qualityScore}/100</p>
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-white/10">
              <div className="h-full rounded-full bg-emerald-400 transition-all" style={{ width: `${qualityScore}%` }} />
            </div>
            <div className="mt-3 flex gap-2">
              <Button type="button" size="sm" variant="outline" disabled={wizardStep <= 1} onClick={() => setWizardStep((s) => Math.max(1, s - 1))}>Prev</Button>
              <Button type="button" size="sm" variant="outline" disabled={wizardStep >= 3} onClick={() => setWizardStep((s) => Math.min(3, s + 1))}>Next</Button>
            </div>
          </div>
          
          <section className={`space-y-4 ${wizardStep === 1 ? "block" : "hidden"}`}>
            <h2 className="text-base font-semibold">{t("newDesign.uploadContextTitle")}</h2>
            <div className="relative group border-2 border-dashed border-white/10 rounded-xl p-6 bg-white/[0.01] hover:bg-white/[0.02] hover:border-emerald-500/30 transition-all text-center">
              {!fileName ? (
                <>
                  <UploadCloud className="w-8 h-8 mx-auto text-white/30 group-hover:text-emerald-400 mb-3 transition-colors" />
                  <p className="text-sm text-white/70">{t("newDesign.uploadContextHint")}</p>
                  <p className="text-xs text-white/40 mt-1">{t("newDesign.uploadContextTypes")}</p>
                  <input 
                    type="file" 
                    accept=".txt,.md,.csv" 
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                </>
              ) : (
                <div className="flex items-center justify-between bg-white/[0.05] p-3 rounded-lg border border-white/10">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-emerald-400" />
                    <span className="text-sm font-medium text-white/90">{fileName}</span>
                  </div>
                  <button 
                    type="button" 
                    onClick={clearFile}
                    className="p-1 hover:bg-white/10 rounded"
                  >
                    <X className="w-4 h-4 text-white/60 hover:text-red-400" />
                  </button>
                </div>
              )}
            </div>
            {fileName && (
              <p className="text-xs text-emerald-400/80 mt-2">
                {t("newDesign.uploadContextLoaded")}
              </p>
            )}
          </section>

          <div className="space-y-6 pt-2">
            <section className="space-y-4">
              <h2 className="text-base font-semibold">{t("newDesign.projectContext")}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="project_title" className="text-white/70">{t("newDesign.projectTitle")}</Label>
                  <Input id="project_title" placeholder={t("newDesign.placeholder.projectTitle")} {...form.register("project_title")} className="bg-white/[0.02] border-white/10 text-white h-11 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20" />
                  <FieldError message={form.formState.errors.project_title?.message} />
                </div>
                <div>
                  <Label htmlFor="project_type" className="text-white/70">{t("newDesign.projectCategory")}</Label>
                  <Input id="project_type" placeholder={t("newDesign.placeholder.projectType")} {...form.register("project_type")} className="bg-white/[0.02] border-white/10 text-white h-11 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20" />
                  <FieldError message={form.formState.errors.project_type?.message} />
                </div>
              </div>
              <div className="pt-2">
                <Label htmlFor="problem_statement" className="text-white/70">{t("newDesign.problemStatement")}</Label>
                <Textarea
                  id="problem_statement"
                  placeholder={t("newDesign.placeholder.problemStatement")}
                  className="min-h-32 bg-white/[0.02] border-white/10 text-white placeholder:text-white/30 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20"
                  {...form.register("problem_statement")}
                />
                <FieldError message={form.formState.errors.problem_statement?.message} />
              </div>
            </section>

            <section className={`space-y-4 pt-6 border-t border-white/5 ${wizardStep === 2 ? "block" : "hidden"}`}>
              <h2 className="text-base font-semibold text-white/90">{t("newDesign.scaleTraffic")}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="expected_users" className="text-white/70">{t("newDesign.expectedUsers")}</Label>
                  <Input id="expected_users" placeholder={t("newDesign.placeholder.expectedUsers")} {...form.register("expected_users")} className="bg-white/[0.02] border-white/10 text-white h-11 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20" />
                  <FieldError message={form.formState.errors.expected_users?.message} />
                </div>
                <div>
                  <Label htmlFor="traffic_assumptions" className="text-white/70">{t("newDesign.trafficAssumptions")}</Label>
                  <Input id="traffic_assumptions" placeholder={t("newDesign.placeholder.trafficAssumptions")} {...form.register("traffic_assumptions")} className="bg-white/[0.02] border-white/10 text-white h-11 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20" />
                  <FieldError message={form.formState.errors.traffic_assumptions?.message} />
                </div>
              </div>
            </section>

            <section className={`space-y-4 pt-6 border-t border-white/5 ${wizardStep === 3 ? "block" : "hidden"}`}>
              <h2 className="text-base font-semibold text-white/90">{t("newDesign.constraintsPlatform")}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="budget_sensitivity" className="text-white/70">{t("newDesign.budgetSensitivity")}</Label>
                  <select
                    id="budget_sensitivity"
                    aria-label={t("newDesign.label.budgetSensitivity")}
                    className="h-11 w-full mt-1.5 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white/90 focus-visible:ring-1 focus-visible:ring-white/20 appearance-none"
                    {...form.register("budget_sensitivity")}
                  >
                    <option value="low" className="bg-[#0a0a0a]">{t("common.low")}</option>
                    <option value="medium" className="bg-[#0a0a0a]">{t("common.medium")}</option>
                    <option value="high" className="bg-[#0a0a0a]">{t("common.high")}</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="preferred_stack" className="text-white/70">{t("newDesign.preferredStack")}</Label>
                  <Input id="preferred_stack" placeholder={t("newDesign.placeholder.preferredStack")} {...form.register("preferred_stack")} className="bg-white/[0.02] border-white/10 text-white h-11 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20" />
                </div>
              </div>
              <div className="pt-2">
                <Label htmlFor="constraints" className="text-white/70">{t("newDesign.constraints")}</Label>
                <Textarea
                  id="constraints"
                  placeholder={t("newDesign.placeholder.constraints")}
                  className="min-h-24 bg-white/[0.02] border-white/10 text-white placeholder:text-white/30 mt-1.5 focus-visible:ring-1 focus-visible:ring-white/20"
                  {...form.register("constraints")}
                />
                <FieldError message={form.formState.errors.constraints?.message} />
              </div>
            </section>
          </div>
        </Card>

        <Card className="lg:col-span-4 p-6 sm:p-8 rounded-2xl border-white/5 bg-[#0a0a0a] shadow-xl h-fit">
          <h2 className="text-base font-semibold text-white/90">{t("newDesign.deploymentRisk")}</h2>
          <Card className="mt-4 border border-emerald-500/20 bg-emerald-500/[0.04] p-4 rounded-xl">
            <h3 className="text-sm font-semibold text-emerald-300">{t("newDesign.quickStartPresets")}</h3>
            <div className="mt-3 grid gap-2">
              {starterPresets.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  className="rounded-lg border border-emerald-500/20 bg-black/20 px-3 py-2 text-left text-xs text-emerald-100/90 hover:bg-emerald-500/10"
                  onClick={() => {
                    Object.entries(preset.values).forEach(([key, value]) => {
                      form.setValue(key as keyof FormData, value as never, { shouldDirty: true });
                    });
                  }}
                >
                  {preset.title}
                </button>
              ))}
            </div>
          </Card>
          <Card className="mt-4 border border-cyan-500/20 bg-cyan-500/[0.04] p-4 rounded-xl">
            <h3 className="text-sm font-semibold text-cyan-300">{t("newDesign.guideTitle")}</h3>
            <ul className="mt-2 list-disc pl-5 space-y-1 text-xs text-cyan-100/80">
              <li>{t("newDesign.guideTraffic")}</li>
              <li>{t("newDesign.guideSensitivity")}</li>
              <li>{t("newDesign.guideConstraints")}</li>
            </ul>
          </Card>
          <div className="mt-4 space-y-5">
            <div>
              <Label htmlFor="deployment_scope" className="text-white/70">{t("newDesign.deploymentRegion")}</Label>
              <select
                id="deployment_scope"
                aria-label={t("newDesign.label.deploymentRegion")}
                className="h-11 w-full mt-1.5 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white/90 focus-visible:ring-1 focus-visible:ring-white/20 appearance-none"
                {...form.register("deployment_scope")}
              >
                <option value="single-region" className="bg-[#0a0a0a]">{t("common.singleRegion")}</option>
                <option value="multi-region" className="bg-[#0a0a0a]">{t("common.multiRegion")}</option>
                <option value="global" className="bg-[#0a0a0a]">{t("common.global")}</option>
              </select>
            </div>

            <div>
              <Label htmlFor="data_sensitivity" className="text-white/70">{t("newDesign.dataSensitivity")}</Label>
              <select
                id="data_sensitivity"
                aria-label={t("newDesign.label.dataSensitivity")}
                className="h-11 w-full mt-1.5 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white/90 focus-visible:ring-1 focus-visible:ring-white/20 appearance-none"
                {...form.register("data_sensitivity")}
              >
                <option value="low" className="bg-[#0a0a0a]">{t("common.low")}</option>
                <option value="medium" className="bg-[#0a0a0a]">{t("common.medium")}</option>
                <option value="high" className="bg-[#0a0a0a]">{t("common.high")}</option>
                <option value="critical" className="bg-[#0a0a0a]">{t("common.critical")}</option>
              </select>
            </div>

            <div>
              <Label htmlFor="mode" className="text-white/70">{t("newDesign.planningMode")}</Label>
              <select
                id="mode"
                aria-label={t("newDesign.label.planningMode")}
                className="h-11 w-full mt-1.5 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white/90 focus-visible:ring-1 focus-visible:ring-white/20 appearance-none"
                {...form.register("mode")}
              >
                <option value="product" className="bg-[#0a0a0a]">{t("newDesign.realProductMode")}</option>
                <option value="interview" className="bg-[#0a0a0a]">{t("newDesign.interviewMode")}</option>
              </select>
            </div>

            <label className="flex items-center gap-3 rounded-xl border border-white/10 p-4 text-sm text-white/70 bg-white/[0.01]">
              <input type="checkbox" className="h-4 w-4 rounded border-white/20 bg-white/[0.02] checked:bg-white" {...form.register("real_time_required")} />
              {t("newDesign.realtimeRequirement")}
            </label>

            <div>
              <Label htmlFor="scale_stance" className="text-white/70">{t("newDesign.scaleStance")}</Label>
              <select
                id="scale_stance"
                className="h-11 w-full mt-1.5 rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white/90 focus-visible:ring-1 focus-visible:ring-white/20 appearance-none"
                {...form.register("scale_stance")}
              >
                <option value="balanced" className="bg-[#0a0a0a]">{t("detail.stanceBalanced")}</option>
                <option value="conservative" className="bg-[#0a0a0a]">{t("detail.stanceConservative")}</option>
                <option value="aggressive" className="bg-[#0a0a0a]">{t("detail.stanceAggressive")}</option>
              </select>
              <p className="mt-2 text-xs text-white/40">{t("newDesign.scaleStanceHelp")}</p>
            </div>

            <Card className="border-dashed border-white/10 bg-white/[0.01] p-5 rounded-xl">
              <div className="flex items-start gap-2">
                <Sparkles className="mt-0.5 h-4 w-4 text-brand" />
                <p className="text-xs text-muted">
                  {t("newDesign.generationIncludes")}
                </p>
              </div>
            </Card>
          </div>

          {error ? <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">{error}</p> : null}

          <Button type="submit" className="mt-8 w-full h-12 bg-white text-black hover:bg-white/90 font-medium rounded-xl" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? t("newDesign.generating") : t("newDesign.generate")}
          </Button>
        </Card>
      </form>
    </div>
  );
}
