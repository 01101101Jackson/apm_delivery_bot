"""Command-line interface for APM Calculator."""

import argparse
import json
import sys
from typing import Optional

from .calculator import APMCalculator
from .types import RevenueInputType, CostRatePeriod


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="apm-calc",
        description="APM / Margin Calculator for project profitability analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monthly revenue and cost in USD
  apm-calc --revenue-type monthly --revenue-amount 15000 --revenue-currency USD \\
           --cost-period monthly --cost-amount 8000 --cost-currency USD \\
           --allocation 1.0 --uplift 0.25 --reporting-currency USD

  # Hourly rates with different currencies
  apm-calc --revenue-type hourly --revenue-amount 150 --revenue-currency EUR \\
           --cost-period hourly --cost-amount 75 --cost-currency GBP \\
           --allocation 0.5 --uplift 0.20 --reporting-currency USD

  # Fixed price contract
  apm-calc --revenue-type fixed_price --revenue-amount 100000 --revenue-currency USD \\
           --contract-duration 6 \\
           --cost-period monthly --cost-amount 10000 --cost-currency USD \\
           --allocation 1.0 --uplift 0.25 --reporting-currency USD

  # List supported currencies
  apm-calc --list-currencies

  # Output as JSON
  apm-calc --revenue-type monthly --revenue-amount 15000 --revenue-currency USD \\
           --cost-period monthly --cost-amount 8000 --cost-currency USD \\
           --allocation 1.0 --uplift 0.25 --reporting-currency USD --json
