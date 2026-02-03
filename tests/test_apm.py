"""Tests for APM calculation module."""

import pytest
from apm_calculator.apm import calculate_apm


class TestAPMCalculation:
    """Tests for APM calculation."""

    def test_basic_margin(self):
        """Basic APM calculation."""
        # Revenue: 10000, Cost: 6000
        # APM = 1 - (6000/10000) = 0.4 (40%)
        result = calculate_apm(10000, 6000)
        assert result == 0.4

    def test_zero_cost_full_margin(self):
        """Zero cost should give 100% margin."""
        result = calculate_apm(10000, 0)
        assert result == 1.0

    def test_break_even(self):
        """Cost equal to revenue should give 0% margin."""
        result = calculate_apm(10000, 10000)
        assert result == 0.0

    def test_loss_scenario(self):
        """Cost exceeding revenue should give negative margin."""
        # Revenue: 10000, Cost: 12000
        # APM = 1 - (12000/10000) = -0.2 (-20%)
        result = calculate_apm(10000, 12000)
        assert abs(result - (-0.2)) < 0.0001

    def test_typical_margin(self):
        """Test typical margin scenarios."""
        # 25% margin
        result = calculate_apm(10000, 7500)
        assert abs(result - 0.25) < 0.0001

        # 50% margin
        result = calculate_apm(10000, 5000)
        assert abs(result - 0.5) < 0.0001

    def test_zero_revenue_raises_error(self):
        """Zero revenue should raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            calculate_apm(0, 5000)

    def test_negative_revenue_raises_error(self):
        """Negative revenue should raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            calculate_apm(-10000, 5000)

    def test_small_values(self):
        """Should handle small values correctly."""
        result = calculate_apm(0.01, 0.006)
        assert abs(result - 0.4) < 0.0001

    def test_large_values(self):
        """Should handle large values correctly."""
        result = calculate_apm(10_000_000, 6_000_000)
        assert result == 0.4
