"""Utility functions for loading additional parts for the ML models."""

import itertools
import logging
import pathlib
from collections.abc import Container
from enum import StrEnum
from typing import Any, Self, TypedDict, cast

import joblib
import numpy as np
import numpy.typing as npt
import pandas as pd
import statsmodels.api as sm
from scipy.interpolate import UnivariateSpline
from scipy.optimize import OptimizeResult, minimize
from sklearn.base import TransformerMixin  # type: ignore
from sklearn.preprocessing import MinMaxScaler, StandardScaler  # type: ignore
from sklego.preprocessing.repeatingbasis import RepeatingBasisFunction  # type: ignore
from statsmodels.tsa.api import ARIMA, ArmaProcess

from app.internal.epl_typing import DailyDataFrame
from app.internal.utils.bank_holidays import UKCountryEnum, get_bank_holidays


class ArmaFitResult(TypedDict):
    """
    Fitting result from the ARMA process.

    Attributes
    ----------
    order
        (p, q)
    params
        Parameters for the ARMA model
    aic
        Akaike information criterion, a scalar statistic upon which we base model choice; to be minimised
    """

    order: tuple[int, int]
    params: npt.NDArray[np.floating]
    aic: float


logger = logging.getLogger(__name__)


class ScalerTypeEnum(StrEnum):
    """Different types of pre-processing scalers for the VAE."""

    Data = "data"
    Aggregate = "aggregate"
    StartTime = "start_time"
    EndTime = "end_time"
    Train = "train"
    Val = "val"
    Test = "test"


class OffsetMethodEnum(StrEnum):
    """Different methods for allocating baselines in 'active day' daily consumption."""

    MinWeekly = "min-weekly"
    Recent = "recent"
    RecentOrNext = "recent-or-next"
    DetectChgpt = "detect-chgpt"


