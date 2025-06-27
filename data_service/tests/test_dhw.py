"""Test Domestic Hot Water assigning through various methods."""

import numpy as np
import pandas as pd
import pytest

from app.internal.epl_typing import HHDataFrame
from app.internal.gas_meters import (
    assign_hh_dhw_even,
    assign_hh_dhw_greedy,
    assign_hh_dhw_poisson,
    midday_sin_weights,
)


def create_sample_df(start_date: str, periods: int) -> HHDataFrame:
    """Create a dataframe with random data."""
    date_range = pd.date_range(start=start_date, periods=periods, freq=pd.Timedelta(minutes=30))
    df = pd.DataFrame({"consumption": np.random.rand(periods) * 10, "hdd": np.random.rand(periods) * 5}, index=date_range)
    return HHDataFrame(df)


@pytest.fixture
def sample_df() -> HHDataFrame:
    """Get 48 hours of sample data."""
    return create_sample_df("2024-01-01", 48)  # 24 hours of data


class TestMiddaySinWeights:
    """Test weighting DHW with sinusoidal weights."""

    def test_basic_functionality(self, sample_df: HHDataFrame) -> None:
        """Test that the array shapes are reasonable."""
        weights = midday_sin_weights(sample_df)

        assert len(weights) == 48
        assert np.all(weights >= 0)
        assert np.argmax(weights) == 24  # Peak at 12:00
        assert weights[0] == weights[-1] == 0  # Zero at midnight

    def test_gamma_effect(self) -> None:
        """Test that we can change the shape of the curve."""
        df = create_sample_df("2024-01-01", 48)
        weights_low_gamma = midday_sin_weights(df, gamma=0.5)
        weights_high_gamma = midday_sin_weights(df, gamma=2)

        assert np.sum(weights_low_gamma) > np.sum(weights_high_gamma)

    def test_all_positive(self) -> None:
        """Test that we don't predict negative usage."""
        df = create_sample_df("2024-01-01", 48)
        weights = midday_sin_weights(df, gamma=0.5)

        assert np.all(weights >= 0)


class TestAssignHHDHWEven:
    """Test that we can assign DHW evenly to half hourly data."""

    def test_basic_functionality(self, sample_df: HHDataFrame) -> None:
        """Test that we haven't mangled the shape of the data."""
        result = assign_hh_dhw_even(sample_df, dhw_kwh=10, hdd_kwh=2)

        assert "dhw" in result.columns
        assert "heating" in result.columns
        assert "predicted" in result.columns
        assert np.isclose(result["dhw"].sum(), 10)
        assert np.allclose(result["heating"], sample_df["hdd"] * 2)
        assert np.allclose(result["predicted"], result["dhw"] + result["heating"])

    def test_empty_df(self) -> None:
        """Test that we identify empty dfs."""
        empty_df = create_sample_df("2024-01-01", 0)
        with pytest.raises(ValueError, match="Can't assign DHW to an empty DataFrame"):
            assign_hh_dhw_even(empty_df, dhw_kwh=10, hdd_kwh=2)


class TestAssignHHDHWGreedy:
    """Test that we can assign DHW greedily to HH data."""

    def test_basic_functionality(self, sample_df: HHDataFrame) -> None:
        """Test that we haven't mangled the shape of the dataframe."""
        result = assign_hh_dhw_greedy(sample_df, dhw_kwh=10, hdd_kwh=2)

        assert "dhw" in result.columns
        assert "heating" in result.columns
        assert np.isclose(result["dhw"].sum(), 10)
        assert np.all(result["dhw"] <= result["consumption"])
        assert np.allclose(result["heating"], result["consumption"] - result["dhw"])

    def test_zero_dhw(self, sample_df: HHDataFrame) -> None:
        """Test that with zero DHW per day, we get zero DHW."""
        result = assign_hh_dhw_greedy(sample_df, dhw_kwh=0, hdd_kwh=2)
        assert np.all(result["dhw"] == 0)
        assert np.allclose(result["heating"], result["consumption"])


class TestAssignHHDHWPoisson:
    """Test random poisson assigning of DHW."""

    @pytest.fixture
    def weights(self) -> np.ndarray:
        """Get some reasonable even weights."""
        return np.ones(48) * 0.1

    def test_basic_functionality(self, sample_df: HHDataFrame, weights: np.ndarray) -> None:
        """Test that the shape of the dataframe is sane."""
        rng = np.random.default_rng(42)
        result = assign_hh_dhw_poisson(sample_df, weights, dhw_event_size=1, hdd_kwh=2, max_output=30, rng=rng)

        assert "dhw" in result.columns
        assert "heating" in result.columns
        assert "predicted" in result.columns
        assert np.all(result["predicted"] <= 30)
        assert np.all(result["heating"] <= result["hdd"] * 2)

    def test_reproducibility(self, sample_df: HHDataFrame, weights: np.ndarray) -> None:
        """Test that we can re-use an RNG."""
        rng = np.random.default_rng(42)
        result1 = assign_hh_dhw_poisson(sample_df, weights, dhw_event_size=1, hdd_kwh=2, max_output=30, rng=rng)
        result2 = assign_hh_dhw_poisson(sample_df, weights, dhw_event_size=1, hdd_kwh=2, max_output=30, rng=rng)

        assert np.allclose(result1["dhw"], result2["dhw"])
