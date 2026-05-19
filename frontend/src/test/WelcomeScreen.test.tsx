import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../i18n/index";
import { WelcomeScreen } from "../components/kiosk/WelcomeScreen";

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("WelcomeScreen", () => {
  it("renders welcome heading in Finnish", () => {
    renderWithI18n(<WelcomeScreen onStart={vi.fn()} />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/Hei!/)).toBeInTheDocument();
  });

  it("renders CTA button", () => {
    renderWithI18n(<WelcomeScreen onStart={vi.fn()} />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("calls onStart when CTA clicked", () => {
    const onStart = vi.fn();
    renderWithI18n(<WelcomeScreen onStart={onStart} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it("CTA button meets touch target size", () => {
    renderWithI18n(<WelcomeScreen onStart={vi.fn()} />);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("min-h-touch");
  });
});
