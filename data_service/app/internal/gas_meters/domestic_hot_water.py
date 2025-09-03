"""
Domestic hot water allocation functions.

Generally, these will take a half hourly or monthly dataframe and attempt to allocate DHW to each period in the dataframe.
There are a few different methods, including a weighted or random assignment pattern.
"""

from collections import defaultdict

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy.optimize

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

    sin_weights: npt.NDArray[np.floating] = np.maximum(np.sin(2 * np.pi * (hours.to_numpy() - 6) / 24), 0) ** gamma

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

    assert pd.api.types.is_timedelta64_dtype(hh_gas_df["timedelta"]), (
        f"Timedelta must be a timedelta64 type, but got {hh_gas_df['timedelta'].dtype}."
    )
    hh_gas_df["dhw"] = dhw_kwh * hh_gas_df["timedelta"] / pd.Timedelta(days=1)
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

        def calculate_loss(x: float, df: pd.DataFrame = day_df) -> float:
            return float((dhw_kwh - np.sum(np.minimum(x, df.consumption))) ** 2)

        res = scipy.optimize.minimize_scalar(calculate_loss)

        hh_gas_df.loc[day_mask, "dhw"] = np.minimum(hh_gas_df.loc[day_mask, "consumption"], float(res.x))
    hh_gas_df["heating"] = hh_gas_df["consumption"] - hh_gas_df["dhw"]
    return hh_gas_df


def get_poisson_weights(
    gas_df: HHDataFrame,
    profile_name: str = "leisure_centre",
) -> npt.NDArray[np.floating]:
    """
    Get a set of DHW weights for a specific type of building.

    Currently only supports a single type of building, a leisure centre,
    and gets the probability of a DHW event at each half-hourly interval.

    Parameters
    ----------
    gas_df
        Half hourly gas readings with a timestamp index.
    profile_name
        The type of building profile you want to retrieve.

    Returns
    -------
    Probabilities of a DHW event at each timestamp.
    Same size as gas_df.index.
    """
    LEISURE_CENTRE_PROFILE = np.array(
        [
            0.013198232248403007,
            0.01287375600497906,
            0.012590233192145514,
            0.013632345855510371,
            0.013437641014097277,
            0.013138909703286081,
            0.013584733222479268,
            0.013554733980577846,
            0.013636726903302655,
            0.013967901456918636,
            0.01601163335327971,
            0.024303485070194746,
            0.023148404054539322,
            0.024754399372273656,
            0.02457767290929792,
            0.02489278968422502,
            0.024926253669862636,
            0.02570723466024378,
            0.024610030785454054,
            0.024824915835003934,
            0.024429236589172326,
            0.02464987677623803,
            0.025127670754196925,
            0.02560170025197006,
            0.02571542345539195,
            0.026111140395528205,
            0.02502172158560853,
            0.02507448091114785,
            0.024910785592999928,
            0.02534098620960944,
            0.024599646981293955,
            0.025563661051187892,
            0.025241393957618815,
            0.026012817635993727,
            0.025947621066111003,
            0.02594415353616745,
            0.0243094597222729,
            0.023969760681742676,
            0.02307386711125132,
            0.023324381216780096,
            0.02131279601511709,
            0.021511182389895602,
            0.019092329127321023,
            0.01451545603032447,
            0.01335064071369023,
            0.012641920193187942,
            0.012914986636965622,
            0.013318870435140474,
        ]
    )
    # This is a stub for us to add different profiles in later
    type_profiles: dict[str, npt.NDArray[np.floating]] = defaultdict(lambda: LEISURE_CENTRE_PROFILE)
    profile = type_profiles[profile_name]
    weights = gas_df.index.map(lambda item: profile[int((item.hour + (item.minute / 60)) * 2)])

    # We want the total sum of DHW to be 1 unit per day, such that we can scale this up later.
    # Is it correct to do this here?
    if "end_ts" in gas_df.columns:
        latest_day = gas_df["end_ts"].max()
    else:
        latest_day = gas_df.index.max()

    if "start_ts" in gas_df.columns:
        earliest_day = gas_df["start_ts"].min()
    else:
        earliest_day = gas_df.index.min()
    days_involved = (latest_day - earliest_day).total_seconds() / (24 * 60 * 60)
    weights_arr = weights.to_numpy()
    weights_arr /= np.sum(weights_arr)
    weights_arr *= days_involved
    return weights_arr


def assign_hh_dhw_poisson(
    hh_gas_df: HHDataFrame,
    weights: npt.NDArray[np.floating],
    dhw_event_size: float,
    hdd_kwh: float,
    flat_heating_kwh: float = 0.0,
    max_output: float = float("inf"),
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
    dhw_fraction
        Fraction of the "DHW" component that's actually DHW. Assigns the rest to heating if this is < 1

    Returns
    -------
    gas_df
        Gas dataframe, augmented with `dhw`, `heating` and `predicted` columns.
    """
    if rng is None:
        rng = np.random.default_rng()
    hh_gas_df["dhw"] = rng.poisson(weights) * dhw_event_size
    hh_gas_df["heating"] = np.minimum((hdd_kwh * hh_gas_df["hdd"]) + flat_heating_kwh, max_output - hh_gas_df["dhw"])
    hh_gas_df["predicted"] = hh_gas_df["dhw"] + hh_gas_df["heating"]
    return hh_gas_df
