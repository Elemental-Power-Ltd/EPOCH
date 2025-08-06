"""Synthetic data generation for electricity meters, using a VAE model."""

import datetime
import enum
import json
import pathlib
from collections.abc import Container

import numpy as np
import pandas as pd
import sklearn.preprocessing  # type: ignore
import torch
from statsmodels.tsa.arima_process import ArmaProcess

from app.internal.epl_typing import DailyDataFrame, HHDataFrame, MonthlyDataFrame

from .model_utils import ScalerTypeEnum, fit_residual_model, load_all_scalers, split_and_baseline_active_days
from .vae import VAE
from .vae_2_0 import VAE as VAE_2_0


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

        # TODO (2024-09-30 JSM): time now encoded using 13 radial basis functions.
        # Let's discuss whether this is the best encoding method.
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
            # Each row is one day, so we could also express this
            # as a concat over [i, :], but this saves some memory and mucking around.
            data={
                "consumption_kwh": np.ravel(result, order="C"),
                "end_ts": start_ts + pd.Timedelta(minutes=30),
                "start_ts": start_ts,
            },
        )
    )


def daily_to_hh_eload_2_0(
    daily_df: DailyDataFrame, scalers: dict[ScalerTypeEnum, sklearn.preprocessing.StandardScaler], model: VAE_2_0
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
        batch_size, n_days = 1, daily_df.shape[0]
        zs = torch.randn(size=[batch_size, n_days, model.latent_dim], dtype=torch.float32)

        # Use the decoder part of the LSTM, with random latent space (so it's not always the same)
        # and some conditioning variables.
        result_scaled = model.decode(zs, consumption_scaled, start_date_scaled, end_date_scaled, seq_len=48)

        # but as we used scaled data all the way through, unscale it here.
        print(result_scaled.squeeze().detach().numpy().shape)
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
            # Each row is one day, so we could also express this
            # as a concat over [i, :], but this saves some memory and mucking around.
            data={
                "consumption_kwh": np.ravel(result, order="C"),
                "end_ts": start_ts + pd.Timedelta(minutes=30),
                "start_ts": start_ts,
            },
        )
    )

