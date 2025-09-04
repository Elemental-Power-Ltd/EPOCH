"""Synthetic data generation for electricity meters, using a VAE model."""

import datetime
import enum
import itertools
import json
import pathlib
from collections.abc import Container
from pathlib import Path
from typing import Any, TypeGuard, cast

import numpy as np
import numpy.typing as npt
import pandas as pd
import sklearn.preprocessing  # type: ignore
import torch
from statsmodels.tsa.arima_process import ArmaProcess  # type: ignore

from app.internal.epl_typing import DailyDataFrame, HHDataFrame, MonthlyDataFrame, SquareHHDataFrame
from app.internal.utils.bank_holidays import UKCountryEnum, get_bank_holidays

from .model_utils import fit_residual_model, predict_var_mean_batched, split_and_baseline_active_days
from .vae_2_0 import VAE


def is_valid_square_hh_dataframe(obj: Any) -> TypeGuard[SquareHHDataFrame]:
    """
    Check if this object is a valid SquareHHDataFrame.

    A SquareHHDataframe has a daily DatetimeIndex, and columns [00:00, 00:30, ..., 23:30]
    None of its entries are NaN.

    Parameters
    ----------
    obj
        Object, probably a dataframe, to check if it's a SquareHHDataFrame

    Returns
    -------
    True if all criteria are met
    False otherwise
    """
    if not isinstance(obj, pd.DataFrame):
        return False

    expected_hours = {datetime.time(hour=h, minute=m) for h, m in itertools.product(range(24), [0, 30])}
    if len(obj.columns) != 48:
        return False

    if any(col not in expected_hours for col in obj.columns):
        return False

    if pd.isna(obj).any().any():
        return False

    if not isinstance(obj.index, pd.DatetimeIndex):
        return False
    return True


class DayTypeEnum(enum.IntEnum):
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


