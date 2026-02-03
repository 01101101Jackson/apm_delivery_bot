"""Tests for exchange rate functionality."""

import pytest
from apm_calculator.exchange_rates import ExchangeRateManager, DEFAULT_EXCHANGE_RATES


class TestExchangeRateManager:
    """Tests for ExchangeRateManager class."""

    def test_default_rates_loaded(self):
        """Default rates should be loaded on initialization."""
        manager = ExchangeRateManager()
        assert "USD" in manager.supported_currencies
        assert "EUR" in manager.supported_currencies
        assert "GBP" in manager.supported_currencies

    def test_usd_rate_is_one(self):
        """USD to USD rate should be 1.0."""
        manager = ExchangeRateManager()
        assert manager.get_rate_to_usd("USD") == 1.0

    def test_custom_rates_override_defaults(self):
        """Custom rates should override default rates."""
        custom_rates = {"EUR": 1.20}
        manager = ExchangeRateManager(custom_rates)
        assert manager.get_rate_to_usd("EUR") == 1.20

    def test_custom_rates_add_new_currencies(self):
        """Custom rates can add new currencies."""
        custom_rates = {"XYZ": 0.5}
        manager = ExchangeRateManager(custom_rates)
        assert "XYZ" in manager.supported_currencies
        assert manager.get_rate_to_usd("XYZ") == 0.5

    def test_unsupported_currency_raises_error(self):
        """Getting rate for unsupported currency should raise ValueError."""
        manager = ExchangeRateManager()
        with pytest.raises(ValueError, match="Unsupported currency"):
            manager.get_rate_to_usd("INVALID")

    def test_convert_to_usd(self):
        """Converting to USD should multiply by rate."""
        manager = ExchangeRateManager({"EUR": 1.10})
        result = manager.convert_to_usd(100, "EUR")
        assert abs(result - 110.0) < 0.001

    def test_convert_from_usd(self):
        """Converting from USD should divide by rate."""
        manager = ExchangeRateManager({"EUR": 1.10})
        result = manager.convert_from_usd(110, "EUR")
        assert abs(result - 100.0) < 0.001

    def test_convert_between_currencies(self):
        """Converting between currencies goes through USD."""
        manager = ExchangeRateManager({
            "EUR": 1.10,  # 1 EUR = 1.10 USD
            "GBP": 1.30,  # 1 GBP = 1.30 USD
        })
        # 100 GBP = 130 USD = ~118.18 EUR
        result = manager.convert(100, "GBP", "EUR")
        expected = 130.0 / 1.10
        assert abs(result - expected) < 0.001

    def test_convert_same_currency(self):
        """Converting same currency should return same amount."""
        manager = ExchangeRateManager()
        result = manager.convert(100, "EUR", "EUR")
        assert result == 100.0

    def test_set_rate(self):
        """Setting a rate should update the rate."""
        manager = ExchangeRateManager()
        manager.set_rate("EUR", 1.50)
        assert manager.get_rate_to_usd("EUR") == 1.50

    def test_set_rate_new_currency(self):
        """Setting a rate for new currency should add it."""
        manager = ExchangeRateManager()
        manager.set_rate("XYZ", 0.75)
        assert "XYZ" in manager.supported_currencies
        assert manager.get_rate_to_usd("XYZ") == 0.75

    def test_set_rate_invalid_rate(self):
        """Setting non-positive rate should raise ValueError."""
        manager = ExchangeRateManager()
        with pytest.raises(ValueError, match="must be positive"):
            manager.set_rate("EUR", 0)
        with pytest.raises(ValueError, match="must be positive"):
            manager.set_rate("EUR", -1)

    def test_case_insensitive_currency_codes(self):
        """Currency codes should be case-insensitive."""
        manager = ExchangeRateManager()
        assert manager.get_rate_to_usd("eur") == manager.get_rate_to_usd("EUR")
        assert manager.get_rate_to_usd("Eur") == manager.get_rate_to_usd("EUR")

    def test_get_all_rates(self):
        """get_all_rates should return a copy of all rates."""
        manager = ExchangeRateManager()
        rates = manager.get_all_rates()
        assert isinstance(rates, dict)
        assert "USD" in rates
        # Modifying returned dict shouldn't affect internal state
        rates["TEST"] = 999
        assert "TEST" not in manager.supported_currencies