def daily_to_hh_eload_3_0(
    daily_df: DailyDataFrame,
    model: VAE_2_0,
    resid_model_path: pathlib.Path | None = None, # partial path to the files describing the residual models
    target_hh_observed_df: HHDataFrame | None = None,
    weekend_inds: tuple = (6,),
    division: str = "england-and-wales",
) -> HHDataFrame:
    """
    Turn a set of daily electricity usages into half hourly meter data.

    ...
    target_hh_observed_df must correspond to dates provided in daily_df

    Parameters
    ----------
    daily_df
        Dataframe with start_ts, end_ts and electricity consumption readings in kWh
    model
        A model, probably a VAE, with a decode method and some latent dimension.
        resid_model_path
            This is a pathlib.Path object that gives the path + model identifier for the set of model files
            that are to be used as a default model for the residuals.
            e.g. resid_model_path = pathlib.Path('/path/to/directory') / 'QB'
            when using the Queen's Buildings to train the residual models

    Returns
    -------
    .
    """
    if (resid_model_path is None) == (target_hh_observed_df is None):
        raise ValueError("Exactly one of 'resid_model_path' or 'target_hh_observed_df' must be provided.")

    if target_hh_observed_df is None:
        use_client_hh = False
    else:
        use_client_hh = True

    # extract 'start_ts' from first record in daily_df, for later use, and discard 'start_ts', 'end_ts' columns
    initial_start_ts = daily_df.start_ts.min()
    final_end_ts = daily_df.end_ts.max()
    daily_df = daily_df.drop(columns=['start_ts', 'end_ts'])


    timestamp_headers = pd.date_range("00:00", "23:30", freq="30min").time

    # split daily data into active and inactive days; remove baseline from active days
    target_daily_active_df, target_daily_inactive_df = split_and_baseline_active_days(
        daily_df, weekend_inds=weekend_inds, division=division
    )

    # scale the baselined daily consumption data for active days, using a *new* StandardScaler
    aggregate_scaler_new = sklearn.preprocessing.StandardScaler()
    consumption_scaled = torch.tensor(
        aggregate_scaler_new.fit_transform(target_daily_active_df["consumption_baselined"].to_numpy().reshape(-1,1)),
        dtype=torch.float32
    )

    # generate a normalised approximate profile for each active day
    vae_output_np = generate_approx_daily_profiles(model, consumption_scaled)

    # rescale baseline / peak of approximate profiles to match daily aggregates
    #   - do this before adding noise to avoid overly scaling the noise
    scaling_factors = target_daily_active_df["consumption_baselined"] / np.sum(vae_output_np, axis=1)
    hh_active_approx_df = pd.DataFrame(
        np.tile(target_daily_active_df["offsets"]/48, (48, 1)).T + vae_output_np*np.tile(scaling_factors, (48, 1)).T,
        columns=timestamp_headers,
        index=target_daily_active_df.index
    )

    # generate hh profiles for inactive days - just divide daily values by 48
    hh_inactive_approx_df = pd.DataFrame(
        np.tile(target_daily_inactive_df.to_numpy(dtype=float) / 48, (1,48)),
        columns=timestamp_headers,
        index=target_daily_inactive_df.index
    )

    # create copy of dataframe to hold final data
    target_hh_df = pd.concat([hh_inactive_approx_df, hh_active_approx_df], axis=0).sort_index()

    if use_client_hh:
        # split client hh data into active and inactive days
        target_hh_obs_active = target_hh_observed_df.loc[np.isin(target_hh_observed_df.index, hh_active_approx_df.index)]
        target_hh_obs_inactive = target_hh_observed_df.loc[np.isin(target_hh_observed_df.index, hh_inactive_approx_df.index)]
        # baseline all days (active and inactive):
        # - for active days, this is subtracting the 'offset' calculated using the appropriate nearest inactive day
        # - for inactive days, this is simply centering the data / zeroing the daily mean
        target_hh_obs_baselined = target_hh_observed_df[timestamp_headers]
        target_hh_obs_baselined.loc[target_hh_obs_active.index] = target_hh_obs_baselined.loc[target_hh_obs_active.index].sub(
            target_daily_active_df.loc[np.isin(target_daily_active_df.index, target_hh_observed_df.index),"offsets"]/48, axis=0
        )
        target_hh_obs_baselined.loc[target_hh_obs_inactive.index] = target_hh_obs_baselined.loc[
            target_hh_obs_inactive.index
            ].sub(
                target_hh_obs_baselined.loc[target_hh_obs_inactive.index].mean(axis=1), axis=0
            )

        # then establish the residuals, assuming that these limited data are to be modelled using the generated VAE output
        # - vae_output used to model the intraday profile on active days; baselined inactive days are simply relabelled here
        target_hh_active_residuals = target_hh_obs_baselined.loc[
                np.isin(target_hh_obs_baselined.index, hh_active_approx_df.index)
            ] - vae_output_np[:target_hh_obs_active.shape[0],:]
        target_hh_inactive_residuals = target_hh_obs_baselined.loc[
                np.isin(target_hh_obs_baselined.index, hh_inactive_approx_df.index)
            ]

        # then model the residuals: extract the trend and fit an ARMA model to the noise
        target_hh_inactive_residtrend_df, ARMA_model_inactive, ARMA_scale_inactive \
            = fit_residual_model(target_hh_inactive_residuals, verbose=True)
        target_hh_active_residtrend_df, ARMA_model_active, ARMA_scale_active \
            = fit_residual_model(target_hh_active_residuals, verbose=True)
    else:
        # load defaults for the residual trends, ARMA noise models, and the std devation of the daily data for active days
        # that was used to train these defaults
        # TODO (JSM 2025-08-06) Should we move all logic for loading residual models to .model_utils?
        with open(resid_model_path.with_name(resid_model_path.name + '_ARMA_model_inactive.json')) as f:
            ARMA_model_inactive_dict = json.load(f)
        with open(resid_model_path.with_name(resid_model_path.name + '_ARMA_model_active.json')) as f:
            ARMA_model_active_dict = json.load(f)

        default_hh_active_residtrend_df = pd.read_csv(
            resid_model_path.with_name(resid_model_path.name + '_residtrend_active.csv')
            )
        default_hh_inactive_residtrend_df = pd.read_csv(
            resid_model_path.with_name(resid_model_path.name + '_residtrend_inactive.csv')
            )
        ARMA_model_active = ArmaProcess(ARMA_model_active_dict["ar_params"], ARMA_model_active_dict["ma_params"])
        ARMA_model_inactive = ArmaProcess(ARMA_model_inactive_dict["ar_params"], ARMA_model_inactive_dict["ma_params"])
        ARMA_scale_active = ARMA_model_active_dict["sigma"]
        ARMA_scale_inactive = ARMA_model_inactive_dict["sigma"]
        reference_hourly_active_std = ARMA_model_active_dict["hourly_active_std"]


    # add fitted trends
    if use_client_hh:
        target_hh_df.loc[target_daily_inactive_df.index] = target_hh_df.loc[target_daily_inactive_df.index] + \
            np.tile(target_hh_inactive_residtrend_df, (target_daily_inactive_df.shape[0],1))
        target_hh_df.loc[target_daily_active_df.index] = target_hh_df.loc[target_daily_active_df.index] + \
            np.tile(target_hh_active_residtrend_df, (target_daily_active_df.shape[0],1))
    else:
        target_hh_df.loc[target_daily_inactive_df.index] = target_hh_df.loc[target_daily_inactive_df.index] + \
            np.tile(default_hh_inactive_residtrend_df, (target_daily_inactive_df.shape[0],1))
        target_hh_df.loc[target_daily_active_df.index] = target_hh_df.loc[target_daily_active_df.index] + \
            np.tile(default_hh_active_residtrend_df, (target_daily_active_df.shape[0],1))

    # Add noise from fitted ARMA distributions
    ## - first, if needed, scale the ARMA_scale_* parameters using the daily aggregate values for the target site
    if not use_client_hh:
        ARMA_scale_active_target = ARMA_scale_active * \
            target_daily_active_df["consumption_baselined"].std() / reference_hourly_active_std
        ARMA_scale_inactive_target = ARMA_scale_active_target.copy()
    else:
        # don't rescale -- if we've used (some) hh data from the client, this is as good as we're going to get
        ARMA_scale_inactive_target = ARMA_scale_inactive
        ARMA_scale_active_target = ARMA_scale_active

    ## - then pre-generate white noise to reduce runtime...
    num_inactive = target_daily_inactive_df.shape[0]
    eps = np.random.normal(scale = ARMA_scale_inactive_target, size=(num_inactive, 48))
    sims = np.empty_like(eps)
    ## ...generate ARMA realisations...
    for i in range(num_inactive):
        sims[i] = ARMA_model_inactive.generate_sample(
            nsample=48,
            scale=1.0,
            distrvs=lambda size, e=eps[i]: e
        )
    ## ...and add the generated noise to the approximate profiles
    target_hh_df.loc[target_daily_inactive_df.index] = target_hh_df.loc[target_daily_inactive_df.index] + sims

    ## - repeat for active dates
    num_active = target_daily_active_df.shape[0]
    eps = np.random.normal(scale = ARMA_scale_active_target, size=(num_active, 48))
    sims = np.empty_like(eps)
    for i in range(num_active):
        sims[i] = ARMA_model_active.generate_sample(
            nsample=48,
            scale=1.0,
            distrvs=lambda size, e=eps[i]: e
        )
    target_hh_df.loc[target_daily_active_df.index] = target_hh_df.loc[target_daily_active_df.index] + sims

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

