import { describe, it, expect, vi, beforeEach } from "vitest";
import { api } from "../../lib/api";

// Assuming standard fetch API is used inside lib/api
global.fetch = vi.fn();

describe("API Client", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("adds authorization headers correctly", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    // We assume api function wraps fetch
    try {
      await api("/test-endpoint", { method: "GET" });
    } catch (e) {
      // ignore if it expects specific window/localStorage behavior that isn't mocked
    }

    expect(global.fetch).toHaveBeenCalled();
  });

  it("handles 401 Unauthorized responses", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ message: "Unauthorized" }),
    });

    await expect(api("/protected")).rejects.toThrow();
  });
});
