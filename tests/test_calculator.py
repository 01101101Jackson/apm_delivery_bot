"""Tests for the main APMCalculator class."""

import pytest
from apm_calculator import APMCalculator, RevenueInputType, CostRatePeriod


class TestAPMCalculator:
    """Integration tests for APMCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create calculator with known rates."""
        return APMCalculator({
            "USD": 1.0,
            "EUR": 1.10,
            "GBP": 1.30,
        })

    def test_simple_monthly_calculation_usd(self, calculator):
        """Simple monthly calculation in USD."""
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,
            revenue_currency="USD",
            cost_rate_period="monthly",
            cost_amount=5000,
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.25,  # 25%
            reporting_currency="USD",
        )

        # Revenue: 10000/month, 120000/year
        assert result.revenue_monthly == 10000
        assert result.revenue_yearly == 120000

        # Base cost: 5000/month, 60000/year
        assert result.base_cost_monthly == 5000
        assert result.base_cost_yearly == 60000

        # Loaded cost: 5000 * 1.25 = 6250/month
        assert result.loaded_cost_monthly == 6250
        assert result.loaded_cost_yearly == 75000

        # APM: 1 - (6250/10000) = 0.375
        assert abs(result.apm_monthly - 0.375) < 0.0001

    def test_hourly_rates_calculation(self, calculator):
        """Calculation with hourly rates."""
        result = calculator.calculate(
            revenue_type="hourly",
            revenue_amount=100,  # $100/hour revenue
            revenue_currency="USD",
            cost_rate_period="hourly",
            cost_amount=50,  # $50/hour cost
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.20,
            reporting_currency="USD",
            hours_per_month=160,
        )

        # Revenue: 100 * 160 = 16000/month
        assert result.revenue_monthly == 16000

        # Base cost: 50 * 160 = 8000/month
        assert result.base_cost_monthly == 8000

        # Loaded cost: 8000 * 1.20 = 9600/month
        assert result.loaded_cost_monthly == 9600

        # APM: 1 - (9600/16000) = 0.4
        assert abs(result.apm_monthly - 0.4) < 0.0001

    def test_fte_scaling(self, calculator):
        """FTE should scale cost but not revenue."""
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,
            revenue_currency="USD",
            cost_rate_period="monthly",
            cost_amount=10000,
            cost_currency="USD",
            allocation_fte=0.5,  # Half time
            uplift_percent=0.0,
            reporting_currency="USD",
        )

        # Revenue is NOT scaled
        assert result.revenue_monthly == 10000

        # Cost IS scaled by FTE
        assert result.base_cost_monthly == 5000

    def test_cross_currency_calculation(self, calculator):
        """Calculation with different currencies."""
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,  # EUR
            revenue_currency="EUR",
            cost_rate_period="monthly",
            cost_amount=5000,  # GBP
            cost_currency="GBP",
            allocation_fte=1.0,
            uplift_percent=0.0,
            reporting_currency="USD",
        )

        # Revenue: 10000 EUR * 1.10 = 11000 USD
        assert result.revenue_monthly == 11000

        # Cost: 5000 GBP * 1.30 = 6500 USD
        assert result.base_cost_monthly == 6500

    def test_reporting_currency_conversion(self, calculator):
        """Results should be in reporting currency."""
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=11000,  # Already in USD
            revenue_currency="USD",
            cost_rate_period="monthly",
            cost_amount=5500,
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.0,
            reporting_currency="EUR",  # Output in EUR
        )

        # 11000 USD / 1.10 = 10000 EUR
        assert abs(result.revenue_monthly - 10000) < 0.01

        # 5500 USD / 1.10 = 5000 EUR
        assert abs(result.base_cost_monthly - 5000) < 0.01

    def test_fixed_price_contract(self, calculator):
        """Fixed price contract should include contract totals."""
        result = calculator.calculate(
            revenue_type="fixed_price",
            revenue_amount=60000,  # Total contract
            revenue_currency="USD",
            contract_duration_months=6,
            cost_rate_period="monthly",
            cost_amount=5000,
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.25,
            reporting_currency="USD",
        )

        # Monthly revenue: 60000 / 6 = 10000
        assert result.revenue_monthly == 10000

        # Contract totals
        assert result.contract_duration_months == 6
        assert result.total_revenue_contract == 60000

        # Total loaded cost: 5000 * 1.25 * 6 = 37500
        assert result.total_loaded_cost_contract == 37500

        # Contract APM: 1 - (37500/60000) = 0.375
        assert abs(result.apm_contract - 0.375) < 0.0001

    def test_result_to_dict(self, calculator):
        """Result should convert to dict properly."""
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,
            revenue_currency="USD",
            cost_rate_period="monthly",
            cost_amount=6000,
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.0,
            reporting_currency="USD",
        )

        d = result.to_dict()
        assert d["reporting_currency"] == "USD"
        assert "revenue" in d
        assert "base_cost" in d
        assert "loaded_cost" in d
        assert "apm" in d

    def test_properties(self, calculator):
        """Calculator should expose valid properties."""
        assert "USD" in calculator.supported_currencies
        assert "hourly" in calculator.revenue_input_types
        assert "monthly" in calculator.cost_rate_periods

    def test_set_exchange_rate(self, calculator):
        """Setting exchange rate should affect calculations."""
        calculator.set_exchange_rate("EUR", 1.20)  # Update rate

        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,
            revenue_currency="EUR",
            cost_rate_period="monthly",
            cost_amount=5000,
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.0,
            reporting_currency="USD",
        )

        # 10000 EUR * 1.20 = 12000 USD
        assert result.revenue_monthly == 12000

    def test_invalid_revenue_type(self, calculator):
        """Invalid revenue type should raise ValueError."""
        with pytest.raises(ValueError):
            calculator.calculate(
                revenue_type="invalid",
                revenue_amount=10000,
                revenue_currency="USD",
                cost_rate_period="monthly",
                cost_amount=5000,
                cost_currency="USD",
                allocation_fte=1.0,
                uplift_percent=0.0,
                reporting_currency="USD",
            )

    def test_invalid_allocation_fte(self, calculator):
        """Invalid FTE should raise ValueError."""
        with pytest.raises(ValueError):
            calculator.calculate(
                revenue_type="monthly",
                revenue_amount=10000,
                revenue_currency="USD",
                cost_rate_period="monthly",
                cost_amount=5000,
                cost_currency="USD",
                allocation_fte=1.5,  # Invalid
                uplift_percent=0.0,
                reporting_currency="USD",
            )

    def test_zero_revenue_apm_error(self, calculator):
        """Zero revenue should raise error in APM calculation."""
        with pytest.raises(ValueError):
            calculator.calculate(
                revenue_type="monthly",
                revenue_amount=0,
                revenue_currency="USD",
                cost_rate_period="monthly",
                cost_amount=5000,
                cost_currency="USD",
                allocation_fte=1.0,
                uplift_percent=0.0,
                reporting_currency="USD",
            )


