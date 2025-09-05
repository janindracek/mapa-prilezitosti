import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ErrorBoundary from "../ErrorBoundary.jsx";

function Boom() {
  throw new Error("kaboom");
}

describe("ErrorBoundary", () => {
  it("catches child errors and renders fallback", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {}); // silence React error logs
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    spy.mockRestore();
  });
});