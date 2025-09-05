import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SignalsList from "../../components/SignalsList.jsx";

describe("SignalsList", () => {
  it("renders items and calls onSelect with the clicked item", () => {
    const onSelect = vi.fn();
    const signals = [
      { id: "s1", label: "Rising exports", score: 7.3 },
      { id: "s2", label: "New markets", score: 5.8 },
    ];

    render(<SignalsList signals={signals} selectedId={"s1"} onSelect={onSelect} />);

    // Ensure both buttons exist
    expect(screen.getByTestId("signal-s1")).toBeInTheDocument();
    expect(screen.getByTestId("signal-s2")).toBeInTheDocument();

    // Click the second item
    fireEvent.click(screen.getByTestId("signal-s2"));

    // Verify callback with item payload
    expect(onSelect).toHaveBeenCalledTimes(1);
    const arg = onSelect.mock.calls[0][0];
    expect(arg).toMatchObject({ id: "s2", label: "New markets", score: 5.8 });
  });
});