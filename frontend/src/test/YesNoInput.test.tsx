import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../i18n/index";
import { YesNoInput } from "../components/kiosk/YesNoInput";

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("YesNoInput", () => {
  it("renders Kyllä and En buttons", () => {
    renderWithI18n(<YesNoInput onSelect={vi.fn()} />);
    expect(screen.getByText("Kyllä")).toBeInTheDocument();
    expect(screen.getByText("En")).toBeInTheDocument();
  });

  it("calls onSelect(1) when Kyllä clicked", () => {
    const onSelect = vi.fn();
    renderWithI18n(<YesNoInput onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Kyllä"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onSelect(0) when En clicked", () => {
    const onSelect = vi.fn();
    renderWithI18n(<YesNoInput onSelect={onSelect} />);
    fireEvent.click(screen.getByText("En"));
    expect(onSelect).toHaveBeenCalledWith(0);
  });

  it("both buttons meet touch target size requirement", () => {
    renderWithI18n(<YesNoInput onSelect={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBe(2);
    buttons.forEach((btn) => {
      expect(btn.className).toContain("min-h-touch");
    });
  });
});
