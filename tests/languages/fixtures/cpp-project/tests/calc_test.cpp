#include "calc.hpp"

#include <gtest/gtest.h>

TEST(Calc, Adds) { EXPECT_EQ(apxoh::add(2, 3), 5); }

TEST(Calc, Subtracts) { EXPECT_EQ(apxoh::subtract(5, 3), 2); }

TEST(Calc, Divides) { EXPECT_EQ(apxoh::divide(10, 2), 5); }

TEST(Calc, RejectsDivisionByZero) {
    EXPECT_THROW(apxoh::divide(1, 0), std::invalid_argument);
}
