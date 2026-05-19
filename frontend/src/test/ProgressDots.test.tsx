import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressDots } from "../components/kiosk/ProgressDots";

describe("ProgressDots", () => {
  it("renders correct number of dots", () => {
    const { container } = render(<ProgressDots total={5} current={0} />);
    // Each dot is a div inside the progressbar
    const dots = container.querySelectorAll("[aria-hidden='true']");
    expect(dots.length).toBe(5);
  });

  it("has progressbar role with correct aria values", () => {
    render(<ProgressDots total={5} current={2} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("3");
    expect(bar.getAttribute("aria-valuemin")).toBe("1");
    expect(bar.getAttribute("aria-valuemax")).toBe("5");
  });

  it("first question shows valuenow=1", () => {
    render(<ProgressDots total={3} current={0} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("1");
  });

  it("last question shows correct valuenow", () => {
    render(<ProgressDots total={3} current={2} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("3");
  });
});