def generate_approx_daily_profiles(
        VAE_model: VAE_2_0,
        consumption_scaled
):
    """Docstring."""
    # generate a normalised approximate profile for each active day
    VAE_model.eval()
    with torch.no_grad():
        # Sample from the latent distribution, MV Gaussian with mean 0 and variance 1.
        # This should be of shape [1, days in dataset, latent_dim]
        zs = torch.randn(
            size=[1, consumption_scaled.shape[0], VAE_model.latent_dim], dtype=torch.float32
        )

        # Use the decoder part of the VAE, with random latent space (so it's not always the same)
        # and some conditioning variables.
        # TODO JSM : note about absolute values, note about zero time inputs
        vae_output = VAE_model.decode(
            zs, torch.abs(consumption_scaled), torch.zeros(1,13), torch.zeros(1,13), seq_len=48
        )
    vae_output = vae_output.squeeze().detach().cpu().numpy()

    # get rid of profiles that are negative and most profiles that start before 7am or end after 8pm
    problem_inds = np.where(
        (np.sum(vae_output[:,:14], axis=1)>0.05) |
        (np.sum(vae_output[:,-8:], axis=1)>0.05) |
        (np.sum(vae_output, axis=1)<0.1)
    )[0]
    while len(problem_inds)>5:
        zs = torch.randn(
            size=[1, len(problem_inds), VAE_model.latent_dim], dtype=torch.float32
        )
        # Use the decoder part of the VAE, with random latent space (so it's not always the same)
        # and some conditioning variables.
        vae_output_new = VAE_model.decode(
            zs, torch.abs(consumption_scaled[problem_inds]), torch.zeros(1,13), torch.zeros(1,13), seq_len=48
        )
        vae_output_new = vae_output_new.squeeze().detach().cpu().numpy()
        vae_output[problem_inds,:] = vae_output_new
        problem_inds = np.where(
            (np.sum(vae_output[:,:14], axis=1)>0.05) |
            (np.sum(vae_output[:,-8:], axis=1)>0.05) |
            (np.sum(vae_output, axis=1)<0.1)
        )[0]

    return vae_output
