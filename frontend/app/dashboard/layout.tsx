"use client";

import React from "react";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { WorkspaceProvider } from "@/lib/workspace-context";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <WorkspaceProvider>
        <DashboardShell>{children}</DashboardShell>
      </WorkspaceProvider>
    </ProtectedRoute>
  );
}