def monthly_to_daily_eload(monthly_df: MonthlyDataFrame) -> DailyDataFrame:
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
    public_holidays = frozenset(get_bank_holidays())
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
    daily_df: DailyDataFrame,
    model: VAE,
    resid_model_path: pathlib.Path | None = None,
    target_hh_observed_df: SquareHHDataFrame | None = None,
    weekend_inds: Container[int] = {
        6,
    },
    division: UKCountryEnum = UKCountryEnum.England,
    rng: np.random.Generator | None = None,
) -> HHDataFrame:
    """
    Turn a set of daily electricity usages into half hourly meter data.

    This works by randomly sampling some point in a latent space and augmenting with the aggregated consumption for the given
    day. We then use a VAE decoder to generate an approximate hh profile, which we refine using time series models trained on
    either a default site or hh data provided by the client.

    If you've only got monthly data, try resampling to daily using `monthly_to_daily_eload` or similar.

    Parameters
    ----------
    daily_df
        Dataframe with start_ts, end_ts and electricity consumption readings in kWh
    model
        A model, probably a VAE, with a decode method and some latent dimension.
    resid_model_path
        A pathlib.Path object that gives the path identifier for the directory containing the model files that are to be used as
        a default model for the residuals. For now, assume only one set of default models - one active, one inactive.
        All model files for the residuals have the suffix `default_`.
    target_hh_observed_df
        A set of half-hourly data for the client's target site, which can be used to train a model for the residuals.
        It must have a column `consumption_kWh` (note capital W)
        Exactly one of resid_model_path or target_hh_observed_df must be provided. The data in target_hh_observed_df must
        correspond to dates provided in daily_df
    weekend_inds
        A set specifying the regular 'non-active' days of the week for the site; default is {6,} for Queen's Buildings.
        This should match the indices provided by .dayofweek
    division
        Which the division of the UK to use to determine the public holidays.
    rng
        Numpy random generator for reproducible results

    Returns
    -------
    Pandas dataframe with halfhourly electricity consumptions. Watch out, as we've put these back into UTC times.
    """
    if (resid_model_path is None) == (target_hh_observed_df is None):
        raise ValueError("Exactly one of 'resid_model_path' or 'target_hh_observed_df' must be provided.")

    if rng is None:
        rng = np.random.default_rng()

    use_client_hh = False if target_hh_observed_df is None else True

    # extract 'start_ts' from first record in daily_df, for later use, and discard 'start_ts', 'end_ts' columns
    initial_start_ts = daily_df.start_ts.min()
    final_end_ts = daily_df.end_ts.max()
    daily_df = daily_df.drop(columns=["start_ts", "end_ts"])

    # split daily data into active and inactive days; remove baseline from active days
    target_daily_active_df, target_daily_inactive_df = split_and_baseline_active_days(
        daily_df, weekend_inds=weekend_inds, division=division
    )
    # scale the baselined daily consumption data for active days, using a *new* StandardScaler
    aggregate_scaler_new = sklearn.preprocessing.StandardScaler()
    consumption_scaled = torch.tensor(
        aggregate_scaler_new.fit_transform(target_daily_active_df["consumption_baselined"].to_numpy().reshape(-1, 1)),
        dtype=torch.float32,
    )

    # generate a normalised approximate profile for each active day
    # we should sample multiple profiles for each day and calculate a mean intraday profile to pass forward
    num_reps = 100
    vae_output_np = generate_approx_daily_profiles(model, np.repeat(consumption_scaled, repeats=num_reps, axis=0))
    vae_output_mean_np = vae_output_np.reshape(num_reps,-1,48).mean(axis=0)

    # rescale baseline / peak of approximate profiles to match daily aggregates
    #   - do this before adding noise to avoid overly scaling the noise
    timestamp_headers = pd.date_range("00:00", "23:30", freq="30min").time
    scaling_factors = target_daily_active_df["consumption_baselined"] / np.sum(vae_output_mean_np, axis=1)
    hh_active_approx_df = pd.DataFrame(
        np.tile(target_daily_active_df["offsets"] / 48, (48, 1)).T + vae_output_mean_np * np.tile(scaling_factors, (48, 1)).T,
        columns=timestamp_headers,
        index=target_daily_active_df.index,
    )

    # generate hh profiles for inactive days - just divide daily values by 48
    hh_inactive_approx_df = pd.DataFrame(
        np.tile(target_daily_inactive_df.to_numpy(dtype=float) / 48, (1, 48)),
        columns=timestamp_headers,
        index=target_daily_inactive_df.index,
    )

    # create copy of dataframe to hold final data
    target_hh_df = pd.concat([hh_inactive_approx_df, hh_active_approx_df], axis=0).sort_index()

    if use_client_hh:
        # split client hh data into active and inactive days
        assert target_hh_observed_df is not None, "Asked to use_client_hh but got a None target_hh_observed_df"
        assert not target_hh_observed_df.empty, "Asked to use_client_hh but got an empty target_hh_observed_df"
        assert is_valid_square_hh_dataframe(target_hh_observed_df), "Got a target_hh_observed_df that isn't a valid square HH"
        target_hh_obs_daily = cast(DailyDataFrame, pd.DataFrame(target_hh_observed_df.sum(axis=1), columns=["consumption_kwh"]))
        target_hh_obs_daily_active, _ = split_and_baseline_active_days(
            target_hh_obs_daily, weekend_inds=weekend_inds, division=division
        )

        is_active_mask = target_hh_observed_df.index.isin(target_hh_obs_daily_active.index)
        assert np.any(is_active_mask), "Must have at least one active day."
        assert not np.all(is_active_mask), "Must have at least one inactive day."
        # baseline all days (active and inactive):
        # - for active days, this is subtracting the 'offset' calculated using the appropriate nearest inactive day
        # - for inactive days, this is simply centering the data / zeroing the daily mean
        target_hh_obs_baselined = target_hh_observed_df.copy()
        target_hh_obs_baselined[is_active_mask] -= target_hh_obs_daily_active["offsets"].to_numpy()[:, np.newaxis] / 48
        target_hh_obs_baselined[~is_active_mask] -= (
            target_hh_obs_baselined[~is_active_mask].mean(axis=1).to_numpy()[:, np.newaxis]
        )
        target_hh_obs_baselined[is_active_mask] = target_hh_obs_baselined[is_active_mask].ffill().bfill()
        target_hh_obs_baselined[~is_active_mask] = target_hh_obs_baselined[~is_active_mask].ffill().bfill()

        # then establish the residuals, assuming that these limited data are to be modelled using the generated VAE output
        # - vae_output used to model the intraday profile on active days; baselined inactive days are simply relabelled here
        # We generate a new VAE output as we can't guarantee that these data are the same shape as the target data
        # (for example, we might have observed data for two years but want to generate for one)
        daily_active_baselined = target_hh_obs_baselined[is_active_mask].sum(axis=1).to_numpy().reshape(-1, 1)
        obs_scaler = sklearn.preprocessing.StandardScaler()
        obs_consumption_scaled = torch.tensor(
            obs_scaler.fit_transform(daily_active_baselined),
            dtype=torch.float32,
        )

        # generate a normalised approximate profile for each active day
        num_reps = 500
        vae_obs = generate_approx_daily_profiles(model, np.repeat(obs_consumption_scaled, repeats=num_reps, axis=0))
        vae_obs_mean = vae_obs.reshape(num_reps,-1,48).mean(axis=0)

        # rescale baseline / peak of approximate profiles to match daily aggregates for active days
        # this is used to calculate residuals and also provide structure for the log-variance regression in fit_residual_model()
        scaling_factors_obs = daily_active_baselined / np.sum(vae_obs_mean, axis=1)[:, None]
        # force an extra axis to satisfy np broadcasting rules
        target_hh_active_approx_df = pd.DataFrame(
            np.tile(target_hh_obs_daily_active["offsets"] / 48, (48, 1)).T + vae_obs_mean * np.tile(scaling_factors_obs, (1, 48)),
            columns=timestamp_headers,
            index=target_hh_obs_daily_active.index,
        )

        target_hh_active_residuals = cast(  # type: ignore
            SquareHHDataFrame,
            target_hh_observed_df[is_active_mask] - target_hh_active_approx_df,
        )
        target_hh_inactive_residuals = target_hh_obs_baselined[~is_active_mask]

        # then model the residuals: extract the trend and fit an ARMA model to the noise
        target_hh_inactive_residtrend_df, var_model_inactive, ARMA_model_inactive, ARMA_scale_inactive, min_noise_inactive, max_noise_inactive = fit_residual_model(
            target_hh_inactive_residuals, vae_struct=None, verbose=True
        )
        target_hh_active_residtrend_df, var_model_active, ARMA_model_active, ARMA_scale_active, min_noise_active, max_noise_active = fit_residual_model(
            target_hh_active_residuals, vae_struct=target_hh_active_approx_df, verbose=True
        )

        # finally, record the min / max observed hh data for clipping the final simulations
        hh_obs_active_min = target_hh_obs_baselined[is_active_mask].min(axis=0)
        hh_obs_inactive_min = target_hh_obs_baselined[~is_active_mask].min(axis=0)
        hh_obs_active_max = target_hh_obs_baselined[is_active_mask].max(axis=0)
        hh_obs_inactive_max = target_hh_obs_baselined[~is_active_mask].max(axis=0)
    else:
        # load defaults for the residual trends, ARMA noise models, and the std devation of the daily data for active days
        # that was used to train these defaults
        # TODO (JSM 2025-08-06) Should we move all logic for loading residual models to .model_utils?
        assert resid_model_path is not None
        assert resid_model_path.is_dir(), f"Resid model path {resid_model_path} is not a directory"
        default_hh_active_residtrend_df = pd.read_csv(Path(resid_model_path, "default_residtrend_active.csv"))
        default_hh_inactive_residtrend_df = pd.read_csv(Path(resid_model_path, "default_residtrend_inactive.csv"))
        ARMA_model_active_dict = json.loads(Path(resid_model_path, "default_ARMA_model_active.json").read_text())
        ARMA_model_inactive_dict = json.loads(Path(resid_model_path, "default_ARMA_model_inactive.json").read_text())
        ARMA_model_active = ArmaProcess(ARMA_model_active_dict["ar_params"], ARMA_model_active_dict["ma_params"])
        ARMA_model_inactive = ArmaProcess(ARMA_model_inactive_dict["ar_params"], ARMA_model_inactive_dict["ma_params"])
        ARMA_scale_active = ARMA_model_active_dict["sigma"]
        ARMA_scale_inactive = ARMA_model_inactive_dict["sigma"]
        reference_daily_active_std = ARMA_model_active_dict["daily_active_std"]
        default_clipping_active_dict = json.loads(Path(resid_model_path, "default_clipping_values_active.json").read_text())
        default_clipping_inactive_dict = json.loads(Path(resid_model_path, "default_clipping_values_inactive.json").read_text())
        default_active_daily_bc_med = default_clipping_active_dict["daily_median_baselined_consumption"]
        default_inactive_daily_bc_med = default_clipping_inactive_dict["daily_median_baselined_consumption"]
        hh_default_active_bc_min = default_clipping_active_dict["hh_min_baselined_consumption"]
        hh_default_inactive_bc_min = default_clipping_inactive_dict["hh_min_baselined_consumption"]
        hh_default_active_bc_max = default_clipping_active_dict["hh_max_baselined_consumption"]
        hh_default_inactive_bc_max = default_clipping_inactive_dict["hh_max_baselined_consumption"]

    target_active_mask = np.isin(target_hh_df.index, hh_active_approx_df.index).astype(bool)
    num_inactive, num_active = target_daily_inactive_df.shape[0], target_daily_active_df.shape[0]
    # add fitted trends
    if use_client_hh:
        target_hh_df[~target_active_mask] += np.tile(target_hh_inactive_residtrend_df, (num_inactive, 1))
        target_hh_df[target_active_mask] += np.tile(target_hh_active_residtrend_df, (num_active, 1))
    else:
        target_hh_df[~target_active_mask] += np.tile(default_hh_inactive_residtrend_df, (num_inactive, 1))
        target_hh_df[target_active_mask] += np.tile(default_hh_active_residtrend_df, (num_active, 1))

    # Add noise from fitted ARMA distributions, incorporating heteroskedasticity
    # - first, if needed, scale the ARMA_scale_* parameters using the daily aggregate values for the target site
    if not use_client_hh:
        ARMA_scale_active_target = (
            ARMA_scale_active * target_daily_active_df["consumption_baselined"].std() / reference_daily_active_std
        )
        ARMA_scale_inactive_target = ARMA_scale_active_target.copy()
    else:
        # don't rescale -- if we've used (some) hh data from the client, this is as good as we're going to get
        ARMA_scale_inactive_target = ARMA_scale_inactive
        ARMA_scale_active_target = ARMA_scale_active

    # - then pre-generate white noise to reduce runtime...
    eps = rng.normal(scale=ARMA_scale_inactive_target, size=(num_inactive, 48))
    sims = np.asarray(
        [
            ARMA_model_inactive.generate_sample(nsample=48, scale=1.0, distrvs=lambda size, e=eps[i]: e)
            for i in range(num_inactive)
        ]
    )
    # - scale by fitted heteroskedasticity factors
    var_factors_inactive = np.exp(var_model_inactive.predict())
    scaled_sims = np.sqrt(var_factors_inactive) * sims
    target_hh_df[~target_active_mask] += np.clip(scaled_sims, min_noise_inactive, max_noise_inactive)

    # - repeat for active dates
    num_active = target_daily_active_df.shape[0]
    eps = rng.normal(scale=ARMA_scale_active_target, size=(num_active, 48))
    sims = np.asarray(
        [ARMA_model_active.generate_sample(nsample=48, scale=1.0, distrvs=lambda size, e=eps[i]: e) for i in range(num_active)]
    )
    var_factors_active = np.exp(var_model_active.predict())
    scaled_sims = np.sqrt(var_factors_active) * sims
    target_hh_df[target_active_mask] += np.clip(scaled_sims, min_noise_active, max_noise_active)

    # perform a final clipping of the _baselined_ simulations to keep all hh simulations within the observed/default bounds
    # also scale the clipped baselined sims to ensure they match the observed daily aggregates
    if use_client_hh:
        target_hh_active_baselined = target_hh_df[target_active_mask] - np.tile(target_daily_active_df["offsets"] / 48, (48, 1)).T
        target_hh_active_baselined = target_hh_active_baselined.clip(hh_obs_active_min, hh_obs_active_max, axis=1)
        target_hh_active_baselined *= np.tile(target_daily_active_df["consumption_baselined"] / target_hh_active_baselined.sum(axis=1), (48,1)).T
        target_hh_df[target_active_mask] = target_hh_active_baselined + np.tile(target_daily_active_df["offsets"] / 48, (48, 1)).T
        # target_hh_df[target_active_mask] = target_hh_df[target_active_mask].clip(
        #     hh_obs_active_min,
        #     hh_obs_active_max,
        #     axis=1)
        target_hh_inactive_baselined = target_hh_df[~target_active_mask] - np.tile(target_daily_inactive_df.to_numpy(dtype=float) / 48, (1, 48))
        target_hh_inactive_baselined = target_hh_inactive_baselined.clip(hh_obs_inactive_min, hh_obs_inactive_max, axis=1)
        target_hh_df[~target_active_mask] = target_hh_inactive_baselined + np.tile(target_daily_inactive_df.to_numpy(dtype=float) / 48, (1, 48))
        target_hh_df[~target_active_mask] *= np.tile(target_daily_inactive_df["consumption_kwh"] / target_hh_df[~target_active_mask].sum(axis=1), (48, 1)).T
        # target_hh_df[~target_active_mask] = target_hh_df[~target_active_mask].clip(
        #     hh_obs_inactive_min,
        #     hh_obs_inactive_max,
        #     axis=1)
    else:
        # scale the defaults according to the median daily (baselined) consumption for in/active days. Use medians because scaling
        # by the min daily (baselined) consumption is nontrivial (min hh value not necessarily in same day as min daily value)
        active_scaling_factor = target_daily_active_df["consumption_baselined"].median() / default_active_daily_bc_med
        inactive_scaling_factor = target_daily_inactive_df.median() / default_inactive_daily_bc_med

        target_hh_active_baselined = target_hh_df[target_active_mask] - np.tile(target_daily_active_df["offsets"] / 48, (48, 1)).T
        target_hh_active_baselined = target_hh_active_baselined.clip(
            active_scaling_factor * hh_default_active_bc_min,
            active_scaling_factor * hh_default_active_bc_max,
            axis=1
            )
        target_hh_active_baselined *= np.tile(target_daily_active_df["consumption_baselined"] / target_hh_active_baselined.sum(axis=1), (48,1)).T
        target_hh_df[target_active_mask] = target_hh_active_baselined + np.tile(target_daily_active_df["offsets"] / 48, (48, 1)).T

        target_hh_inactive_baselined = target_hh_df[~target_active_mask] - np.tile(target_daily_inactive_df.to_numpy(dtype=float) / 48, (1, 48))
        target_hh_inactive_baselined = target_hh_inactive_baselined.clip(
            inactive_scaling_factor * hh_default_inactive_bc_min,
            inactive_scaling_factor * hh_default_inactive_bc_max,
            axis=1
            )
        target_hh_df[~target_active_mask] = target_hh_inactive_baselined + np.tile(target_daily_inactive_df.to_numpy(dtype=float) / 48, (1, 48))
        target_hh_df[~target_active_mask] *= np.tile(target_daily_inactive_df["consumption_kwh"] / target_hh_df[~target_active_mask].sum(axis=1), (48,1)).T

    start_ts = pd.date_range(initial_start_ts, final_end_ts, freq=pd.Timedelta(minutes=30), inclusive="left")
    return HHDataFrame(
        pd.DataFrame(
            index=pd.DatetimeIndex(
                start_ts,
                name="start_ts",
            ),
            # Each row is one day, so we could also express this
            # as a concat over [i, :], but this saves some memory and mucking around.
            data={
                "consumption_kwh": np.ravel(target_hh_df, order="C"),
                "end_ts": start_ts + pd.Timedelta(minutes=30),
                "start_ts": start_ts,
            },
        )
    )


