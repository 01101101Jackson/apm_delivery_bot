"""Cost calculation module."""

from dataclasses import dataclass

from .types import CostInput, CostRatePeriod
from .exchange_rates import ExchangeRateManager


@dataclass
class CostCalculation:
    """Normalized cost values in USD."""
    # Base cost (after FTE scaling, before uplift)
    base_cost_monthly_usd: float
    base_cost_yearly_usd: float

    # Loaded cost (after uplift)
    loaded_cost_monthly_usd: float
    loaded_cost_yearly_usd: float


def calculate_cost(
    cost_input: CostInput,
    uplift_percent: float,
    exchange_manager: ExchangeRateManager
) -> CostCalculation:
    """
    Calculate normalized cost values in USD.

    Cost IS scaled by FTE allocation.
    Uplift is applied after FTE scaling.

    Formula:
        Base Cost = Rate * FTE
        Loaded Cost = Base Cost * (1 + Uplift%)

    Args:
        cost_input: Cost input configuration
        uplift_percent: Overhead/uplift percentage (e.g., 0.25 for 25%)
        exchange_manager: Exchange rate manager for currency conversion

    Returns:
        CostCalculation with base and loaded costs in USD

    Raises:
        ValueError: If uplift_percent is negative
    """
    if uplift_percent < 0:
        raise ValueError("Uplift percentage cannot be negative")

    # Convert cost amount to USD
    rate_usd = exchange_manager.convert_to_usd(
        cost_input.amount,
        cost_input.currency
    )

    # Normalize to monthly rate
    if cost_input.rate_period == CostRatePeriod.HOURLY:
        # Hourly rate -> monthly = rate * hours_per_month
        monthly_rate_usd = rate_usd * cost_input.hours_per_month

    elif cost_input.rate_period == CostRatePeriod.MONTHLY:
        monthly_rate_usd = rate_usd

    elif cost_input.rate_period == CostRatePeriod.ANNUAL:
        monthly_rate_usd = rate_usd / 12

    else:
        raise ValueError(f"Unknown cost rate period: {cost_input.rate_period}")

    # Apply FTE scaling to base cost
    base_cost_monthly_usd = monthly_rate_usd * cost_input.allocation_fte
    base_cost_yearly_usd = base_cost_monthly_usd * 12

    # Apply uplift to get loaded cost
    loaded_cost_monthly_usd = base_cost_monthly_usd * (1 + uplift_percent)
    loaded_cost_yearly_usd = base_cost_yearly_usd * (1 + uplift_percent)

    return CostCalculation(
        base_cost_monthly_usd=base_cost_monthly_usd,
        base_cost_yearly_usd=base_cost_yearly_usd,
        loaded_cost_monthly_usd=loaded_cost_monthly_usd,
        loaded_cost_yearly_usd=loaded_cost_yearly_usd
    )
