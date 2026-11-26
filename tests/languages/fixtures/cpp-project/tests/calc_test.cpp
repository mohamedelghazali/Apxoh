#include "calc.hpp"

#include <gtest/gtest.h>

TEST(Calc, Adds) { EXPECT_EQ(gencode_gov::add(2, 3), 5); }

TEST(Calc, Subtracts) { EXPECT_EQ(gencode_gov::subtract(5, 3), 2); }

TEST(Calc, Divides) { EXPECT_EQ(gencode_gov::divide(10, 2), 5); }

TEST(Calc, RejectsDivisionByZero) {
    EXPECT_THROW(gencode_gov::divide(1, 0), std::invalid_argument);
}
