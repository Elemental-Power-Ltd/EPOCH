"""Utility functions for loading additional parts for the ML models."""

import pathlib
from enum import StrEnum

import joblib
import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.base import TransformerMixin  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore
from sklego.preprocessing.repeatingbasis import RepeatingBasisFunction  # type: ignore


class ScalerTypeEnum(StrEnum):
    """Different types of pre-processing scalers for the VAE."""

    Data = "data"
    Aggregate = "aggregate"
    StartTime = "start_time"
    EndTime = "end_time"


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

    def fit(self, X: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
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
        return self.basis_function.transform(X_preprocessed)

    def fit_transform(self, X: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        """
        Fit the RepeatingBasisFunction instance and transform the input data.

        Args:
            X (numpy.ndarray): The input data.

        Returns
        -------
            numpy.ndarray: The transformed data.
        """
        if not self.is_fitted:
            X_preprocessed = self._preprocess(X)
            self.basis_function.fit(X_preprocessed)
            self.is_fitted = True
            return self.basis_function.transform(X_preprocessed)
        else:
            return self.transform(X)


def load_scaler(path: str | pathlib.Path, refresh: bool = False) -> StandardScaler:
    """
    Load a saved StandardScaler from a file.

    Parameters
    ----------
    path (str):
        Path to the saved StandardScaler file.
    refresh:
        Whether we should re-save these to a file after loading.
        This is useful if you have updated scikit learn and it's complaining!

    Returns
    -------
    StandardScaler:
        The loaded StandardScaler object.

    Raises
    ------
    FileNotFoundError:
        If the specified file does not exist.
    ValueError:
        If the loaded object is not a StandardScaler.
    """
    try:
        scaler = joblib.load(path)
        # if not isinstance(scaler, StandardScaler):
        #     raise ValueError("Loaded object is not a StandardScaler")
        # TODO (2024-09-16 JSM) This was commented out as the new time scaler (for rbf encoding months) is not a StandardScaler
        # Reintroduce scaler typechecking for time scalers.

        if refresh:
            joblib.dump(scaler, path)
        return scaler
    except FileNotFoundError as ex:
        raise FileNotFoundError(f"No StandardScaler found at {path}") from ex


def load_all_scalers(
    directory: str | pathlib.Path = pathlib.Path(".", "models", "final"),
    refresh: bool = False
) -> dict[ScalerTypeEnum, StandardScaler]:
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
    return {
        ScalerTypeEnum.Data: load_scaler(pathlib.Path(directory) / "elecVAE_data_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.Aggregate: load_scaler(pathlib.Path(directory) / "elecVAE_aggregate_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.StartTime: load_scaler(pathlib.Path(directory) / "elecVAE_start_time_scaler.joblib", refresh=refresh),
        ScalerTypeEnum.EndTime: load_scaler(pathlib.Path(directory) / "elecVAE_end_time_scaler.joblib", refresh=refresh),
    }
