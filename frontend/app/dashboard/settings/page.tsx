"use client";

import { useState } from "react";
import { useI18n } from "@/i18n/i18n-context";
import { User, Palette, Key, Check, Users, Crown, Pencil, Eye, Trash2, UserPlus, Mail, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import useSWR from "swr";
import { api } from "@/lib/api";
import { useWorkspace, WorkspaceRole } from "@/lib/workspace-context";
import { AuthUser } from "@/types/auth";

type UserSettings = {
  theme: string;
  default_mode: string;
};

const ROLE_META: Record<WorkspaceRole, { label: string; icon: React.ElementType; color: string }> = {
  admin: { label: "Admin", icon: Crown, color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  editor: { label: "Editor", icon: Pencil, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  viewer: { label: "Viewer", icon: Eye, color: "text-white/40 bg-white/5 border-white/10" },
};

function RoleBadge({ role }: { role: WorkspaceRole }) {
  const meta = ROLE_META[role];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest ${meta.color}`}>
      <meta.icon className="h-2.5 w-2.5" />
      {meta.label}
    </span>
  );
}

function InviteDialog({ onClose }: { onClose: () => void }) {
  const { inviteMember } = useWorkspace();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<WorkspaceRole>("editor");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      await inviteMember(email.trim(), role);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to invite member");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0d0d0d] p-8 shadow-[0_32px_80px_-16px_rgba(0,0,0,0.9)]">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 border border-white/10">
            <UserPlus className="h-4 w-4 text-white/60" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Invite Team Member</h3>
            <p className="text-xs text-white/40">They need an existing SystemForge account.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/60 uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30 pointer-events-none" />
              <input
                type="email"
                required
                autoFocus
                className="w-full rounded-xl border border-white/10 bg-white/[0.02] pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-white/20"
                placeholder="colleague@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/60 uppercase tracking-wider">Role</label>
            <div className="grid grid-cols-3 gap-2">
              {(["admin", "editor", "viewer"] as WorkspaceRole[]).map((r) => {
                const meta = ROLE_META[r];
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`flex flex-col items-center gap-1.5 rounded-xl border py-3 text-xs font-semibold uppercase tracking-wider transition-all ${
                      role === r ? meta.color : "border-white/5 bg-transparent text-white/40 hover:border-white/10 hover:text-white/60"
                    }`}
                  >
                    <meta.icon className="h-3.5 w-3.5" />
                    {meta.label}
                  </button>
                );
              })}
            </div>
          </div>

          {error && <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 rounded-xl border border-white/10 py-2.5 text-sm text-white/60 hover:text-white hover:border-white/20 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={busy} className="flex-1 rounded-xl bg-white py-2.5 text-sm font-semibold text-black hover:bg-white/90 disabled:opacity-50 transition-colors">
              {busy ? "Sending..." : "Send Invite"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { t } = useI18n();
  const { activeWorkspace, activeRole, members, removeMember, updateMemberRole } = useWorkspace();
  const [activeTab, setActiveTab] = useState("profile");
  const [showInvite, setShowInvite] = useState(false);

  const { data: settings, mutate } = useSWR<UserSettings>("/users/me/settings", api);
  const { data: me } = useSWR<AuthUser>("/auth/me", api);
  const { data: sessions, mutate: mutateSessions } = useSWR<{ items: { id: number; is_revoked: boolean; created_at: string; expires_at: string }[] }>("/auth/sessions", api);
  const { data: abuseSummary } = useSWR<Record<string, number>>("/security/abuse-summary?days=7", api);
  const { data: anomalySummary } = useSWR<{ anomaly_score: number; anomalies: string[] }>("/security/anomaly-summary", api);
  const { data: auditTrail } = useSWR<{ items: { ts: string; action: string; actor_user_id: number; metadata?: Record<string, unknown> }[] }>("/security/audit-trail?limit=20", api);
  const { data: apiVersions } = useSWR<{ current: string; compatibility: string; sunset_at?: string | null }>("/health/api-versions", api);

  const updateSetting = async (key: keyof UserSettings, value: string) => {
    if (!settings) return;
    const previous = { ...settings };
    const updated = { ...settings, [key]: value };
    mutate(updated, false); // Optimistic update
    try {
      await api("/users/me/settings", {
        method: "PATCH",
        body: JSON.stringify({ [key]: value }),
      });
    } catch (err) {
      console.error(err);
      mutate(previous, false); // Revert on failure
    }
  };

  const tabs = [
    { id: "profile", label: "Profile Details", icon: User },
    { id: "team", label: "Team", icon: Users },
    { id: "preferences", label: "Appearance", icon: Palette },
    { id: "api", label: "API Keys", icon: Key },
    { id: "security", label: "Security Ops", icon: ShieldAlert },
    { id: "sessions", label: "Sessions", icon: Key },
  ];

  return (
    <div className="max-w-5xl space-y-8 animate-in fade-in zoom-in-95 duration-500">
      {showInvite && <InviteDialog onClose={() => setShowInvite(false)} />}

      <div>
        <h1 className="text-3xl font-medium tracking-tight bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent">
          {t("settings.title")}
        </h1>
        <p className="mt-2 text-sm text-white/50">{t("settings.subtitle")}</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 items-start">
        {/* Navigation Sidebar */}
        <aside className="w-full lg:w-64 shrink-0 flex flex-col gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id ? "bg-white/10 text-white" : "text-white/50 hover:text-white/90 hover:bg-white/[0.05]"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </aside>

        {/* Content Area */}
        <div className="flex-1 w-full space-y-6">
          {/* ── PROFILE ── */}
          {activeTab === "profile" && (
            <div className="space-y-6">
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-32 bg-indigo-500/5 blur-[100px] rounded-full pointer-events-none" />
                <h3 className="text-lg font-medium text-white/90">Personal Information</h3>
                <p className="text-sm text-white/40 mt-1">Manage your account details and email address.</p>
                <div className="mt-8 space-y-5">
                  <div className="grid gap-2">
                    <label className="text-xs font-medium text-white/70 uppercase tracking-wider">Full Name</label>
                    <Input value={me?.full_name ?? ""} readOnly className="bg-white/[0.02] border-white/10 text-white h-11" />
                  </div>
                  <div className="grid gap-2">
                    <label className="text-xs font-medium text-white/70 uppercase tracking-wider">Email Address</label>
                    <Input value={me?.email ?? ""} readOnly className="bg-transparent border-white/5 text-white/50 h-11 opacity-50 cursor-not-allowed" />
                  </div>
                </div>
                <div className="mt-8 pt-6 border-t border-white/5 flex justify-end gap-3">
                  <Button variant="ghost" className="text-white/70 hover:text-white hover:bg-white/5 border border-transparent">Cancel</Button>
                  <Button className="bg-white text-black hover:bg-white/90 font-medium">Save Changes</Button>
                </div>
              </Card>
              <Card className="border-red-500/10 bg-red-500/[0.02] p-6 sm:p-8">
                <h3 className="text-lg font-medium text-red-400">Danger Zone</h3>
                <p className="text-sm text-white/40 mt-1">Permanently delete your account and all generated architectures.</p>
                <div className="mt-6 flex">
                  <Button variant="outline" className="bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/20">Delete Account</Button>
                </div>
              </Card>
            </div>
          )}

          {/* ── TEAM ── */}
          {activeTab === "team" && (
            <div className="space-y-6">
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-40 bg-violet-500/5 blur-[120px] rounded-full pointer-events-none" />
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-medium text-white/90">{activeWorkspace?.name ?? "Workspace"}</h3>
                    <p className="text-sm text-white/40 mt-1">Manage your team members, roles, and access levels.</p>
                  </div>
                  {(activeRole === "admin" || activeRole === "editor") && (
                    <button
                      onClick={() => setShowInvite(true)}
                      className="flex shrink-0 items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-black hover:bg-white/90 transition-colors"
                    >
                      <UserPlus className="h-3.5 w-3.5" />
                      Invite Member
                    </button>
                  )}
                </div>

                {/* Stats row */}
                <div className="mt-6 grid grid-cols-3 gap-3">
                  {(["admin", "editor", "viewer"] as WorkspaceRole[]).map((r) => {
                    const count = members.filter((m) => m.role === r).length;
                    const meta = ROLE_META[r];
                    return (
                      <div key={r} className={`rounded-xl border p-4 ${meta.color} bg-opacity-5`}>
                        <p className="text-2xl font-bold">{count}</p>
                        <p className="text-xs font-semibold uppercase tracking-wider mt-1 opacity-70">{meta.label}s</p>
                      </div>
                    );
                  })}
                </div>
              </Card>

              <Card className="border-white/5 bg-[#0a0a0a] overflow-hidden">
                {members.length === 0 ? (
                  <div className="py-16 text-center">
                    <Users className="h-8 w-8 text-white/20 mx-auto mb-3" />
                    <p className="text-sm text-white/40">No members yet. Invite your first team member.</p>
                    <button onClick={() => setShowInvite(true)} className="mt-4 text-sm text-white/60 hover:text-white underline underline-offset-4 transition-colors">
                      Invite team member →
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="border-b border-white/5 px-6 py-4">
                      <div className="grid grid-cols-[1fr_auto_auto] gap-4 text-[10px] font-semibold uppercase tracking-widest text-white/30">
                        <span>Member</span>
                        <span>Role</span>
                        <span className="w-8" />
                      </div>
                    </div>
                    {members.map((member, idx) => (
                      <div
                        key={member.id}
                        className={`grid grid-cols-[1fr_auto_auto] items-center gap-4 px-6 py-4 transition-colors hover:bg-white/[0.02] ${idx !== members.length - 1 ? "border-b border-white/5" : ""}`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/5 border border-white/10 text-xs font-bold text-white/70 shrink-0">
                            {member.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-white/90 truncate">{member.full_name}</p>
                            <p className="text-xs text-white/40 truncate">{member.email}</p>
                          </div>
                        </div>
                        <div>
                          {activeRole === "admin" ? (
                            <select
                              value={member.role}
                              onChange={(e) => updateMemberRole(member.id, e.target.value as WorkspaceRole)}
                              className="rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest bg-transparent cursor-pointer focus:outline-none focus:ring-1 focus:ring-white/20 transition-colors"
                              style={{ fontSize: "10px" }}
                            >
                              {(["admin", "editor", "viewer"] as WorkspaceRole[]).map((r) => (
                                <option key={r} value={r}>{r}</option>
                              ))}
                            </select>
                          ) : (
                            <RoleBadge role={member.role} />
                          )}
                        </div>
                        <div className="w-8 flex justify-end">
                          {activeRole === "admin" && (
                            <button
                              onClick={() => removeMember(member.id)}
                              className="flex h-7 w-7 items-center justify-center rounded-lg text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all"
                              title="Remove member"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          )}

          {/* ── APPEARANCE ── */}
          {activeTab === "preferences" && (
            <div className="space-y-6">
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8 relative overflow-hidden">
                <div className="absolute top-0 left-0 p-32 bg-blue-500/5 blur-[100px] rounded-full pointer-events-none" />
                <h3 className="text-lg font-medium text-white/90">Appearance</h3>
                <p className="text-sm text-white/40 mt-1">Customize how SystemForge looks on your device.</p>
                <div className="mt-8 grid grid-cols-2 gap-4">
                  <div
                    onClick={() => updateSetting("theme", "dark")}
                    className={`rounded-xl border p-4 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors ${
                      settings?.theme === "dark" 
                        ? "bg-white/[0.05] border-white/20 ring-1 ring-white/20" 
                        : "bg-white/[0.01] border-white/5 hover:border-white/10"
                    }`}
                  >
                    <div className="h-10 w-10 rounded-full bg-black border border-white/10 flex items-center justify-center">
                      {settings?.theme === "dark" && <Check className="h-4 w-4 text-white" />}
                    </div>
                    <span className="text-sm font-medium text-white">Dark Mode</span>
                  </div>
                  <div
                    onClick={() => updateSetting("theme", "light")}
                    className={`rounded-xl border p-4 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors ${
                      settings?.theme === "light" 
                        ? "bg-white/[0.05] border-white/20 ring-1 ring-white/20" 
                        : "bg-white/[0.01] border-white/5 hover:border-white/10"
                    }`}
                  >
                    <div className="h-10 w-10 rounded-full bg-white border border-black/10 flex items-center justify-center">
                      {settings?.theme === "light" && <Check className="h-4 w-4 text-black" />}
                    </div>
                    <span className="text-sm font-medium text-white">Light Mode</span>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* ── API KEYS ── */}
          {activeTab === "api" && (
            <div className="space-y-6">
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8 relative overflow-hidden">
                <div className="absolute bottom-0 right-0 p-32 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />
                <h3 className="text-lg font-medium text-white/90">API Credentials</h3>
                <p className="text-sm text-white/40 mt-1">Manage your API keys for programmable access to the architecture generation engine.</p>
                <div className="mt-8 text-center py-12 rounded-xl border border-dashed border-white/10 bg-white/[0.01]">
                  <Key className="h-8 w-8 text-white/20 mx-auto mb-3" />
                  <p className="text-sm text-white/50">You don&apos;t have any active API keys.</p>
                  <Button className="mt-4 bg-white/10 text-white hover:bg-white/20 border border-white/5">Generate Secret Key</Button>
                </div>
              </Card>
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8">
                <h3 className="text-lg font-medium text-white/90">Abuse Analytics (7d)</h3>
                <p className="text-sm text-white/40 mt-1">Operational visibility for abuse/risk events across API and realtime channels.</p>
                <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(abuseSummary ?? {}).map(([k, v]) => (
                    <div key={k} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                      <p className="text-xl font-semibold text-white/90">{v}</p>
                      <p className="text-xs text-white/40 mt-1">{k.replaceAll("_", " ")}</p>
                    </div>
                  ))}
                </div>
              </Card>
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8">
                <h3 className="text-lg font-medium text-white/90">API Contract Governance</h3>
                <div className="mt-4 space-y-2 text-sm text-white/60">
                  <p>Current API version: <span className="text-white/90">{apiVersions?.current ?? "v1"}</span></p>
                  <p>Compatibility: {apiVersions?.compatibility ?? "semver-compatible additive changes within major versions"}</p>
                  <p>Sunset: {apiVersions?.sunset_at ?? "Not scheduled"}</p>
                </div>
              </Card>
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8">
                <h3 className="text-lg font-medium text-white/90">Anomaly Detection</h3>
                <p className="mt-2 text-sm text-white/60">Anomaly score: {anomalySummary?.anomaly_score ?? 0}</p>
                <div className="mt-2 space-y-1">
                  {(anomalySummary?.anomalies ?? []).map((a) => (
                    <p key={a} className="text-xs text-amber-300">{a}</p>
                  ))}
                </div>
              </Card>
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8">
                <h3 className="text-lg font-medium text-white/90">Security Audit Trail</h3>
                <div className="mt-3 space-y-2">
                  {(auditTrail?.items ?? []).map((row, idx) => (
                    <p key={`${row.ts}-${idx}`} className="text-xs text-white/60">
                      {new Date(row.ts).toLocaleString()} • {row.action} • user #{row.actor_user_id}
                    </p>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {activeTab === "sessions" && (
            <div className="space-y-6">
              <Card className="border-white/5 bg-[#0a0a0a] p-6 sm:p-8">
                <h3 className="text-lg font-medium text-white/90">Device Sessions</h3>
                <p className="text-sm text-white/40 mt-1">View and revoke active refresh-token sessions.</p>
                <div className="mt-4 space-y-2">
                  {(sessions?.items ?? []).map((session) => (
                    <div key={session.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.02] p-3">
                      <p className="text-xs text-white/60">
                        #{session.id} • {new Date(session.created_at).toLocaleString()} • expires {new Date(session.expires_at).toLocaleDateString()}
                      </p>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={session.is_revoked}
                        onClick={async () => {
                          await api(`/auth/sessions/${session.id}`, { method: "DELETE" });
                          mutateSessions();
                        }}
                      >
                        {session.is_revoked ? "Revoked" : "Revoke"}
                      </Button>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

