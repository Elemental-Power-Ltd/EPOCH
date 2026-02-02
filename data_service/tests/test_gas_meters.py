"""Tests for gas meter conversion and sampling functions."""

import numpy as np
import pandas as pd
import pytest
from app.internal.epl_typing import HHDataFrame, NonHHDataFrame, WeatherDataFrame
from app.internal.gas_meters import assign_hh_dhw_even, hh_gas_to_monthly, monthly_to_hh_hload

TEST_RNG = np.random.default_rng(np.random.SeedSequence(3141592653))


@pytest.fixture
def gas_df() -> HHDataFrame:
    """Get an example halfhourly dataframe."""
    rng = TEST_RNG
    timestamps = pd.date_range(start="2024-01-01", periods=48 * 31 * 3, freq="30min")
    consumption = rng.uniform(1, 100, size=len(timestamps))
    hdd = rng.uniform(1, 20, size=len(timestamps))

    return HHDataFrame(
        pd.DataFrame(
            {"consumption": consumption, "hdd": hdd, "end_ts": timestamps + pd.Timedelta(minutes=30)}, index=timestamps
        )
    )


@pytest.fixture
def monthly_gas_df(gas_df: HHDataFrame) -> NonHHDataFrame:
    """Get an example resampled monthly dataframe."""
    return hh_gas_to_monthly(gas_df)


@pytest.fixture
def weather_df() -> WeatherDataFrame:
    """Get a fake weather dataframe."""
    rng = TEST_RNG

    timestamps = pd.date_range(start="2024-01-01", periods=24 * 31 * 3, freq="1h")
    temp = rng.uniform(-10, 30, size=len(timestamps))
    humidity = rng.uniform(30, 80, size=len(timestamps))
    solarradiation = rng.uniform(0, 100, size=len(timestamps))
    pressure = rng.uniform(980, 1050, size=len(timestamps))
    windspeed = rng.uniform(0, 10, size=len(timestamps))
    return WeatherDataFrame(
        pd.DataFrame(
            {
                "temp": temp,
                "humidity": humidity,
                "solarradiation": solarradiation,
                "pressure": pressure,
                "windspeed": windspeed,
            },
            index=timestamps,
        )
    )


class TestHHGasToMonthly:
    """Test resampling half hourly gas to monthly."""

    def test_output_columns(self, gas_df: HHDataFrame) -> None:
        """Test if the output dataframe has the expected columns."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        assert "start_ts" in monthly_gas_df.columns
        assert "end_ts" in monthly_gas_df.columns
        assert "days" in monthly_gas_df.columns

    def test_output_data(self, gas_df: HHDataFrame) -> None:
        """Test if the output dataframe contains valid data."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        assert pytest.approx(monthly_gas_df["consumption"].sum()) == gas_df["consumption"].sum()
        assert pytest.approx(monthly_gas_df["days"].sum()) == len(gas_df) / 48

    def test_start_end_dates(self, gas_df: HHDataFrame) -> None:
        """Test if start_ts and end_ts are within the expected range."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        assert (monthly_gas_df["start_ts"] >= gas_df.index.min()).all()
        assert (monthly_gas_df["end_ts"] <= gas_df.index.max() + pd.Timedelta(minutes=30)).all()

    def test_days_calculation(self, gas_df: HHDataFrame) -> None:
        """Test if the days column is correctly calculated."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        expected_days = (monthly_gas_df["end_ts"] - monthly_gas_df["start_ts"]).dt.total_seconds() / 86400
        np.testing.assert_allclose(monthly_gas_df["days"], expected_days, rtol=1e-5)


class TestAssignDHWEven:
    """Test assigning domestic hot water evenly."""

    def test_output_columns(self, gas_df: HHDataFrame) -> None:
        """Test if the output dataframe has the expected columns."""
        dhw_kwh = 10
        hdd_kwh = 0.5
        result_df = assign_hh_dhw_even(gas_df, dhw_kwh, hdd_kwh)
        assert "dhw" in result_df.columns
        assert "heating" in result_df.columns

    def test_dhw_calculation(self, gas_df: HHDataFrame) -> None:
        """Test if the dhw column is correctly calculated."""
        dhw_kwh = 10
        hdd_kwh = 0.5
        result_df = assign_hh_dhw_even(gas_df, dhw_kwh, hdd_kwh)
        expected_dhw = dhw_kwh * gas_df["timedelta"] / pd.Timedelta(days=1)  # type: ignore
        np.testing.assert_allclose(result_df["dhw"], expected_dhw, rtol=1e-5)

    def test_heating_calculation(self, gas_df: HHDataFrame) -> None:
        """Test if the heating column is correctly calculated."""
        dhw_kwh = 10
        hdd_kwh = 0.5
        result_df = assign_hh_dhw_even(gas_df, dhw_kwh, hdd_kwh)
        expected_heating = gas_df["hdd"] * hdd_kwh
        np.testing.assert_allclose(result_df["heating"], expected_heating, rtol=1e-5)

    def test_index_type(self, gas_df: HHDataFrame) -> None:
        """Test if the input dataframe has a DatetimeIndex."""
        dhw_kwh = 10
        hdd_kwh = 0.5
        with pytest.raises(AssertionError):
            assign_hh_dhw_even(HHDataFrame(gas_df.reset_index()), dhw_kwh, hdd_kwh)


class TestMonthlyToHHHload:
    """Test that we can upsample monthly data to half hourly heating loads."""

    def test_output_columns(self, gas_df: HHDataFrame, weather_df: WeatherDataFrame) -> None:
        """Test if the output dataframe has the expected columns."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        result_df = monthly_to_hh_hload(monthly_gas_df, weather_df)
        assert "dhw" in result_df.columns
        assert "heating" in result_df.columns
        assert "predicted" in result_df.columns

    def test_dhw_calculation(self, gas_df: HHDataFrame, weather_df: WeatherDataFrame) -> None:
        """Test if the dhw column is correctly calculated."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        result_df = monthly_to_hh_hload(monthly_gas_df, weather_df)
        assert "dhw" in result_df.columns
        assert result_df["dhw"].sum() >= 0

    def test_heating_calculation(self, gas_df: HHDataFrame, weather_df: WeatherDataFrame) -> None:
        """Test if the heating column is correctly calculated."""
        monthly_gas_df = hh_gas_to_monthly(gas_df)
        result_df = monthly_to_hh_hload(monthly_gas_df, weather_df)
        assert "heating" in result_df.columns
        assert result_df["heating"].sum() >= 0
