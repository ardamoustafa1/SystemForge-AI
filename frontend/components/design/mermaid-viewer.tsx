"use client";

import { useEffect, useMemo, useState } from "react";
import mermaid from "mermaid";
import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n/i18n-context";

type Props = { code: string };

export function MermaidViewer({ code }: Props) {
  const { t } = useI18n();
  const [svg, setSvg] = useState<string>("");
  const elementId = useMemo(() => `mermaid-${Math.random().toString(36).slice(2, 9)}`, []);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: "dark" });
    mermaid
      .render(elementId, code)
      .then(({ svg: rendered }) => setSvg(rendered))
      .catch(() => setSvg(""));
  }, [code, elementId]);

  if (!svg) {
    return (
      <Card className="p-4" role="status" aria-live="polite">
        <div className="text-sm text-muted">{t("common.diagramRenderFailed")}</div>
        <pre className="mt-3 overflow-x-auto rounded bg-zinc-950 p-3 text-xs">{code}</pre>
      </Card>
    );
  }

  return <Card className="overflow-x-auto p-4" role="img" aria-label={t("common.architectureDiagram")} dangerouslySetInnerHTML={{ __html: svg }} />;
}
