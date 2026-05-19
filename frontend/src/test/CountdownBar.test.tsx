import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../i18n/index";
import { CountdownBar } from "../components/kiosk/CountdownBar";

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("CountdownBar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders with initial seconds", () => {
    const onComplete = vi.fn();
    renderWithI18n(<CountdownBar seconds={10} onComplete={onComplete} />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("calls onComplete after countdown expires", () => {
    const onComplete = vi.fn();
    renderWithI18n(<CountdownBar seconds={3} onComplete={onComplete} />);
    expect(onComplete).not.toHaveBeenCalled();

    act(() => { vi.advanceTimersByTime(3000); });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it("decrements progressbar aria-valuenow each second", () => {
    const onComplete = vi.fn();
    renderWithI18n(<CountdownBar seconds={5} onComplete={onComplete} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("5");

    act(() => { vi.advanceTimersByTime(1000); });
    expect(bar.getAttribute("aria-valuenow")).toBe("4");
  });

  it("has accessible aria attributes", () => {
    const onComplete = vi.fn();
    renderWithI18n(<CountdownBar seconds={10} onComplete={onComplete} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuemin")).toBe("0");
    expect(bar.getAttribute("aria-valuemax")).toBe("10");
    expect(bar.getAttribute("aria-label")).toBeTruthy();
  });
});
