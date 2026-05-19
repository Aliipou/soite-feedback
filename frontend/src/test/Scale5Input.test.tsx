import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../i18n/index";
import { Scale5Input } from "../components/kiosk/Scale5Input";

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("Scale5Input", () => {
  it("renders 5 emoji buttons", () => {
    renderWithI18n(<Scale5Input onSelect={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBe(5);
  });

  it("calls onSelect with correct value when button clicked", () => {
    const onSelect = vi.fn();
    renderWithI18n(<Scale5Input onSelect={onSelect} />);
    // Click the 4th button (value=4)
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[3]);
    expect(onSelect).toHaveBeenCalledWith(4);
  });

  it("all buttons have aria-labels", () => {
    renderWithI18n(<Scale5Input onSelect={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => {
      expect(btn.getAttribute("aria-label")).toBeTruthy();
    });
  });

  it("selected button has aria-pressed=true", () => {
    renderWithI18n(<Scale5Input onSelect={vi.fn()} selected={3} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons[2].getAttribute("aria-pressed")).toBe("true");
    expect(buttons[0].getAttribute("aria-pressed")).toBe("false");
  });

  it("meets minimum touch target requirement (has min-h-touch class)", () => {
    renderWithI18n(<Scale5Input onSelect={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => {
      expect(btn.className).toContain("min-h-touch");
    });
  });

  it("group has aria-label for screen readers", () => {
    renderWithI18n(<Scale5Input onSelect={vi.fn()} />);
    expect(screen.getByRole("group")).toBeInTheDocument();
  });
});
