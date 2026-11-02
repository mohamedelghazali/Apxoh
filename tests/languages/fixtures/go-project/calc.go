// Package calc is a minimal calculator for Apxoh fixture testing.
package calc

import "errors"

// Add returns a + b.
func Add(a, b int) int { return a + b }

// Subtract returns a - b.
func Subtract(a, b int) int { return a - b }

// Divide returns a / b, or an error if b is zero.
func Divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("cannot divide by zero")
    }
    return a / b, nil
}
