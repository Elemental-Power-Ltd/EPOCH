"""
Data preprocessing module for time series upsampling.

This module provides functions for preparing data for the TransformerVAE model,
including loading, cleaning and sequence preparation.
"""

from pathlib import Path
from typing import TypedDict

import numpy as np
import numpy.typing as npt
import pandas as pd
import torch
from govuk_bank_holidays.bank_holidays import BankHolidays  # type: ignore
from scipy.stats import median_abs_deviation
from sklearn.preprocessing import StandardScaler  # type: ignore
from torch.utils.data import DataLoader, Dataset

from app.internal.elec_meters.model_utils import CustomMinMaxScaler, RBFTimestampEncoder


class SplitDataDict(TypedDict):  # noqa: D101
    hh_train: npt.NDArray[np.floating]
    daily_train: npt.NDArray[np.floating]
    start_times_train: npt.NDArray[np.floating]
    end_times_train: npt.NDArray[np.floating]
    unscaled_start_times_train: npt.NDArray[np.floating]
    unscaled_end_times_train: npt.NDArray[np.floating]
    hh_val: npt.NDArray[np.floating]
    daily_val: npt.NDArray[np.floating]
    start_times_val: npt.NDArray[np.floating]
    end_times_val: npt.NDArray[np.floating]
    unscaled_start_times_val: npt.NDArray[np.floating]
    unscaled_end_times_val: npt.NDArray[np.floating]
    hh_test: npt.NDArray[np.floating]
    daily_test: npt.NDArray[np.floating]
    start_times_test: npt.NDArray[np.floating]
    end_times_test: npt.NDArray[np.floating]
    data_scaler_train: CustomMinMaxScaler | None
    data_scaler_val: CustomMinMaxScaler | None
    data_scaler_test: CustomMinMaxScaler | None
    aggregate_scaler: StandardScaler | None
    start_time_scaler: RBFTimestampEncoder
    end_time_scaler: RBFTimestampEncoder
    unscaled_start_times_test: npt.NDArray[np.floating]
    unscaled_end_times_test: npt.NDArray[np.floating]
    hh_train_scales: npt.NDArray[np.floating] | None
    hh_train_mins: npt.NDArray[np.floating] | None
    hh_val_scales: npt.NDArray[np.floating] | None
    hh_val_mins: npt.NDArray[np.floating] | None
    hh_test_scales: npt.NDArray[np.floating] | None
    hh_test_mins: npt.NDArray[np.floating] | None


class DataPipelineDict(TypedDict):  # noqa: D101
    train_loader: DataLoader
    val_loader: DataLoader
    test_loader: DataLoader
    features_dim: int
    hh_train: npt.NDArray[np.floating]
    daily_train: npt.NDArray[np.floating]
    unscaled_start_times_train: npt.NDArray[np.floating]
    unscaled_end_times_train: npt.NDArray[np.floating]
    hh_val: npt.NDArray[np.floating]
    daily_val: npt.NDArray[np.floating]
    unscaled_start_times_val: npt.NDArray[np.floating]
    unscaled_end_times_val: npt.NDArray[np.floating]
    hh_test: npt.NDArray[np.floating]
    daily_test: npt.NDArray[np.floating]
    unscaled_start_times_test: npt.NDArray[np.floating]
    unscaled_end_times_test: npt.NDArray[np.floating]
    data_scaler_train: CustomMinMaxScaler | None
    data_scaler_val: CustomMinMaxScaler | None
    data_scaler_test: CustomMinMaxScaler | None
    aggregate_scaler: StandardScaler | None
    start_time_scaler: RBFTimestampEncoder | None
    end_time_scaler: RBFTimestampEncoder | None
    dbg_loadeddata: pd.DataFrame
    dbg_cleaneddata: pd.DataFrame
    dbg_hhdata: npt.NDArray[np.floating]


