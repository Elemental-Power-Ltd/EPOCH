"""Building Adjusted Internal Temperature and feelslike calculations."""

import numpy as np
import pandas as pd

from ..epl_typing import WeatherDataFrame
from ..utils import relative_to_specific_humidity


def building_adjusted_internal_temperature(
    weather_df: WeatherDataFrame,
    solar_gain: float = 0.012,
    wind_chill: float = -0.20,
    humidity_discomfort: float = 0.05,
    smoothing: float = 0.5,
) -> pd.Series:
    r"""
    Calculate a "building adjusted internal temperature" via Staffell et al's methodology.

    This is a "feelslike" temperature, weighted for sun, wind and humidity.

    Implements the equation
        $$ \text{BAIT} = T + w_\text{solar}(S - S^\\star) - w_\text{wind}(W - W^\\star)
                        + w_\text{humidity}(H - H^\\star)(T - T^\\star) $$
    where $ w_\text{factor}$ is a weighting for a specific factor,
    and the starred values are all "setpoints".

    We could improve on this in future by revisiting the setpoint calculations.

    See Also
    --------
    A global model of hourly space heating and cooling demand at multiple spatial scales
    Iain Staffell, Stefan Pfenninger, Nathan Johnson
    https://doi.org/10.1038/s41560-023-01341-5

    Parameters
    ----------
    weather_df
        Weather dataframe with columns `["temp", "solarradiation", "windspeed", "humidity", "pressure"]`
    solar_gain
        Effect of the sun on building temperature in [°C  / (W m^-2)].
        Reasonable values are about 0.012.
    wind_chill
        Effect of wind speed on building temperature in [°C / (ms^-1)].
        Reasonable values are about -0.20.
    humidity_discomfort
        Effect of humidity on building temperature in °C / (g kg^-1)].
        Watch out for this one, as humidity is often measured as a %.
        Reasonable values are about 0.05.
    smoothing
        Smoothing factor for the previous day's temperatures. Smooths (d-1) and (d-2).

    Returns
    -------
        Numpy array of feelslike temperatures, adjusted for the weather
    """
    assert isinstance(weather_df.index, pd.DatetimeIndex), "Weather DataFrame must have a DatetimeIndex"
    assert weather_df.index.diff().mean() < pd.Timedelta(days=1), "Weather DataFrame must be half-hourly, hourly or daily"  # type: ignore
    assert weather_df.index.max() - weather_df.index.min() > pd.Timedelta(days=2), "Must have at least 2 days of data"
    # This method uses humidity in g kg^-1, which isn't easily available
    # from VisualCrossing. Compute it here if it hasn't been done for us.
    if "specific_humidity" not in weather_df.columns:
        humidity_series = relative_to_specific_humidity(
            rel_hum=weather_df["humidity"],
            air_temp=weather_df["temp"],
            air_pressure=weather_df["pressure"],
        )
    else:
        humidity_series = weather_df["specific_humidity"]
    # copy this so we don't modify our original dataframe
    bait = weather_df["temp"].copy()
    solar_setpoint = 100.0 + 7 * bait
    wind_setpoint = 4.5 - 0.025 * bait
    humidity_setpoint = np.exp(1.1 + 0.06 * bait)
    temp_setpoint = 16.0

    bait += (weather_df["solarradiation"] - solar_setpoint) * solar_gain
    bait += (weather_df["windspeed"] - wind_setpoint) * wind_chill
    bait += (weather_df["temp"] - temp_setpoint) * (humidity_series - humidity_setpoint) * humidity_discomfort

    # This is not strictly the BAIT method, which uses daily data, but
    # seems like an upgrade to me.
    prev_24 = bait.rolling("1D").mean()
    # this is a bit cheeky, as it doesn't strictly handle the first day correctly
    # but for either a full year of data (or a sufficiently small sample)
    # it's good enough
    prev_48 = np.roll(prev_24.to_numpy(), 1)
    bait_smooth = bait + (smoothing * prev_24) + (smoothing**2 * prev_48)
    bait_smooth /= 1 + smoothing + smoothing**2

    blend_lo = 15.0
    blend_hi = 23.0
    blend_weight = 0.5
    # When the temperature is above 15°C, start
    # mixing in some of the raw outside air to represent people
    # opening windows.
    blend_mid = (blend_hi + blend_lo) / 2.0
    blend_diff = blend_hi - blend_lo
    blend = 10.0 * (weather_df["temp"].to_numpy() - blend_mid) / blend_diff
    blend = blend_weight / (1.0 + np.exp(-blend))

    res = (bait * (1.0 - blend)) + (weather_df["temp"].to_numpy() * blend)
    assert isinstance(res, pd.Series), str(type(res))
    return res
