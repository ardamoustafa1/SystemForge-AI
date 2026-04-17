import {
  parseEventPayload,
  parseWsEnvelope,
  deliveryUpdatedSchema,
  messageAcceptedSchema,
  messageNewSchema,
  readUpdatedSchema,
  sessionResumedPayloadSchema,
  sessionWelcomePayloadSchema,
  syncResponseSchema,
  typingPayloadSchema,
  typingUpdatedSchema,
  wsErrorSchema,
  WsEnvelope,
} from "@/lib/ws-contract";
import { getWebSocketUrl } from "@/lib/env";

type Handlers = {
  onConnected?: () => void;
  onDisconnected?: (reason: string) => void;
  onTransportError?: () => void;
  onSessionWelcome?: (payload: ReturnType<typeof sessionWelcomePayloadSchema.parse>) => void;
  onSessionResumed?: (payload: ReturnType<typeof sessionResumedPayloadSchema.parse>) => void;
  onReconnectScheduled?: (delayMs: number) => void;
  onMessageAccepted?: (payload: ReturnType<typeof messageAcceptedSchema.parse>) => void;
  onMessageNew?: (payload: ReturnType<typeof messageNewSchema.parse>) => void;
  onDeliveryUpdated?: (payload: ReturnType<typeof deliveryUpdatedSchema.parse>) => void;
  onReadUpdated?: (payload: ReturnType<typeof readUpdatedSchema.parse>) => void;
  onSyncResponse?: (payload: ReturnType<typeof syncResponseSchema.parse>) => void;
  onTypingUpdated?: (payload: ReturnType<typeof typingUpdatedSchema.parse>) => void;
  onErrorEvent?: (payload: ReturnType<typeof wsErrorSchema.parse>) => void;
  onUnknownEvent?: (envelope: WsEnvelope) => void;
};

type ConnectOptions = {
  resume?: boolean;
  lastServerSeqByConversation?: Record<string, number>;
};

export class WsClient {
  private socket: WebSocket | null = null;
  private url: string | null = null;
  private handlers: Handlers;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private shouldReconnect = true;
  private connectOptions: ConnectOptions = {};

  constructor(handlers: Handlers = {}) {
    this.handlers = handlers;
  }

