"""Functions to do regression analysis on heating / weather data."""

import datetime

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy.optimize
from sklearn.linear_model import LinearRegression  # type: ignore

from ...models.weather import BaitAndModelCoefs
from ..epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ..heating import building_adjusted_internal_temperature
from .domestic_hot_water import assign_hh_dhw_even


def compute_monthly_hdd(
    gas_df: MonthlyDataFrame,
    weather_df: WeatherDataFrame,
    solar_gain: float,
    wind_chill: float,
    humidity_discomfort: float,
    smoothing: float,
    thresh: float,
) -> npt.NDArray[np.floating]:
    """
     Compute the heating degree days matching specific periods of gas data (probably monthly).

     The weather data has to be at a higher resolution than the gas data for accurate calculation.
     This method will compute the HDD at high resolution, using a specific set of BAIT parameters,
     and then group them into the gas time periods.

    Parameters
    ----------
     gas_df
         Monthly (or similar) gas meter readings
     weather_df
         Hourly (or similar) weather data, suitable for BAIT
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
     thresh
         See BAIT docs

    Returns
    -------
     heating_degree_days
         Heating degree day array of the same size as the
    """
    bait = building_adjusted_internal_temperature(
        weather_df,
        solar_gain=solar_gain,
        wind_chill=wind_chill,
        humidity_discomfort=humidity_discomfort,
        smoothing=smoothing,
    )
    # we do it this numpy diff and pad way as pandas puts a NaT in the first element we can't remove
    # (and is off-by-one). We also can't use the "to_end" as then we have to manually compute the end
    # values, and they're the wrong types.
    timedelta = np.pad(np.ediff1d(weather_df.index.values).astype(np.timedelta64), (0, 1), mode="edge") / np.timedelta64(1, "D")

    # We can't guarantee that we've got evenly sized periods.
    # Take the start and end timestamps for each period of gas data, and
    # calculate the B-HDDs for each period.
    hdds = []
    for start_ts, end_ts in zip(gas_df.start_ts, gas_df.end_ts, strict=False):
        hdd_mask = np.logical_and(weather_df.index >= start_ts, weather_df.index < end_ts)
        period_hdd = np.maximum(thresh - bait[hdd_mask], 0.0)
        period_time = timedelta[hdd_mask]

        hdd = np.sum(period_hdd * period_time)
        hdds.append(hdd)
    return np.asarray(hdds, dtype=np.float32)


def predict_heating_load(gas_df: MonthlyDataFrame) -> npt.NDArray[np.float32]:
    """
    Predict heating load for a monthly (or similar) gas usage dataframe.

    This gas usage dataframe should already be augmented with HDD data
    and period length information, it will not work for half hourly data.

    Parameters
    ----------
    gas_df
        Gas usage dataframe with long (multi-day) usage periods and HDD

    Returns
    -------
        predicted gas usage from heating degree days
    """
    assert "hdd" in gas_df.columns, "Must have `hdd` in gas_df. Have you augmented it?"
    mdl = LinearRegression(positive=True, fit_intercept=False)
    xs = np.vstack([gas_df["days"], gas_df["hdd"].to_numpy()]).T
    ys = gas_df["consumption"].to_numpy()
    mdl.fit(xs, ys, sample_weight=gas_df["days"].to_numpy())
    predicted: npt.NDArray[np.floating] = mdl.predict(xs)
    return predicted


def score_bait_coefficients(x: list[float], gas_df: MonthlyDataFrame, weather_df: WeatherDataFrame) -> float:
    """
    Score a set of BAIT coefficients depending on how well they can predict heating load.

    Pass this into scipy.optimize.minimize, you only very rarely want to use this yourself.
    Pass in different resolutions of gas and weather data: monthly gas, and hourly weather.
    This is to even out the noise in gas data.

    Parameters
    ----------
    x
        Scipy parameter list, in the form [solar_gain, wind_chill, humidity_discomfort, smoothing, threshold]
    gas_df
        Monthly or similar gas usage dataframe
    weather_df
        Hourly weather dataframe, used for HDD calculations.
    """
    assert "start_ts" in gas_df.columns, "Must have start_ts in gas dataframe, did you pass in HH?"
    assert "end_ts" in gas_df.columns, "Must have end_ts in gas dataframe, did you pass in HH?"
    gas_df["hdd"] = compute_monthly_hdd(gas_df, weather_df, *x)
    predicted = predict_heating_load(gas_df)
    ys = gas_df["consumption"].to_numpy()
    # aim to minimize the mean squared loss, we want this to be zero
    return float(np.sum((predicted - ys) ** 2))


