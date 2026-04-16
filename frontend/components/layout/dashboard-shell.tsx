"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, FolderKanban, PlusSquare, Settings, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { WorkspaceSwitcher } from "@/components/layout/workspace-switcher";
import { useAuth } from "@/features/auth/auth-context";
import { useI18n } from "@/i18n/i18n-context";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useAuth();
  const { t } = useI18n();
  const nav = [
    { href: "/dashboard", label: t("common.overview"), icon: BarChart3 },
    { href: "/dashboard/designs", label: t("common.designs"), icon: FolderKanban },
    { href: "/dashboard/jobs", label: "Jobs", icon: History },
    { href: "/dashboard/new", label: t("common.newDesign"), icon: PlusSquare },
    { href: "/dashboard/settings", label: t("common.settings"), icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid min-h-screen grid-cols-1 md:grid-cols-[250px_1fr]">
        <aside className="hidden border-r border-white/5 bg-[#0a0a0a] p-4 md:flex md:flex-col">
          <div className="mb-6 pl-2">
            <div className="flex items-center gap-3 text-lg font-medium text-white/90">
              <FolderKanban className="h-4 w-4 text-white/70" />
              <span>SystemForge AI</span>
            </div>
            <p className="mt-2 text-[10px] uppercase tracking-widest text-white/30 font-medium">{t("landing.badge")}</p>
          </div>
          {/* Workspace Switcher in sidebar */}
          <div className="mb-6">
            <WorkspaceSwitcher />
          </div>
          <nav className="space-y-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors hover:bg-white/[0.03] hover:text-white/90",
                  pathname === item.href ? "bg-white/[0.05] text-white" : "text-white/50",
                )}
                href={item.href}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-w-0">
          <header className="flex h-16 items-center justify-between border-b border-white/5 bg-[#0a0a0a]/80 px-6 backdrop-blur-xl">
            <div className="flex items-center gap-3">
              {/* Mobile workspace switcher */}
              <div className="md:hidden">
                <WorkspaceSwitcher />
              </div>
              <div className="hidden md:block">
                <p className="text-[11px] uppercase tracking-widest text-white/40 font-medium">{t("layout.workspace")}</p>
                <p className="truncate text-sm text-white/80 font-medium mt-0.5">{user?.email ?? "-"}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher />
              <Link href="/dashboard/new" className="md:hidden">
                <Button variant="outline" size="sm" className="border-white/10 bg-transparent hover:bg-white/5 text-white/90">
                  {t("common.newDesign")}
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                className="border-white/10 bg-transparent hover:bg-white/5 text-white/90"
                onClick={() => {
                  signOut();
                  router.push("/auth/sign-in");
                }}
              >
                {t("common.signOut")}
              </Button>
            </div>
          </header>
          <div className="p-4 sm:p-8 max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