class CustomMinMaxScaler(MinMaxScaler):
    """
    A wrapper class around the MinMaxScaler class from scikit-learn.

    This class performs preprocessing on the input X before calling the
    transform() method of the MinMax class.
    """

    feature_range: tuple[float, float]
    copy: bool
    clip: bool
    n: int
    axis: int
    scale_: npt.NDArray[np.floating]
    min_: npt.NDArray[np.floating]

    def __init__(
        self, n: int = 9, feature_range: tuple[float, float] = (0.0, 1.0), copy: bool = True, clip: bool = False, axis: int = 0
    ):
        """
        Set up the additional features for the minmax scaler.

        Parameters
        ----------
        n
            Number of initial values to take to set the scale for
        axis
            Which axis to operate on
        feature_range
            Desired range of the transformed data
        copy
            Whether to copy the input data
        clip
            Whether to clip the input data to the feature range
        """
        # first 9 values corresponds to 00:00-04:00 inclusive for
        self.n = n
        self.axis = axis
        super().__init__(feature_range=feature_range, copy=copy, clip=clip)

    def fit(self, X: npt.NDArray[np.floating], y: npt.NDArray[np.floating] | None = None) -> Self:
        """
        Fit the instance: perform any preprocessing and calculate the custom min and standard max.

        Args:
            X (numpy.ndarray): The input data.

        Returns
        -------
            self
        """
        X = np.asarray(X)
        if self.axis == 1:
            X = X.T

        # Compute custom min (mean of first n values) and max (global max)
        mean_val = np.mean(X[: self.n], axis=0)
        max_val = np.max(X, axis=0)

        self.data_min_ = mean_val
        self.data_max_ = max_val
        self.data_range_ = self.data_max_ - self.data_min_
        self.data_range_[self.data_range_ == 0.0] = 1.0

        scale_range = self.feature_range[1] - self.feature_range[0]
        self.scale_ = scale_range / self.data_range_
        self.min_ = self.feature_range[0] - self.data_min_ * self.scale_

        return self

    def transform(self, X: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        """Transform the data using the custom-fitted MinMaxScaler."""
        X = np.asarray(X)
        if self.axis == 1:
            return cast(npt.NDArray[np.floating], (X.T * self.scale_ + self.min_).T)
        else:
            return cast(npt.NDArray[np.floating], X * self.scale_ + self.min_)

    def inverse_transform(self, X: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        """Perform the inverse transformation on the data using the custom-fitted MinMaxScaler."""
        X = np.asarray(X)
        if self.axis == 1:
            return cast(npt.NDArray[np.floating], ((X.T - self.min_) / self.scale_).T)
        else:
            return cast(npt.NDArray[np.floating], (X - self.min_) / self.scale_)

    def fit_transform(
        self, X: npt.NDArray[np.floating], y: npt.NDArray[np.floating] | None = None, **fit_params: dict
    ) -> npt.NDArray[np.floating]:
        """Fit the custom MinMaxScaler and perform the resulting transformation."""
        X = np.asarray(X)
        return cast(npt.NDArray[np.floating], super().fit_transform(X, y, **fit_params))


class RBFTimestampEncoder(TransformerMixin):
    """
    A wrapper class around the RepeatingBasisFunction class from scikit-lego.

    This class performs preprocessing on the input X before calling the
    transform() method of the RepeatingBasisFunction class.
    """

    def __init__(self, n_periods: int, input_range: tuple[int, int]):
        """
        Initialize the wrapper class.

        Args:
            **kwargs: Keyword arguments passed to the RepeatingBasisFunction
                constructor.
        """
        self.basis_function = RepeatingBasisFunction(n_periods=n_periods, input_range=input_range)
        self.is_fitted = False
        self.n_periods = n_periods

    def _preprocess(self, X: npt.NDArray[np.floating]) -> npt.NDArray[np.integer]:
        """
        Apply preprocessing to the input X.

        Args:
            X (numpy.ndarray): The input data.

        Returns
        -------
            numpy.ndarray: The preprocessed data.
        """
        # Preprocess the data: X is an ndarray, with each element being
        # a Unix timestamp in seconds. Instead, we want to know the day
        # of the year
        # TODO (2024-09-24 JSM): inputs are being coerced to and from
        # datetime types, to minimise disruption before demo day. Let's
        # streamline this.
        # TODO (2024-10-01 MHJB): the type hints are actually correct here, but pandas complains anyway
        X_dates = pd.to_datetime(X.flatten(), unit="s", origin="unix")  # type: ignore
        X_dayofyear = X_dates.dayofyear.to_numpy().reshape(-1, 1)
        return X_dayofyear

    def fit(self, X: npt.NDArray[np.floating]) -> Self:
        """
        Fit the RepeatingBasisFunction instance and perform any preprocessing.

        Args:
            X (numpy.ndarray): The input data.

        Returns
        -------
            self
        """
        X_preprocessed = self._preprocess(X)
        self.basis_function.fit(X_preprocessed)
        self.is_fitted = True
        return self

    def transform(self, X: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        """
        Transform the input data using the RepeatingBasisFunction.

        Args:
            X (numpy.ndarray): The input data.

        Returns
        -------
            numpy.ndarray: The transformed data.
        """
        if not self.is_fitted:
            raise ValueError("The model needs to be fitted before transforming data.")
        X_preprocessed = self._preprocess(X)
        result: npt.NDArray[np.floating] = self.basis_function.transform(X_preprocessed)
        return result

    def fit_transform(
        self, X: npt.NDArray[np.floating], y: npt.NDArray[np.floating] | None = None, **fit_params: Any
    ) -> npt.NDArray[np.floating]:
        """
        Fit the RepeatingBasisFunction instance and transform the input data.

        Args:
            X (numpy.ndarray): The input data.

        Returns
        -------
            numpy.ndarray: The transformed data.
        """
        if not self.is_fitted:
            self.fit(X)
        return self.transform(X)


def load_StandardScaler(path: pathlib.Path, refresh: bool = False) -> StandardScaler:
    """
    Load a saved StandardScaler from a file.

    Parameters
    ----------
    path (str)
        Path to the saved StandardScaler file.
    refresh
        Whether we should re-save these to a file after loading.
        This is useful if you have updated scikit learn and it's complaining!

    Returns
    -------
    scaler
        The loaded StandardScaler object.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the loaded object is not a StandardScaler.
    """
    try:
        scaler = joblib.load(path)
        if not isinstance(scaler, StandardScaler):
            raise TypeError("Loaded object is not a StandardScaler")

        if refresh:
            joblib.dump(scaler, path)
    except FileNotFoundError as ex:
        raise FileNotFoundError(f"No StandardScaler found at {path}") from ex

    return scaler


def load_CustomMinMaxScaler(path: pathlib.Path, refresh: bool = False) -> CustomMinMaxScaler:
    """
    Load a saved instance of CustomMinMaxScaler from a joblib file.

    Parameters
    ----------
    path (str)
        Path to the saved joblib file.
    refresh
        Whether we should re-save these to a file after loading.
        This is useful if you have updated scikit learn and it's complaining!

    Returns
    -------
    scaler
        The loaded CustomMinMaxScaler object.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the loaded object is not a CustomMinMaxScaler.
    """
    try:
        scaler = joblib.load(path)
        if not isinstance(scaler, CustomMinMaxScaler):
            raise TypeError("Loaded object is not a CustomMinMaxScaler")

        if refresh:
            joblib.dump(scaler, path)
    except FileNotFoundError as ex:
        raise FileNotFoundError(f"No scaler found at {path}") from ex

    return scaler


def load_RBFTimestampEncoder(path: pathlib.Path, refresh: bool = False) -> RBFTimestampEncoder:
    """
    Load a saved instance of RBFTimestampEncoder (which we treat as a scaler) from a joblib file.

    Parameters
    ----------
    path (str)
        Path to the saved joblib file.
    refresh
        Whether we should re-save these to a file after loading.
        This is useful if you have updated scikit learn and it's complaining!

    Returns
    -------
    scaler
        The loaded RBFTimestampEncoder object.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the loaded object is not a RBFTimestampEncoder.
    """
    try:
        scaler = joblib.load(path)
        if not isinstance(scaler, RBFTimestampEncoder):
            raise TypeError("Loaded object is not an RBFTimestampEncoder")

        if refresh:
            joblib.dump(scaler, path)
    except FileNotFoundError as ex:
        raise FileNotFoundError(f"No scaler found at {path}") from ex

    return scaler


def load_all_scalers(
    directory: pathlib.Path = pathlib.Path(".", "models", "final"), refresh: bool = False, use_new: bool = True
) -> dict[ScalerTypeEnum, CustomMinMaxScaler | RBFTimestampEncoder | StandardScaler]:
    """
    Load all the scalers found within a specific directory.

    The default path should find them, but you might want to change it if you're testing different scalers or
    running the model from a notebook.

    Parameters
    ----------
    directory
        The directory to search for scalers in

    Returns
    -------
    Dictionary of scalers with the type as the key and the scaler object as the value.

    """
    if use_new:
        return {
            ScalerTypeEnum.Train: load_CustomMinMaxScaler(
                directory / "elecTransformerVAE_data_scaler_train.joblib", refresh=refresh
            ),
            ScalerTypeEnum.Val: load_CustomMinMaxScaler(
                directory / "elecTransformerVAE_data_scaler_val.joblib", refresh=refresh
            ),
            ScalerTypeEnum.Test: load_CustomMinMaxScaler(
                directory / "elecTransformerVAE_data_scaler_test.joblib", refresh=refresh
            ),
            ScalerTypeEnum.Aggregate: load_StandardScaler(
                directory / "elecTransformerVAE_aggregate_scaler.joblib", refresh=refresh
            ),
            ScalerTypeEnum.StartTime: load_RBFTimestampEncoder(
                directory / "elecTransformerVAE_start_time_scaler.joblib", refresh=refresh
            ),
            ScalerTypeEnum.EndTime: load_RBFTimestampEncoder(
                directory / "elecTransformerVAE_end_time_scaler.joblib", refresh=refresh
            ),
        }
    return {
        ScalerTypeEnum.Data: load_StandardScaler(directory / "elecVAE_data_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.Aggregate: load_StandardScaler(directory / "elecVAE_aggregate_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.StartTime: load_RBFTimestampEncoder(directory / "elecVAE_start_time_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.EndTime: load_RBFTimestampEncoder(directory / "elecVAE_end_time_scaler.joblib", refresh=refresh),
    }


def allocate_active_offsets(
    active_daily: DailyDataFrame, inactive_daily: DailyDataFrame, method: OffsetMethodEnum = OffsetMethodEnum.DetectChgpt
) -> np.ndarray:
    """
    Establish value for offset component of 'business as usual' daily aggregates.

    In order to model the intraday electricity demand profile for a site that is active (i.e. operating on a
    normal day), we first establish an offset level: this is the component of the daily demand that corresponds
    to the site's usage on a inactive day (e.g. weekends, bank holidays).

    We establish the offset for each active day by comparing to the surrounding days that are already marked as
    inactive.

    Parameters
    ----------
    active_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is active, i.e. operating as usual.
    inactive_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is inactive (e.g. weekends, bank holidays)
    method
        A StrEnum to indicate the method used. Corresponds to one of {'min-weekly', 'recent', 'recent-or-next', 'detect-chgpt'}
        Defaults to 'detect-chgpt'.

    Returns
    -------
    active_daily_offset
        A dataframe containing the offset component of the daily aggregate values in active_daily, with a pd.DatetimeIndex.
    """
    match method:
        case OffsetMethodEnum.MinWeekly:
            active_daily_offset = handle_offsets_min_weekly(active_daily, inactive_daily)
        case OffsetMethodEnum.Recent:
            active_daily_offset = handle_offsets_recent(active_daily, inactive_daily)
        case OffsetMethodEnum.RecentOrNext:
            active_daily_offset = handle_offsets_recent_or_next(active_daily, inactive_daily)
        case OffsetMethodEnum.DetectChgpt:
            active_daily_offset = handle_offsets_chgpt(active_daily, inactive_daily)

    return active_daily_offset


def handle_offsets_min_weekly(active_daily: DailyDataFrame, inactive_daily: DailyDataFrame) -> npt.NDArray[np.floating]:
    """
    Establish active day offsets: for each fixed week, use the min value in the labelled inactive days.

    Parameters
    ----------
    active_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is active, i.e. operating as usual.
    inactive_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is inactive (e.g. weekends, bank holidays)

    Returns
    -------
    npt.NDArray[np.floating]
        The offsets to use for each active day as the corresponding 'inactive day component'
    """
    # use min "inactive day" value in each fixed week (Mon-Sun inclusive; labelled on the Sunday)
    weeklymin_inactive = inactive_daily.resample(rule="W-SUN", closed="right").min().ffill()
    # from inactive days, take minimum over each week; forward fill if a week contains no inactive days
    # use min (rather than e.g. median) as we want to avoid active daily values being less than the allocated offset
    # find position in index of weeklymin_inactive that each record of active_daily would be inserted
    active_daily_index = active_daily.index.to_numpy()
    pos = np.searchsorted(weeklymin_inactive.index.to_numpy(), active_daily_index, side="left")
    # use "left": weeklymin_inactive.index uses the Sunday as a label, so days in the week indexed a[i] are indexed by
    #  v with a[i-1] < v <= a[i].
    # allocate the corresponding weekly offset to each index of active_daily
    active_daily_offset = np.empty_like(active_daily_index, dtype=float)
    active_daily_offset[pos >= 0] = weeklymin_inactive.iloc[pos[pos >= 0]]  # valid lookups
    return active_daily_offset


def handle_offsets_recent(active_daily: DailyDataFrame, inactive_daily: DailyDataFrame) -> npt.NDArray[np.floating]:
    """
    Establish active day offsets: use the value for the most recent labelled inactive day.

    Parameters
    ----------
    active_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is active, i.e. operating as usual.
    inactive_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is inactive (e.g. weekends, bank holidays)

    Returns
    -------
    npt.NDArray[np.floating]
        The offsets to use for each active day as the corresponding 'inactive day component'
    """
    # as active_daily_offset, use value from most recent inactive day
    # find position in index of inactive_daily that each record of active_daily would be inserted
    active_daily_index = active_daily.index.to_numpy()
    pos = np.searchsorted(inactive_daily.index.to_numpy(), active_daily_index, side="right") - 1
    # here, we're looking for the 'most recent' reference index a for each given index v. This is a[i-1] where
    # a[i-1] <= v < a[i]. So we use side="right" and subtract one from the returned index, to get i-1.
    # allocate the corresponding value of inactive_daily to each index of active_daily
    active_daily_offset = np.empty_like(active_daily_index, dtype=float)
    active_daily_offset[pos >= 0] = inactive_daily.iloc[pos[pos >= 0]]  # valid lookups
    active_daily_offset[pos < 0] = inactive_daily.iloc[0]  # default for active dates before first inactive date
    return active_daily_offset


def handle_offsets_recent_or_next(active_daily: DailyDataFrame, inactive_daily: DailyDataFrame) -> npt.NDArray[np.floating]:
    """
    Establish active day offsets: use whichever value is closer in aggregate, the most recent or the next inactive day.

    Parameters
    ----------
    active_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is active, i.e. operating as usual.
    inactive_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is inactive (e.g. weekends, bank holidays)

    Returns
    -------
    npt.NDArray[np.floating]
        The offsets to use for each active day as the corresponding 'inactive day component'
    """
    # as active_daily_offset, use either most recent or next inactive day, whichever is closer in aggregate value
    # logic here is that the offset represents the energy usage without daily profile
    # changes in offset could start on active days or inactive days; in each case, a given active day's
    # offset is most likely to correspond to the inactive day that is closest in aggregate value
    # find position in index of inactive_daily that each record of active_daily would be inserted
    active_daily_index = active_daily.index.to_numpy()
    pos = np.searchsorted(inactive_daily.index.to_numpy(), active_daily_index, side="left") - 1
    # allocate the corresponding value of inactive_daily to each index of active_daily
    prev_inactive = np.empty_like(active_daily_index, dtype=float)
    prev_inactive[pos >= 0] = inactive_daily.iloc[pos[pos >= 0]]  # valid lookups for most recent inactive value
    prev_inactive[pos < 0] = inactive_daily.iloc[0]  # before first ref date
    # allocate the corresponding value of inactive_daily to each index of active_daily
    next_inactive = np.empty_like(active_daily_index, dtype=float)
    next_inactive[pos >= 0] = inactive_daily.iloc[pos[pos >= 0] + 1]  # valid lookups for next inactive value
    next_inactive[pos < 0] = inactive_daily.iloc[0]  # before first ref date

    # use masking to return the offset that gives the smallest positive difference in aggregate from the active value
    # first replace the negative values with np.inf
    prev_inactive_posdiff = np.where(
        active_daily["consumption_kwh"] - prev_inactive >= 0, active_daily["consumption_kwh"] - prev_inactive, np.inf
    )
    next_inactive_posdiff = np.where(
        active_daily["consumption_kwh"] - next_inactive >= 0, active_daily["consumption_kwh"] - next_inactive, np.inf
    )
    # then create a mask that selects the indices for which is the smaller positive diff
    use_prevoffset = prev_inactive_posdiff <= next_inactive_posdiff
    # select the previous or next inactive day accordingly
    active_daily_offset = np.where(use_prevoffset, prev_inactive, next_inactive)
    return active_daily_offset


def handle_offsets_chgpt(active_daily: DailyDataFrame, inactive_daily: DailyDataFrame) -> npt.NDArray[np.floating]:
    """
    Establish active day offsets.

    For each set of contiguous active days detect the day where the offset changes from the most recent to the next inactive day
    value.

    Parameters
    ----------
    active_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is active, i.e. operating as usual.
    inactive_daily
        A dataframe containing daily aggregate values in a column "consumption_kwh", and with a pd.DatetimeIndex.
        These correspond to days for which the site is inactive (e.g. weekends, bank holidays)

    Returns
    -------
    npt.NDArray[np.floating]
        The offsets to use for each active day as the corresponding 'inactive day component'
    """
    # for each interval between inactive dates, we detect the point at which the baseline changes:
    #  - if the bookending inactive values are both lower than the active values, we choose the date in the interval that
    #    results in the minimum squared residual between active and inactive values.
    #  - if one of the bookending inactive values is above the active values, we use this to constrain the possible dates
    inactive_daily_index = inactive_daily.index.to_numpy()
    inactive_daily_vals = inactive_daily.to_numpy()
    active_daily_index = active_daily.index.to_numpy()
    active_daily_vals = active_daily.to_numpy()

    active_daily_offset = np.empty_like(active_daily_index, dtype=float)

    # deal separately with the case where there are active days before or after all inactive days
    if active_daily_index[0] < inactive_daily_index[0]:
        mask = active_daily_index < inactive_daily_index[0]
        idx = np.where(mask)[0]
        active_daily_offset[idx] = inactive_daily_vals[0]
    if active_daily_index[-1] > inactive_daily_index[-1]:
        mask = active_daily_index > inactive_daily_index[-1]
        idx = np.where(mask)[0]
        active_daily_offset[idx] = inactive_daily_vals[-1]

    for i in range(len(inactive_daily_index) - 1):
        t0, t1 = inactive_daily_index[i], inactive_daily_index[i + 1]
        a, b = inactive_daily_vals[i], inactive_daily_vals[i + 1]

        # isolate segment of active days between inactive days
        mask = np.logical_and(active_daily_index >= t0, active_daily_index <= t1)
        idx = np.where(mask)[0]
        if len(idx) == 0:
            continue
        signal = active_daily_vals[idx]
        n = len(signal)

        # compute residual cost of assigning baseline a vs b
        cost = np.full(n + 1, np.inf)  # initialise infinite total cost
        sum_sig = np.cumsum(signal)
        sum_sig2 = np.cumsum(signal**2)

        for k in range(n + 1):  # try changepoint at position k in signal
            if np.all(signal[:k] >= a) and np.all(signal[k:] >= b):
                # if a, b are both valid baselines for this split, then calculate the cost,
                #   o/w ignore k as a possible changepoint
                if k == 0:
                    cost[k] = np.sum((signal - b) ** 2)
                elif k == n:
                    cost[k] = np.sum((signal - a) ** 2)
                else:
                    # minimise total cost = cost_a + cost_b
                    cost_a = sum_sig2[k - 1] - 2 * a * sum_sig[k - 1] + k * a**2
                    cost_b = (sum_sig2[-1] - sum_sig2[k - 1]) - 2 * b * (sum_sig[-1] - sum_sig[k - 1]) + (n - k) * b**2
                    cost[k] = cost_a[0] + cost_b[0]

        cp = np.argmin(cost)
        if cost[cp] == np.inf:  # no k for which a,b are both valid baselines
            # fallback: try all-a or all-b
            if np.all(signal >= a):
                active_daily_offset[idx] = a
            elif np.all(signal >= b):
                active_daily_offset[idx] = b
            else:  # at least one value in signal is less than a (and sim. for b)
                active_daily_offset[idx] = np.min((a, b))
        elif cp == 0:
            active_daily_offset[idx] = b
        elif cp == n:
            active_daily_offset[idx] = a
        else:
            active_daily_offset[idx[:cp]] = a
            active_daily_offset[idx[cp:]] = b
    return active_daily_offset


def split_and_baseline_active_days(
    df_daily_all: DailyDataFrame, weekend_inds: Container[int] = (5, 6), division: UKCountryEnum = UKCountryEnum.England
) -> tuple[DailyDataFrame, DailyDataFrame]:
    """
    Extract "inactive days" (i.e. weekend/holidays) from daily aggregates; use these to baseline the remaining days.

    We model active days and inactive days separately,
    expecting the active days to display more [canonical/regular] intraday variation.
    We distinguish between the two types of day by first assuming inactive days to include Bank Holidays and days of the week
    indicated by the provided index (Monday=0, Sunday=6);
    we use these inactive days as a 'baseline' above which active days vary.
    By removing this baseline, we use simple outlier detection methods to identify remaining inactive days (e.g. between
    Christmas and New Year).

    Parameters
    ----------
    df_daily_all
        must have datetime index
    weekend_inds
        defaults to (5,6) for Saturday and Sunday
    division
        which division of the UK to use to determine the public holidays; defaults to England

    Returns
    -------
    df_daily_active
        contains baseline/offset and "baselined" values (i.e. with the baseline removed)
        has datetime index
    df_daily_inactive
        has datetime index
    """
    # Ascertain the public holiday and 'weekend' dates to use in the first split
    holiday_dates = frozenset(get_bank_holidays(division))
    assert isinstance(df_daily_all.index, pd.DatetimeIndex), df_daily_all.index

    # Perform the initial split: extract inactive dates and define remaining records of df_daily_all as active days
    is_holiday = df_daily_all.index.map(lambda dt: dt.date() in holiday_dates).to_numpy()
    is_weekend = df_daily_all.index.map(lambda dt: dt.weekday() in weekend_inds).to_numpy()
    is_inactive = np.logical_or(is_holiday, is_weekend)
    df_daily_inactive, df_daily_active = df_daily_all[is_inactive], df_daily_all[~is_inactive]

    # forward fill any nan records: do so separately for inactive and active days
    df_daily_inactive = df_daily_inactive.ffill(inplace=False)
    df_daily_active = df_daily_active.ffill(inplace=False)
    assert isinstance(df_daily_inactive.index, pd.DatetimeIndex)
    assert isinstance(df_daily_active.index, pd.DatetimeIndex)

    # for each active date, establish the appropriate inactive date
    # (either the most recent or the next) to use as a baseline/offset
    df_daily_active["offsets"] = allocate_active_offsets(
        cast(DailyDataFrame, pd.DataFrame(df_daily_active["consumption_kwh"])),
        df_daily_inactive,
        method=OffsetMethodEnum.DetectChgpt,
    )
    # assume active date baseline to be piecewise constant between inactive dates;
    # find optimal changepoint.

    # remove offsets for all active dates
    df_daily_active["consumption_baselined"] = df_daily_active["consumption_kwh"] - df_daily_active["offsets"]

    # after baselining, use robust outlier detection (via modified Z-score) to pick out "site-specific" inactive dates
    # modified z-score = 0.6745(x - median) / MAD
    med = np.nanmedian(df_daily_active["consumption_baselined"])
    med_abs_dev = np.nanmedian(np.abs(df_daily_active["consumption_baselined"] - med))
    z_score_mod = 0.6745 * ((df_daily_active["consumption_baselined"] - med) / med_abs_dev)
    site_specific_inactive_inds = df_daily_active.index[np.where(z_score_mod < -3.5)[0]]  # only interested in low outliers

    # move by using datetime indexing only
    df_daily_inactive = cast(
        DailyDataFrame,
        pd.concat([df_daily_inactive, df_daily_active["consumption_kwh"].loc[site_specific_inactive_inds]]).sort_index(),
    )
    df_daily_active = df_daily_active.drop(site_specific_inactive_inds)

    return df_daily_active, df_daily_inactive


def joint_nll(params: npt.NDArray[np.floating], models: list[ARIMA]) -> float:
    """
    Compute the total negative log-likelihood across a list of ARIMA model instances.

    This is used in `fit_shared_arma()` below, where each entry in `models` is an instance of the
    same model, but associated with different observed data.

    Parameters
    ----------
    params (npt.NDArray[np.floating])
        Parameter vector (AR, MA, σ²).
    models (list[ARIMA])
        List of ARIMA model instances.

    Returns
    -------
    total (float)
        Total negative log-likelihood. Returns np.inf on failure.
    """
    total = 0.0
    for m in models:
        try:
            ll = m.loglike(params, transformed=False)  # use raw AR, MA, sigma-sq params (not internal transformed form)
            if not np.isfinite(ll):  # invalid region
                return np.inf
            total -= ll  # negative log likelihood
        except Exception:
            return np.inf  # penalise with infinite loss for e.g., LU decomposition failure
    return total


def fit_shared_arma_model(
    data: npt.NDArray[np.floating],
    p: int,
    q: int,
    max_iter: int = 500,
) -> OptimizeResult | None:
    """
    Fit a shared ARMA(p, q) model across multiple time series using joint MLE.

    Standard ARIMA fitting from statsmodels.tsa doesn't allow for multiple independent
    time series observations, but we can use its methods to compose our own approach

    Parameters
    ----------
    data (np.ndarray)
        2D array of shape (n_series, series_len), assumed to be detrended and stationary.
    p (int)
        Order of the AR component.
    q (int)
        Order of the MA component.
    max_iter (int)
        Maximum number of iterations for the optimizer.

    Returns
    -------
    tuple[np.ndarray, float] (optional)
        A tuple containing:
        - params: Fitted parameter vector (AR, MA, σ²)
        - aic: Akaike Information Criterion
        Returns None if fitting fails or model is not stationary.
    """
    if p == q == 0:
        return None

    try:
        models = [
            ARIMA(
                y,
                order=(p, 0, q),
                trend="n",
                enforce_stationarity=True,
                enforce_invertibility=True,
            )
            for y in data
        ]
    except Exception:  # if model creation within the fitting function failed, skip this choice of (p,q)
        return None

    sigma2_init = np.mean(data.var(axis=1))  # better scalar init for sigma-sq, compared to data.var()
    init = np.r_[np.zeros(p + q), sigma2_init]
    bounds = [(-np.inf, np.inf)] * (p + q) + [(1e-6, np.inf)]  # sigma-sq > 0

    return minimize(
        joint_nll,
        init,
        args=(models,),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": max_iter},
    )


def select_best_shared_arma_model(
    data: np.ndarray,
    p_max: int = 3,
    q_max: int = 3,
    max_iter: int = 500,
) -> ArmaFitResult:
    """
    Grid search over (p, q) to find best shared ARMA(p, q) model by AIC.

    Parameters
    ----------
    data (np.ndarray)
        2D array of shape (n_series, series_len), assumed to be detrended and stationary.
    p_max (int)
        Maximum AR order to search.
    q_max (int)
        Maximum MA order to search.
    max_iter (int)
        Max optimizer iterations per fit.

    Returns
    -------
        tuple[(p, q), params, aic]: Best model order, parameters, and AIC.
    """
    best_result: ArmaFitResult | None = None

    for p, q in itertools.product(range(p_max + 1), range(q_max + 1)):
        if p == q == 0:
            continue  # ARMA(0,0) is white noise - skip this case
        result = fit_shared_arma_model(data, p, q, max_iter=max_iter)
        if result is None:
            continue  # if model creation within the fitting function failed, skip this choice of (p,q)
        if not result.success:
            continue  # if the optimiser fails to find a valid minimum, skip this choice of (p,q)

        ar_poly = np.r_[1, -result.x[:p]]
        ma_poly = np.r_[1, result.x[p : p + q]]
        arma = ArmaProcess(ar_poly, ma_poly)

        if p > 0 and not arma.isstationary:  # ensure we only consider stationary models for simulating from
            continue

        k = p + q + 1
        aic = 2 * k + 2 * result.fun  # result.fun = joint NLL

        if best_result is None or aic < best_result["aic"]:
            best_result = {"order": (p, q), "params": result.x, "aic": aic}

    if best_result is None:
        raise ValueError("Couldn't fit a best ARMA model.")
    return best_result


def fit_residual_model(
    resids: pd.DataFrame,
    vae_struct: pd.DataFrame | None = None,
    verbose: bool = False
) -> tuple[pd.DataFrame, sm.OLS | None, ArmaProcess, float]:
    """
    Fit a crude trend to the given residuals and then fit an ARMA process to the detrended residuals.

    Parameters
    ----------
    resids
        a DataFrame containing a set of observed residuals; axis 1 is of length 48
    vae_struct
        contains the structural vae component removed from the observed data to obtain `resids`; same size as `resids`
    verbose (boolean, default False)
        Set this to True if you want progress statements to be printed

    Returns
    -------
    trend (pandas.DataFrame)
        an estimated trend, comprising 48 values over 24h
    ARMA_model
        a fitted ARMA model instance
    ARMA_scale
        the standard deviation for the innovations of the fitted ARMA process
    """
    assert not resids.empty, "Got an empty residuals dataframe in fit_residual_model."
    assert not resids.isna().any().any(), "Got NaN values in resids"

    if verbose:
        logger.info("Fitting trend & ARMA model...")

    # trend = resids.mean(axis=0)
    trend = fit_pooled_spline(resids)
    resids_detrended = resids.sub(trend)

    if vae_struct is not None:
        resids_detrended_stable, var_lm = stabilise_variance(resids_detrended, vae_struct + trend)
    else:
        resids_detrended_stable, var_lm = stabilise_variance(resids_detrended, trend)

    best = select_best_shared_arma_model(resids_detrended_stable.to_numpy(), p_max=3, q_max=3)
    if len(best) > 0:
        p, q = best["order"]
        ar_coefs = best["params"][:p]
        ma_coefs = best["params"][p : p + q]
        sigma2 = best["params"][-1]
        ar = np.r_[1, -ar_coefs]
        ma = np.r_[1, ma_coefs]
        ARMA_model = ArmaProcess(ar, ma)
        # use ArmaProcess() for simulation as it is lightweight, built for generating multiple iid realisations
        ARMA_scale = np.sqrt(sigma2)
        if verbose:
            logger.info("  Best (p, q): %s", best["order"])
            logger.info("  AR coefficients: %s", ar_coefs)
            logger.info("  MA coefficients: %s", ma_coefs)
            logger.info("  Shared sigma-sq: %s", sigma2)
            logger.info("  AIC: %s", best["aic"])
    else:
        logger.info("No valid ARMA model found.")

    trend_as_df = pd.DataFrame(trend, index=resids.columns).T
    return trend_as_df, var_lm, ARMA_model, ARMA_scale

def fit_pooled_spline(
    resids: pd.DataFrame,
    smooth_factor: float | None = None,
    order: int = 3
) -> pd.Series:
    """
    Fit a pooled penalised spline f(t) to input residuals.

    This is preferred to the sample mean as it usually results in lower overall variance for the demeaned residuals.
    By design, the pooled spline captures more low-frequency structure than the column means, and contains less high-freq
    variation. The remaining noise process (after subtracting the spline / col means) may therefore have more high-freq
    power but less low-freq power; the trade-off hear will typically be beneficial, reducing the total overall power (variance)
    in the demeaned noise process.

    Parameters
    ----------
    resids
        a DataFrame containing a set of observed residuals; axis 1 is of length 48
    smooth_factor
        smoothing factor for UnivariateSpline. If None, set to a near-unbiased default.
    order
        spline order (default to a cubic spline).

    Returns
    -------
    f_hat
        a smoothed common trend, indexed by columns of resids
    # spline
    #     a fitted UnivariateSpline object for later evaluation
    """
    n = resids.shape[1]
    t = np.arange(n, dtype=float)

    # pooled mean across realisations (sufficient statistic for the mean term)
    y_bar = resids.mean(axis=0).to_numpy()

    # inverse-variance weights (stabilise when m is small / heteroskedastic across t)
    var_t = resids.var(axis=0, ddof=1).to_numpy()
    w = 1.0 / np.maximum(var_t, np.finfo(float).eps)

    # SciPy uses 's' as the allowed weighted RSS: sum_i w_i (y_i - f(t_i))^2 <= s
    # With w_i ≈ 1/Var and correct model, E[RSS_w] ≈ n, so s≈n is a good fast default.
    if smooth_factor is None:
        smooth_factor = float(n)

    spline = UnivariateSpline(t, y_bar, w=w, k=order, s=smooth_factor)
    f_hat = pd.Series(spline(t), index=resids.columns)
    return f_hat#, spline

def stabilise_variance(
    ts: pd.DataFrame,
    structure: pd.DataFrame,
) -> tuple[pd.Series,sm.OLS]:
    """
    Stabilise the variance of a heteroskedastic time series.

    We assume `ts` contains independent time series realisations of the same process, which is heteroskedastic.
    We do so by regressing the log-variance of the observations at each time step against a structural component,
    specified in `structure`, and related quantities.
    Apply this stabilisation to detrended residuals to help subsequent ARMA model selection; without this, ARMA model choice
    tends to bias models with larger MA components, inflating the variance of the fitted ARMA process.

    Parameters
    ----------
    ts
        a DataFrame containing a set of heteroskedastic observed time series; axis 1 is of length 48
    structure
        a DataFrame containing a structural component for `ts`, or a proxy thereof; same shape as `ts`;
        to be used as a predictor for the time-varying variance in `ts`

    Returns
    -------
    ts_std
        a DataFrame containing the variance-stabilised version of `ts`
    """
    var_t_est = ts.var(axis=0, ddof=1).to_numpy()
    log_var = np.log(np.maximum(var_t_est, np.finfo(float).eps))

    S = structure.mean(axis=0).to_numpy()  # regressing against S captures level-dependent variance
    dS = np.diff(S, prepend=S[0])   # regressing against abs(dS) captures bursts during sudden structural changes
    X = np.column_stack([S, S**2, np.abs(dS)]) # regressing against S^2 captures nonlinear effects
    X = sm.add_constant(X)

    lin_model = sm.OLS(log_var, X).fit()
    log_var_fitted = lin_model.predict(X)
    var_fitted = np.exp(log_var_fitted)
    ts_std = ts/np.sqrt(var_fitted)

    ts_std_as_df = pd.DataFrame(ts_std, index=ts.index)
    return ts_std_as_df, lin_model

def predict_var_mean_batched(
    model: sm.OLS,
    observed_structure: pd.DataFrame,
    min_var=1e-8
) -> npt.NDArray[np.floating]:
    """
    Compute plug-in variance trajectories for multiple observations of the structural predictor.

    `model` is assumed to have been returned by `stabilise_variance`, and contains a fitted linear model regressing log-variance
    against the structure vector and related derivatives.

    Parameters
    ----------
    model : statsmodels.regression.linear_model.RegressionResults
        Fitted OLS (or GLS) model with predictors in the order
        [const, S, S^2, np.abs(dS)]
    observed_structure : pandas.DataFrame, shape (m, n)
        Matrix of structural paths from the offsets, scaled VAE & deterministic residuals combined.
        Rows correspond to independent realisations, columns to time points.
    min_var : float, default=1e-8
        Minimum variance floor to enforce numerical stability when exponentiating log-variance predictions.

    Returns
    -------
    var_hat : ndarray, shape (m, n)
        Predicted variance trajectories for each realisation and time point, computed as exp(X @ beta).
    """
    S = observed_structure.to_numpy(dtype=float)
    dS = np.concatenate([np.zeros((S.shape[0],1)),
                        np.diff(S, axis=1)], axis=1)

    # Build X tensor in the same order as model.params; here we assume ['const','S','S2','abs_dS']
    X = np.stack([np.ones_like(S), S, S**2, np.abs(dS)], axis=-1)

    beta = model.params#.to_numpy()
    logv = np.einsum('p,mnp->mn', beta, X)
    return np.exp(np.maximum(logv, np.log(min_var)))
