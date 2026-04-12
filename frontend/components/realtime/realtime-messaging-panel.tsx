"use client";

import { FormEvent, useState } from "react";

import { useRealtimeMessaging } from "@/features/realtime/use-realtime-messaging";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/i18n-context";

export function RealtimeMessagingPanel({ conversationId }: { conversationId: number }) {
  const { t } = useI18n();
  const { connectionState, canSend, messages, lastError, socketId, sendMessage } = useRealtimeMessaging(conversationId);
  const [draft, setDraft] = useState("");

  const onSubmit = (evt: FormEvent) => {
    evt.preventDefault();
    if (!draft.trim()) return;
    sendMessage(draft);
    setDraft("");
  };

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium">{t("realtime.title")}</h2>
        <span className="text-xs text-muted">
          {t("realtime.state")}: {connectionState}
          {socketId ? ` | ${t("realtime.socket")}: ${socketId}` : ""}
        </span>
      </div>
      <p className="mt-2 text-xs text-muted">
        {t("realtime.description")}
      </p>
      <p className="mt-1 text-xs text-muted">{t("realtime.partialNote")}</p>

      {lastError ? <p className="mt-3 text-sm text-red-300">{lastError}</p> : null}

      <form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <Input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={t("realtime.inputPlaceholder")} />
        <Button type="submit" disabled={!canSend}>
          {t("realtime.send")}
        </Button>
      </form>

      <div className="mt-4 max-h-64 space-y-2 overflow-y-auto rounded-md border border-border p-3">
        {messages.length === 0 ? (
          <p className="text-sm text-muted">{t("realtime.empty")}</p>
        ) : (
          messages.map((message) => (
            <div key={`${message.clientMsgId ?? "srv"}-${message.messageId}-${message.serverSeq}`} className="rounded border border-border/60 bg-black/20 p-2 text-sm">
              <p>{message.text}</p>
              <p className="mt-1 text-xs text-muted">
                seq={message.serverSeq} id={message.messageId} status={message.status ?? t("realtime.statusUnknown")}
              </p>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
