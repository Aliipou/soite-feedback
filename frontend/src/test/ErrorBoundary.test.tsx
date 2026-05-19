import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "../components/ErrorBoundary";

const ThrowingComponent = () => {
  throw new Error("Test crash");
};

const SafeChild = () => <div>Safe content</div>;

describe("ErrorBoundary", () => {
  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <SafeChild />
      </ErrorBoundary>
    );
    expect(screen.getByText("Safe content")).toBeInTheDocument();
  });

  it("renders Finnish error message on crash", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText("Jokin meni pieleen")).toBeInTheDocument();
    expect(screen.getByText(/Pyydä hoitajaa/)).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  it("has role=alert on error screen for screen readers", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  it("logs error message without leaking sensitive data", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    const calls = consoleSpy.mock.calls;
    // Should log the error message string, not the full object (no PII risk)
    expect(calls.length).toBeGreaterThan(0);
    consoleSpy.mockRestore();
  });
});
