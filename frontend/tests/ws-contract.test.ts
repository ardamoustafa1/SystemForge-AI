import { describe, expect, it } from "vitest";

import { parseWsEnvelope, messageAcceptedSchema, wsErrorSchema } from "@/lib/ws-contract";

describe("ws contract schemas", () => {
  it("parses message.accepted envelope", () => {
    const envelope = parseWsEnvelope({
      type: "message.accepted",
      schema_version: 1,
      payload: {
        message_id: 10,
        client_msg_id: "a33a9859-8541-4455-8f7c-dfbe66863e40",
        conversation_id: 2,
        server_seq: 11,
        outbox_event_id: 14,
        deduped: false,
        accepted_at_ms: 12345,
      },
    });
    const payload = messageAcceptedSchema.parse(envelope.payload);
    expect(payload.message_id).toBe(10);
  });

  it("parses error envelope payload", () => {
    const payload = wsErrorSchema.parse({
      code: "SEND_FAILED",
      message: "Failed",
      retryable: true,
      retry_after_ms: 500,
    });
    expect(payload.code).toBe("SEND_FAILED");
  });
});
