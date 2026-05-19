import "@testing-library/jest-dom";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

// Mock navigator.onLine
Object.defineProperty(window.navigator, "onLine", {
  writable: true,
  value: true,
});

// Mock crypto.randomUUID
Object.defineProperty(window.crypto, "randomUUID", {
  value: vi.fn(() => "00000000-0000-4000-a000-000000000001"),
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });
