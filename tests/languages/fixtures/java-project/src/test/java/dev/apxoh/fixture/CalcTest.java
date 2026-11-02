package dev.apxoh.fixture;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class CalcTest {
    @Test void adds() { assertEquals(5, Calc.add(2, 3)); }

    @Test void subtracts() { assertEquals(2, Calc.subtract(5, 3)); }

    @Test void divides() { assertEquals(5, Calc.divide(10, 2)); }

    @Test void rejectsDivisionByZero() {
        assertThrows(ArithmeticException.class, () -> Calc.divide(1, 0));
    }
}