def monthly_to_hh_hload(gas_df: MonthlyDataFrame, weather_df: WeatherDataFrame) -> HHDataFrame:
    """
    Take monthly gas readings and use them to synthesise half hourly heating load data.

    This will optimise the BAIT coefficients to find a good temperature -> HDD mapping,
    and then fit a domestic hot water (DHW) / heating regression model to the coarse monthly data.

    Then, it will resample the weather data into half hourly chunks (it often comes in hourly),
    and assign DHW and heating load to each chunk according to the fitted model and the weather.

    Parameters
    ----------
    gas_df
        Coarse gas dataframe, with `start_ts`, `end_ts` and `consumption` columns. Probably monthly.
    weather_df
        Weather dataframe with `temp`, `humidity`, `solarradiation`, `pressure` and `windspeed` columns. Probably hourly.

    Returns
    -------
    hload_df
        Heating load dataframe at half hourly resolution with `dhw`, `heating` and `predicted` columns.
    """
    bait_initial = [
        0.012,  # solar gain
        -0.20,  # wind chill
        -0.05,  # humidity discomfort
        0.5,  # smoothing
        15.5,  # threshold
    ]

    result = scipy.optimize.minimize(
        score_bait_coefficients,
        bait_initial,
        args=(gas_df, weather_df),
        method="Nelder-Mead",
        bounds=[(0, None), (None, 0), (None, None), (0, 1), (13, 20)],
    )  # type: ignore
    assert result.success, "Optimisation did not succeed"
    bait_fitted = result.x
    bait_hdd = compute_monthly_hdd(
        gas_df=gas_df,
        weather_df=weather_df,
        solar_gain=bait_fitted[0],
        wind_chill=bait_fitted[1],
        humidity_discomfort=bait_fitted[2],
        smoothing=bait_fitted[3],
        thresh=bait_fitted[4],
    )  # type: ignore
    gas_df["hdd"] = bait_hdd

    mdl = LinearRegression(positive=True, fit_intercept=False)
    xs = np.vstack([gas_df["days"].to_numpy(), gas_df["hdd"].to_numpy()]).T
    ys = gas_df["consumption"].to_numpy().reshape(-1, 1)
    mdl.fit(xs, ys)

    hh_weather_df = WeatherDataFrame(weather_df.resample("30min").mean().interpolate(method="time"))
    bait = building_adjusted_internal_temperature(
        hh_weather_df,
        solar_gain=bait_fitted[0],
        wind_chill=bait_fitted[1],
        humidity_discomfort=bait_fitted[2],
        smoothing=bait_fitted[3],
    )

    hload_df: HHDataFrame = HHDataFrame(
        pd.DataFrame(
            index=pd.date_range(
                gas_df.start_ts.min(),
                gas_df.start_ts.max(),
                freq=pd.Timedelta(minutes=30),
                tz=datetime.UTC,
            )
        )
    )
    hh_bait_hdd = np.maximum(bait_fitted[4] - bait, 0) / 48
    hload_df["hdd"] = hh_bait_hdd

    # TODO (2024-06-28 MHJB): Add different options for how to assign DHW and heating (even, greedy, poisson)
    hload_df = assign_hh_dhw_even(hload_df, dhw_kwh=mdl.coef_[0, 0], hdd_kwh=mdl.coef_[0, 1])

    # TODO (2024-06-28 MHJB): add a "normalise to monthly readings" feature
    return hload_df


def fit_bait_and_model(gas_df: MonthlyDataFrame, weather_df: WeatherDataFrame, apply_bait: bool = True) -> BaitAndModelCoefs:
    """
    Fit BAIT coefficients and a heating load models for these dataframes.

    This will first fit the BAIT model using the weather : gas regression,
    and then will fit a new heating and DHW model from those best coefficients.

    Parameters
    ----------
    gas_df
        Coarse gas dataframe with consumption information
    weather_df
        Weather dataframe with enough info for BAIT

    Returns
    -------
    BaitAndModelCoeffs
        fitted BAIT coefficients, model information and a score
    """
    # These are the "default" values from the original BAIT paper
    bait_initial = [
        0.012 if apply_bait else 0.0,  # solar gain
        -0.20 if apply_bait else 0.0,  # wind chill
        -0.05 if apply_bait else 0.0,  # humidity discomfort
        0.5 if apply_bait else 0.0,  # smoothing
        15.5,  # threshold
    ]

    result = scipy.optimize.minimize(
        score_bait_coefficients,
        bait_initial,
        args=(gas_df, weather_df),
        method="Nelder-Mead",
        bounds=[
            (0.0, None if apply_bait else 0.0),
            (None if apply_bait else 0.0, 0.0),
            (None if apply_bait else 0.0, None if apply_bait else 0.0),
            (0.0, 1.0 if apply_bait else 0.0),
            (13, 20),
        ],
    )  # type: ignore
    assert result.success, "Optimisation did not succeed"
    bait_fitted = result.x
    bait_hdd = compute_monthly_hdd(
        gas_df=gas_df,
        weather_df=weather_df,
        solar_gain=bait_fitted[0],
        wind_chill=bait_fitted[1],
        humidity_discomfort=bait_fitted[2],
        smoothing=bait_fitted[3],
        thresh=bait_fitted[4],
    )

    mdl = LinearRegression(positive=True, fit_intercept=False)
    xs = np.vstack([gas_df["days"].to_numpy(), bait_hdd]).T
    ys = gas_df["consumption"].to_numpy().reshape(-1, 1)
    mdl.fit(xs, ys)

    score = float(mdl.score(xs, ys))
    return BaitAndModelCoefs(
        solar_gain=bait_fitted[0],
        wind_chill=bait_fitted[1],
        humidity_discomfort=bait_fitted[2],
        smoothing=bait_fitted[3],
        threshold=bait_fitted[4],
        heating_kwh=mdl.coef_[0, 1],
        dhw_kwh=mdl.coef_[0, 0],
        r2_score=score,
    )
