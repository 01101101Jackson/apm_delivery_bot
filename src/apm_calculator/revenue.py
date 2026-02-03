"""Revenue calculation module."""

from dataclasses import dataclass
from typing import Optional

from .types import RevenueInput, RevenueInputType
from .exchange_rates import ExchangeRateManager


@dataclass
class RevenueCalculation:
    """Normalized revenue values in USD."""
    monthly_usd: float
    yearly_usd: float
    contract_duration_months: Optional[int] = None
    total_contract_usd: Optional[float] = None


def calculate_revenue(
    revenue_input: RevenueInput,
    exchange_manager: ExchangeRateManager
) -> RevenueCalculation:
    """
    Calculate normalized revenue values in USD.

    Revenue is NOT scaled by FTE - it represents the full contract value.

    Args:
        revenue_input: Revenue input configuration
        exchange_manager: Exchange rate manager for currency conversion

    Returns:
        RevenueCalculation with monthly and yearly USD values
    """
    # Convert revenue amount to USD
    amount_usd = exchange_manager.convert_to_usd(
        revenue_input.amount,
        revenue_input.currency
    )

    # Normalize to monthly and yearly based on input type
    if revenue_input.input_type == RevenueInputType.HOURLY:
        # Hourly rate -> monthly = rate * hours_per_month
        monthly_usd = amount_usd * revenue_input.hours_per_month
        yearly_usd = monthly_usd * 12

    elif revenue_input.input_type == RevenueInputType.MONTHLY:
        monthly_usd = amount_usd
        yearly_usd = monthly_usd * 12

    elif revenue_input.input_type == RevenueInputType.ANNUAL:
        yearly_usd = amount_usd
        monthly_usd = yearly_usd / 12

    elif revenue_input.input_type == RevenueInputType.FIXED_PRICE:
        # Fixed price over contract duration
        # Total revenue is the fixed price
        total_contract_usd = amount_usd
        duration = revenue_input.contract_duration_months

        # Monthly revenue = total / duration
        monthly_usd = total_contract_usd / duration
        yearly_usd = monthly_usd * 12

        return RevenueCalculation(
            monthly_usd=monthly_usd,
            yearly_usd=yearly_usd,
            contract_duration_months=duration,
            total_contract_usd=total_contract_usd
        )

    else:
        raise ValueError(f"Unknown revenue input type: {revenue_input.input_type}")

    return RevenueCalculation(
        monthly_usd=monthly_usd,
        yearly_usd=yearly_usd
    )
