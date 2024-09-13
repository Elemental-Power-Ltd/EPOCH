"""Synthetic data generation for electricity meters, using a VAE model."""

import datetime
import enum
from collections.abc import Container

import numpy as np
import pandas as pd
import sklearn.preprocessing  # type: ignore
import torch

from app.internal.epl_typing import DailyDataFrame, HHDataFrame, MonthlyDataFrame

from .model_utils import ScalerTypeEnum, load_all_scalers
from .vae import VAE


class DayTypeEnum(int, enum.Enum):
    """Types of days: Mondays / Fridays, Midweek, and Weekend / Holidays."""

    MondayOrFriday = 1
    MidWeek = 2
    WeekendOrHoliday = 3


# Split of days across 3 classes; median aggregate power in each class for a set of office data.
DAY_TYPE_WEIGHTS = pd.DataFrame(
    index=[DayTypeEnum.MondayOrFriday, DayTypeEnum.MidWeek, DayTypeEnum.WeekendOrHoliday],
    data={"median_weight": [0.25, 0.25, 0.19]},
)
DAY_TYPE_WEIGHTS /= DAY_TYPE_WEIGHTS["median_weight"].sum()


def day_type(date: datetime.date | pd.Timestamp, public_holidays: Container[datetime.date]) -> DayTypeEnum:
    """
    Get the "type" of this day: whether it's a holiday, shoulder day or midweek.

    Parameters
    ----------
    date
        A specific date you want thhe type for
    public_holidays
        Which days are public holidays or bank holidays.

    Returns
    -------
    Enum marking the specific type of this day (may change in future)
    """
    if date in public_holidays:
        return DayTypeEnum.WeekendOrHoliday
    # TODO: this would make an elegant switch-case
    if date.weekday() == 5 or date.weekday() == 6:
        return DayTypeEnum.WeekendOrHoliday
    if 1 <= date.weekday() <= 3:
        return DayTypeEnum.MidWeek
    return DayTypeEnum.MondayOrFriday


def monthly_to_daily_eload(monthly_df: MonthlyDataFrame, public_holidays: Container[datetime.date]) -> DailyDataFrame:
    """
    Turn a set of monthly readings into approximate daily electricity usages.

    This uses daily profiles, splitting up the usage proportionally according to the "type" of a given day
    and how many of that type are in each month.

    Parameters
    ----------
    daily_df
        Dataframe with start_ts, end_ts and electricity consumption readings in kWh on an approximately monthly scale.
    public_holidays
        Which days are public holidays or bank holidays.

    Returns
    -------
    Pandas dataframe with weighted daily electricity consumptions.
    """
    if monthly_df.empty:
        return DailyDataFrame(monthly_df)
    daily_usages = []
    for start_ts, end_ts, aggregate in zip(monthly_df.start_ts, monthly_df.end_ts, monthly_df.consumption_kwh, strict=False):
        month_dates = pd.date_range(start_ts, end_ts, freq=pd.Timedelta(days=1), normalize=True, inclusive="both")

        # For this "month", get the type of each day and how many of each type of day there are.
        # Then use this to weight the daily aggregrate.
        day_types = month_dates.map(lambda d: day_type(d, public_holidays))
        day_type_counts = day_types.value_counts(normalize=False, ascending=True)
        day_type_weights = DAY_TYPE_WEIGHTS["median_weight"] / day_type_counts

        # We do this weird binding to prevent the internal loop of `.map` from using the wrong values of aggregate
        # and weights.
        # See https://docs.astral.sh/ruff/rules/function-uses-loop-variable/
        daily_usage = day_types.map(lambda day, agg=aggregate, weights=day_type_weights: agg * weights[day])

        daily_usages.append(pd.DataFrame(index=month_dates, data=daily_usage, columns=["consumption_kwh"]))

    total_daily_df = DailyDataFrame(pd.concat(daily_usages))
    total_daily_df.index.name = "start_ts"
    total_daily_df["start_ts"] = total_daily_df.index
    total_daily_df["end_ts"] = total_daily_df.index + pd.Timedelta(days=1)
    return total_daily_df


