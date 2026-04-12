"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Sparkles } from "lucide-react";

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
  const { t } = useI18n();
  const [error, setError] = useState("");
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
    },
    mode: "onBlur",
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setError("");
    try {
      const { scale_stance, ...input } = values;
      const response = await api<{ id: number; title: string }>("/designs", {
        method: "POST",
        body: JSON.stringify({ input, scale_stance }),
      });
      router.push(`/dashboard/designs/${response.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Design generation failed");
    }
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("newDesign.title")}
        subtitle={t("newDesign.subtitle")}
      />

      <form className="grid gap-4 lg:grid-cols-12" onSubmit={onSubmit}>
        <Card className="lg:col-span-8 p-6">
          <div className="space-y-6">
            <section className="space-y-4">
              <h2 className="text-base font-semibold">{t("newDesign.projectContext")}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="project_title">{t("newDesign.projectTitle")}</Label>
                  <Input id="project_title" placeholder={t("newDesign.placeholder.projectTitle")} {...form.register("project_title")} />
                  <FieldError message={form.formState.errors.project_title?.message} />
                </div>
                <div>
                  <Label htmlFor="project_type">{t("newDesign.projectCategory")}</Label>
                  <Input id="project_type" placeholder={t("newDesign.placeholder.projectType")} {...form.register("project_type")} />
                  <FieldError message={form.formState.errors.project_type?.message} />
                </div>
              </div>
              <div>
                <Label htmlFor="problem_statement">{t("newDesign.problemStatement")}</Label>
                <Textarea
                  id="problem_statement"
                  placeholder={t("newDesign.placeholder.problemStatement")}
                  className="min-h-32"
                  {...form.register("problem_statement")}
                />
                <FieldError message={form.formState.errors.problem_statement?.message} />
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="text-base font-semibold">{t("newDesign.scaleTraffic")}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="expected_users">{t("newDesign.expectedUsers")}</Label>
                  <Input id="expected_users" placeholder={t("newDesign.placeholder.expectedUsers")} {...form.register("expected_users")} />
                  <FieldError message={form.formState.errors.expected_users?.message} />
                </div>
                <div>
                  <Label htmlFor="traffic_assumptions">{t("newDesign.trafficAssumptions")}</Label>
                  <Input id="traffic_assumptions" placeholder={t("newDesign.placeholder.trafficAssumptions")} {...form.register("traffic_assumptions")} />
                  <FieldError message={form.formState.errors.traffic_assumptions?.message} />
                </div>
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="text-base font-semibold">{t("newDesign.constraintsPlatform")}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="budget_sensitivity">{t("newDesign.budgetSensitivity")}</Label>
                  <select
                    id="budget_sensitivity"
                    aria-label={t("newDesign.label.budgetSensitivity")}
                    className="h-10 w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm"
                    {...form.register("budget_sensitivity")}
                  >
                    <option value="low">{t("common.low")}</option>
                    <option value="medium">{t("common.medium")}</option>
                    <option value="high">{t("common.high")}</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="preferred_stack">{t("newDesign.preferredStack")}</Label>
                  <Input id="preferred_stack" placeholder={t("newDesign.placeholder.preferredStack")} {...form.register("preferred_stack")} />
                </div>
              </div>
              <div>
                <Label htmlFor="constraints">{t("newDesign.constraints")}</Label>
                <Textarea
                  id="constraints"
                  placeholder={t("newDesign.placeholder.constraints")}
                  className="min-h-24"
                  {...form.register("constraints")}
                />
                <FieldError message={form.formState.errors.constraints?.message} />
              </div>
            </section>
          </div>
        </Card>

        <Card className="lg:col-span-4 p-6">
          <h2 className="text-base font-semibold">{t("newDesign.deploymentRisk")}</h2>
          <div className="mt-4 space-y-4">
            <div>
              <Label htmlFor="deployment_scope">{t("newDesign.deploymentRegion")}</Label>
              <select
                id="deployment_scope"
                aria-label={t("newDesign.label.deploymentRegion")}
                className="h-10 w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm"
                {...form.register("deployment_scope")}
              >
                <option value="single-region">{t("common.singleRegion")}</option>
                <option value="multi-region">{t("common.multiRegion")}</option>
                <option value="global">{t("common.global")}</option>
              </select>
            </div>

            <div>
              <Label htmlFor="data_sensitivity">{t("newDesign.dataSensitivity")}</Label>
              <select
                id="data_sensitivity"
                aria-label={t("newDesign.label.dataSensitivity")}
                className="h-10 w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm"
                {...form.register("data_sensitivity")}
              >
                <option value="low">{t("common.low")}</option>
                <option value="medium">{t("common.medium")}</option>
                <option value="high">{t("common.high")}</option>
                <option value="critical">{t("common.critical")}</option>
              </select>
            </div>

            <div>
              <Label htmlFor="mode">{t("newDesign.planningMode")}</Label>
              <select
                id="mode"
                aria-label={t("newDesign.label.planningMode")}
                className="h-10 w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm"
                {...form.register("mode")}
              >
                <option value="product">{t("newDesign.realProductMode")}</option>
                <option value="interview">{t("newDesign.interviewMode")}</option>
              </select>
            </div>

            <label className="flex items-center gap-2 rounded-md border border-border p-3 text-sm text-muted">
              <input type="checkbox" className="h-4 w-4 rounded border-border" {...form.register("real_time_required")} />
              {t("newDesign.realtimeRequirement")}
            </label>

            <div>
              <Label htmlFor="scale_stance">{t("newDesign.scaleStance")}</Label>
              <select
                id="scale_stance"
                className="mt-1 h-10 w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm"
                {...form.register("scale_stance")}
              >
                <option value="balanced">{t("detail.stanceBalanced")}</option>
                <option value="conservative">{t("detail.stanceConservative")}</option>
                <option value="aggressive">{t("detail.stanceAggressive")}</option>
              </select>
              <p className="mt-1 text-xs text-muted">{t("newDesign.scaleStanceHelp")}</p>
            </div>

            <Card className="border-dashed p-4">
              <div className="flex items-start gap-2">
                <Sparkles className="mt-0.5 h-4 w-4 text-brand" />
                <p className="text-xs text-muted">
                  {t("newDesign.generationIncludes")}
                </p>
              </div>
            </Card>
          </div>

          {error ? <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">{error}</p> : null}

          <Button type="submit" className="mt-6 w-full" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? t("newDesign.generating") : t("newDesign.generate")}
          </Button>
        </Card>
      </form>
    </div>
  );
}
