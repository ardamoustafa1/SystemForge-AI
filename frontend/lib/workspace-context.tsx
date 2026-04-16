"use client";

import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

export type WorkspaceRole = "admin" | "editor" | "viewer";

export type WorkspaceSummary = {
  id: number;
  name: string;
  role: WorkspaceRole;
  created_at: string;
};

export type WorkspaceMember = {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  role: WorkspaceRole;
  joined_at: string;
};

type WorkspaceContextType = {
  workspaces: WorkspaceSummary[];
  activeWorkspace: WorkspaceSummary | null;
  activeRole: WorkspaceRole | null;
  members: WorkspaceMember[];
  loading: boolean;
  switchWorkspace: (id: number) => Promise<void>;
  createWorkspace: (name: string) => Promise<WorkspaceSummary>;
  inviteMember: (email: string, role: WorkspaceRole) => Promise<void>;
  updateMemberRole: (memberId: number, role: WorkspaceRole) => Promise<void>;
  removeMember: (memberId: number) => Promise<void>;
  refreshWorkspace: () => Promise<void>;
};

const WorkspaceContext = createContext<WorkspaceContextType | null>(null);

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return ctx;
}

// Keep the active workspace ID in a module-level variable so api.ts can read it synchronously
let _activeWorkspaceId: number | null = null;
export function getActiveWorkspaceId() {
  return _activeWorkspaceId;
}

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceSummary | null>(null);
  const [activeRole, setActiveRole] = useState<WorkspaceRole | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch all workspaces the user belongs to
  const loadWorkspaces = useCallback(async () => {
    try {
      const all = await api<WorkspaceSummary[]>("/workspaces");
      setWorkspaces(all);

      // Determine active workspace from localStorage or default to first
      const savedId = typeof window !== "undefined" ? localStorage.getItem("sf_active_workspace") : null;
      const match = savedId ? all.find((w) => w.id === Number(savedId)) : null;
      const chosen = match ?? all[0] ?? null;
      if (chosen) {
        await _activateWorkspace(chosen, all);
      } else {
        setLoading(false);
      }
    } catch {
      setLoading(false);
    }
  }, []);

  const _activateWorkspace = useCallback(async (ws: WorkspaceSummary, allWs?: WorkspaceSummary[]) => {
    _activeWorkspaceId = ws.id;
    if (typeof window !== "undefined") localStorage.setItem("sf_active_workspace", String(ws.id));
    setActiveWorkspace(ws);
    setActiveRole(ws.role);
    if (allWs) setWorkspaces(allWs);
    try {
      const detail = await api<{ workspace: { id: number; name: string; created_at: string; updated_at: string }; role: string; members: WorkspaceMember[] }>(
        `/workspaces/${ws.id}`
      );
      setMembers(detail.members);
    } catch {
      setMembers([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  const switchWorkspace = useCallback(async (id: number) => {
    setLoading(true);
    const ws = workspaces.find((w) => w.id === id);
    if (ws) await _activateWorkspace(ws);
    // Persist as default on the server too (best effort)
    try { await api(`/workspaces/${id}/default`, { method: "POST" }); } catch { /* ignore */ }
  }, [workspaces, _activateWorkspace]);

  const createWorkspace = useCallback(async (name: string): Promise<WorkspaceSummary> => {
    const res = await api<{ workspace: { id: number; name: string; created_at: string }; role: string }>("/workspaces", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    const newWs: WorkspaceSummary = { id: res.workspace.id, name: res.workspace.name, role: res.role as WorkspaceRole, created_at: res.workspace.created_at };
    setWorkspaces((prev) => [...prev, newWs]);
    await _activateWorkspace(newWs);
    return newWs;
  }, [_activateWorkspace]);

  const refreshWorkspace = useCallback(async () => {
    if (!activeWorkspace) return;
    await _activateWorkspace(activeWorkspace);
  }, [activeWorkspace, _activateWorkspace]);

  const inviteMember = useCallback(async (email: string, role: WorkspaceRole) => {
    if (!activeWorkspace) return;
    await api(`/workspaces/${activeWorkspace.id}/members`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
    await refreshWorkspace();
  }, [activeWorkspace, refreshWorkspace]);

  const updateMemberRole = useCallback(async (memberId: number, role: WorkspaceRole) => {
    if (!activeWorkspace) return;
    await api(`/workspaces/${activeWorkspace.id}/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
    await refreshWorkspace();
  }, [activeWorkspace, refreshWorkspace]);

  const removeMember = useCallback(async (memberId: number) => {
    if (!activeWorkspace) return;
    await api(`/workspaces/${activeWorkspace.id}/members/${memberId}`, { method: "DELETE" });
    await refreshWorkspace();
  }, [activeWorkspace, refreshWorkspace]);

  return (
    <WorkspaceContext.Provider value={{ workspaces, activeWorkspace, activeRole, members, loading, switchWorkspace, createWorkspace, inviteMember, updateMemberRole, removeMember, refreshWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
}
