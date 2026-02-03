"""APM (margin) calculation module."""


def calculate_apm(revenue: float, loaded_cost: float) -> float:
    """
    Calculate APM (margin) from revenue and loaded cost.

    APM = 1 - (Loaded Cost / Revenue)

    A positive APM indicates profit, negative indicates loss.
    APM of 0.25 means 25% margin.
    APM of 1.0 means 100% margin (zero cost).
    APM of 0.0 means break-even.
    APM < 0 means loss.

    Args:
        revenue: Revenue amount
        loaded_cost: Loaded cost amount (after uplift)

    Returns:
        APM as a decimal (e.g., 0.25 for 25% margin)

    Raises:
        ValueError: If revenue is zero or negative
    """
    if revenue <= 0:
        raise ValueError("Revenue must be positive to calculate APM")

    return 1 - (loaded_cost / revenue)
