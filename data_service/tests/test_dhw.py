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
    date_range = pd.date_range(start=start_date, periods=periods, freq=pd.Timedelta(minutes=30))
    df = pd.DataFrame({"consumption": np.random.rand(periods) * 10, "hdd": np.random.rand(periods) * 5}, index=date_range)
    return HHDataFrame(df)


@pytest.fixture
def sample_df() -> HHDataFrame:
    return create_sample_df("2024-01-01", 48)  # 24 hours of data


# Test classes


class TestMiddaySinWeights:
    def test_basic_functionality(self, sample_df: HHDataFrame) -> None:
        weights = midday_sin_weights(sample_df)

        assert len(weights) == 48
        assert np.all(weights >= 0)
        assert np.argmax(weights) == 24  # Peak at 12:00
        assert weights[0] == weights[-1] == 0  # Zero at midnight

    def test_gamma_effect(self) -> None:
        df = create_sample_df("2024-01-01", 48)
        weights_low_gamma = midday_sin_weights(df, gamma=0.5)
        weights_high_gamma = midday_sin_weights(df, gamma=2)

        assert np.sum(weights_low_gamma) > np.sum(weights_high_gamma)

    def test_all_positive(self) -> None:
        df = create_sample_df("2024-01-01", 48)
        weights = midday_sin_weights(df, gamma=0.5)

        assert np.all(weights >= 0)


class TestAssignHHDHWEven:
    def test_basic_functionality(self, sample_df: HHDataFrame) -> None:
        result = assign_hh_dhw_even(sample_df, dhw_kwh=10, hdd_kwh=2)

        assert "dhw" in result.columns
        assert "heating" in result.columns
        assert "predicted" in result.columns
        assert np.isclose(result["dhw"].sum(), 10)
        assert np.allclose(result["heating"], sample_df["hdd"] * 2)
        assert np.allclose(result["predicted"], result["dhw"] + result["heating"])

    def test_empty_df(self) -> None:
        empty_df = create_sample_df("2024-01-01", 0)
        with pytest.raises(ValueError, match="Can't assign DHW to an empty DataFrame"):
            assign_hh_dhw_even(empty_df, dhw_kwh=10, hdd_kwh=2)


class TestAssignHHDHWGreedy:
    def test_basic_functionality(self, sample_df: HHDataFrame) -> None:
        result = assign_hh_dhw_greedy(sample_df, dhw_kwh=10, hdd_kwh=2)

        assert "dhw" in result.columns
        assert "heating" in result.columns
        assert np.isclose(result["dhw"].sum(), 10)
        assert np.all(result["dhw"] <= result["consumption"])
        assert np.allclose(result["heating"], result["consumption"] - result["dhw"])

    def test_zero_dhw(self, sample_df: HHDataFrame) -> None:
        result = assign_hh_dhw_greedy(sample_df, dhw_kwh=0, hdd_kwh=2)
        assert np.all(result["dhw"] == 0)
        assert np.allclose(result["heating"], result["consumption"])


class TestAssignHHDHWPoisson:
    @pytest.fixture
    def weights(self) -> np.ndarray:
        return np.ones(48) * 0.1

    def test_basic_functionality(self, sample_df: HHDataFrame, weights: np.ndarray) -> None:
        rng = np.random.default_rng(42)
        result = assign_hh_dhw_poisson(sample_df, weights, dhw_kwh=1, hdd_kwh=2, max_output=30, rng=rng)

        assert "dhw" in result.columns
        assert "heating" in result.columns
        assert "predicted" in result.columns
        assert np.all(result["predicted"] <= 30)
        assert np.all(result["heating"] <= result["hdd"] * 2)

    def test_reproducibility(self, sample_df: HHDataFrame, weights: np.ndarray) -> None:
        rng = np.random.default_rng(42)
        result1 = assign_hh_dhw_poisson(sample_df, weights, dhw_kwh=1, hdd_kwh=2, max_output=30, rng=rng)
        result2 = assign_hh_dhw_poisson(sample_df, weights, dhw_kwh=1, hdd_kwh=2, max_output=30, rng=rng)

        assert np.allclose(result1["dhw"], result2["dhw"])
