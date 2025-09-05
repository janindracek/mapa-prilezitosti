import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Controls from "../../components/Controls.jsx";

describe("Controls", () => {
  it("renders and calls onChange when selections change", () => {
    const onChange = vi.fn();

    render(
      <Controls
        countries={["CZ", "DE"]}
        years={[2020, 2021]}
        metrics={["exports", "imports"]}
        country={"CZ"}
        year={2020}
        metric={"exports"}
        onChange={onChange}
      />
    );

    // Change country
    fireEvent.change(screen.getByTestId("country-select"), {
      target: { value: "DE" },
    });
    expect(onChange).toHaveBeenCalled();
    let arg = onChange.mock.calls.at(-1)[0];
    expect(arg.country).toBe("DE");

    // Change year
    fireEvent.change(screen.getByTestId("year-select"), {
      target: { value: "2021" },
    });
    arg = onChange.mock.calls.at(-1)[0];
    expect(arg.year).toBe("2021");

    // Change metric
    fireEvent.change(screen.getByTestId("metric-select"), {
      target: { value: "imports" },
    });
    arg = onChange.mock.calls.at(-1)[0];
    expect(arg.metric).toBe("imports");
  });
});