"use client";

import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n/i18n-context";

export default function UseCasesPage() {
  const { t } = useI18n();
  return (
    <div className="container-page py-10">
      <PageHeader
        title={t("useCases.pageTitle")}
        subtitle={t("useCases.pageSubtitle")}
      />
      <Card className="mt-6 p-6 text-sm text-muted">
        {t("useCases.pageBody")}
      </Card>
    </div>
  );
}
