"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { WsClient } from "@/lib/ws-client";

export type RealtimeMessage = {
  messageId: number;
  conversationId: number;
  senderUserId: number;
  text: string;
  serverSeq: number;
  createdAt?: string;
  status?: "pending" | "accepted" | "delivered" | "read";
  clientMsgId?: string;
};

export function useRealtimeMessaging(conversationId: number) {
  const [connectionState, setConnectionState] = useState<"idle" | "connecting" | "connected" | "reconnecting" | "error">("idle");
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  const [lastError, setLastError] = useState<string | null>(null);
  const [socketId, setSocketId] = useState<string | null>(null);
  const [lastServerSeq, setLastServerSeq] = useState(0);
  const clientRef = useRef<WsClient | null>(null);
  const lastServerSeqRef = useRef(0);
  const seqMap = useMemo(() => ({ [String(conversationId)]: lastServerSeqRef.current }), [conversationId]);

  useEffect(() => {
    lastServerSeqRef.current = lastServerSeq;
  }, [lastServerSeq]);

  useEffect(() => {
    if (!conversationId || conversationId <= 0) {
      return;
    }
    setConnectionState("connecting");
    const client = new WsClient({
      onConnected: () => {
        setConnectionState("connected");
        setLastError(null);
      },
      onDisconnected: () => {
        setConnectionState("reconnecting");
      },
      onReconnectScheduled: () => {
        setConnectionState("reconnecting");
      },
      onSessionWelcome: (payload) => {
        setSocketId(payload.socket_id);
        client.requestSync({ conversationId, afterServerSeq: lastServerSeqRef.current, limit: 100 });
      },
      onSessionResumed: (payload) => {
        const raw = payload as unknown as { requires_sync?: boolean };
        if (raw.requires_sync) {
          client.requestSync({ conversationId, afterServerSeq: lastServerSeqRef.current, limit: 100 });
        }
      },
      onMessageAccepted: (payload) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.clientMsgId === payload.client_msg_id
              ? {
                  ...msg,
                  messageId: payload.message_id,
                  serverSeq: payload.server_seq,
                  status: "accepted",
                }
              : msg,
          ),
        );
        setLastServerSeq((current) => Math.max(current, payload.server_seq));
      },
      onMessageNew: (payload) => {
        const text = typeof payload.content_json.text === "string" ? payload.content_json.text : JSON.stringify(payload.content_json);
        const item: RealtimeMessage = {
          messageId: payload.message_id,
          conversationId: payload.conversation_id,
          senderUserId: payload.sender_user_id,
          text,
          serverSeq: payload.server_seq,
          createdAt: payload.created_at,
          status: "accepted",
          clientMsgId: payload.client_msg_id,
        };
        setMessages((prev) => {
          if (prev.some((m) => m.messageId === item.messageId)) return prev;
          return [...prev, item].sort((a, b) => a.serverSeq - b.serverSeq);
        });
        setLastServerSeq((current) => Math.max(current, item.serverSeq));
      },
      onDeliveryUpdated: (payload) => {
        setMessages((prev) => prev.map((msg) => (msg.messageId === payload.message_id ? { ...msg, status: "delivered" } : msg)));
      },
      onReadUpdated: (payload) => {
        setMessages((prev) =>
          prev.map((msg) => (msg.conversationId === payload.conversation_id && msg.serverSeq <= payload.read_upto_server_seq ? { ...msg, status: "read" } : msg)),
        );
      },
      onSyncResponse: (payload) => {
        const hydrated: RealtimeMessage[] = payload.events
          .filter((evt) => evt.type === "message.new")
          .map((evt) => {
            const p = evt.payload as Record<string, unknown>;
            return {
              messageId: Number(p.message_id),
              conversationId: Number(p.conversation_id),
              senderUserId: Number(p.sender_user_id),
              text: typeof (p.content_json as { text?: unknown })?.text === "string" ? String((p.content_json as { text?: string }).text) : JSON.stringify(p.content_json ?? {}),
              serverSeq: Number(p.server_seq),
              createdAt: typeof p.created_at === "string" ? p.created_at : undefined,
              status: "accepted" as const,
              clientMsgId: typeof p.client_msg_id === "string" ? p.client_msg_id : undefined,
            };
          })
          .filter((m) => Number.isFinite(m.messageId) && m.messageId > 0 && Number.isFinite(m.serverSeq));
        setMessages((prev) => {
          const merged = [...prev];
          for (const item of hydrated) {
            if (!merged.some((m) => m.messageId === item.messageId)) {
              merged.push(item);
            }
          }
          return merged.sort((a, b) => a.serverSeq - b.serverSeq);
        });
        if (typeof payload.last_server_seq === "number") {
          setLastServerSeq((current) => Math.max(current, payload.last_server_seq ?? 0));
        }
      },
      onErrorEvent: (payload) => {
        setLastError(`${payload.code}: ${payload.message}`);
        setConnectionState("error");
      },
      onTransportError: () => {
        setLastError("TRANSPORT_ERROR: websocket transport error");
      },
    });
    clientRef.current = client;
    client.connect(WsClient.buildDefaultUrl(), {
      resume: true,
      lastServerSeqByConversation: seqMap,
    });
    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, [conversationId, seqMap]);

  const sendMessage = useCallback(
    (text: string) => {
      const client = clientRef.current;
      if (!client || !text.trim() || connectionState !== "connected") return;
      const clientMsgId = `web-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
      setMessages((prev) => [
        ...prev,
        {
          messageId: -1,
          conversationId,
          senderUserId: -1,
          text: text.trim(),
          serverSeq: lastServerSeq + 1,
          status: "pending",
          clientMsgId,
        },
      ]);
      client.sendMessage({
        clientMsgId,
        conversationId,
        content: text.trim(),
      });
    },
    [conversationId, lastServerSeq, connectionState],
  );

  return {
    connectionState,
    canSend: connectionState === "connected",
    messages,
    lastError,
    socketId,
    sendMessage,
  };
}
