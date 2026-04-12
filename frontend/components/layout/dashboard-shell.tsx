"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, FolderKanban, PlusSquare, Settings } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
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
    { href: "/dashboard/new", label: t("common.newDesign"), icon: PlusSquare },
    { href: "/dashboard/settings", label: t("common.settings"), icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="grid min-h-screen grid-cols-1 md:grid-cols-[250px_1fr]">
        <aside className="hidden border-r border-border bg-surface/70 p-4 md:block">
          <div className="mb-8">
            <div className="flex items-center gap-2 text-lg font-semibold">
              <FolderKanban className="h-5 w-5 text-brand" />
              <span>SystemForge AI</span>
            </div>
            <p className="mt-1 text-xs text-muted">{t("landing.badge")}</p>
          </div>
          <nav className="space-y-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted transition-colors hover:bg-zinc-900/50 hover:text-foreground",
                  pathname === item.href && "bg-zinc-900 text-foreground",
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
          <header className="flex h-16 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur">
            <div>
              <p className="text-sm font-medium">{t("layout.workspace")}</p>
              <p className="truncate text-xs text-muted">{user?.email ?? "-"}</p>
            </div>
            <div className="flex items-center gap-2">
              <LanguageSwitcher />
              <Link href="/dashboard/new" className="md:hidden">
                <Button variant="outline" size="sm">
                  {t("common.newDesign")}
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  signOut();
                  router.push("/auth/sign-in");
                }}
              >
                {t("common.signOut")}
              </Button>
            </div>
          </header>
          <div className="p-4 sm:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
