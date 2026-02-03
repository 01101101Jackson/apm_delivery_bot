"""Tests for type definitions and validation."""

import pytest
from apm_calculator.types import (
    RevenueInputType,
    CostRatePeriod,
    RevenueInput,
    CostInput,
    CalculationResult,
)


class TestRevenueInputType:
    """Tests for RevenueInputType enum."""

    def test_all_types_exist(self):
        """All expected revenue input types should exist."""
        assert RevenueInputType.HOURLY.value == "hourly"
        assert RevenueInputType.MONTHLY.value == "monthly"
        assert RevenueInputType.ANNUAL.value == "annual"
        assert RevenueInputType.FIXED_PRICE.value == "fixed_price"

    def test_from_string(self):
        """Should be able to create enum from string value."""
        assert RevenueInputType("hourly") == RevenueInputType.HOURLY
        assert RevenueInputType("fixed_price") == RevenueInputType.FIXED_PRICE


class TestCostRatePeriod:
    """Tests for CostRatePeriod enum."""

    def test_all_periods_exist(self):
        """All expected cost rate periods should exist."""
        assert CostRatePeriod.HOURLY.value == "hourly"
        assert CostRatePeriod.MONTHLY.value == "monthly"
        assert CostRatePeriod.ANNUAL.value == "annual"


class TestRevenueInput:
    """Tests for RevenueInput dataclass."""

    def test_valid_monthly_input(self):
        """Valid monthly input should be created successfully."""
        revenue = RevenueInput(
            input_type=RevenueInputType.MONTHLY,
            amount=10000,
            currency="USD"
        )
        assert revenue.amount == 10000
        assert revenue.currency == "USD"
        assert revenue.hours_per_month == 160.0  # default

    def test_valid_hourly_input(self):
        """Valid hourly input should be created successfully."""
        revenue = RevenueInput(
            input_type=RevenueInputType.HOURLY,
            amount=100,
            currency="EUR",
            hours_per_month=176
        )
        assert revenue.amount == 100
        assert revenue.hours_per_month == 176

    def test_valid_fixed_price_input(self):
        """Valid fixed price input should be created successfully."""
        revenue = RevenueInput(
            input_type=RevenueInputType.FIXED_PRICE,
            amount=100000,
            currency="USD",
            contract_duration_months=6
        )
        assert revenue.amount == 100000
        assert revenue.contract_duration_months == 6

    def test_negative_amount_raises_error(self):
        """Negative revenue amount should raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            RevenueInput(
                input_type=RevenueInputType.MONTHLY,
                amount=-100,
                currency="USD"
            )

    def test_zero_hours_per_month_raises_error(self):
        """Zero hours per month should raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            RevenueInput(
                input_type=RevenueInputType.HOURLY,
                amount=100,
                currency="USD",
                hours_per_month=0
            )

    def test_fixed_price_without_duration_raises_error(self):
        """Fixed price without contract duration should raise ValueError."""
        with pytest.raises(ValueError, match="Contract duration"):
            RevenueInput(
                input_type=RevenueInputType.FIXED_PRICE,
                amount=100000,
                currency="USD"
            )

    def test_fixed_price_with_zero_duration_raises_error(self):
        """Fixed price with zero duration should raise ValueError."""
        with pytest.raises(ValueError, match="Contract duration"):
            RevenueInput(
                input_type=RevenueInputType.FIXED_PRICE,
                amount=100000,
                currency="USD",
                contract_duration_months=0
            )


class TestCostInput:
    """Tests for CostInput dataclass."""

    def test_valid_monthly_input(self):
        """Valid monthly cost input should be created successfully."""
        cost = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD"
        )
        assert cost.amount == 5000
        assert cost.allocation_fte == 1.0  # default

    def test_valid_with_fte(self):
        """Valid input with FTE allocation should be created."""
        cost = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=0.5
        )
        assert cost.allocation_fte == 0.5

    def test_negative_amount_raises_error(self):
        """Negative cost amount should raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            CostInput(
                rate_period=CostRatePeriod.MONTHLY,
                amount=-100,
                currency="USD"
            )

    def test_fte_below_zero_raises_error(self):
        """FTE below 0 should raise ValueError."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            CostInput(
                rate_period=CostRatePeriod.MONTHLY,
                amount=5000,
                currency="USD",
                allocation_fte=-0.1
            )

    def test_fte_above_one_raises_error(self):
        """FTE above 1 should raise ValueError."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            CostInput(
                rate_period=CostRatePeriod.MONTHLY,
                amount=5000,
                currency="USD",
                allocation_fte=1.1
            )

    def test_fte_boundary_values(self):
        """FTE at boundary values (0 and 1) should be valid."""
        cost_zero = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=0
        )
        assert cost_zero.allocation_fte == 0

        cost_one = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=1
        )
        assert cost_one.allocation_fte == 1


class TestCalculationResult:
    """Tests for CalculationResult dataclass."""

    def test_basic_result(self):
        """Basic result without contract should be created."""
        result = CalculationResult(
            reporting_currency="USD",
            revenue_monthly=10000,
            revenue_yearly=120000,
            base_cost_monthly=5000,
            base_cost_yearly=60000,
            loaded_cost_monthly=6250,
            loaded_cost_yearly=75000,
            apm_monthly=0.375,
            apm_yearly=0.375,
        )
        assert result.reporting_currency == "USD"
        assert result.apm_monthly == 0.375
        assert result.contract_duration_months is None

    def test_to_dict_basic(self):
        """to_dict should return properly formatted dict."""
        result = CalculationResult(
            reporting_currency="USD",
            revenue_monthly=10000,
            revenue_yearly=120000,
            base_cost_monthly=5000,
            base_cost_yearly=60000,
            loaded_cost_monthly=6250,
            loaded_cost_yearly=75000,
            apm_monthly=0.375,
            apm_yearly=0.375,
        )
        d = result.to_dict()
        assert d["reporting_currency"] == "USD"
        assert d["revenue"]["monthly"] == 10000.00
        assert d["apm"]["monthly"] == 0.375
        assert "contract" not in d

    def test_to_dict_with_contract(self):
        """to_dict with contract should include contract section."""
        result = CalculationResult(
            reporting_currency="USD",
            revenue_monthly=10000,
            revenue_yearly=120000,
            base_cost_monthly=5000,
            base_cost_yearly=60000,
            loaded_cost_monthly=6250,
            loaded_cost_yearly=75000,
            apm_monthly=0.375,
            apm_yearly=0.375,
            contract_duration_months=6,
            total_revenue_contract=60000,
            total_loaded_cost_contract=37500,
            apm_contract=0.375,
        )
        d = result.to_dict()
        assert "contract" in d
        assert d["contract"]["duration_months"] == 6
        assert d["contract"]["total_revenue"] == 60000.00
        assert d["contract"]["apm"] == 0.375
