"""Tests for cost calculation module."""

import pytest
from apm_calculator.cost import calculate_cost, CostCalculation
from apm_calculator.types import CostInput, CostRatePeriod
from apm_calculator.exchange_rates import ExchangeRateManager


class TestCostCalculation:
    """Tests for cost calculation."""

    @pytest.fixture
    def exchange_manager(self):
        """Create exchange manager with known rates."""
        return ExchangeRateManager({
            "USD": 1.0,
            "EUR": 1.10,
            "GBP": 1.30,
        })

    def test_monthly_cost_full_fte_no_uplift(self, exchange_manager):
        """Monthly cost with full FTE and no uplift."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        assert result.base_cost_monthly_usd == 5000
        assert result.base_cost_yearly_usd == 60000
        assert result.loaded_cost_monthly_usd == 5000  # no uplift
        assert result.loaded_cost_yearly_usd == 60000

    def test_monthly_cost_with_uplift(self, exchange_manager):
        """Monthly cost with uplift applied."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 0.25, exchange_manager)  # 25% uplift

        assert result.base_cost_monthly_usd == 5000
        assert result.loaded_cost_monthly_usd == 6250  # 5000 * 1.25
        assert result.loaded_cost_yearly_usd == 75000

    def test_monthly_cost_with_fte_scaling(self, exchange_manager):
        """Cost should be scaled by FTE allocation."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=10000,
            currency="USD",
            allocation_fte=0.5
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        # 10000 * 0.5 = 5000 base cost
        assert result.base_cost_monthly_usd == 5000
        assert result.base_cost_yearly_usd == 60000

    def test_fte_and_uplift_combined(self, exchange_manager):
        """FTE scaling should happen before uplift."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=10000,
            currency="USD",
            allocation_fte=0.5
        )
        result = calculate_cost(cost_input, 0.20, exchange_manager)  # 20% uplift

        # Base: 10000 * 0.5 = 5000
        # Loaded: 5000 * 1.20 = 6000
        assert result.base_cost_monthly_usd == 5000
        assert result.loaded_cost_monthly_usd == 6000

    def test_hourly_cost_default_hours(self, exchange_manager):
        """Hourly cost with default hours per month."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.HOURLY,
            amount=50,  # $50/hour
            currency="USD",
            hours_per_month=160,
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        # 50 * 160 = 8000 monthly
        assert result.base_cost_monthly_usd == 8000
        assert result.base_cost_yearly_usd == 96000

    def test_hourly_cost_with_fte(self, exchange_manager):
        """Hourly cost with FTE scaling."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.HOURLY,
            amount=50,
            currency="USD",
            hours_per_month=160,
            allocation_fte=0.5
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        # 50 * 160 * 0.5 = 4000 monthly
        assert result.base_cost_monthly_usd == 4000

    def test_annual_cost(self, exchange_manager):
        """Annual cost should be normalized to monthly."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.ANNUAL,
            amount=120000,
            currency="USD",
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        # 120000 / 12 = 10000 monthly
        assert result.base_cost_monthly_usd == 10000
        assert result.base_cost_yearly_usd == 120000

    def test_currency_conversion(self, exchange_manager):
        """Cost in different currency should be converted."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="EUR",  # 1 EUR = 1.10 USD
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        # 5000 EUR * 1.10 = 5500 USD
        assert result.base_cost_monthly_usd == 5500
        assert result.base_cost_yearly_usd == 66000

    def test_zero_fte(self, exchange_manager):
        """Zero FTE should result in zero cost."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=10000,
            currency="USD",
            allocation_fte=0
        )
        result = calculate_cost(cost_input, 0.25, exchange_manager)

        assert result.base_cost_monthly_usd == 0
        assert result.loaded_cost_monthly_usd == 0

    def test_negative_uplift_raises_error(self, exchange_manager):
        """Negative uplift should raise ValueError."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=1.0
        )
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_cost(cost_input, -0.1, exchange_manager)

    def test_zero_uplift_same_as_base(self, exchange_manager):
        """Zero uplift should make loaded cost equal to base cost."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=8000,
            currency="USD",
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 0.0, exchange_manager)

        assert result.base_cost_monthly_usd == result.loaded_cost_monthly_usd
        assert result.base_cost_yearly_usd == result.loaded_cost_yearly_usd

    def test_high_uplift(self, exchange_manager):
        """High uplift values should work correctly."""
        cost_input = CostInput(
            rate_period=CostRatePeriod.MONTHLY,
            amount=5000,
            currency="USD",
            allocation_fte=1.0
        )
        result = calculate_cost(cost_input, 1.0, exchange_manager)  # 100% uplift

        assert result.base_cost_monthly_usd == 5000
        assert result.loaded_cost_monthly_usd == 10000  # doubled
