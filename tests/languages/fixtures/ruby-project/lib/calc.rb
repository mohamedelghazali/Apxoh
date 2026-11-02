# frozen_string_literal: true

# Minimal calculator for Apxoh fixture testing.
module Calc
  module_function

  def add(a, b)
    a + b
  end

  def subtract(a, b)
    a - b
  end

  def divide(a, b)
    raise ArgumentError, "cannot divide by zero" if b.zero?

    a / b
  end
end
