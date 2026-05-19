import { describe, it, expect, beforeEach } from "vitest";
import { setAccessToken, getAccessToken, clearAccessToken, hasAccessToken } from "../auth/tokenStore";

describe("tokenStore (in-memory, never localStorage)", () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it("starts with no token", () => {
    expect(getAccessToken()).toBeNull();
    expect(hasAccessToken()).toBe(false);
  });

  it("stores and retrieves access token", () => {
    setAccessToken("test-jwt-token");
    expect(getAccessToken()).toBe("test-jwt-token");
    expect(hasAccessToken()).toBe(true);
  });

  it("clears token on clearAccessToken", () => {
    setAccessToken("test-jwt-token");
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
    expect(hasAccessToken()).toBe(false);
  });

  it("does NOT store token in localStorage (XSS protection)", () => {
    setAccessToken("xss-sensitive-token");
    // localStorage must not contain the access token
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("xss-sensitive-token")).toBeNull();
    // Verify token is only in memory
    expect(getAccessToken()).toBe("xss-sensitive-token");
  });

  it("overwrites existing token", () => {
    setAccessToken("old-token");
    setAccessToken("new-token");
    expect(getAccessToken()).toBe("new-token");
  });
});
