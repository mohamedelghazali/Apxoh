package calc

import "testing"

func TestAdd(t *testing.T) {
    if got := Add(2, 3); got != 5 {
        t.Errorf("Add(2,3) = %d, want 5", got)
    }
}

func TestSubtract(t *testing.T) {
    if got := Subtract(5, 3); got != 2 {
        t.Errorf("Subtract(5,3) = %d, want 2", got)
    }
}

func TestDivide(t *testing.T) {
    got, err := Divide(10, 2)
    if err != nil {
        t.Fatal(err)
    }
    if got != 5 {
        t.Errorf("Divide(10,2) = %d, want 5", got)
    }
}

func TestDivideByZero(t *testing.T) {
    if _, err := Divide(1, 0); err == nil {
        t.Error("expected error for Divide(1,0)")
    }
}