  static buildDefaultUrl() {
    const raw = getWebSocketUrl().replace(/\/$/, "");
    let wsUrl = raw;

    if (raw.startsWith("http://")) {
      wsUrl = raw.replace(/^http:\/\//, "ws://");
    } else if (raw.startsWith("https://")) {
      wsUrl = raw.replace(/^https:\/\//, "wss://");
    } else if (raw.startsWith("/")) {
      if (typeof window !== "undefined") {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${protocol}//${window.location.host}${raw}`;
      }
    }

    if (!wsUrl.endsWith("/ws")) {
      wsUrl = `${wsUrl}/ws`;
    }
    return wsUrl;
  }

  connect(url: string, options: ConnectOptions = {}) {
    this.shouldReconnect = true;
    this.url = url;
    this.connectOptions = options;
    this.socket = new WebSocket(url);
    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.handlers.onConnected?.();
      this.send("session.hello", {
        protocol_version: 1,
        resume: Boolean(options.resume),
        last_server_seq_by_conversation: options.lastServerSeqByConversation ?? {},
      });
    };
    this.socket.onmessage = (evt) => {
      try {
        const parsed = parseWsEnvelope(JSON.parse(evt.data));
        this.dispatch(parsed);
      } catch {
        this.handlers.onTransportError?.();
      }
    };
    this.socket.onerror = () => {
      this.handlers.onTransportError?.();
    };
    this.socket.onclose = (evt) => {
      this.stopHeartbeat();
      this.handlers.onDisconnected?.(evt.reason || "socket_closed");
      if (!this.shouldReconnect) {
        return;
      }
      const delayMs = Math.min(1000 * 2 ** this.reconnectAttempts, 10000);
      this.reconnectAttempts += 1;
      this.handlers.onReconnectScheduled?.(delayMs);
      this.reconnectTimer = setTimeout(() => {
        if (!this.url) return;
        this.connect(this.url, { ...this.connectOptions, resume: true });
      }, delayMs);
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
    this.socket?.close();
    this.socket = null;
  }

  send(type: string, payload: Record<string, unknown>) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }
    const eventId = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `evt-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
    const safePayload = parseEventPayload(type, payload);
    this.socket.send(
      JSON.stringify({
        v: 1,
        event_id: eventId,
        type,
        ts_ms: Date.now(),
        payload: safePayload,
      }),
    );
  }

  sendHeartbeat(status: "online" | "away" = "online") {
    this.send("presence.heartbeat", {
      status,
      client_ts_ms: Date.now(),
    });
  }

  sendTypingStarted(conversationId: number) {
    this.send("typing.started", { conversation_id: conversationId, ttl_ms: 5000 });
  }

  sendTypingStopped(conversationId: number) {
    this.send("typing.stopped", { conversation_id: conversationId, ttl_ms: 1000 });
  }

  sendMessage(input: { clientMsgId: string; conversationId: number; content: string; contentType?: "text" | "markdown" | "json" }) {
    this.send("message.send", {
      client_msg_id: input.clientMsgId,
      conversation_id: input.conversationId,
      content_type: input.contentType ?? "text",
      content: input.content,
      client_ts_ms: Date.now(),
    });
  }

  requestSync(input: { conversationId: number; afterServerSeq?: number; afterMessageId?: number; limit?: number }) {
    this.send("sync.request", {
      conversation_id: input.conversationId,
      after_server_seq: input.afterServerSeq ?? 0,
      after_message_id: input.afterMessageId,
      limit: input.limit ?? 200,
    });
  }

  private startHeartbeat(intervalSeconds: number) {
    this.stopHeartbeat();
    const ms = Math.max(5000, intervalSeconds * 1000);
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat("online");
    }, ms);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private dispatch(envelope: WsEnvelope) {
    if (envelope.type === "session.welcome") {
      const payload = sessionWelcomePayloadSchema.parse(envelope.payload);
      this.handlers.onSessionWelcome?.(payload);
      this.startHeartbeat(payload.heartbeat_interval_sec);
      return;
    }
    if (envelope.type === "session.resumed") {
      const payload = sessionResumedPayloadSchema.parse(envelope.payload);
      this.handlers.onSessionResumed?.(payload);
      return;
    }
    if (envelope.type === "message.accepted") {
      const payload = messageAcceptedSchema.parse(envelope.payload);
      this.handlers.onMessageAccepted?.(payload);
      return;
    }
    if (envelope.type === "message.new") {
      const payload = messageNewSchema.parse(envelope.payload);
      this.handlers.onMessageNew?.(payload);
      return;
    }
    if (envelope.type === "delivery.updated") {
      const payload = deliveryUpdatedSchema.parse(envelope.payload);
      this.handlers.onDeliveryUpdated?.(payload);
      return;
    }
    if (envelope.type === "read.updated") {
      const payload = readUpdatedSchema.parse(envelope.payload);
      this.handlers.onReadUpdated?.(payload);
      return;
    }
    if (envelope.type === "sync.response") {
      const payload = syncResponseSchema.parse(envelope.payload);
      this.handlers.onSyncResponse?.(payload);
      return;
    }
    if (envelope.type === "typing.updated") {
      const payload = typingUpdatedSchema.parse(envelope.payload);
      this.handlers.onTypingUpdated?.(payload);
      return;
    }
    if (envelope.type === "error") {
      const payload = wsErrorSchema.parse(envelope.payload);
      this.handlers.onErrorEvent?.(payload);
      return;
    }
    this.handlers.onUnknownEvent?.(envelope);
  }
}