def daily_to_hh_eload(
    daily_df: DailyDataFrame, scalers: dict[ScalerTypeEnum, sklearn.preprocessing.StandardScaler], model: VAE
) -> HHDataFrame:
    """
    Turn a set of daily electricity usages into half hourly meter data.

    This works by randomly sampling some point in a latent space and augmenting with a series of conditioning variables,
    including the start and end dates of the period that we're sampling.
    If you've only got monthly data, try resampling to daily using `monthly_to_daily_eload` or similar.

    Parameters
    ----------
    daily_df
        Dataframe with start_ts, end_ts and electricity consumption readings in kWh
    scalers
        A dictionary of Aggregate, StartTime, EndTime and Data scalers used to normalise the data
    model
        A model, probably a VAE, with a decode method and some latent dimension.

    Returns
    -------
    Pandas dataframe with halfhourly electricity consumptions. Watch out, as we've put these back into UTC times.
    """
    if daily_df.empty:
        return HHDataFrame(daily_df)
    with torch.no_grad():
        consumption_scaled = torch.from_numpy(
            scalers[ScalerTypeEnum.Aggregate]
            .transform(daily_df["consumption_kwh"].to_numpy().reshape(-1, 1))
            .astype(np.float32)
        )

        # TODO (2024-09-05 MHJB): linearly encoding time is a bad idea.
        # Let's instead add some clever one-hot encoding for months, or sinusoidal time encoding?
        start_date_scaled = torch.from_numpy(
            scalers[ScalerTypeEnum.StartTime]
            .transform(daily_df["start_ts"].to_numpy(dtype="datetime64[s]").reshape(-1, 1))
            .astype(np.float32)
        )
        end_date_scaled = torch.from_numpy(
            scalers[ScalerTypeEnum.EndTime]
            .transform(daily_df["end_ts"].to_numpy(dtype="datetime64[s]").reshape(-1, 1))
            .astype(np.float32)
        )
        # Sample from the latent space, which is ideally given by a normal distribution with mean 0 and variance 1.
        # This should be [days in dataset, latent_dim] size
        zs = torch.randn(size=[daily_df.shape[0], model.latent_dim], dtype=torch.float32)

        # Use the decoder part of the LSTM, with random latent space (so it's not always the same)
        # and some conditioning variables.
        result_scaled = model.decode(zs, consumption_scaled, start_date_scaled, end_date_scaled, seq_len=48)

        # but as we used scaled data all the way through, unscale it here.
        result = scalers[ScalerTypeEnum.Data].inverse_transform(result_scaled.squeeze().detach().numpy())

    # The scaled data is almost certainly wrong, but we know the daily usages! So re-calibrate the model's outputs
    # to those usages (in an ideal world, the weighting factors are all 1, but alas)
    predicted_daily = result.sum(axis=1)
    actual_daily = daily_df["consumption_kwh"].to_numpy()
    weighting_factors = (actual_daily / predicted_daily)[:, np.newaxis]
    result *= weighting_factors

    start_ts = pd.date_range(daily_df.start_ts.min(), daily_df.end_ts.max(), freq=pd.Timedelta(minutes=30), inclusive="left")
    return HHDataFrame(
        pd.DataFrame(
            index=pd.DatetimeIndex(
                start_ts,
                name="start_ts",
            ),
            # I am relatively sure that this is the right ravel -- each column is one day, so we could also express this
            # as a concat over [i, :], but this saves some memory and mucking around.
            data={
                "consumption_kwh": np.ravel(result, order="F"),
                "end_ts": start_ts + pd.Timedelta(minutes=30),
                "start_ts": start_ts,
            },
        )
    )


def monthly_to_hh_eload(
    elec_df: MonthlyDataFrame,
    model: VAE,
    public_holidays: Container[datetime.date],
    scalers: dict[ScalerTypeEnum, sklearn.preprocessing.StandardScaler] | None = None,
) -> HHDataFrame:
    """
    Generate a reasonable-looking half hourly electricity load using a pre-trained VAE.

    If you've already got daily data, use the `daily_to_hh_eload` function directly.
    This works by first resampling using daily weighted profiles according to "type" of day (e.g. holiday, midweek)
    and then putting each day into the VAE with some conditioning variables.

    Parameters
    ----------
    elec_df
        Pandas dataframe with start_ts, end_ts and consumption_kwh columns for electricty usage
    model
        VAE model with latent dimension and a `.decode(...)` method.
    public_holidays
        Which days within this period are public holidays (ideally a frozenset for fast lookup)
    scalers
        Data preprocessors used by the VAE with the relevant `.fit` method.

    Returns
    -------
    Half hourly pandas dataframe with start_ts, end_ts and consumption_kwh columns
    """
    if elec_df.empty:
        return HHDataFrame(elec_df)

    if scalers is None:
        scalers = load_all_scalers()

    # If we've already got half hourly data, don't resample for those days
    # (this can sometimes happen as an oddity of resampling)
    is_hh_mask = (elec_df["end_ts"] - elec_df["start_ts"]) < pd.Timedelta(hours=24)
    daily_df = monthly_to_daily_eload(MonthlyDataFrame(elec_df[~is_hh_mask]), public_holidays)
    halfhourly_df = daily_to_hh_eload(daily_df, scalers=scalers, model=model)
    if not elec_df[is_hh_mask].empty:
        # TODO (2024-09-06 MHJB): make this also not resample for daily data
        halfhourly_df = HHDataFrame(pd.concat([halfhourly_df, elec_df[is_hh_mask]]))
    return HHDataFrame(halfhourly_df.sort_index())
