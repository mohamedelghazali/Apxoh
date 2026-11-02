package dev.apxoh.fixture;

public final class Calc {
    private Calc() {}

    public static int add(int a, int b) {
        return a + b;
    }

    public static int subtract(int a, int b) {
        return a - b;
    }

    public static int divide(int a, int b) {
        if (b == 0) throw new ArithmeticException("cannot divide by zero");
        return a / b;
    }
}
