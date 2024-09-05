"""Utility functions for loading additional parts for the ML models."""

import enum
import pathlib

import joblib
from sklearn.preprocessing import StandardScaler  # type: ignore


class ScalerTypeEnum(str, enum.Enum):
    """Different types of pre-processing scalers for the VAE."""

    Data = "data"
    Aggregate = "aggregate"
    StartTime = "start_time"
    EndTime = "end_time"


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


def load_all_scalers(
    directory: str | pathlib.Path = pathlib.Path(".", "models", "final"),
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
        ScalerTypeEnum.Data: load_scaler(pathlib.Path(directory) / "elecVAE_data_scaler.joblib"),
        ScalerTypeEnum.Aggregate: load_scaler(pathlib.Path(directory) / "elecVAE_aggregate_scaler.joblib"),
        ScalerTypeEnum.StartTime: load_scaler(pathlib.Path(directory) / "elecVAE_start_time_scaler.joblib"),
        ScalerTypeEnum.EndTime: load_scaler(pathlib.Path(directory) / "elecVAE_end_time_scaler.joblib"),
    }
