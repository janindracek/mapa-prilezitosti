import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Controls from "../../components/Controls.jsx";

describe("Controls a11y", () => {
  it("associates labels with selects", async () => {
    const onChange = vi.fn();
    render(
      <Controls
        countries={["CZ","DE"]}
        years={[2020,2021]}
        metrics={["exports","imports"]}
        country={"CZ"}
        year={2020}
        metric={"exports"}
        onChange={onChange}
      />
    );
    // Accessible queries by label text
    const country = screen.getByLabelText(/country/i);
    const year = screen.getByLabelText(/year/i);
    const metric = screen.getByLabelText(/metric/i);
    expect(country).toHaveAttribute("id", "country-select");
    expect(year).toHaveAttribute("id", "year-select");
    expect(metric).toHaveAttribute("id", "metric-select");

    // Keyboard change still works
    await userEvent.selectOptions(country, "DE");
    expect(onChange).toHaveBeenCalled();
  });
});