class TimeSeriesDataset(Dataset):
    """Dataset class for time series data with half-hourly values and daily aggregates."""

    def __init__(
        self,
        hh_data: npt.NDArray[np.floating],
        daily_data: npt.NDArray[np.floating],
        start_times: npt.NDArray[np.floating],
        end_times: npt.NDArray[np.floating],
    ):
        """
        Initialize the dataset.

        Parameters
        ----------
            hh_data: tensor of half-hourly data with shape [n_samples, n_days, 48, features]
            daily_data: tensor of daily aggregates with shape [n_samples, n_days, features]
            start_times: tensor of start timestamps with shape [n_samples, n_days, features]
            end_times: tensor of end timestampes with shape [n_samples, n_days, features]

        NB: samples comprise multiple days of half hourly data; batches are formed over all multi-day samples
        """
        self.hh_data = hh_data
        self.daily_data = daily_data
        self.start_times = start_times
        self.end_times = end_times

        # Calculate derived properties
        self.n_samples = hh_data.shape[0]
        self.n_days = daily_data.shape[1]

    def __len__(self) -> int:
        """Magic method to return the number of samples in the time series data class."""
        return int(self.n_samples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        """
        Magic getitem method to extract one sample from the time series data class.

        Parameters
        ----------
            idx: Index of the sample

        Returns
        -------
            A dict containing the half-hourly and daily data, along with the start and end times for the sample
        """
        return {
            "data": torch.tensor(self.hh_data[idx], dtype=torch.float),
            "aggregate": torch.tensor(self.daily_data[idx], dtype=torch.float),
            "start_time": torch.tensor(self.start_times[idx], dtype=torch.float),  # UNIX time, in seconds
            "end_time": torch.tensor(self.end_times[idx], dtype=torch.float),  # UNIX time, in seconds
        }


def load_time_series(file_path: Path, date_column: str = "date", value_column: str | None = None) -> pd.DataFrame:
    """
    Load time series data from a file. If multiple value columns are available, the relevant column should be specified.

    Parameters
    ----------
    file_path
        Path to the data file
    date_column
        Name of the date column
    value_column
        Name of the value column

    Returns
    -------
        DataFrame with time series data
    """
    # Load data
    if value_column is None:
        df = pd.read_csv(file_path)
    else:
        df = pd.read_csv(file_path, usecols=[date_column, value_column])

    # Convert date column to datetime
    df[date_column] = pd.to_datetime(df[date_column], format="mixed")

    return df.set_index(date_column).sort_index()


def clean_time_series(
    df: pd.DataFrame, value_column: str = "value", handle_outliers: bool = True, z_score_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Clean time series data by handling missing values and outliers.

    Parameters
    ----------
    df
        DataFrame with time series data
    value_column
        Name of the value column
    handle_outlier
        Whether to handle outliers
    z_score_threshold
        Robust Z-score threshold for outlier detection

    Returns
    -------
        Cleaned DataFrame
    """
    assert isinstance(df.index, pd.DatetimeIndex), "Index must be datetime"

    # Make a copy to avoid modifying the original
    df_clean = df.copy()

    # Assume df has a datetime index with regular frequency but could be missing timestamps
    # freq = df_clean.index.to_series().diff().mode()[0]
    diffs = df_clean.index.to_series().diff()
    modes = diffs.mode()
    if not modes.empty and isinstance(modes[0], pd.Timedelta):
        freq: pd.Timedelta = modes[0]  # type: ignore
    else:
        freq = pd.Timedelta(minutes=30)  # default to half-hourly

    full_index = pd.date_range(start=df_clean.index.min(), end=df_clean.index.max(), freq=freq)
    df_clean = df_clean.reindex(full_index)

    # Handle missing values for any gaps up to 3H
    # Apply a label to <=3H contiguous blocks of rows with missing samples
    gap = df.index.to_series().diff().gt(pd.Timedelta("3h"))
    big_gap_mask = gap.cumsum().ffill()
    #  apply interpolation only within blocks identified by the mask
    df_clean[value_column] = df_clean.groupby(big_gap_mask)[value_column].transform(lambda x: x.interpolate(method="time"))

    # Handle outliers if requested
    if handle_outliers:
        # Calculate robust z-scores, unless MAD=0, in which case use regular z-scores
        mad = median_abs_deviation(df_clean[value_column])
        if mad == 0:
            z_scores = np.abs((df_clean[value_column] - df_clean[value_column].median()) / df_clean[value_column].std())
        else:
            z_scores = np.abs((df_clean[value_column] - df_clean[value_column].median()) / mad)  # type: ignore

        # Identify outliers
        outliers = z_scores > z_score_threshold

        if outliers.any():
            # Replace outliers with rolling median
            # TODO (JSM: 2025-05-05) There is probably a more appropriate way to deal with outliers
            window_size = 7  # One week
            df_clean.loc[outliers, value_column] = (
                df_clean[value_column].rolling(window=window_size, center=True, min_periods=1).median()
            )

    return df_clean


def add_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add covariates to a dataframe which marks if a day is a holiday or weekend.

    Parameters
    ----------
    df
        Dataframe with datetime index

    Returns
    -------
        Pandas dataframe with new columns including `is_hol_or_wknd`
    """
    assert isinstance(df.index, pd.DatetimeIndex)
    # Fetch UK bank holidays and convert dates to a set for fast lookup
    bh = BankHolidays(use_cached_holidays=True)
    uk_holidays = bh.get_holidays()
    holiday_dates = frozenset(pd.Timestamp(event["date"]) for event in uk_holidays)

    def is_holiday_or_weekend(date: pd.Timestamp) -> bool:
        """
        Check if this date is a public holiday, or on a weekend.

        Parameters
        ----------
        date
            Pandas datetime to check

        Returns
        -------
            True if bank holiday, Saturday or Sunday.
        """
        return date in holiday_dates or date.weekday() >= 5

    df["is_hol_or_wknd"] = df.index.to_series().apply(is_holiday_or_weekend)
    df["contains_NaNs"] = df.isna().any(axis=1)
    df["day_of_wk"] = df.index.day_name()
    return df


def create_hh_daily_data(
    df: pd.DataFrame, value_column: str = "value"
) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
    """
    Create half-hourly and daily data arrays from a DataFrame containing hh values.

    Parameters
    ----------
    df
        DataFrame with half-hourly time series data
    value_column
        Name of the value column giving the hh meter reading

    Returns
    -------
        Tuple of (hh_data, daily_data, start_times, end_times)
    """
    # Ensure data is sorted by date
    df = df.sort_index()

    # Group by day
    # daily_groups = df.groupby(pd.Grouper(freq='D'))
    # pd.Grouper(freq='D') drops days that are entirely NaN; we do not want this
    daily_groups = df.resample("D")

    # Create daily aggregates (sum for the value column)
    daily_list = []
    for _, group in daily_groups:
        if value_column in group.columns:
            # Sum the value column
            daily_sum = group[value_column].sum(min_count=48)  # min_count=48 ensures that nans are preserved through the sum
            daily_list.append(daily_sum)

    daily_data = np.array(daily_list).reshape(-1, 1)

    # create start and end timestamps for each day's data; should be same length as daily_data
    start_times = daily_groups.first().index.astype(np.int64) // 10**9
    # UNIX timestamps -- seconds since 1970-01-01T00:00:00
    end_times = start_times + (24 * 60 * 60)  # end times

    start_times_arr = start_times.to_numpy().reshape(-1, 1)
    end_times_arr = end_times.to_numpy().reshape(-1, 1)

    # Create rectangular matrix for hh data
    daily_groups = daily_groups.apply(lambda x: x.tolist())  # type: ignore
    hh_data = np.array(pd.DataFrame(daily_groups.iloc[:, 0].tolist(), index=daily_groups.index))  # type: ignore

    return hh_data, daily_data, start_times_arr, end_times_arr


def create_sliding_windows(data: npt.NDArray[np.floating], window_size: int, stride: int = 1) -> npt.NDArray[np.floating]:
    """
    Create sliding windows from a time series.

    Parameters
    ----------
    data
        Time series data array
    window_size
        Size of each window
    stride
        Stride between consecutive windows

    Returns
    -------
        Array of sliding windows
    """
    n_samples = (len(data) - window_size) // stride + 1
    windows = []

    for i in range(n_samples):
        start_idx = i * stride
        end_idx = start_idx + window_size
        windows.append(data[start_idx:end_idx])

    return np.array(windows)


def split_data(
    hh_data: npt.NDArray[np.floating],
    daily_data: npt.NDArray[np.floating],
    start_times: npt.NDArray[np.floating],
    end_times: npt.NDArray[np.floating],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    normalize: bool = True,
    window_size: int = 7,
    window_stride: int = 2,
) -> SplitDataDict:
    """
    Split data into train, validation, and test sets, fit any necessary scalers and augment data using sliding windows.

    Parameters
    ----------
    hh_data
        Array of half-hourly values of shape [n_days, 48, features]
    daily_data
        Array of daily aggregates of shape [n_days, 1, features]
    start_times
        Array of start timestamps with shape [n_days, 1]
    end_times
        Array of end timestamps with shape [n_days, 1]
    train_ratio
        Ratio of data to use for training of shape [n_days, 1]
    val_ratio
        Ratio of data to use for validation of shape [n_days, 1]
    normalize
        Whether to normalize / scale the data
    window_size
        size of sliding window to use for creating multi-day samples
    window_stride
        stride to use in sliding window for creating multi-day samples

    Returns
    -------
        Dictionary containing data np.ndarrays: daily, half-hourly data and daily start/end timestamps
    """
    n_features = hh_data.shape[2]
    n_days = daily_data.shape[0]
    indices = np.arange(n_days)

    # Calculate split points
    train_end = int(n_days * train_ratio)
    val_end = int(n_days * (train_ratio + val_ratio))

    # Split data
    hh_train = hh_data[indices[:train_end]]
    daily_train = daily_data[indices[:train_end]]
    unscaled_start_times_train = start_times[indices[:train_end]]  # store the unscaled versions for returning
    unscaled_end_times_train = end_times[indices[:train_end]]

    hh_val = hh_data[indices[train_end:val_end]]
    daily_val = daily_data[indices[train_end:val_end]]
    unscaled_start_times_val = start_times[indices[train_end:val_end]]
    unscaled_end_times_val = end_times[indices[train_end:val_end]]

    hh_test = hh_data[indices[val_end:]]
    daily_test = daily_data[indices[val_end:]]
    unscaled_start_times_test = start_times[indices[val_end:]]
    unscaled_end_times_test = end_times[indices[val_end:]]

    # Fit scalers to training data if requested
    data_scaler_train = None
    data_scaler_val = None
    data_scaler_test = None
    aggregate_scaler = None
    hh_train_scales = None
    hh_train_mins = None
    hh_val_scales = None
    hh_val_mins = None
    hh_test_scales = None
    hh_test_mins = None
    if normalize:
        # Fit scalers to training data; use separate scalers for each dataset
        # data_scaler = StandardScaler()
        data_scaler_train = CustomMinMaxScaler(axis=1)
        aggregate_scaler = StandardScaler()
        # hh_train = data_scaler.fit_transform(hh_train.reshape(train_end, 48*n_features))
        # hh_train = data_scaler.fit_transform(hh_train.reshape(train_end*48*n_features, 1))
        hh_train = data_scaler_train.fit_transform(hh_train.reshape(train_end, 48 * n_features))
        hh_train_scales = data_scaler_train.scale_
        hh_train_mins = data_scaler_train.min_
        hh_train = hh_train.reshape(train_end, 48, n_features)
        daily_train = aggregate_scaler.fit_transform(daily_train.reshape(train_end, n_features))
        daily_train = daily_train.reshape(train_end, 1, n_features)

        # Apply fitted scalers to validation and test sets
        # hh_val = data_scaler.transform(hh_val.reshape((val_end-train_end), 48*n_features))
        # hh_val = data_scaler.transform(hh_val.reshape((val_end-train_end)*48*n_features, 1))
        data_scaler_val = CustomMinMaxScaler(axis=1)
        hh_val = data_scaler_val.fit_transform(hh_val.reshape((val_end - train_end), 48 * n_features))
        hh_val_scales = data_scaler_val.scale_
        hh_val_mins = data_scaler_val.min_
        hh_val = hh_val.reshape((val_end - train_end), 48, n_features)
        daily_val = aggregate_scaler.transform(daily_val.reshape((val_end - train_end), n_features))
        daily_val = daily_val.reshape((val_end - train_end), 1, n_features)

        # hh_test = data_scaler.transform(hh_test.reshape((n_days-val_end), 48*n_features))
        # hh_test = data_scaler.transform(hh_test.reshape((n_days-val_end)*48*n_features, 1))
        data_scaler_test = CustomMinMaxScaler(axis=1)
        hh_test = data_scaler_test.fit_transform(hh_test.reshape((n_days - val_end), 48 * n_features))
        hh_test_scales = data_scaler_test.scale_
        hh_test_mins = data_scaler_test.min_
        hh_test = hh_test.reshape((n_days - val_end), 48, n_features)
        daily_test = aggregate_scaler.transform(daily_test.reshape((n_days - val_end), n_features))
        daily_test = daily_test.reshape((n_days - val_end), 1, n_features)

    # Always transform the start and end times
    start_time_scaler = RBFTimestampEncoder(n_periods=13, input_range=(1, 365))
    end_time_scaler = RBFTimestampEncoder(n_periods=13, input_range=(1, 365))
    start_times_train = start_time_scaler.fit_transform(unscaled_start_times_train)
    end_times_train = end_time_scaler.fit_transform(unscaled_end_times_train)
    start_times_val = start_time_scaler.transform(unscaled_start_times_val)
    end_times_val = end_time_scaler.transform(unscaled_end_times_val)
    start_times_test = start_time_scaler.transform(unscaled_start_times_test)
    end_times_test = end_time_scaler.transform(unscaled_end_times_test)

    # create multi-day samples within train/val/test sets using a sliding window
    hh_train = create_sliding_windows(hh_train, window_size, window_stride)
    daily_train = create_sliding_windows(daily_train, window_size, window_stride)
    start_times_train = create_sliding_windows(start_times_train, window_size, window_stride)
    end_times_train = create_sliding_windows(end_times_train, window_size, window_stride)
    unscaled_start_times_train = create_sliding_windows(unscaled_start_times_train, window_size, window_stride)
    unscaled_end_times_train = create_sliding_windows(unscaled_end_times_train, window_size, window_stride)

    hh_val = create_sliding_windows(hh_val, window_size, window_stride)
    daily_val = create_sliding_windows(daily_val, window_size, window_stride)
    start_times_val = create_sliding_windows(start_times_val, window_size, window_stride)
    end_times_val = create_sliding_windows(end_times_val, window_size, window_stride)
    unscaled_start_times_val = create_sliding_windows(unscaled_start_times_val, window_size, window_stride)
    unscaled_end_times_val = create_sliding_windows(unscaled_end_times_val, window_size, window_stride)

    hh_test = create_sliding_windows(hh_test, window_size, window_stride)
    daily_test = create_sliding_windows(daily_test, window_size, window_stride)
    start_times_test = create_sliding_windows(start_times_test, window_size, window_stride)
    end_times_test = create_sliding_windows(end_times_test, window_size, window_stride)
    unscaled_start_times_test = create_sliding_windows(unscaled_start_times_test, window_size, window_stride)
    unscaled_end_times_test = create_sliding_windows(unscaled_end_times_test, window_size, window_stride)

    # until now, missing data (nans) have been kept in to preserve time ordering
    # some days will contain nans and these will appear in multiple multi-day windows
    # remove these now
    to_drop = np.where(np.isnan(daily_train))[0]
    if to_drop.size != 0:
        hh_train = np.delete(hh_train, to_drop, axis=0)
        daily_train = np.delete(daily_train, to_drop, axis=0)
        start_times_train = np.delete(start_times_train, to_drop, axis=0)
        end_times_train = np.delete(end_times_train, to_drop, axis=0)
        unscaled_start_times_train = np.delete(unscaled_start_times_train, to_drop, axis=0)
        unscaled_end_times_train = np.delete(unscaled_end_times_train, to_drop, axis=0)
    to_drop = np.where(np.isnan(daily_val))[0]
    if to_drop.size != 0:
        hh_val = np.delete(hh_val, to_drop, axis=0)
        daily_val = np.delete(daily_val, to_drop, axis=0)
        start_times_val = np.delete(start_times_val, to_drop, axis=0)
        end_times_val = np.delete(end_times_val, to_drop, axis=0)
        unscaled_start_times_val = np.delete(unscaled_start_times_val, to_drop, axis=0)
        unscaled_end_times_val = np.delete(unscaled_end_times_val, to_drop, axis=0)
    to_drop = np.where(np.isnan(daily_test))[0]
    if to_drop.size != 0:
        hh_test = np.delete(hh_test, to_drop, axis=0)
        daily_test = np.delete(daily_test, to_drop, axis=0)
        start_times_test = np.delete(start_times_test, to_drop, axis=0)
        end_times_test = np.delete(end_times_test, to_drop, axis=0)
        unscaled_start_times_test = np.delete(unscaled_start_times_test, to_drop, axis=0)
        unscaled_end_times_test = np.delete(unscaled_end_times_test, to_drop, axis=0)

    # datasets should now have shape [n_samples, n_days, 48, features] or [n_samples, n_days, features]

    # we return the four scaled datasets (hh,daily,start_times,end_times) in their separate splits
    # we also return the fitted scalers
    # since the RBFTimestampEncoder does not have a native .inverse_transform() function, we also return the unscaled timestamps
    return {
        "hh_train": hh_train,
        "daily_train": daily_train,
        "start_times_train": start_times_train,
        "end_times_train": end_times_train,
        "unscaled_start_times_train": unscaled_start_times_train,
        "unscaled_end_times_train": unscaled_end_times_train,
        "hh_val": hh_val,
        "daily_val": daily_val,
        "start_times_val": start_times_val,
        "end_times_val": end_times_val,
        "unscaled_start_times_val": unscaled_start_times_val,
        "unscaled_end_times_val": unscaled_end_times_val,
        "hh_test": hh_test,
        "daily_test": daily_test,
        "start_times_test": start_times_test,
        "end_times_test": end_times_test,
        "data_scaler_train": data_scaler_train,
        "data_scaler_val": data_scaler_val,
        "data_scaler_test": data_scaler_test,
        "aggregate_scaler": aggregate_scaler,
        "start_time_scaler": start_time_scaler,
        "end_time_scaler": end_time_scaler,
        "unscaled_start_times_test": unscaled_start_times_test,
        "unscaled_end_times_test": unscaled_end_times_test,
        "hh_train_scales": hh_train_scales,
        "hh_train_mins": hh_train_mins,
        "hh_val_scales": hh_val_scales,
        "hh_val_mins": hh_val_mins,
        "hh_test_scales": hh_test_scales,
        "hh_test_mins": hh_test_mins,
    }


def create_data_loaders(
    hh_train: npt.NDArray[np.floating],
    daily_train: npt.NDArray[np.floating],
    start_times_train: npt.NDArray[np.floating],
    end_times_train: npt.NDArray[np.floating],
    hh_val: npt.NDArray[np.floating],
    daily_val: npt.NDArray[np.floating],
    start_times_val: npt.NDArray[np.floating],
    end_times_val: npt.NDArray[np.floating],
    batch_size: int = 32,
    num_workers: int = 4,
) -> tuple[DataLoader, DataLoader]:
    """
    Create DataLoader objects for training and validation.

    Parameters
    ----------
    hh_train
        Training half-hourly data
    daily_train
        Training daily data
    start_times_train
        collection of 13-length vector representations of start timestamp for each date; training data
    end_times_train
        collection of 13-length vector representations of end timestamp for each date; training data
    hh_val
        Validation half-hourly data
    daily_val
        Validation daily data
    start_times_val
        collection of 13-length vector representations of start timestamp for each date; validation data
    end_times_val
        collection of 13-length vector representations of end timestamp for each date; validation data
    batch_size
        Batch size
    num_workers
        Number of worker processes

    Returns
    -------
        Tuple of (train_loader, val_loader)
    """
    train_dataset = TimeSeriesDataset(hh_train, daily_train, start_times_train, end_times_train)
    val_dataset = TimeSeriesDataset(hh_val, daily_val, start_times_val, end_times_val)

    # Set the number of threads before DataLoader or any parallel tasks
    torch.set_num_threads(1)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    return train_loader, val_loader


def prepare_data_pipeline(
    file_path: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    batch_size: int = 32,
    normalize: bool = True,
    window_size: int = 7,
    window_stride: int = 2,
    handle_outliers: bool = True,
    date_column: str = "date",
    value_column: str = "value",
) -> DataPipelineDict:
    """
    Complete data preparation pipeline.

    Parameters
    ----------
    file_path
        Path to the data file
    train_ratio
        Ratio of data to use for training
    val_ratio
        Ratio of data to use for validation
    batch_size
        Batch size for data loaders
    normalize
        Whether to normalize the data
    window_size
        size of sliding window to use for creating multi-day samples
    window_stride
        stride to use in sliding window for creating multi-day samples
    handle_outliers
        Whether to handle outliers
    date_column
        Name of the date column
    value_column
        Name of the value column

    Returns
    -------
        Dictionary containing prepared data and metadata
    """
    # Load data
    df = load_time_series(file_path, date_column, value_column)
    df_clean = clean_time_series(df, value_column, handle_outliers=handle_outliers)

    # Create half-hourly and daily data
    hh_data, daily_data, start_times, end_times = create_hh_daily_data(df_clean, value_column)

    features_dim = hh_data.shape[2] if len(hh_data.shape) > 2 else 1

    if hh_data.shape[-1] != features_dim:
        hh_data = hh_data[..., np.newaxis]

    split_data_dict = split_data(
        hh_data, daily_data, start_times, end_times, train_ratio, val_ratio, normalize, window_size, window_stride
    )

    # Create data loaders
    train_loader, val_loader = create_data_loaders(
        split_data_dict["hh_train"],
        split_data_dict["daily_train"],
        split_data_dict["start_times_train"],
        split_data_dict["end_times_train"],
        split_data_dict["hh_val"],
        split_data_dict["daily_val"],
        split_data_dict["start_times_val"],
        split_data_dict["end_times_val"],
        batch_size,
    )

    test_dataset = TimeSeriesDataset(
        split_data_dict["hh_test"],
        split_data_dict["daily_test"],
        split_data_dict["start_times_test"],
        split_data_dict["end_times_test"],
    )

    # Set the number of threads before DataLoader or any parallel tasks
    torch.set_num_threads(1)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)

    return {
        "train_loader": train_loader,
        "val_loader": val_loader,
        "test_loader": test_loader,
        "features_dim": features_dim,
        "hh_train": split_data_dict["hh_train"],
        "daily_train": split_data_dict["daily_train"],
        "unscaled_start_times_train": split_data_dict["unscaled_start_times_train"],
        "unscaled_end_times_train": split_data_dict["unscaled_end_times_train"],
        "hh_val": split_data_dict["hh_val"],
        "daily_val": split_data_dict["daily_val"],
        "unscaled_start_times_val": split_data_dict["unscaled_start_times_val"],
        "unscaled_end_times_val": split_data_dict["unscaled_end_times_val"],
        "hh_test": split_data_dict["hh_test"],
        "daily_test": split_data_dict["daily_test"],
        "unscaled_start_times_test": split_data_dict["unscaled_start_times_test"],
        "unscaled_end_times_test": split_data_dict["unscaled_end_times_test"],
        "data_scaler_train": split_data_dict["data_scaler_train"],
        "data_scaler_val": split_data_dict["data_scaler_val"],
        "data_scaler_test": split_data_dict["data_scaler_test"],
        "aggregate_scaler": split_data_dict["aggregate_scaler"],
        "start_time_scaler": split_data_dict["start_time_scaler"],
        "end_time_scaler": split_data_dict["end_time_scaler"],
        "dbg_loadeddata": df,
        "dbg_cleaneddata": df_clean,
        "dbg_hhdata": hh_data,
    }
