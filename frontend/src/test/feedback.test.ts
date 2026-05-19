import { describe, it, expect, beforeEach } from "vitest";
import { getDeviceToken } from "../api/feedback";

describe("getDeviceToken", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("generates a UUID on first call", () => {
    const token = getDeviceToken();
    expect(token).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    );
  });

  it("returns the same token on subsequent calls", () => {
    const first = getDeviceToken();
    const second = getDeviceToken();
    expect(first).toBe(second);
  });

  it("persists token in localStorage", () => {
    const token = getDeviceToken();
    expect(localStorage.getItem("soite_device_token")).toBe(token);
  });

  it("reuses existing token from localStorage", () => {
    localStorage.setItem("soite_device_token", "existing-token");
    const token = getDeviceToken();
    expect(token).toBe("existing-token");
  });
});