class TestAPMCalculatorEdgeCases:
    """Edge case tests for APMCalculator."""

    def test_very_low_fte(self):
        """Very low FTE should work correctly."""
        calculator = APMCalculator()
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,
            revenue_currency="USD",
            cost_rate_period="monthly",
            cost_amount=10000,
            cost_currency="USD",
            allocation_fte=0.01,  # 1%
            uplift_percent=0.0,
            reporting_currency="USD",
        )

        assert result.base_cost_monthly == 100  # 10000 * 0.01

    def test_loss_scenario(self):
        """Loss scenario should show negative APM."""
        calculator = APMCalculator()
        result = calculator.calculate(
            revenue_type="monthly",
            revenue_amount=10000,
            revenue_currency="USD",
            cost_rate_period="monthly",
            cost_amount=15000,
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.0,
            reporting_currency="USD",
        )

        # APM: 1 - (15000/10000) = -0.5
        assert result.apm_monthly == -0.5

    def test_annual_cost_hourly_revenue(self):
        """Mixed periods should normalize correctly."""
        calculator = APMCalculator()
        result = calculator.calculate(
            revenue_type="hourly",
            revenue_amount=100,
            revenue_currency="USD",
            cost_rate_period="annual",
            cost_amount=96000,  # 8000/month = 50/hour
            cost_currency="USD",
            allocation_fte=1.0,
            uplift_percent=0.0,
            reporting_currency="USD",
            hours_per_month=160,
        )

        # Revenue: 100 * 160 = 16000/month
        assert result.revenue_monthly == 16000

        # Cost: 96000 / 12 = 8000/month
        assert result.base_cost_monthly == 8000
