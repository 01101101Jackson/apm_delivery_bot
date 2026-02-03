"""Exchange rate management for currency conversions."""

from typing import Dict


# Default exchange rates: Currency -> USD
# These are static rates that can be edited
DEFAULT_EXCHANGE_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,      # 1 EUR = 1.08 USD
    "GBP": 1.27,      # 1 GBP = 1.27 USD
    "CHF": 1.13,      # 1 CHF = 1.13 USD
    "AUD": 0.65,      # 1 AUD = 0.65 USD
    "CAD": 0.74,      # 1 CAD = 0.74 USD
    "JPY": 0.0067,    # 1 JPY = 0.0067 USD
    "CNY": 0.14,      # 1 CNY = 0.14 USD
    "INR": 0.012,     # 1 INR = 0.012 USD
    "SGD": 0.75,      # 1 SGD = 0.75 USD
    "HKD": 0.13,      # 1 HKD = 0.13 USD
    "NZD": 0.61,      # 1 NZD = 0.61 USD
    "SEK": 0.096,     # 1 SEK = 0.096 USD
    "NOK": 0.094,     # 1 NOK = 0.094 USD
    "DKK": 0.145,     # 1 DKK = 0.145 USD
    "ZAR": 0.055,     # 1 ZAR = 0.055 USD
    "BRL": 0.20,      # 1 BRL = 0.20 USD
    "MXN": 0.058,     # 1 MXN = 0.058 USD
}


class ExchangeRateManager:
    """Manages currency exchange rates for conversions."""

    def __init__(self, rates: Dict[str, float] = None):
        """
        Initialize with exchange rates.

        Args:
            rates: Dictionary of currency code -> USD rate.
                   If None, uses default rates.
        """
        self._rates = dict(DEFAULT_EXCHANGE_RATES)
        if rates:
            self._rates.update(rates)

    @property
    def supported_currencies(self) -> list:
        """Get list of supported currency codes."""
        return sorted(self._rates.keys())

    def get_rate_to_usd(self, currency: str) -> float:
        """
        Get the exchange rate from a currency to USD.

        Args:
            currency: Currency code (e.g., 'EUR', 'GBP')

        Returns:
            Exchange rate to USD

        Raises:
            ValueError: If currency is not supported
        """
        currency = currency.upper()
        if currency not in self._rates:
            raise ValueError(
                f"Unsupported currency: {currency}. "
                f"Supported currencies: {', '.join(self.supported_currencies)}"
            )
        return self._rates[currency]

    def get_rate_from_usd(self, currency: str) -> float:
        """
        Get the exchange rate from USD to a currency.

        Args:
            currency: Currency code (e.g., 'EUR', 'GBP')

        Returns:
            Exchange rate from USD
        """
        return 1.0 / self.get_rate_to_usd(currency)

    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """
        Convert an amount from a currency to USD.

        Args:
            amount: Amount to convert
            from_currency: Source currency code

        Returns:
            Amount in USD
        """
        rate = self.get_rate_to_usd(from_currency)
        return amount * rate

    def convert_from_usd(self, amount: float, to_currency: str) -> float:
        """
        Convert an amount from USD to another currency.

        Args:
            amount: Amount in USD
            to_currency: Target currency code

        Returns:
            Amount in target currency
        """
        rate = self.get_rate_from_usd(to_currency)
        return amount * rate

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert an amount between any two currencies.

        Converts through USD as the base currency.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Converted amount
        """
        if from_currency.upper() == to_currency.upper():
            return amount
        usd_amount = self.convert_to_usd(amount, from_currency)
        return self.convert_from_usd(usd_amount, to_currency)

    def set_rate(self, currency: str, rate_to_usd: float):
        """
        Set or update an exchange rate.

        Args:
            currency: Currency code
            rate_to_usd: Exchange rate to USD

        Raises:
            ValueError: If rate is not positive
        """
        if rate_to_usd <= 0:
            raise ValueError("Exchange rate must be positive")
        self._rates[currency.upper()] = rate_to_usd

    def get_all_rates(self) -> Dict[str, float]:
        """Get a copy of all exchange rates."""
        return dict(self._rates)
