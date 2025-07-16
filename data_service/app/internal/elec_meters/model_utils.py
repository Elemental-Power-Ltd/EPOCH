"""Utility functions for loading additional parts for the ML models."""

import logging
import pathlib
from enum import StrEnum
from typing import Any, Self, cast, overload

import joblib
import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.base import TransformerMixin  # type: ignore
from sklearn.preprocessing import MinMaxScaler, StandardScaler  # type: ignore
from sklego.preprocessing.repeatingbasis import RepeatingBasisFunction  # type: ignore

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


class CustomMinMaxScaler(MinMaxScaler):
    """
    A wrapper class around the MinMaxScaler class from scikit-learn.

    This class performs preprocessing on the input X before calling the
    transform() method of the MinMax class.
    """

    feature_range: tuple
    copy: bool
    clip: bool
    n: int
    axis: int

    def __init__(self, n: int = 9, feature_range: tuple = (0, 1),
                 copy: bool = True, clip: bool = False, axis: int = 0):
        # first 9 values corresponds to 00:00-04:00 inclusive for
        self.n = n
        self.axis = axis
        super().__init__(feature_range=feature_range, copy=copy, clip=clip)

    def fit(self, X, y=None):
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
        mean_val = np.mean(X[:self.n], axis=0)
        max_val = np.max(X, axis=0)

        self.data_min_ = mean_val
        self.data_max_ = max_val
        self.data_range_ = self.data_max_ - self.data_min_
        self.data_range_[self.data_range_ == 0.0] = 1.0

        scale_range = self.feature_range[1] - self.feature_range[0]
        self.scale_ = scale_range / self.data_range_
        self.min_ = self.feature_range[0] - self.data_min_ * self.scale_

        return self

    def transform(self, X):
        """Transform the data using the custom-fitted MinMaxScaler."""
        X = np.asarray(X)
        if self.axis == 1:
            return (X.T * self.scale_ + self.min_).T
        else:
            return X * self.scale_ + self.min_

    def inverse_transform(self, X):
        """Perform the inverse transformation on the data using the custom-fitted MinMaxScaler."""
        X = np.asarray(X)
        if self.axis == 1:
            return ((X.T - self.min_) / self.scale_).T
        else:
            return (X - self.min_) / self.scale_

    def fit_transform(self, X, y=None, **fit_params):
        """Fit the custom MinMaxScaler and perform the resulting transformation."""
        X = np.asarray(X)
        return super().fit_transform(X, y, **fit_params)


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
        result: npt.NDArray[np.floating] = self.basis_function.transform(X_preprocessed) # type: ignore
        return result

    @overload
    def fit_transform(self, X: npt.NDArray[np.floating], y: None = ..., **fit_params: Any) -> npt.NDArray[np.floating]: ...
    @overload
    def fit_transform(self, X: Any, y: Any = None, **fit_params: Any): ...

    def fit_transform(self, X: Any, y=None, **fit_params):
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
            ScalerTypeEnum.Train: load_CustomMinMaxScaler(directory / "elecTransformerVAE_data_scaler_train.joblib", refresh=refresh),
            ScalerTypeEnum.Val: load_CustomMinMaxScaler(directory / "elecTransformerVAE_data_scaler_val.joblib", refresh=refresh),
            ScalerTypeEnum.Test: load_CustomMinMaxScaler(directory / "elecTransformerVAE_data_scaler_test.joblib", refresh=refresh),
            ScalerTypeEnum.Aggregate: load_StandardScaler(directory / "elecTransformerVAE_aggregate_scaler.joblib", refresh=refresh),
            ScalerTypeEnum.StartTime: load_RBFTimestampEncoder(directory / "elecTransformerVAE_start_time_scaler.joblib", refresh=refresh),
            ScalerTypeEnum.EndTime: load_RBFTimestampEncoder(directory / "elecTransformerVAE_end_time_scaler.joblib", refresh=refresh),
        }
    return {
        ScalerTypeEnum.Data: load_StandardScaler(directory / "elecVAE_data_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.Aggregate: load_StandardScaler(directory / "elecVAE_aggregate_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.StartTime: load_RBFTimestampEncoder(directory / "elecVAE_start_time_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.EndTime: load_RBFTimestampEncoder(directory / "elecVAE_end_time_scaler.joblib", refresh=refresh),
    }
