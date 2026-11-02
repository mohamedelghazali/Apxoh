namespace Apxoh.Fixture;

public static class Calc
{
    public static int Add(int a, int b) => a + b;

    public static int Subtract(int a, int b) => a - b;

    public static int Divide(int a, int b)
    {
        if (b == 0) throw new DivideByZeroException("cannot divide by zero");
        return a / b;
    }
}
