"""Main APM Calculator class integrating all calculation modules."""

from typing import Dict, Optional

from .types import (
    RevenueInput,
    RevenueInputType,
    CostInput,
    CostRatePeriod,
    CalculationResult
)
from .exchange_rates import ExchangeRateManager
from .revenue import calculate_revenue
from .cost import calculate_cost
from .apm import calculate_apm


class APMCalculator:
    """
    APM / Margin Calculator for project profitability analysis.

    Calculates project margin by modelling revenue vs consultant cost,
    supporting different commercial models, currencies, time allocations,
    and overhead uplift.

    All calculations are performed in USD, then converted to reporting currency.
    """

    DEFAULT_HOURS_PER_MONTH = 160.0

    def __init__(self, exchange_rates: Dict[str, float] = None):
        """
        Initialize the APM Calculator.

        Args:
            exchange_rates: Optional custom exchange rates (currency -> USD).
                           If None, uses default rates.
        """
        self._exchange_manager = ExchangeRateManager(exchange_rates)

    @property
    def supported_currencies(self) -> list:
        """Get list of supported currency codes."""
        return self._exchange_manager.supported_currencies

    @property
    def revenue_input_types(self) -> list:
        """Get list of revenue input type options."""
        return [t.value for t in RevenueInputType]

    @property
    def cost_rate_periods(self) -> list:
        """Get list of cost rate period options."""
        return [p.value for p in CostRatePeriod]

    def set_exchange_rate(self, currency: str, rate_to_usd: float):
        """
        Set or update an exchange rate.

        Args:
            currency: Currency code (e.g., 'EUR')
            rate_to_usd: Exchange rate to USD
        """
        self._exchange_manager.set_rate(currency, rate_to_usd)

    def get_exchange_rates(self) -> Dict[str, float]:
        """Get all current exchange rates."""
        return self._exchange_manager.get_all_rates()

    def calculate(
        self,
        # Revenue inputs
        revenue_type: str,
        revenue_amount: float,
        revenue_currency: str,
        # Cost inputs
        cost_rate_period: str,
        cost_amount: float,
        cost_currency: str,
        allocation_fte: float,
        # Uplift
        uplift_percent: float,
        # Reporting
        reporting_currency: str,
        # Optional
        hours_per_month: float = None,
        contract_duration_months: int = None,
    ) -> CalculationResult:
        """
        Calculate APM and all related values.

        Args:
            revenue_type: Revenue input type ('hourly', 'monthly', 'annual', 'fixed_price')
            revenue_amount: Revenue amount in revenue_currency
            revenue_currency: Currency code for revenue
            cost_rate_period: Cost rate period ('hourly', 'monthly', 'annual')
            cost_amount: Cost rate amount in cost_currency
            cost_currency: Currency code for cost
            allocation_fte: FTE allocation (0 to 1)
            uplift_percent: Overhead/uplift percentage (e.g., 0.25 for 25%)
            reporting_currency: Currency code for output
            hours_per_month: Hours per month (default: 160)
            contract_duration_months: Contract duration (required for fixed_price)

        Returns:
            CalculationResult with all calculated values in reporting currency
        """
        if hours_per_month is None:
            hours_per_month = self.DEFAULT_HOURS_PER_MONTH

        # Parse enum values
        rev_type = RevenueInputType(revenue_type.lower())
        cost_period = CostRatePeriod(cost_rate_period.lower())

        # Create input objects
        revenue_input = RevenueInput(
            input_type=rev_type,
            amount=revenue_amount,
            currency=revenue_currency.upper(),
            hours_per_month=hours_per_month,
            contract_duration_months=contract_duration_months
        )

        cost_input = CostInput(
            rate_period=cost_period,
            amount=cost_amount,
            currency=cost_currency.upper(),
            hours_per_month=hours_per_month,
            allocation_fte=allocation_fte
        )

        # Calculate revenue and cost in USD
        revenue_calc = calculate_revenue(revenue_input, self._exchange_manager)
        cost_calc = calculate_cost(cost_input, uplift_percent, self._exchange_manager)

        # Calculate APM
        apm_monthly = calculate_apm(
            revenue_calc.monthly_usd,
            cost_calc.loaded_cost_monthly_usd
        )
        apm_yearly = calculate_apm(
            revenue_calc.yearly_usd,
            cost_calc.loaded_cost_yearly_usd
        )

        # Convert all values to reporting currency
        reporting_currency = reporting_currency.upper()

        revenue_monthly = self._exchange_manager.convert_from_usd(
            revenue_calc.monthly_usd, reporting_currency
        )
        revenue_yearly = self._exchange_manager.convert_from_usd(
            revenue_calc.yearly_usd, reporting_currency
        )
        base_cost_monthly = self._exchange_manager.convert_from_usd(
            cost_calc.base_cost_monthly_usd, reporting_currency
        )
        base_cost_yearly = self._exchange_manager.convert_from_usd(
            cost_calc.base_cost_yearly_usd, reporting_currency
        )
        loaded_cost_monthly = self._exchange_manager.convert_from_usd(
            cost_calc.loaded_cost_monthly_usd, reporting_currency
        )
        loaded_cost_yearly = self._exchange_manager.convert_from_usd(
            cost_calc.loaded_cost_yearly_usd, reporting_currency
        )

        # Build result
        result = CalculationResult(
            reporting_currency=reporting_currency,
            revenue_monthly=revenue_monthly,
            revenue_yearly=revenue_yearly,
            base_cost_monthly=base_cost_monthly,
            base_cost_yearly=base_cost_yearly,
            loaded_cost_monthly=loaded_cost_monthly,
            loaded_cost_yearly=loaded_cost_yearly,
            apm_monthly=apm_monthly,
            apm_yearly=apm_yearly,
        )

        # Handle fixed price contract
        if rev_type == RevenueInputType.FIXED_PRICE:
            duration = revenue_calc.contract_duration_months

            # Total contract values
            total_revenue_usd = revenue_calc.total_contract_usd
            total_loaded_cost_usd = cost_calc.loaded_cost_monthly_usd * duration

            # APM for full contract
            apm_contract = calculate_apm(total_revenue_usd, total_loaded_cost_usd)

            # Convert to reporting currency
            total_revenue_reporting = self._exchange_manager.convert_from_usd(
                total_revenue_usd, reporting_currency
            )
            total_loaded_cost_reporting = self._exchange_manager.convert_from_usd(
                total_loaded_cost_usd, reporting_currency
            )

            result.contract_duration_months = duration
            result.total_revenue_contract = total_revenue_reporting
            result.total_loaded_cost_contract = total_loaded_cost_reporting
            result.apm_contract = apm_contract

        return result

    def calculate_from_inputs(
        self,
        revenue_input: RevenueInput,
        cost_input: CostInput,
        uplift_percent: float,
        reporting_currency: str
    ) -> CalculationResult:
        """
        Calculate APM using pre-built input objects.

        Args:
            revenue_input: Revenue input configuration
            cost_input: Cost input configuration
            uplift_percent: Overhead/uplift percentage
            reporting_currency: Currency code for output

        Returns:
            CalculationResult with all calculated values
        """
        return self.calculate(
            revenue_type=revenue_input.input_type.value,
            revenue_amount=revenue_input.amount,
            revenue_currency=revenue_input.currency,
            cost_rate_period=cost_input.rate_period.value,
            cost_amount=cost_input.amount,
            cost_currency=cost_input.currency,
            allocation_fte=cost_input.allocation_fte,
            uplift_percent=uplift_percent,
            reporting_currency=reporting_currency,
            hours_per_month=revenue_input.hours_per_month,
            contract_duration_months=revenue_input.contract_duration_months
        )
