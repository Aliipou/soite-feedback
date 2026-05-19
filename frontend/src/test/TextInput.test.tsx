import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import i18n from "../i18n/index";
import { TextInput } from "../components/kiosk/TextInput";

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("TextInput", () => {
  it("renders textarea and both buttons", () => {
    renderWithI18n(<TextInput onSubmit={vi.fn()} onSkip={vi.fn()} />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByText("Ohita")).toBeInTheDocument();
    expect(screen.getByText("Lähetä palaute →")).toBeInTheDocument();
  });

  it("calls onSkip when Ohita clicked", () => {
    const onSkip = vi.fn();
    renderWithI18n(<TextInput onSubmit={vi.fn()} onSkip={onSkip} />);
    fireEvent.click(screen.getByText("Ohita"));
    expect(onSkip).toHaveBeenCalled();
  });

  it("calls onSubmit with trimmed text when Lähetä clicked", async () => {
    const onSubmit = vi.fn();
    renderWithI18n(<TextInput onSubmit={onSubmit} onSkip={vi.fn()} />);
    await userEvent.type(screen.getByRole("textbox"), "  Great service  ");
    fireEvent.click(screen.getByText("Lähetä palaute →"));
    expect(onSubmit).toHaveBeenCalledWith("Great service");
  });

  it("enforces 500 character limit", async () => {
    renderWithI18n(<TextInput onSubmit={vi.fn()} onSkip={vi.fn()} />);
    const textarea = screen.getByRole("textbox");
    const longText = "a".repeat(600);
    await userEvent.type(textarea, longText);
    // Textarea maxLength or slice should limit to 500
    expect((textarea as HTMLTextAreaElement).value.length).toBeLessThanOrEqual(500);
  });

  it("shows character counter", async () => {
    renderWithI18n(<TextInput onSubmit={vi.fn()} onSkip={vi.fn()} />);
    await userEvent.type(screen.getByRole("textbox"), "Hello");
    expect(screen.getByText(/5 \/ 500/)).toBeInTheDocument();
  });

  it("textarea has associated label for accessibility", () => {
    renderWithI18n(<TextInput onSubmit={vi.fn()} onSkip={vi.fn()} />);
    const textarea = screen.getByRole("textbox");
    // Either has a visible label or aria-label
    const hasLabel = textarea.id && document.querySelector(`label[for="${textarea.id}"]`);
    const hasAriaLabel = textarea.getAttribute("aria-label") || textarea.getAttribute("aria-labelledby");
    expect(hasLabel || hasAriaLabel).toBeTruthy();
  });
});
