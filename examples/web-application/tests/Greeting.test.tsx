import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Greeting } from "../src/components/Greeting";

describe("Greeting", () => {
  it("greets by name", () => {
    render(<Greeting name="Alice" />);
    expect(screen.getByText("Hello, Alice!")).toBeDefined();
  });

  it("falls back for empty name", () => {
    render(<Greeting name="" />);
    expect(screen.getByText("Hello, stranger!")).toBeDefined();
  });
});
