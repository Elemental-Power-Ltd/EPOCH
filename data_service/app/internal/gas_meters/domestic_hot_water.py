import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy.optimize  # type: ignore

from ..epl_typing import HHDataFrame


def midday_sin_weights(hh_gas_df: HHDataFrame, gamma: float = 1.0) -> npt.NDArray[np.floating]:
    """
    Calculate sinusoidal weightings favouring the middle of the day.

    This will have probabilities between 06:00 and 18:00, peaking at 12:00 and
    a generally sinusoidal shape between those times.
    You can use the `gamma` factor to make the shape squarer (low `gamma`)
    or more midday focussed (high `gamma`).

    Parameters
    ----------
    hh_gas_df
        Half hourly readings, ideally evenly spaced, with a timestamp index
    gamma
        Sinusoidal shape power. `gamma` < 1 makes closer to a square wave, `gamma` > 1 makes closer to Dirac deltas

    Returns
    -------
    npt.NDArray[np.floating]
        Array of the same shape as hh_gas_df.index with event probabilities as its entries.
    """
    assert isinstance(hh_gas_df.index, pd.DatetimeIndex), "Gas Dataframe must have a `start_ts` index."
    hours = hh_gas_df.index.hour + hh_gas_df.index.minute / 60 + hh_gas_df.index.second / (60 * 60)

    sin_weights = np.maximum(np.sin(2 * np.pi * (hours.to_numpy() - 6) / 24), 0) ** gamma

    # Normalise the weights such that the weights for each day is 1
    # by dividing by the total number of days
    # this may cause trouble if there is a different amount of data per day
    norm = (hh_gas_df.index.max() - hh_gas_df.index.min()).total_seconds() / (24 * 60 * 60)
    sin_weights /= norm
    return sin_weights


def assign_hh_dhw_even(hh_gas_df: HHDataFrame, dhw_kwh: float, hdd_kwh: float) -> HHDataFrame:
    """
    Assign domestic hot water and heating splits to high resolution gas data.

    This works by assigning the domestic hot water evenly across every reading,
    and assigning heating according to the heating degree days measurement.

    Parameters
    ----------
    hh_gas_df
        Half hour gas usage dataframe, with consumption in kWh
    dhw_kwh
        Daily domestic hot water usage, in kWh
    hdd_kwh
        Hot water usage per heating degree day, in kWh / HDD

    Returns
    -------
    hh_gas_df
        Gas dataframe with DHW and heating components.
    """
    # TODO (2024-06-25 MHJB): allow for weighting, and predicted components
    assert isinstance(hh_gas_df.index, pd.DatetimeIndex), "Half-hourly Gas DataFrame must have a DatetimeIndex"

    if hh_gas_df.empty:
        raise ValueError("Can't assign DHW to an empty DataFrame")
    if "timedelta" not in hh_gas_df.columns:
        hh_gas_df["timedelta"] = np.pad(np.ediff1d(hh_gas_df.index.values).astype(np.timedelta64), (0, 1), mode="edge")

    assert pd.api.types.is_timedelta64_dtype(
        hh_gas_df["timedelta"]
    ), f"Timedelta must be a timedelta64 type, but got {hh_gas_df["timedelta"].dtype}."
    hh_gas_df["dhw"] = dhw_kwh * hh_gas_df["timedelta"] / pd.Timedelta(days=1)  # type: ignore
    hh_gas_df["heating"] = hh_gas_df["hdd"] * hdd_kwh
    hh_gas_df["predicted"] = hh_gas_df["dhw"] + hh_gas_df["heating"]
    return hh_gas_df


def assign_hh_dhw_greedy(hh_gas_df: HHDataFrame, dhw_kwh: float, hdd_kwh: float) -> HHDataFrame:
    """
    Assign domestic hot water and heating splits to high resolution gas data.

    This works greedily for DHW, assigning the first `x` kWh of each reading to DHW, and the rest
    to heating. The value for `x` is chosen for each day as the amount that will make the daily DHW
    usage correct, if it is possible.

    Parameters
    ----------
    hh_gas_df
        Half hour gas usage dataframe, with consumption in kWh
    dhw_kwh
        Daily domestic hot water usage, in kWh
    hdd_kwh
        Hot water usage per heating degree day, in kWh / HDD

    Returns
    -------
    hh_gas_df
        Gas dataframe with DHW and heating components.
    """
    # TODO (2024-06-25 MHJB): allow for weighting, and predicted components
    assert isinstance(hh_gas_df.index, pd.DatetimeIndex), "Half-hourly Gas DataFrame must have a DatetimeIndex"
    for day in np.unique(hh_gas_df.index.date):
        day_mask: npt.NDArray[np.bool_] = hh_gas_df.index.date == day
        day_df = hh_gas_df[day_mask]
        # we use this default argument to please ruff, otherwise we can trip over a late binding
        # for the dataframe
        # https://docs.astral.sh/ruff/rules/function-uses-loop-variable/
        res = scipy.optimize.minimize_scalar(lambda x, df=day_df: (dhw_kwh - np.sum(np.minimum(x, df.consumption))) ** 2)

        hh_gas_df.loc[day_mask, "dhw"] = np.minimum(hh_gas_df.loc[day_mask, "consumption"], float(res.x))
    hh_gas_df["heating"] = hh_gas_df["consumption"] - hh_gas_df["dhw"]
    return hh_gas_df


def assign_hh_dhw_poisson(
    hh_gas_df: HHDataFrame,
    weights: npt.NDArray[np.floating],
    dhw_kwh: float | npt.NDArray[np.floating],
    hdd_kwh: float,
    max_output: float = 30.0,
    rng: np.random.Generator | None = None,
) -> HHDataFrame:
    """
    Assign domestic hot water usage according to a Poisson distribution, randomly throughout time.

    Samples with `weight`s provided, which can be of any length of time. These will be repeated
    until every time period in the data is covered, so you can provide daily / weekly / monthly
    weightings to cover an arbitrary length.
    Each weight should cover the time interval provided in the `gas_df`, so i.e. a 30 minute gas
    dataframe should have `weight`s representing each half hour.

    Doesn't need consumption to be pre-filled, as this is a random sampling method so won't line up
    perfectly with the exact consumption (but as a caveat, be careful with the `dhw_kwh` and `hdd_kwh` calibration!)

    Parameters
    ----------
    gas_df
        Gas usage dataframe at the desired resolution. Must have HDD column filled in, but not necessarily consumption.
    weights
        Average number of DHW events per time period
    dhw_kwh
        Domestic hot water usage per event, in kWh
    hdd_kwh
        Link between HDD and heating load, in kWh / HDD
    max_output
        Maximum boiler output, in kWh per period.
    rng
        Numpy random generator for reproducible results

    Returns
    -------
    gas_df
        Gas dataframe, augmented with `dhw`, `heating` and `predicted` columns.
    """
    if rng is None:
        rng = np.random.default_rng()

    # TODO (2024-06-26 MHJB): calibrate and normalise these somehow for reasonable daily usage?
    hh_gas_df["dhw"] = rng.poisson(weights) * dhw_kwh
    hh_gas_df["heating"] = np.minimum(hdd_kwh * hh_gas_df["hdd"], max_output - hh_gas_df["dhw"])
    hh_gas_df["predicted"] = hh_gas_df["dhw"] + hh_gas_df["heating"]
    return hh_gas_df
