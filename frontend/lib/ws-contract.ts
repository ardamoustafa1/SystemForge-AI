import { z } from "zod";

const seqMapSchema = z.record(z.string(), z.number().int().nonnegative());

export const wsEnvelopeSchema = z.object({
  v: z.literal(1).default(1),
  event_id: z.string().min(1).max(128),
  type: z.string().min(1).max(64),
  ts_ms: z.number().int().nonnegative(),
  trace_id: z.string().min(1).max(128).optional(),
  correlation_id: z.string().min(1).max(128).optional(),
  payload: z.record(z.string(), z.unknown()).default({}),
});

export type WsEnvelope = z.infer<typeof wsEnvelopeSchema>;

export const sessionHelloPayloadSchema = z.object({
  protocol_version: z.literal(1).default(1),
  resume: z.boolean().default(false),
  last_server_seq_by_conversation: seqMapSchema.default({}),
});

export const sessionWelcomePayloadSchema = z.object({
  user_id: z.number().int().positive(),
  socket_id: z.string().min(1).max(128),
  server_ts_ms: z.number().int().nonnegative(),
  heartbeat_interval_sec: z.number().int().min(5).max(120),
  session_expires_at_ms: z.number().int().nonnegative().optional(),
});

export const sessionResumedPayloadSchema = z.object({
  user_id: z.number().int().positive(),
  socket_id: z.string().min(1).max(128),
  resumed: z.boolean(),
  replayed_events: z.number().int().nonnegative(),
  server_ts_ms: z.number().int().nonnegative(),
});

export const presenceHeartbeatPayloadSchema = z.object({
  status: z.enum(["online", "away"]).default("online"),
  client_ts_ms: z.number().int().nonnegative().optional(),
});

export const pongPayloadSchema = z.object({
  socket_id: z.string().min(1),
  server_ts_ms: z.number().int().nonnegative(),
});

export const messageAcceptedSchema = z.object({
  message_id: z.number().int().positive(),
  client_msg_id: z.string().min(1).max(64),
  conversation_id: z.number().int().positive(),
  server_seq: z.number().int().nonnegative(),
  outbox_event_id: z.number().int().nullable().optional(),
  deduped: z.boolean(),
  accepted_at_ms: z.number().int().nonnegative(),
});

export const messageSendSchema = z.object({
  client_msg_id: z.string().min(1).max(64),
  conversation_id: z.number().int().positive(),
  content_type: z.enum(["text", "markdown", "json"]).default("text"),
  content: z.union([z.string(), z.record(z.string(), z.unknown())]),
  client_ts_ms: z.number().int().nonnegative().optional(),
});

export const messageNewSchema = z.object({
  message_id: z.number().int().positive(),
  conversation_id: z.number().int().positive(),
  sender_user_id: z.number().int().positive(),
  recipient_user_ids: z.array(z.number().int().positive()).optional(),
  content_type: z.enum(["text", "markdown", "json"]),
  content_json: z.record(z.string(), z.unknown()),
  created_at: z.string().datetime().optional(),
  server_seq: z.number().int().nonnegative(),
  client_msg_id: z.string().min(1).max(64).optional(),
});

export const messageDeliveredSchema = z.object({
  message_id: z.number().int().positive(),
  conversation_id: z.number().int().positive().optional(),
  delivered_at_ms: z.number().int().nonnegative().optional(),
});

export const messageReadSchema = z.object({
  conversation_id: z.number().int().positive(),
  read_upto_server_seq: z.number().int().nonnegative(),
  read_at_ms: z.number().int().nonnegative().optional(),
});

export const deliveryUpdatedSchema = z.object({
  message_id: z.number().int().positive(),
  conversation_id: z.number().int().positive(),
  recipient_user_id: z.number().int().positive(),
  delivered_at_ms: z.number().int().nonnegative(),
});

export const readUpdatedSchema = z.object({
  conversation_id: z.number().int().positive(),
  reader_user_id: z.number().int().positive(),
  read_upto_server_seq: z.number().int().nonnegative(),
  read_at_ms: z.number().int().nonnegative(),
});

export const syncRequestSchema = z.object({
  conversation_id: z.number().int().positive(),
  after_server_seq: z.number().int().nonnegative().default(0),
  after_message_id: z.number().int().positive().optional(),
  limit: z.number().int().min(1).max(1000).default(200),
});

export const syncResponseSchema = z.object({
  conversation_id: z.number().int().positive().optional(),
  after_server_seq: z.number().int().nonnegative().nullable().optional(),
  after_message_id: z.number().int().positive().nullable().optional(),
  events: z
    .array(
      z.object({
        type: z.string().min(1).max(64),
        payload: z.record(z.string(), z.unknown()),
      }),
    )
    .default([]),
  last_server_seq: z.number().int().nonnegative().optional(),
  has_more: z.boolean(),
  server_ts_ms: z.number().int().nonnegative(),
});

export const typingPayloadSchema = z.object({
  conversation_id: z.number().int().positive(),
  ttl_ms: z.number().int().min(1000).max(30000).default(8000),
});

export const wsErrorSchema = z.object({
  code: z.string().min(1).max(64),
  message: z.string().min(1).max(512),
  retryable: z.boolean(),
  retry_after_ms: z.number().int().nonnegative().optional(),
});

export function parseWsEnvelope(raw: unknown): WsEnvelope {
  return wsEnvelopeSchema.parse(raw);
}

export function parseEventPayload(type: string, payload: unknown): unknown {
  switch (type) {
    case "session.hello":
      return sessionHelloPayloadSchema.parse(payload);
    case "session.welcome":
      return sessionWelcomePayloadSchema.parse(payload);
    case "session.resumed":
      return sessionResumedPayloadSchema.parse(payload);
    case "presence.heartbeat":
      return presenceHeartbeatPayloadSchema.parse(payload);
    case "pong":
      return pongPayloadSchema.parse(payload);
    case "message.send":
      return messageSendSchema.parse(payload);
    case "message.accepted":
      return messageAcceptedSchema.parse(payload);
    case "message.new":
      return messageNewSchema.parse(payload);
    case "message.delivered":
      return messageDeliveredSchema.parse(payload);
    case "message.read":
      return messageReadSchema.parse(payload);
    case "delivery.updated":
      return deliveryUpdatedSchema.parse(payload);
    case "read.updated":
      return readUpdatedSchema.parse(payload);
    case "sync.request":
      return syncRequestSchema.parse(payload);
    case "sync.response":
      return syncResponseSchema.parse(payload);
    case "typing.started":
    case "typing.stopped":
    case "typing.updated":
      return typingPayloadSchema.parse(payload);
    case "error":
      return wsErrorSchema.parse(payload);
    default:
      return payload;
  }
}
