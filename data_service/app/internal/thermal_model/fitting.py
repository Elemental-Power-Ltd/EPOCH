"""Functions for fitting structural and fabric data to a set of gas data."""

import datetime
from typing import cast

import numpy as np
import numpy.typing as npt
import pandas as pd
from bayes_opt import BayesianOptimization

from ...models.heating_load import ThermalModelResult
from ..epl_typing import HHDataFrame
from ..gas_meters.domestic_hot_water import get_poisson_weights
from ..utils.conversions import joule_to_kwh
from .building_elements import BuildingElement
from .integrator import simulate
from .network import HeatNetwork, create_simple_structure


def resample_to_gas_df(sim_df: pd.DataFrame, gas_df: pd.DataFrame) -> npt.NDArray[np.floating]:
    """
    Resample a dataframe with timestamps and a heating usage column to match the periods in a gas dataframe.

    Parameters
    ----------
    sim_df
        Simulation result dataframe with timestamp index (representing the start times) and a heating_usage
        column in kWh -- watch out for the units!
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
        samples.append(sim_df.loc[mask, "heating_usage"].sum())
    return np.asarray(samples)


def parameters_to_loss(
    scale_factor: float,
    ach: float,
    u_value: float,
    boiler_power: float,
    setpoint: float,
    dhw_usage: float,
    gas_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    elec_df: pd.DataFrame | None,
    start_ts: datetime.datetime | None = None,
    end_ts: datetime.datetime | None = None,
) -> float:
    """
    Calculate the gas usage loss for a specific set of parameters.

    Parameters
    ----------
    gas_df
        Gas dataframe with columns [start_ts, end_ts, consumption].
        Consumption should be in kWh.
        If this is provided we can use it to match the start and end periods.
    weather_df
        External weather dataframe including the "temp", "windspeed" and "solarradiation"; ideally hourly
        but is interpolated for the simulation.
    elec_df
        Electrical usage dataframe including a "consumption_kwh" column.
        This is interpolated to find a power at a given timestamp.
    start_ts
        Earliest timestamp to simulate. If not provided, use the earliest time in gas_df.
    end_ts
        Latest timestamp to simulate. If not provided, use the latest time in gas_df.

    Returns
    -------
        L2 loss for this set of parameters in (kWh)^2
    """
    if start_ts is None:
        start_ts = gas_df["start_ts"].min() if "start_ts" in gas_df.columns else gas_df.index.max()
    if end_ts is None:
        end_ts = gas_df["end_ts"].max() if "end_ts" in gas_df.columns else gas_df.index.max()

    try:
        sim_df = simulate_parameters(
            scale_factor=scale_factor,
            ach=ach,
            u_value=u_value,
            boiler_power=boiler_power,
            setpoint=setpoint,
            weather_df=weather_df,
            elec_df=elec_df,
            start_ts=start_ts,
            end_ts=end_ts,
        )
        DHW_EVENT_SIZE = 1.0
        # daily usage, the Poisson weights are normalised to 1.0
        dhw_weights = get_poisson_weights(HHDataFrame(sim_df)) * dhw_usage
        rng = np.random.default_rng()
        total_dhw_usage = rng.poisson(dhw_weights, dhw_weights.size) * DHW_EVENT_SIZE
        sim_df["heating_usage"] += total_dhw_usage
    except AssertionError:
        # We need the "bad" outcome to roughly match the scale of the good outcomes,
        # so that we can sensibly fit Gaussians during the Bayesian optimisation.
        worst_energy_loss = np.sum(gas_df["consumption"]) ** 2 * 1.1
        worst_temperature_loss = 50**2 * (end_ts - start_ts).total_seconds() / 300.0
        return cast(float, worst_energy_loss + worst_temperature_loss)
    resampled_df = resample_to_gas_df(sim_df, gas_df)
    energy_loss = cast(float, np.sum(np.power(gas_df["consumption"] - resampled_df, 2.0)))

    # How closely we want the boiler to control the temperatures for the thermal loss.
    setpoint_width = 3.0
    temperature_loss = cast(
        float,
        np.sum(
            np.maximum(
                (sim_df["temperatures"] - (setpoint + setpoint_width)) * (sim_df["temperatures"] - (setpoint - setpoint_width)),
                0,
            )
        ),
    )

    temperature_loss_scale = cast(float, max(gas_df.consumption) / 100.0)
    return energy_loss + temperature_loss_scale * temperature_loss


def create_structure_from_params(
    scale_factor: float = 1.0, ach: float = 1.0, u_value: float = 2.2, boiler_power: float = 24e3, setpoint: float = 21
) -> HeatNetwork:
    """
    Create a simple structure with some fitted parameters.

    This wraps around create_simple_structure, and then changes the parameters of the links
    directly afterwards.

    You should use this if you want to get exactly the same structure as you'd get oufr om
    `simulate_parameters`.

    Parameters
    ----------
    scale_factor
        Scale factor of the building compared to the default, which is 50m^2 with 5m high walls.
    ach
        Air changes per hour in this building (as a fraction of total air)
    u_value
        U value of main structural material for walls.
    boiler_power
        Boiler power in W, also scales up the size of the heating system linearlly.
    setpoint
        Equivalent 24/7 thermostat setpoint for the boiler.

    Returns
    -------
    HeatNetwork
        Simple structure with the values changed.
    """
    hm = create_simple_structure(
        wall_width=10.0 * scale_factor,
        wall_height=5.0 * scale_factor,
        window_area=1.0 * scale_factor,
        floor_area=50.0 * scale_factor,
    )

    hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].power = boiler_power
    hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].setpoint_temperature = setpoint

    # Radiators are assumed to be slightly undersized compared to the boiler.
    hm.edges[BuildingElement.HeatingSystem, BuildingElement.InternalAir]["radiative"].power = boiler_power * 0.75

    # Scale up the thermal mass of the heating system according to the boiler size
    hm.nodes[BuildingElement.HeatingSystem]["thermal_mass"] *= (
        boiler_power / hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].power
    )

    hm.edges[BuildingElement.InternalAir, BuildingElement.ExternalAir]["convective"].ach = ach
    for v in [BuildingElement.WallEast, BuildingElement.WallSouth, BuildingElement.WallNorth, BuildingElement.WallWest]:
        hm.edges[BuildingElement.InternalAir, v]["conductive"].heat_transfer = u_value
    return hm


def simulate_parameters(
    scale_factor: float,
    ach: float,
    u_value: float,
    boiler_power: float,
    setpoint: float,
    weather_df: pd.DataFrame,
    elec_df: pd.DataFrame | None,
    start_ts: datetime.datetime,
    end_ts: datetime.datetime,
    dt: datetime.timedelta | None = None,
) -> pd.DataFrame:
    """
    Calculate the gas usage loss for a specific set of parameters.

    Parameters
    ----------
    weather_df
        External weather dataframe including the "temp", "windspeed" and "solarradiation"; ideally hourly
        but is interpolated for the simulation.
    elec_df
        Electrical usage dataframe including a "consumption_kwh" column.
        This is interpolated to find a power at a given timestamp.
    start_ts
        Earliest timestamp to simulate. If not provided, use the earliest time in gas_df.
    end_ts
        Latest timestamp to simulate. If not provided, use the latest time in gas_df.

    Returns
    -------
    simulated_df: pd.DataFrame
        The results of the simulation between start_ts and end_ts for this building.
        Returns a "temperature", "heating_usage" column and is indexed by simulation time.
        You probably want to resample this to your period of interest.
    """
    if dt is None:
        dt = datetime.timedelta(minutes=3)
    hm = create_structure_from_params(
        scale_factor=scale_factor, ach=ach, u_value=u_value, boiler_power=boiler_power, setpoint=setpoint
    )
    sim_df = simulate(hm, external_df=weather_df, start_ts=start_ts, end_ts=end_ts, dt=dt, elec_df=elec_df)
    # Note the change of units here
    sim_df.heating_usage = -joule_to_kwh(sim_df.heating_usage)
    return sim_df


def fit_to_gas_usage(
    gas_df: pd.DataFrame, weather_df: pd.DataFrame, elec_df: pd.DataFrame | None = None, n_iter: int = 300
) -> ThermalModelResult:
    """
    Fit some building parameters to a gas consumption pattern.

    This will use Bayesian Optimisation to estimate the best parameters for the `create_structure_from_params` function.

    Parameters
    ----------
    gas_df
        Gas usage dataframe with start_ts, end_ts and consumption columns
    weather_df
        Hourly weather dataframe with "temp", "windspeed", "solarradiation" columns
    elec_df
        Electricity usage dataframe with "consumption" columns (optional)

    Returns
    -------
    dict[str, float]
        kwarg parameters for `create_simple_structure` that provide the best fit to the gas data.
    """
    pbounds = {
        "scale_factor": (0.1, 20.0),
        "ach": (0.01, 20.0),
        "u_value": (0.1, 2.5),
        "boiler_power": (0, 60e3),  # Boiler Size in kW
        "setpoint": (16, 24),
        "dhw_usage": (0, max(gas_df.consumption)),
    }
    opt = BayesianOptimization(
        # There's a minus in here as BayesianOptimisation tries to maximise,
        # and we want to minimize the loss.
        f=lambda scale_factor, ach, u_value, boiler_power, setpoint, dhw_usage: -parameters_to_loss(
            scale_factor,
            ach=ach,
            u_value=u_value,
            boiler_power=boiler_power,
            setpoint=setpoint,
            dhw_usage=dhw_usage,
            gas_df=gas_df,
            weather_df=weather_df,
            elec_df=elec_df,
            start_ts=None,  # calculate automatically from gas meters
            end_ts=None,  # calculate automatically from gas meters
        ),
        pbounds=pbounds,
    )
    opt.maximize(init_points=int(np.ceil(n_iter / 10)), n_iter=n_iter)

    assert opt.max is not None
    assert opt.max["params"] is not None
    return ThermalModelResult(
        scale_factor=opt.max["params"]["scale_factor"],
        ach=opt.max["params"]["ach"],
        u_value=opt.max["params"]["u_value"],
        boiler_power=opt.max["params"]["boiler_power"],
        setpoint=opt.max["params"]["setpoint"],
        dhw_usage=opt.max["params"]["dhw_usage"],
    )
