"""Utility functions for training the VAE model."""

import pathlib

import fastdtw  # type: ignore
import pandas as pd
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import Dataset

from ..utils.bank_holidays import get_bank_holidays_sync

# from tslearn.clustering import TimeSeriesKMeans
# from tslearn.metrics import dtw


# classes
# Custom dataset class
class TimeSeriesDataset(Dataset):  # noqa: D101
    def __init__(self, data: torch.Tensor, aggregate: torch.Tensor, start_times: torch.Tensor, end_times: torch.Tensor):
        self.data = data
        self.aggregate = aggregate
        self.start_times = start_times
        self.end_times = end_times

    def __len__(self) -> int:
        """Magic method to return the length of the time series data class."""
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        """Magic getitem method for the time series data class."""
        return {
            "data": torch.tensor(self.data[idx], dtype=torch.float),
            "aggregate": torch.tensor(self.aggregate[idx], dtype=torch.float),
            "start_time": torch.tensor(self.start_times[idx], dtype=torch.float),  # UNIX time, in seconds
            "end_time": torch.tensor(self.end_times[idx], dtype=torch.float),  # UNIX time, in seconds
        }


def add_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """CHECK IF DATE IS A UK BANK HOLIDAY."""
    # Fetch UK bank holidays and convert dates to a set for fast lookup

    holiday_dates = set(get_bank_holidays_sync())
    # Function to check if a date is a public holiday or weekend

    def is_holiday_or_weekend(date: pd.Timestamp) -> bool:
        return date in holiday_dates or date.weekday() >= 5

    # add boolean column: is the record on a BH or weekend?
    df["is_hol_or_wknd"] = df.index.to_series().apply(is_holiday_or_weekend)

    # ==== CHECK IF THERE ARE ANY NaN VALUES IN EACH DAY
    df["contains_NaNs"] = df.isna().any(axis=1)

    # ==== ADD COLUMNS FOR DAILY AGGREGATES AND DAY OF WEEK LABELS
    df["daily_aggs"] = df[~df["contains_NaNs"]].iloc[:, :48].sum(axis=1)
    # df['day_of_wk'] = pd.to_datetime(df.index.astype('str')).day_name()
    assert isinstance(df.index, pd.DatetimeIndex)
    df["day_of_wk"] = df.index.day_name()
    return df


def load_and_process_DfT(file_path: pathlib.Path) -> pd.DataFrame:
    """Load the data and extract only electricity data."""
    df = pd.read_csv(file_path, index_col=3)
    df = df[df["Meter"] == "Total Imported Electricity"]
    df = df.drop(columns=["Site", "Meter", "Unit"])

    df.index = pd.to_datetime(df.index, dayfirst=True)
    # converts to a datetime index, preserves unit of measurement, expects day first

    df = add_covariates(df)
    return df


def load_and_process_long(file_path: pathlib.Path) -> pd.DataFrame:
    """Load and process electricity data when the CSV file has two columns: datetime and HH read."""
    df = pd.read_csv(file_path, header=0, names=["datetime", "value"])
    df["datetime"] = pd.to_datetime(df["datetime"], format="%d %b %Y %H:%M")
    df["date"] = df["datetime"].dt.date
    df["time"] = df["datetime"].dt.strftime("%H:%M")
    df = df.pivot_table(index="date", columns="time", values="value")

    df.index = pd.to_datetime(df.index, dayfirst=True)
    df = add_covariates(df)
    return df


# define functions for training VAE model


