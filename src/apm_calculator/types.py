"""Type definitions and enums for APM Calculator."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RevenueInputType(Enum):
    """Revenue input type options."""
    HOURLY = "hourly"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    FIXED_PRICE = "fixed_price"


class CostRatePeriod(Enum):
    """Cost rate period options."""
    HOURLY = "hourly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


@dataclass
class RevenueInput:
    """Revenue input configuration."""
    input_type: RevenueInputType
    amount: float
    currency: str
    hours_per_month: float = 160.0
    contract_duration_months: Optional[int] = None

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Revenue amount must be non-negative")
        if self.hours_per_month <= 0:
            raise ValueError("Hours per month must be positive")
        if self.input_type == RevenueInputType.FIXED_PRICE:
            if self.contract_duration_months is None or self.contract_duration_months <= 0:
                raise ValueError("Contract duration must be specified and positive for fixed price revenue")


@dataclass
class CostInput:
    """Cost input configuration."""
    rate_period: CostRatePeriod
    amount: float
    currency: str
    hours_per_month: float = 160.0
    allocation_fte: float = 1.0

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Cost amount must be non-negative")
        if self.hours_per_month <= 0:
            raise ValueError("Hours per month must be positive")
        if not 0 <= self.allocation_fte <= 1:
            raise ValueError("Allocation FTE must be between 0 and 1")


@dataclass
class CalculationResult:
    """Complete calculation results in reporting currency."""
    reporting_currency: str

    # Revenue
    revenue_monthly: float
    revenue_yearly: float

    # Base cost (after FTE scaling, before uplift)
    base_cost_monthly: float
    base_cost_yearly: float

    # Loaded cost (after uplift)
    loaded_cost_monthly: float
    loaded_cost_yearly: float

    # APM / Margin
    apm_monthly: float
    apm_yearly: float

    # Fixed price specific (optional)
    contract_duration_months: Optional[int] = None
    total_revenue_contract: Optional[float] = None
    total_loaded_cost_contract: Optional[float] = None
    apm_contract: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        result = {
            "reporting_currency": self.reporting_currency,
            "revenue": {
                "monthly": round(self.revenue_monthly, 2),
                "yearly": round(self.revenue_yearly, 2),
            },
            "base_cost": {
                "monthly": round(self.base_cost_monthly, 2),
                "yearly": round(self.base_cost_yearly, 2),
            },
            "loaded_cost": {
                "monthly": round(self.loaded_cost_monthly, 2),
                "yearly": round(self.loaded_cost_yearly, 2),
            },
            "apm": {
                "monthly": round(self.apm_monthly, 4),
                "yearly": round(self.apm_yearly, 4),
            },
        }

        if self.contract_duration_months is not None:
            result["contract"] = {
                "duration_months": self.contract_duration_months,
                "total_revenue": round(self.total_revenue_contract, 2),
                "total_loaded_cost": round(self.total_loaded_cost_contract, 2),
                "apm": round(self.apm_contract, 4),
            }

        return result