"""
    )

    # Revenue inputs
    revenue_group = parser.add_argument_group("Revenue Inputs")
    revenue_group.add_argument(
        "--revenue-type", "-rt",
        choices=["hourly", "monthly", "annual", "fixed_price"],
        help="Revenue input type"
    )
    revenue_group.add_argument(
        "--revenue-amount", "-ra",
        type=float,
        help="Revenue amount"
    )
    revenue_group.add_argument(
        "--revenue-currency", "-rc",
        help="Revenue currency (e.g., USD, EUR, GBP)"
    )
    revenue_group.add_argument(
        "--contract-duration", "-cd",
        type=int,
        help="Contract duration in months (required for fixed_price)"
    )

    # Cost inputs
    cost_group = parser.add_argument_group("Cost Inputs")
    cost_group.add_argument(
        "--cost-period", "-cp",
        choices=["hourly", "monthly", "annual"],
        help="Cost rate period"
    )
    cost_group.add_argument(
        "--cost-amount", "-ca",
        type=float,
        help="Cost rate amount"
    )
    cost_group.add_argument(
        "--cost-currency", "-cc",
        help="Cost currency (e.g., USD, EUR, GBP)"
    )
    cost_group.add_argument(
        "--allocation", "-a",
        type=float,
        default=1.0,
        help="FTE allocation (0-1, default: 1.0)"
    )

    # Uplift
    parser.add_argument(
        "--uplift", "-u",
        type=float,
        default=0.0,
        help="Overhead/uplift percentage (e.g., 0.25 for 25%%, default: 0)"
    )

    # Reporting
    parser.add_argument(
        "--reporting-currency", "-o",
        help="Reporting currency for output (e.g., USD, EUR)"
    )

    # Optional
    parser.add_argument(
        "--hours-per-month",
        type=float,
        default=160.0,
        dest="hours_per_month",
        help="Hours per month for hourly rate conversion (default: 160)"
    )

    # Output format
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON"
    )

    # Utility commands
    parser.add_argument(
        "--list-currencies",
        action="store_true",
        help="List supported currencies and exit"
    )
    parser.add_argument(
        "--list-rates",
        action="store_true",
        help="List exchange rates and exit"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )

    return parser


def validate_args(args) -> Optional[str]:
    """Validate arguments, return error message if invalid."""
    # Skip validation for utility commands
    if args.list_currencies or args.list_rates or args.interactive:
        return None

    required = [
        ("--revenue-type", args.revenue_type),
        ("--revenue-amount", args.revenue_amount),
        ("--revenue-currency", args.revenue_currency),
        ("--cost-period", args.cost_period),
        ("--cost-amount", args.cost_amount),
        ("--cost-currency", args.cost_currency),
        ("--reporting-currency", args.reporting_currency),
    ]

    missing = [name for name, value in required if value is None]
    if missing:
        return f"Missing required arguments: {', '.join(missing)}"

    if args.revenue_type == "fixed_price" and args.contract_duration is None:
        return "--contract-duration is required for fixed_price revenue type"

    if not 0 <= args.allocation <= 1:
        return "--allocation must be between 0 and 1"

    if args.uplift < 0:
        return "--uplift cannot be negative"

    return None


def format_currency(amount: float, currency: str) -> str:
    """Format a currency amount."""
    return f"{currency} {amount:,.2f}"


def format_percent(value: float) -> str:
    """Format a percentage value."""
    return f"{value * 100:.2f}%"


def print_result(result, as_json: bool = False):
    """Print calculation results."""
    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    currency = result.reporting_currency

    print("\n" + "=" * 60)
    print("APM CALCULATION RESULTS")
    print("=" * 60)

    print(f"\nReporting Currency: {currency}")

    print("\n--- Revenue ---")
    print(f"  Monthly:  {format_currency(result.revenue_monthly, currency)}")
    print(f"  Yearly:   {format_currency(result.revenue_yearly, currency)}")

    print("\n--- Base Cost (FTE-adjusted, before uplift) ---")
    print(f"  Monthly:  {format_currency(result.base_cost_monthly, currency)}")
    print(f"  Yearly:   {format_currency(result.base_cost_yearly, currency)}")

    print("\n--- Loaded Cost (after uplift) ---")
    print(f"  Monthly:  {format_currency(result.loaded_cost_monthly, currency)}")
    print(f"  Yearly:   {format_currency(result.loaded_cost_yearly, currency)}")

    print("\n--- APM / Margin ---")
    print(f"  Monthly:  {format_percent(result.apm_monthly)}")
    print(f"  Yearly:   {format_percent(result.apm_yearly)}")

    if result.contract_duration_months is not None:
        print(f"\n--- Fixed Price Contract ({result.contract_duration_months} months) ---")
        print(f"  Total Revenue:      {format_currency(result.total_revenue_contract, currency)}")
        print(f"  Total Loaded Cost:  {format_currency(result.total_loaded_cost_contract, currency)}")
        print(f"  Contract APM:       {format_percent(result.apm_contract)}")

    print("\n" + "=" * 60)


def run_interactive(calculator: APMCalculator):
    """Run the calculator in interactive mode."""
    print("\n" + "=" * 60)
    print("APM CALCULATOR - Interactive Mode")
    print("=" * 60)

    print("\nSupported currencies:", ", ".join(calculator.supported_currencies))

    def get_choice(prompt: str, choices: list) -> str:
        """Get a choice from a list."""
        while True:
            print(f"\n{prompt}")
            for i, choice in enumerate(choices, 1):
                print(f"  {i}. {choice}")
            try:
                idx = int(input("Enter choice number: ")) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except (ValueError, IndexError):
                pass
            print("Invalid choice, please try again.")

    def get_float(prompt: str, min_val: float = None, max_val: float = None) -> float:
        """Get a float value."""
        while True:
            try:
                value = float(input(f"{prompt}: "))
                if min_val is not None and value < min_val:
                    print(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"Value must be at most {max_val}")
                    continue
                return value
            except ValueError:
                print("Please enter a valid number.")

    def get_int(prompt: str, min_val: int = None) -> int:
        """Get an integer value."""
        while True:
            try:
                value = int(input(f"{prompt}: "))
                if min_val is not None and value < min_val:
                    print(f"Value must be at least {min_val}")
                    continue
                return value
            except ValueError:
                print("Please enter a valid integer.")

    def get_currency(prompt: str) -> str:
        """Get a currency code."""
        supported = calculator.supported_currencies
        while True:
            currency = input(f"{prompt} ({', '.join(supported)}): ").upper()
            if currency in supported:
                return currency
            print(f"Unsupported currency. Please choose from: {', '.join(supported)}")

    # Revenue inputs
    print("\n--- REVENUE INPUTS ---")
    revenue_type = get_choice("Select revenue input type:", calculator.revenue_input_types)
    revenue_amount = get_float("Enter revenue amount", min_val=0)
    revenue_currency = get_currency("Enter revenue currency")

    contract_duration = None
    if revenue_type == "fixed_price":
        contract_duration = get_int("Enter contract duration (months)", min_val=1)

    # Cost inputs
    print("\n--- COST INPUTS ---")
    cost_period = get_choice("Select cost rate period:", calculator.cost_rate_periods)
    cost_amount = get_float("Enter cost rate amount", min_val=0)
    cost_currency = get_currency("Enter cost currency")
    allocation = get_float("Enter FTE allocation (0-1)", min_val=0, max_val=1)

    # Uplift
    print("\n--- UPLIFT ---")
    uplift = get_float("Enter uplift/overhead percentage (e.g., 0.25 for 25%)", min_val=0)

    # Hours per month (if hourly rates used)
    hours_per_month = 160.0
    if revenue_type == "hourly" or cost_period == "hourly":
        use_default = input("\nUse default hours per month (160)? [Y/n]: ").strip().lower()
        if use_default == "n":
            hours_per_month = get_float("Enter hours per month", min_val=1)

    # Reporting currency
    print("\n--- REPORTING ---")
    reporting_currency = get_currency("Enter reporting currency for output")

    # Calculate
    try:
        result = calculator.calculate(
            revenue_type=revenue_type,
            revenue_amount=revenue_amount,
            revenue_currency=revenue_currency,
            cost_rate_period=cost_period,
            cost_amount=cost_amount,
            cost_currency=cost_currency,
            allocation_fte=allocation,
            uplift_percent=uplift,
            reporting_currency=reporting_currency,
            hours_per_month=hours_per_month,
            contract_duration_months=contract_duration,
        )
        print_result(result)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    calculator = APMCalculator()

    # Handle utility commands
    if args.list_currencies:
        print("Supported currencies:")
        for currency in calculator.supported_currencies:
            print(f"  {currency}")
        return

    if args.list_rates:
        print("Exchange rates (currency -> USD):")
        for currency, rate in sorted(calculator.get_exchange_rates().items()):
            print(f"  {currency}: {rate}")
        return

    if args.interactive:
        run_interactive(calculator)
        return

    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Calculate
    try:
        result = calculator.calculate(
            revenue_type=args.revenue_type,
            revenue_amount=args.revenue_amount,
            revenue_currency=args.revenue_currency,
            cost_rate_period=args.cost_period,
            cost_amount=args.cost_amount,
            cost_currency=args.cost_currency,
            allocation_fte=args.allocation,
            uplift_percent=args.uplift,
            reporting_currency=args.reporting_currency,
            hours_per_month=args.hours_per_month,
            contract_duration_months=args.contract_duration,
        )
        print_result(result, as_json=args.json)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
