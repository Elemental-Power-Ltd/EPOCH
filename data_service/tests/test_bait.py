"""Tests for the Building Adjusted Internal Temperature algorithm."""

import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest

from app.internal.epl_typing import WeatherDataFrame
from app.internal.heating import building_adjusted_internal_temperature
from app.internal.utils import relative_to_specific_humidity

TEST_RNG = np.random.default_rng(np.random.SeedSequence(3141592653))


@pytest.fixture
def weather_df() -> WeatherDataFrame:
    """Get a reasonable fake weatheer dataframe."""
    rng = TEST_RNG
    timestamps = pd.date_range(start="2024-01-01", periods=72, freq="h")
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
                "windspeed": windspeed,
                "pressure": pressure,
            },
            index=timestamps,
        )
    )


class TestHumidityConversion:
    """Test the relative to specific humidity conversion function."""

    def test_nonsense_humidity(self) -> None:
        """Test that we reject nonsense humidities."""
        with pytest.raises(AssertionError):
            result = relative_to_specific_humidity(-100, 25.0, 1000)
        with pytest.raises(AssertionError):
            result = relative_to_specific_humidity(1000, 25.0, 1000)

        result = relative_to_specific_humidity(85, 25.0, 1013.25)
        assert result is not None

    def test_nonsense_pressures(self) -> None:
        """Test that we reject nonsense pressures."""
        with pytest.raises(AssertionError):
            result = relative_to_specific_humidity(85, 25.0, 101325)
        with pytest.raises(AssertionError):
            result = relative_to_specific_humidity(85, 25.0, 0.1)
        result = relative_to_specific_humidity(85, 25.0, 1013.25)
        assert result is not None

    def test_nonsense_temperatures(self) -> None:
        """Test that we reject nonsense temperatures."""
        with pytest.raises(AssertionError):
            result = relative_to_specific_humidity(85, -273, 1013.25)
        with pytest.raises(AssertionError):
            result = relative_to_specific_humidity(85, 303.25, 1013.25)
        result = relative_to_specific_humidity(85, 25.0, 1013.25)
        assert result is not None

    def test_monotonic_humidity(self) -> None:
        """Test that an increase in relative humidity leads to an increase in abs humidity."""
        rel_humidities = np.linspace(0, 100, 101)
        abs_humidities: npt.NDArray = relative_to_specific_humidity(rel_humidities, 21.0, 1013.25)  # type: ignore
        assert np.all(np.ediff1d(abs_humidities) > 0)

    def test_monotonic_temperature(self) -> None:
        """Test that an increase in temperature leads to an increase in abs humidity."""
        temps: npt.NDArray = np.linspace(-10, 40, 51)
        abs_humidities: npt.NDArray = relative_to_specific_humidity(85.0, temps, 1013.25)  # type: ignore
        assert np.all(np.ediff1d(abs_humidities) > 0)


class TestBAIT:
    """Test the BAIT algorithm directly."""

    def test_index_quality(self, weather_df: WeatherDataFrame) -> None:
        """Test if we catch that the input dataframe has a DatetimeIndex."""
        with pytest.raises(AssertionError):
            building_adjusted_internal_temperature(WeatherDataFrame(weather_df.reset_index()))

    def test_too_long_periods(self, weather_df: WeatherDataFrame) -> None:
        """Test if we catch if we've given daily or coarser data."""
        with pytest.raises(AssertionError):
            building_adjusted_internal_temperature(weather_df.resample("1D").sum())

    def test_not_enough_data(self, weather_df: WeatherDataFrame) -> None:
        """Test if we catch that we didn't provide enough data."""
        with pytest.raises(AssertionError):
            building_adjusted_internal_temperature(WeatherDataFrame(weather_df.iloc[:4, :]))

    def test_same_size(self, weather_df: WeatherDataFrame) -> None:
        """Test if we get the same number of BAIT values out."""
        bait = building_adjusted_internal_temperature(weather_df)
        assert bait.shape[0] == len(weather_df)

    def test_reasonable_values(self, weather_df: WeatherDataFrame) -> None:
        """Test that the BAIT values aren't nonsense."""
        bait = building_adjusted_internal_temperature(weather_df)
        assert np.all(bait < 30.0)
        assert np.all(bait > -10.0)
