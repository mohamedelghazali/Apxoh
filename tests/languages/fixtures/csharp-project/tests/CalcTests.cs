using Xunit;

namespace Apxoh.Fixture.Tests;

public class CalcTests
{
    [Fact] public void Adds() => Assert.Equal(5, Calc.Add(2, 3));

    [Fact] public void Subtracts() => Assert.Equal(2, Calc.Subtract(5, 3));

    [Fact] public void Divides() => Assert.Equal(5, Calc.Divide(10, 2));

    [Fact] public void RejectsDivisionByZero()
        => Assert.Throws<DivideByZeroException>(() => Calc.Divide(1, 0));
}