def monthly_to_hh_eload(
    elec_df: MonthlyDataFrame,
    model: VAE,
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
    scalers
        Data preprocessors used by the VAE with the relevant `.fit` method.

    Returns
    -------
    Half hourly pandas dataframe with start_ts, end_ts and consumption_kwh columns
    """
    if elec_df.empty:
        return HHDataFrame(elec_df)

    # If we've already got half hourly data, don't resample for those days
    # (this can sometimes happen as an oddity of resampling)
    is_hh_mask = (elec_df["end_ts"] - elec_df["start_ts"]) < pd.Timedelta(hours=24)
    daily_df = monthly_to_daily_eload(MonthlyDataFrame(elec_df[~is_hh_mask]))
    halfhourly_df = daily_to_hh_eload(daily_df, model=model)
    if not elec_df[is_hh_mask].empty:
        # TODO (2024-09-06 MHJB): make this also not resample for daily data
        halfhourly_df = HHDataFrame(pd.concat([halfhourly_df, elec_df[is_hh_mask]]))
    return HHDataFrame(halfhourly_df.sort_index())


def generate_approx_daily_profiles(
    VAE_model: VAE,
    consumption_scaled: torch.Tensor,
) -> npt.NDArray[np.floating]:
    """
    Use the decoder component of a trained VAE to generate approximate intraday electricity demand profiles.

    The decoder of the VAE_2_0 class takes random draws from the latent distribution as well as daily aggregate values, and
    returns a half-hourly profile for each independent input. The decoder also ostensibly conditions on the start and end
    timestamps for each day, however these are not currently used in practice; we input zero-tensors instead.
    TODO (2025-08-13 JSM): remove timestamp conditioning in VAE_2_0; this is asking too much of the VAE

    The daily aggregate values are provided in consumption_scaled; these should have already been scaled using a
    StandardScaler().

    In the current version of the trained VAE, negative scaled values of consumption_scaled result in poor approximate profiles,
    so we use the absolute value of the scaled consumption in the logic below.
    TODO (2025-08-13 JSM): More intensive training (using more data) might help this.

    Parameters
    ----------
    VAE_model
        A trained instance of the VAE_2_0 class of model
    consumption_scaled
        A tensor containing the scaled daily aggregate electricity consumption for each required profile

    Returns
    -------
    vae_output
        A numpy array containing an approximate (scaled) half-hourly profile in each row.
        There are consumption_scaled.shape[0] rows / profiles and 48 columns.
    """
    # generate a normalised approximate profile for each active day
    VAE_model.eval()
    with torch.no_grad():
        # Sample from the latent distribution, MV Gaussian with mean 0 and variance 1.
        # This should be of shape [1, days in dataset, latent_dim]
        zs = torch.randn(size=[1, consumption_scaled.shape[0], VAE_model.latent_dim], dtype=torch.float32)

        # Use the decoder part of the VAE, with random latent space (so it's not always the same)
        # and some conditioning variables.
        vae_output_tf = VAE_model.decode(zs, torch.abs(consumption_scaled), torch.zeros(1, 13), torch.zeros(1, 13), seq_len=48)
    vae_output = vae_output_tf.squeeze().detach().cpu().numpy()

    # get rid of profiles that are negative and most profiles that start before 7am or end after 8pm
    active_day_first_hh = 14  # 07:00 - 07:30
    active_day_last_hh = -9  # 19:30 - 20:00
    problem_inds = np.where(
        (np.sum(vae_output[:, :active_day_first_hh], axis=1) > 0.05)
        | (np.sum(vae_output[:, active_day_last_hh + 1 :], axis=1) > 0.05)
        | (np.sum(vae_output, axis=1) < 0.1)
    )[0]
    while len(problem_inds) > 5:
        zs = torch.randn(size=[1, len(problem_inds), VAE_model.latent_dim], dtype=torch.float32)
        # Use the decoder part of the VAE, with random latent space (so it's not always the same)
        # and some conditioning variables.
        vae_output_new_tf = VAE_model.decode(
            zs, torch.abs(consumption_scaled[problem_inds]), torch.zeros(1, 13), torch.zeros(1, 13), seq_len=48
        )
        vae_output_new = vae_output_new_tf.squeeze().detach().cpu().numpy()
        vae_output[problem_inds, :] = vae_output_new
        problem_inds = np.where(
            (np.sum(vae_output[:, :active_day_first_hh], axis=1) > 0.05)
            | (np.sum(vae_output[:, active_day_last_hh + 1 :], axis=1) > 0.05)
            | (np.sum(vae_output, axis=1) < 0.1)
        )[0]

    return vae_output