def vae_loss_function_simple(
    reconstructed_x: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, log_var: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Calculate the loss, comprising the reconstruction loss and the KL-div loss.

    Uses accumulated mse between inputs and reconstructions at each timestamp, to evaluate the reconstruction loss.

    Parameters
    ----------
    reconstructed_x (Tensor)
        Reconstructed time series data of shape (batch_size, seq_len, input_dim)
    x (Tensor)
        Time series data of shape (batch_size, seq_len, input_dim).
    mu (Tensor)
        Mean of the latent space distribution.
    log_var (Tensor)
        Log variance of the latent space distribution.

    Returns
    -------
    reconstruction_loss + kld_loss (Tensor)
        sum of the below loss components
    reconstruction_loss (Tensor)
        reconstruction loss, distance between input time series and its reconstruction
    kld_loss (Tensor)
        KL divergence between the encoder distn (with given params mu, log_var) and the (std Gaussian) latent prior
    """
    reconstruction_loss = nn.MSELoss(reduction="sum")(reconstructed_x, x)
    kld_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
    return reconstruction_loss + kld_loss, reconstruction_loss, kld_loss


def dtw_loss(x: torch.Tensor, reconstructed_x: torch.Tensor) -> torch.Tensor:
    """
    Evaluate the reconstruction loss, using dynamic time warping (DTW).

    This is to allow for temporal shifts in the reconstructed load profiles.
    Intended to better reflect accuracy in the overall 'shape' of the profile, rather than focusing on local values.

    Parameters
    ----------
    x (Tensor)
        Time series data of shape (batch_size, seq_len, input_dim).
    reconstructed_x (Tensor)
        Reconstructed time series data of shape (batch_size, seq_len, input_dim)

    Returns
    -------
    sbd_dist (Tensor)
        evaluated DTW-based distance between input time series.
    """
    dtw_dist = 0.0
    for i in range(x.size(0)):  # Iterate over each sample in the batch
        series_1 = x[i].cpu().numpy()
        series_2 = reconstructed_x[i].cpu().detach().numpy()
        dist, _ = fastdtw(series_1, series_2)
        dtw_dist += dist
    dtw_dist /= x.size(0)  # Average DTW distance across the batch
    return torch.tensor(dtw_dist, requires_grad=True)


def sbd_loss(x: torch.Tensor, reconstructed_x: torch.Tensor) -> float:
    """
    Evaluate the reconstruction loss using shape-based distance (SBD) to allow for temporal shifts, similarly to DTW (above).

    This approach makes use of fast Fourier transforms, making it more comp efficient than DTW.

    Parameters
    ----------
    x (Tensor)
        Time series data of shape (batch_size, seq_len, input_dim).
    reconstructed_x (Tensor)
        Reconstructed time series data of shape (batch_size, seq_len, input_dim)

    Returns
    -------
    sbd_dist (Tensor)
        evaluated shape-based distance between input time series.
    """
    sbd_dist = 0.0
    for i in range(x.size(0)):  # Iterate over each sample in the batch
        series_1 = x[i]
        series_2 = reconstructed_x[i]

        # Normalize the series to have zero mean and unit variance
        series_1 = (series_1 - series_1.mean()) / series_1.std()
        series_2 = (series_2 - series_2.mean()) / series_2.std()

        # Calculate cross-correlation
        # cross_corr = F.conv1d(
        #   series_1.unsqueeze(0).unsqueeze(0),
        #   series_2.unsqueeze(0).unsqueeze(0),
        #   padding=series_1.size(0) - 1)
        cross_corr = F.conv1d(series_1.unsqueeze(0), series_2.unsqueeze(0), padding=series_1.size(0) - 1)
        cross_corr = cross_corr.squeeze()

        # SBD is computed as 1 - max(normalized cross-correlation)
        max_corr = torch.max(cross_corr) / series_1.size(0)
        sbd_dist += 1 - max_corr

    # Average SBD distance across the batch
    sbd_dist /= x.size(0)
    return sbd_dist


# Function to compute the VAE loss (assuming SBD-based reconstruction loss)
def vae_loss_function(
    reconstructed_x: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, log_var: torch.Tensor
) -> tuple[torch.Tensor, float, torch.Tensor]:
    """
    Calculate the loss, comprising the reconstruction loss and the KL-div loss.

    Uses the shape-based distance to evaluate the reconstruction loss.

    Parameters
    ----------
    reconstructed_x (Tensor)
        Reconstructed time series data of shape (batch_size, seq_len, input_dim)
    x (Tensor)
        Time series data of shape (batch_size, seq_len, input_dim).
    mu (Tensor)
        Mean of the latent space distribution.
    log_var (Tensor)
        Log variance of the latent space distribution.

    Returns
    -------
    reconstruction_loss + kld_loss (Tensor)
        sum of the below loss components
    reconstruction_loss (Tensor)
        reconstruction loss, distance between input time series and its reconstruction
    kld_loss (Tensor)
        KL divergence between the encoder distn (with given params mu, log_var) and the (std Gaussian) latent prior
    """
    # Compute reconstruction loss using Shape-Based Distance (SBD)
    reconstruction_loss = sbd_loss(x, reconstructed_x)

    # Compute KLD loss
    kld_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())

    # Return total loss (reconstruction + KL divergence)
    return reconstruction_loss + kld_loss, reconstruction_loss, kld_loss
