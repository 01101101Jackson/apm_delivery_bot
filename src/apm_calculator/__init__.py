"""APM / Margin Calculator for project profitability analysis."""

from .calculator import APMCalculator
from .types import RevenueInputType, CostRatePeriod, CalculationResult

__all__ = ["APMCalculator", "RevenueInputType", "CostRatePeriod", "CalculationResult"]
__version__ = "1.0.0"
