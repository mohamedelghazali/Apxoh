/** Minimal calculator module for Apxoh fixture testing. */

/**
 * Add two numbers.
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
export function add(a, b) {
  return a + b;
}

/**
 * Subtract two numbers.
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
export function subtract(a, b) {
  return a - b;
}

/**
 * Divide two numbers.
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
export function divide(a, b) {
  if (b === 0) throw new Error("cannot divide by zero");
  return a / b;
}
