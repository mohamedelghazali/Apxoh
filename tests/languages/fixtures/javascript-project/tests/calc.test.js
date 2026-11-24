import { describe, it, expect } from "vitest";
import { add, subtract, divide } from "../src/calc.js";

describe("calc", () => {
  it("adds", () => expect(add(2, 3)).toBe(5));
  it("subtracts", () => expect(subtract(5, 3)).toBe(2));
  it("divides", () => expect(divide(10, 2)).toBe(5));
  it("rejects division by zero", () => {
    expect(() => divide(1, 0)).toThrow("cannot divide by zero");
  });
});
