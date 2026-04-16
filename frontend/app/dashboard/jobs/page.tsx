"use client";

import useSWR from "swr";
import Link from "next/link";

import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";

type JobCenterResponse = {
  jobs: { job_type: string; job_id?: string; design_id?: number; status: string; tracked_at: string; format?: "pdf" | "markdown" }[];
  recent_generations: { design_id: number; generation_ms: number; updated_at: string }[];
};

export default function JobsPage() {
  const { data, mutate } = useSWR<JobCenterResponse>("/dashboard/job-center", api);

  return (
    <div className="space-y-6">
      <PageHeader title="Async Job Center" subtitle="Export and generation history for operational visibility." />
      <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] p-5">
        <h3 className="text-sm font-semibold text-white/90 mb-3">Tracked Jobs</h3>
        <div className="space-y-2">
          {(data?.jobs ?? []).map((job, idx) => (
            <div key={`${job.job_id ?? job.design_id}-${idx}`} className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] p-2">
              <p className="text-xs text-white/60">
                {job.job_type} • {job.status} • {job.job_id ?? `design:${job.design_id ?? "-"}`} • {new Date(job.tracked_at).toLocaleString()}
              </p>
              <div className="flex items-center gap-2">
                {job.design_id ? (
                  <Link href={`/dashboard/designs/${job.design_id}`} className="text-xs text-white/60 hover:text-white">
                    open
                  </Link>
                ) : null}
                {job.design_id ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      await api("/dashboard/job-center/retry", {
                        method: "POST",
                        body: JSON.stringify({
                          job_type: job.job_type,
                          design_id: job.design_id,
                          format: job.format ?? "pdf",
                        }),
                      });
                      mutate();
                      if (typeof window !== "undefined") {
                        window.dispatchEvent(new Event("sf-job-retried"));
                      }
                    }}
                  >
                    retry
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card className="rounded-2xl border-white/5 bg-[#0a0a0a] p-5">
        <h3 className="text-sm font-semibold text-white/90 mb-3">Recent Generations</h3>
        <div className="space-y-2">
          {(data?.recent_generations ?? []).map((row) => (
            <p key={`${row.design_id}-${row.updated_at}`} className="text-xs text-white/60">
              design #{row.design_id} • {row.generation_ms} ms • {new Date(row.updated_at).toLocaleString()}
            </p>
          ))}
        </div>
      </Card>
    </div>
  );
}

