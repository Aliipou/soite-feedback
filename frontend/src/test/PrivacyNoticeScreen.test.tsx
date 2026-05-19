import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../i18n/index";
import { PrivacyNoticeScreen } from "../components/kiosk/PrivacyNoticeScreen";

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("PrivacyNoticeScreen", () => {
  it("renders privacy title", () => {
    renderWithI18n(<PrivacyNoticeScreen onStart={vi.fn()} />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByText("Tietosuoja")).toBeInTheDocument();
  });

  it("shows anonymity notice text", () => {
    renderWithI18n(<PrivacyNoticeScreen onStart={vi.fn()} />);
    expect(screen.getByText(/anonyymi/)).toBeInTheDocument();
  });

  it("renders start button", () => {
    renderWithI18n(<PrivacyNoticeScreen onStart={vi.fn()} />);
    expect(screen.getByRole("button")).toBeInTheDocument();
    expect(screen.getByText("Aloita kysely")).toBeInTheDocument();
  });

  it("calls onStart when button clicked", () => {
    const onStart = vi.fn();
    renderWithI18n(<PrivacyNoticeScreen onStart={onStart} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it("button meets minimum touch target size", () => {
    renderWithI18n(<PrivacyNoticeScreen onStart={vi.fn()} />);
    expect(screen.getByRole("button").className).toContain("min-h-touch");
  });
});
