//! Minimal calculator for Apxoh fixture testing.

/// Add a + b.
pub fn add(a: i32, b: i32) -> i32 { a + b }

/// Subtract a - b.
pub fn subtract(a: i32, b: i32) -> i32 { a - b }

/// Divide a / b. Panics if b is zero.
pub fn divide(a: i32, b: i32) -> i32 {
    assert!(b != 0, "cannot divide by zero");
    a / b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds() { assert_eq!(add(2, 3), 5); }

    #[test]
    fn subtracts() { assert_eq!(subtract(5, 3), 2); }

    #[test]
    fn divides() { assert_eq!(divide(10, 2), 5); }

    #[test]
    #[should_panic(expected = "cannot divide by zero")]
    fn rejects_division_by_zero() { divide(1, 0); }
}
