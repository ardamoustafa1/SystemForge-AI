"use client";

import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n/i18n-context";

export default function SettingsPage() {
  const { t } = useI18n();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">{t("settings.title")}</h1>
      <Card className="p-5">
        <h2 className="font-medium">{t("settings.subtitle")}</h2>
        <p className="mt-2 text-sm text-muted">
          Workspace-level settings are modeled in backend `user_settings` and ready for expansion to team/workspace support.
        </p>
      </Card>
    </div>
  );
}
