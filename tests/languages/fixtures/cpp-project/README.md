# C++ Fixture Project

Minimal C++20 project (CMake + GoogleTest) for Apxoh's language detection tests.

- `src/calc.cpp` — calculator
- `tests/calc_test.cpp` — GoogleTest tests
- Run: `cmake -S . -B build && cmake --build build && ctest --test-dir build`
