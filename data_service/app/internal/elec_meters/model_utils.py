"""Utility functions for loading additional parts for the ML models."""

import pathlib

import joblib
from sklearn.preprocessing import StandardScaler  # type: ignore


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
        if not isinstance(scaler, StandardScaler):
            raise ValueError("Loaded object is not a StandardScaler")

        if refresh:
            joblib.dump(scaler, path)
        return scaler
    except FileNotFoundError as ex:
        raise FileNotFoundError(f"No StandardScaler found at {path}") from ex
