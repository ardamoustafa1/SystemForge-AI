"use client";

import { FormEvent, useState } from "react";

import { useRealtimeMessaging } from "@/features/realtime/use-realtime-messaging";
import { useAuth } from "@/features/auth/auth-context";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/i18n-context";

export function RealtimeMessagingPanel({ conversationId }: { conversationId: number }) {
  const { t } = useI18n();
  const { user } = useAuth();
  const { connectionState, canSend, messages, lastError, socketId, typingUsers, sendTyping, sendMessage } = useRealtimeMessaging(conversationId);
  const [draft, setDraft] = useState("");

  const onSubmit = (evt: FormEvent) => {
    evt.preventDefault();
    if (!draft.trim()) return;
    sendMessage(draft);
    setDraft("");
  };

  const onDraftChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDraft(e.target.value);
    sendTyping();
  };

  return (
    <Card className="p-5 flex flex-col h-[500px]">
      <div className="flex items-center justify-between gap-3 mb-2">
        <h2 className="text-lg font-medium">{t("realtime.title")}</h2>
        <span className="text-xs text-muted-foreground">
          {connectionState} {socketId ? `| ${socketId.substring(0, 8)}...` : ""}
        </span>
      </div>
      
      {lastError ? <p className="mt-1 text-sm text-red-300">{lastError}</p> : null}

      <div className="flex-1 mt-2 space-y-3 overflow-y-auto rounded-md border border-border bg-black/5 p-4 flex flex-col">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center my-auto">{t("realtime.empty")}</p>
        ) : (
          messages.map((message) => {
            const isOptimistic = message.senderUserId === -1;
            const isMe = isOptimistic || message.senderUserId === user?.id;

            return (
              <div key={`${message.clientMsgId ?? "srv"}-${message.messageId}-${message.serverSeq}`} className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${isMe ? "bg-primary text-primary-foreground rounded-br-sm" : "bg-card text-card-foreground border border-border rounded-bl-sm"}`}>
                  <p className="leading-relaxed whitespace-pre-wrap">{message.text}</p>
                  <div className={`mt-1 flex items-center justify-end text-[10px] gap-1 opacity-70 ${isMe ? "text-primary-foreground" : "text-muted-foreground"}`}>
                    <span>{message.createdAt ? new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ""}</span>
                    {isMe && (
                      <span className="ml-1 tracking-tighter">
                        {message.status === "pending" && <span className="opacity-50">🕒</span>}
                        {message.status === "accepted" && <span>✓</span>}
                        {message.status === "delivered" && <span>✓✓</span>}
                        {message.status === "read" && <span className="text-blue-300">✓✓</span>}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
        {typingUsers.length > 0 && (
          <div className="flex justify-start">
            <div className="bg-card text-muted-foreground border border-border rounded-2xl rounded-tl-sm px-4 py-2 text-sm italic flex items-center gap-2">
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={onSubmit} className="mt-4 flex gap-2 pt-2">
        <Input 
          value={draft} 
          onChange={onDraftChange} 
          placeholder={t("realtime.inputPlaceholder")} 
          className="rounded-full px-4"
        />
        <Button type="submit" disabled={!canSend} className="rounded-full px-6">
          {t("realtime.send")}
        </Button>
      </form>
    </Card>
  );
}
