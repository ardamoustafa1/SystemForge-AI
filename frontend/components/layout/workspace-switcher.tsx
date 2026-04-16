"use client";

import { useState } from "react";
import { ChevronDown, CheckCircle2, Plus, LayoutGrid } from "lucide-react";
import { useWorkspace } from "@/lib/workspace-context";
import { useI18n } from "@/i18n/i18n-context";

export function WorkspaceSwitcher() {
  const { workspaces, activeWorkspace, activeRole, switchWorkspace, createWorkspace } = useWorkspace();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || busy) return;
    setBusy(true);
    try {
      await createWorkspace(newName.trim());
      setNewName("");
      setCreating(false);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  const roleColors: Record<string, string> = {
    admin: "text-amber-400",
    editor: "text-emerald-400",
    viewer: "text-white/40",
  };

  if (!activeWorkspace) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl border border-white/5 bg-[#0a0a0a] px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.03] hover:border-white/10 transition-all"
      >
        <LayoutGrid className="h-3.5 w-3.5 text-white/40" />
        <span className="max-w-[120px] truncate font-medium">{activeWorkspace.name}</span>
        <span className={`text-[10px] font-semibold uppercase tracking-widest ${roleColors[activeRole ?? "viewer"]}`}>
          {activeRole}
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-white/30 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute top-[calc(100%+8px)] left-0 z-50 min-w-[220px] rounded-2xl border border-white/5 bg-[#0d0d0d] shadow-[0_24px_60px_-12px_rgba(0,0,0,0.8)] p-2">
          <p className="px-3 py-1.5 text-[10px] font-semibold tracking-widest text-white/30 uppercase">{t("workspace.listLabel")}</p>
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => {
                switchWorkspace(ws.id);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition-colors ${
                ws.id === activeWorkspace.id
                  ? "bg-white/[0.05] text-white"
                  : "text-white/60 hover:bg-white/[0.03] hover:text-white/90"
              }`}
            >
              <span className="flex-1 truncate text-left font-medium">{ws.name}</span>
              <span className={`text-[10px] font-bold uppercase ${roleColors[ws.role]}`}>{ws.role}</span>
              {ws.id === activeWorkspace.id && <CheckCircle2 className="h-3.5 w-3.5 text-white/40 shrink-0" />}
            </button>
          ))}

          <div className="my-2 border-t border-white/5" />

          {creating ? (
            <form onSubmit={handleCreate} className="px-2 pb-1">
              <input
                autoFocus
                className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-white/20"
                placeholder={t("workspace.namePlaceholder")}
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <div className="mt-2 flex gap-2">
                <button
                  type="submit"
                  disabled={busy}
                  className="flex-1 rounded-lg bg-white py-1.5 text-xs font-semibold text-black hover:bg-white/90 disabled:opacity-50"
                >
                  {busy ? t("workspace.creating") : t("common.create")}
                </button>
                <button
                  type="button"
                  onClick={() => setCreating(false)}
                  className="rounded-lg border border-white/5 px-3 py-1.5 text-xs text-white/50 hover:text-white"
                >
                  {t("common.cancel")}
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setCreating(true)}
              className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm text-white/50 hover:bg-white/[0.03] hover:text-white/90 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              {t("workspace.new")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
