"""Tests for revenue calculation module."""

import pytest
from apm_calculator.revenue import calculate_revenue, RevenueCalculation
from apm_calculator.types import RevenueInput, RevenueInputType
from apm_calculator.exchange_rates import ExchangeRateManager


class TestRevenueCalculation:
    """Tests for revenue calculation."""

    @pytest.fixture
    def exchange_manager(self):
        """Create exchange manager with known rates."""
        return ExchangeRateManager({
            "USD": 1.0,
            "EUR": 1.10,  # 1 EUR = 1.10 USD
            "GBP": 1.30,  # 1 GBP = 1.30 USD
        })

    def test_monthly_revenue_usd(self, exchange_manager):
        """Monthly USD revenue should be normalized correctly."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.MONTHLY,
            amount=10000,
            currency="USD"
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        assert result.monthly_usd == 10000
        assert result.yearly_usd == 120000

    def test_monthly_revenue_eur(self, exchange_manager):
        """Monthly EUR revenue should be converted to USD."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.MONTHLY,
            amount=10000,
            currency="EUR"
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        # 10000 EUR * 1.10 = 11000 USD
        assert result.monthly_usd == 11000
        assert result.yearly_usd == 132000

    def test_annual_revenue(self, exchange_manager):
        """Annual revenue should be normalized to monthly."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.ANNUAL,
            amount=120000,
            currency="USD"
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        assert result.yearly_usd == 120000
        assert result.monthly_usd == 10000

    def test_hourly_revenue_default_hours(self, exchange_manager):
        """Hourly revenue with default hours per month."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.HOURLY,
            amount=100,  # $100/hour
            currency="USD",
            hours_per_month=160  # default
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        # 100 * 160 = 16000 monthly
        assert result.monthly_usd == 16000
        assert result.yearly_usd == 192000

    def test_hourly_revenue_custom_hours(self, exchange_manager):
        """Hourly revenue with custom hours per month."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.HOURLY,
            amount=100,
            currency="USD",
            hours_per_month=176
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        # 100 * 176 = 17600 monthly
        assert result.monthly_usd == 17600
        assert result.yearly_usd == 211200

    def test_fixed_price_revenue(self, exchange_manager):
        """Fixed price revenue should calculate monthly from total."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.FIXED_PRICE,
            amount=60000,  # Total contract value
            currency="USD",
            contract_duration_months=6
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        # 60000 / 6 = 10000 monthly
        assert result.monthly_usd == 10000
        assert result.yearly_usd == 120000
        assert result.contract_duration_months == 6
        assert result.total_contract_usd == 60000

    def test_fixed_price_revenue_different_currency(self, exchange_manager):
        """Fixed price in different currency should convert total."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.FIXED_PRICE,
            amount=100000,  # 100000 EUR
            currency="EUR",
            contract_duration_months=10
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        # 100000 EUR * 1.10 = 110000 USD total
        # 110000 / 10 = 11000 monthly
        assert abs(result.total_contract_usd - 110000) < 0.01
        assert abs(result.monthly_usd - 11000) < 0.01
        assert abs(result.yearly_usd - 132000) < 0.01

    def test_zero_revenue(self, exchange_manager):
        """Zero revenue should be valid."""
        revenue_input = RevenueInput(
            input_type=RevenueInputType.MONTHLY,
            amount=0,
            currency="USD"
        )
        result = calculate_revenue(revenue_input, exchange_manager)

        assert result.monthly_usd == 0
        assert result.yearly_usd == 0
