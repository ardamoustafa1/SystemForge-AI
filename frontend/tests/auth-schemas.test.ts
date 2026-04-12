import { describe, expect, it } from "vitest";

import { signInSchema, signUpSchema } from "@/features/auth/schemas";

describe("auth schemas", () => {
  it("accepts valid sign-in payload", () => {
    const parsed = signInSchema.safeParse({
      email: "engineer@example.com",
      password: "StrongPass1",
    });
    expect(parsed.success).toBe(true);
  });

  it("rejects weak sign-up password", () => {
    const parsed = signUpSchema.safeParse({
      full_name: "Jane Doe",
      email: "jane@example.com",
      password: "weakpass",
    });
    expect(parsed.success).toBe(false);
  });
});
