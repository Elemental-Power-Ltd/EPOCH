"""Functions for fitting structural and fabric data to a set of gas data."""

import datetime

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy.optimize

from ..utils.conversions import joule_to_kwh
from .building_elements import BuildingElement
from .integrator import simulate
from .network import create_simple_structure


def fit_to_gas_usage(gas_df: pd.DataFrame, weather_df: pd.DataFrame) -> None:
    """
    Fit a simplified structure (four walls, two windows) to the gas usage data we've observed.

    This will create the bare minimum structure via `create_simple_structure` and attempt to find the
    U values and sizes that correctly reproduce the gas usage data provided, given a set of weather.

    More gas usage data will work better for this, but it should be fine with enough monthly readings.
    The weather data you will want to be relatively granular: hourly VisualCrossing data should be enough.

    Parameters
    ----------
    gas_df
        Pandas dataframe with (start_ts, end_ts, consumption) columns where consumption is in kWh
    weather_df
        VisualCrossing weather dataframe with datetime index, "temp", "solarradiation" and "windspeed" columns.

    Returns
    -------
    ???? not sure yet, could be anything!
    """

    def resample_to_gas_df(sim_df: pd.DataFrame, gas_df: pd.DataFrame) -> npt.NDArray[np.floating]:
        """
        Resample a dataframe with timestamps and a heating usage column to match the periods in a gas dataframe.

        Parameters
        ----------
        sim_df
            Simulation result dataframe with timestamp index (representing the start times) and a heating_usage
            column in J
        gas_df
            Actual gas usage dataframe with periods of interest to resample to, in form of start_ts and end_ts columns

        Returns
        -------
            Numpy array of the same length as gas_df, where the 0th entry represents the summed values in sim_df for
            the 0th row of gas_df (and so on)
        """
        samples = []
        for start_ts, end_ts in zip(gas_df["start_ts"], gas_df["end_ts"], strict=False):
            mask = np.logical_and(sim_df.index >= start_ts, sim_df.index < end_ts)
            samples.append(joule_to_kwh(sim_df.loc[mask, "heating_usage"].sum()))
        return np.asarray(samples)

    def simulate_parameters(x: npt.NDArray[np.floating], /, gas_df: pd.DataFrame, weather_df: pd.DataFrame) -> float:
        """
        Calculate the gas usage loss for a specific set of parameters.

        The parameters, passed as array x, represent:
            - x[0]: a building size scale factor
            - x[1]: a convective air changes per hour factor, between 0 and 10
            - x[2]: U-values of the wall material

        Parameters
        ----------
        x
            Scipy parameter vector
        gas_df
            Gas dataframe with columns [start_ts, end_ts, consumption].
            Consumption should be in kWh.

        Returns
        -------
            L2 loss for this set of parameters in (kWh)^2
        """
        hm = create_simple_structure(wall_area=10.0 * x[0], window_area=1.0 * x[0], floor_area=50.0 * x[0])
        hm.edges[BuildingElement.InternalAir, BuildingElement.ExternalAir]["convective"].ach = x[1]

        for v in [(BuildingElement.WallEast, BuildingElement.WallSouth, BuildingElement.WallNorth, BuildingElement.WallWest)]:
            hm.edges[BuildingElement.InternalAir, v]["conductive"]["heat_transfer"] = x[2]

        sim_df = simulate(
            hm, weather_df, start_ts=gas_df.index.min(), end_ts=gas_df.index.max(), dt=datetime.timedelta(minutes=5)
        )
        resampled_df = resample_to_gas_df(sim_df, gas_df)
        return float(np.sum(np.power(gas_df["consumption"] - resampled_df, 2.0)))

    res = scipy.optimize.minimize(
        simulate_parameters,
        x0=[1.0, 1.5, 2.0],
        args=(gas_df, weather_df),
        bounds=[
            (0.0, 10.0),  # Scale factor
            (0.0, 10.0),  # ACH
            (0.0, 10.0),  # U values
        ],
    )

    print(res)

    # TODO (2024-12-10 MHJB): finish this off?
