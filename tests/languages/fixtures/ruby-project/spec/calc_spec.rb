# frozen_string_literal: true

require_relative "../lib/calc"

RSpec.describe Calc do
  it "adds" do
    expect(described_class.add(2, 3)).to eq(5)
  end

  it "subtracts" do
    expect(described_class.subtract(5, 3)).to eq(2)
  end

  it "divides" do
    expect(described_class.divide(10, 2)).to eq(5)
  end

  it "rejects division by zero" do
    expect { described_class.divide(1, 0) }.to raise_error(ArgumentError)
  end
end
