"""Synthetic data generation for electricity meters, using a VAE model."""

import datetime
from datetime import timedelta
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd
import torch

from .model_utils import load_scaler
from .vae import VAE

# Split of days across 3 classes; median aggregate power in each class for a set of office data.
MON2DAY_CLASS_SPLITS = {"Class 1 median": 0.25, "Class 2 median": 0.25, "Class 3 median": 0.19}

DATA_SCALER = load_scaler(Path(".", "models", "final", "elecVAE_data_scaler.joblib"))
AGGREGATE_SCALER = load_scaler(Path(".", "models", "final", "elecVAE_aggregate_scaler.joblib"))
START_TIME_SCALER = load_scaler(Path(".", "models", "final", "elecVAE_start_time_scaler.joblib"))
END_TIME_SCALER = load_scaler(Path(".", "models", "final", "elecVAE_end_time_scaler.joblib"))


def daily_to_hh_eload(
    model: VAE, aggregate: npt.NDArray, start_date: npt.NDArray, end_date: npt.NDArray, num_samples: int = 1
) -> npt.NDArray:
    """
    Generate samples of day-length synthetic HH electricity data, using the decoder component of the VAE.

    This returns a numpy array with one sample in each row.

    Parameters
    ----------
    model (VAE):
        a trained model from the VAE class, which contains a .decoder() method
    aggregate (array):
        the required daily aggregate electricity load
    start_date (array):
        a float array containing the timestamp corresponding to 00:00 at the start of the day
        for which synthetic data is required
    end_date (array):
        a float array containing the timestamp corresponding to 00:00 at the start of the next day
    num_samples (int):
        an int specifying the number of synthetic time series that are required

    Returns
    -------
    synthetic_data (array)
        an array with one sample in each row and 48 columns, containing hh synthetic data for the specified date

    """
    aggregate_scaled = AGGREGATE_SCALER.transform(aggregate)
    start_date_scaled = START_TIME_SCALER.transform(start_date)
    end_date_scaled = END_TIME_SCALER.transform(end_date)

    model.eval()
    with torch.no_grad():
        z = torch.randn(num_samples, model.latent_dim)
        aggregate_scaled = torch.tensor(aggregate_scaled, dtype=torch.float).view(-1, 1).repeat(num_samples, 1)
        start_date_scaled = torch.tensor(start_date_scaled, dtype=torch.float).view(-1, 1).repeat(num_samples, 1)
        end_date_scaled = torch.tensor(end_date_scaled, dtype=torch.float).view(-1, 1).repeat(num_samples, 1)
        synthetic_dat_scaled = model.decode(z, aggregate_scaled, start_date_scaled, end_date_scaled, 48)

    synthetic_data = DATA_SCALER.inverse_transform(synthetic_dat_scaled.squeeze(2))  # Inverse transform to original scale

    # Scale synthetic data to ensure the sum matches the aggregate value
    synthetic_sums = synthetic_data.sum(axis=1, keepdims=True)
    scaling_factors = aggregate / synthetic_sums
    synthetic_data = synthetic_data * scaling_factors

    return synthetic_data


def monthly_to_hh_eload(
    month_labels: pd.Series,
    holiday_dates: pd.Series | frozenset[datetime.date],
    monthly_aggregates: list[float] | npt.NDArray[np.floating],
    model: VAE,
) -> pd.DataFrame:
    """
    Generate samples of month-length synthetic HH electricity data, using the decoder component of a VAE.

    Parameters
    ----------
    month_labels (series)
        a pandas series of datetime entries, with one entry per monthly aggregate; e.g. the date for the first of the month
    holiday_dates (series)
        a pandas series of datetime entries, indicating the date of any public holidays
    monthly_aggregates (list)
        a list containing aggregate values for each month that we wish to generate hh data for
    generate_daily_profile (callable)
        a function to generate hh electricity profiles given a daily aggregate
    model (VAE)
        a trained model from the VAE class, which contains a .decoder() method

    Returns
    -------
    synthetic_data (array)
        an array with one sample in each row and 48 columns, containing hh synthetic data for the specified date
    """
    # Create a date range for the entire period
    start_date = min(month_labels)
    end_date = max(month_labels) + pd.offsets.MonthEnd(1)
    date_range = pd.date_range(
        start=start_date, end=end_date + pd.Timedelta(days=1) - pd.Timedelta(minutes=30), freq=pd.Timedelta(minutes=30)
    )

    # Create a DataFrame with the date range
    df = pd.DataFrame(index=date_range, columns=["consumption"])

    # Convert holiday dates to a set of date objects for faster lookup
    if isinstance(holiday_dates, pd.Series):
        holidays = frozenset(holiday_dates.dt.date)
    else:
        holidays = frozenset(holiday_dates)

    # Iterate through each month
    for month_start, monthly_aggregate in zip(month_labels, monthly_aggregates, strict=True):
        month_end = month_start + pd.offsets.MonthEnd(1)

        # Distribute the monthly aggregate across days
        month_daterange = pd.date_range(month_start, month_end, freq="D")
        # assume three classes of day: Monday/Friday; Tuesday/Weds/Thursday; weekend/public holiday
        # split the monthly aggregate in the ratio
        # (num_class1 * class1_factor) : (num_class2 * class2_factor) : (num_class3 * class3_factor)
        # where the factors for each class are calculated below (using median daily aggs from a training dataset)
        # classfactor = [class1_median, class2_median, class3_median]
        classfactor = [
            MON2DAY_CLASS_SPLITS["Class 1 median"],
            MON2DAY_CLASS_SPLITS["Class 2 median"],
            MON2DAY_CLASS_SPLITS["Class 3 median"],
        ]
        # Calculate the number of Mondays/Fridays in the month
        class1days = sum((date.weekday() in {0, 4}) and (date.date() not in holidays) for date in month_daterange)
        # Calculate the number of Tues/Weds/Thurs in the month
        class2days = sum((date.weekday() in {1, 2, 3}) and (date.date() not in holidays) for date in month_daterange)
        # Calculate the number of weekends / pubhols in the month
        class3days = sum((date.weekday() in {5, 6}) and (date.date() not in holidays) for date in month_daterange) + sum(
            date.date() in holidays for date in month_daterange
        )

        denom = classfactor[0] * class1days + classfactor[1] * class2days + classfactor[2] * class3days
        class1_daily_agg = monthly_aggregate * classfactor[0] / denom
        class2_daily_agg = monthly_aggregate * classfactor[1] / denom
        class3_daily_agg = monthly_aggregate * classfactor[2] / denom

        # Generate half-hourly data for each day in the month
        for day in range(month_start.days_in_month):
            current_date = month_start + timedelta(days=day)
            is_holiday = current_date.date() in holidays

            if is_holiday:
                daily_aggregate = class3_daily_agg
            elif current_date.weekday() in {0, 4}:
                daily_aggregate = class1_daily_agg
            elif current_date.weekday() in {1, 2, 3}:
                daily_aggregate = class2_daily_agg
            elif current_date.weekday() in {5, 6}:
                daily_aggregate = class3_daily_agg

            # Generate half-hourly data for the day
            half_hourly_data = daily_to_hh_eload(
                model,
                np.array(daily_aggregate).reshape(-1, 1),
                np.array([current_date.timestamp()]).reshape(-1, 1),
                np.array([current_date.timestamp() + 86400]).reshape(-1, 1),
                1,
            )  # include isholiday

            # Assign the half-hourly data to the DataFrame
            start_idx = current_date
            end_idx = current_date + timedelta(days=1) - timedelta(minutes=30)
            df.loc[start_idx:end_idx, "consumption"] = half_hourly_data

    return df
