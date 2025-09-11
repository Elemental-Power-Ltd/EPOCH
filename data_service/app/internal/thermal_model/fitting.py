"""Functions for fitting structural and fabric data to a set of gas data."""

import datetime
from pathlib import Path
from typing import cast

import numpy as np
import numpy.typing as npt
import pandas as pd
from bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer
from sklearn.metrics import r2_score  # type: ignore

from ...models.heating_load import InterventionEnum, ThermalModelResult
from ..epl_typing import HHDataFrame, SeedLike
from ..gas_meters.domestic_hot_water import get_poisson_weights
from .building_fabric import apply_interventions_to_structure
from .heat_capacities import U_VALUES_PATH
from .integrator import simulate
from .network import create_structure_from_params


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
    u_values_path: Path = U_VALUES_PATH,
    seed: SeedLike | None = None,
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
    scale_factor
        Scale area for the floor, with 1.0 being a 100m^2 floor
    ach
        Air changes per hour
    boiler_power
        Maximum heat output of the heat sourcein W
    setpoint
        target temperature for thermostatic control of the heat source
    dhw_usage
        kWh of domestic hot water used per day

    Returns
    -------
        L2 loss for this set of parameters in (kWh)^2
    """
    if start_ts is None:
        start_ts = gas_df["start_ts"].min() if "start_ts" in gas_df.columns else gas_df.index.min()
    if end_ts is None:
        end_ts = gas_df["end_ts"].max() if "end_ts" in gas_df.columns else gas_df.index.max()

    try:
        sim_df = simulate_parameters(
            scale_factor=scale_factor,
            ach=ach,
            u_value=u_value,
            boiler_power=boiler_power,
            dhw_usage=dhw_usage,
            setpoint=setpoint,
            weather_df=weather_df,
            elec_df=elec_df,
            start_ts=start_ts,
            end_ts=end_ts,
            u_values_path=u_values_path,
            seed=seed,
        )
    except AssertionError:
        # We need the "bad" outcome to roughly match the scale of the good outcomes,
        # so that we can sensibly fit Gaussians during the Bayesian optimisation.
        worst_energy_loss = np.sum(gas_df["consumption"]) ** 2 * 1.1
        worst_temperature_loss = 50**2 * (end_ts - start_ts).total_seconds() / 300.0
        worst_aggregate_loss = worst_energy_loss
        return cast(float, 100.0 * (worst_energy_loss + worst_temperature_loss + worst_aggregate_loss))
    resampled_df = resample_to_gas_df(sim_df, gas_df)
    energy_loss = cast(float, np.sum(np.power(gas_df["consumption"] - resampled_df, 2.0)))

    aggregrate_loss = cast(float, (gas_df["consumption"].sum() - np.sum(resampled_df)) ** 2)
    # How closely we want the boiler to control the temperatures for the thermal loss.
    # We generally want the temperatures to be within a few degrees of the setpoint
    # at all points during the year, to punish under- or over- heating.
    setpoint_width = 3.0
    temperature_mins = np.maximum(setpoint, sim_df["external_temperatures"]) + setpoint_width
    temperature_maxes = np.maximum(setpoint, sim_df["external_temperatures"]) - setpoint_width
    temperature_loss = cast(
        float,
        np.sum(
            np.maximum(
                (sim_df["temperatures"] - temperature_mins) * (sim_df["temperatures"] - temperature_maxes),
                0,
            )
        ),
    )

    temperature_loss_scale = cast(float, max(gas_df.consumption) / 100.0)
    return energy_loss + temperature_loss_scale * temperature_loss + aggregrate_loss


def simulate_parameters(
    scale_factor: float,
    ach: float,
    u_value: float,
    boiler_power: float,
    setpoint: float,
    dhw_usage: float,
    weather_df: pd.DataFrame,
    elec_df: pd.DataFrame | None,
    start_ts: datetime.datetime,
    end_ts: datetime.datetime,
    dt: datetime.timedelta | None = None,
    interventions: list[InterventionEnum] | list[str] | None = None,
    u_values_path: Path = U_VALUES_PATH,
    seed: SeedLike | None = None,
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
    scale_factor
        Scale area for the floor, with 1.0 being a 100m^2 floor
    ach
        Air changes per hour
    boiler_power
        Maximum heat output of the heat sourcein W
    setpoint
        target temperature for thermostatic control of the heat source
    dhw_usage
        kWh of domestic hot water used per day
    dt
        Timestep to use in the integrator
    interventions
        List of fabric interventions to apply to a structure
    u_values_path
        Path to a JSON file of U values for the building's fabric

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
        scale_factor=scale_factor,
        ach=ach,
        u_value=u_value,
        boiler_power=boiler_power,
        setpoint=setpoint,
        u_values_path=u_values_path,
    )
    if interventions is not None:
        hm = apply_interventions_to_structure(hm, interventions, u_values_path=u_values_path)
    sim_df = simulate(hm, external_df=weather_df, start_ts=start_ts, end_ts=end_ts, dt=dt, elec_df=elec_df)

    DHW_EVENT_SIZE = 1.0
    dhw_weights = get_poisson_weights(HHDataFrame(sim_df)) * dhw_usage
    rng = np.random.default_rng(seed=seed)
    total_dhw_usage = rng.poisson(dhw_weights, dhw_weights.size) * DHW_EVENT_SIZE
    sim_df["dhw"] = total_dhw_usage
    return sim_df


def calculate_thermal_model_r2(
    params: ThermalModelResult,
    gas_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    elec_df: pd.DataFrame | None = None,
    u_values_path: Path = U_VALUES_PATH,
    seed: SeedLike | None = None,
) -> float:
    """
    Calculate how effective this thermal model is at reproducing the actual gas meter data.

    This will run a simulation over the time period we have gas meter data for, and calculate the r2_score
    of (actual_gas, simulated_gas) including DHW.

    Parameters
    ----------
    params
        Thermal model parameters to use for the simulation
    gas_df
        Gas dataframe with a `consumption` column to measure against
    weather_df
        Weather dataframe over the same period as the gas_df
    elec_df
        Electricity dataframe for internal gains
    u_values_path
        Path to file containing u values; will default sensibly but watch out if you're in a notebook.

    Returns
    -------
    float
        r2_score of the simulated gas against real gas. 1.0 is the best possible score, but can be infinitely negative.
    """
    # We want to simulate the total gas usage over the time that we have gas data for.
    # Note that for long time periods, this might be slow (e.g. if we have 3 years of data)
    start_ts = gas_df["start_ts"].min() if "start_ts" in gas_df.columns else gas_df.index.min()
    end_ts = gas_df["end_ts"].max() if "end_ts" in gas_df.columns else gas_df.index.max()

    sim_df = simulate_parameters(
        scale_factor=params.scale_factor,
        ach=params.ach,
        u_value=params.u_value,
        boiler_power=params.boiler_power,
        setpoint=params.setpoint,
        dhw_usage=params.dhw_usage,
        elec_df=elec_df,
        start_ts=start_ts,
        end_ts=end_ts,
        weather_df=weather_df,
        dt=None,
        interventions=None,
        u_values_path=u_values_path,
        seed=seed,
    )

    sim_gas_usages = []
    for start_ts, end_ts in zip(gas_df.start_ts, gas_df.end_ts, strict=False):
        sim_within_mask = np.logical_and(sim_df.index >= start_ts, sim_df.index < end_ts)
        if np.any(sim_within_mask):
            heating_usage_within = sim_df.loc[sim_within_mask, "heating_usage"].sum()
            dhw_usage_within = sim_df.loc[sim_within_mask, "dhw"].sum()
        else:
            # In this case, we got an empty time period with no simulated sections.
            # This is unusual, but we handle it sensibly here.
            heating_usage_within = 0.0
            dhw_usage_within = 0.0
        sim_gas_usages.append(heating_usage_within + dhw_usage_within)
    return float(r2_score(gas_df["consumption"].to_numpy(), np.asarray(sim_gas_usages)))


def fit_to_gas_usage(
    gas_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    elec_df: pd.DataFrame | None = None,
    n_iter: int = 300,
    hints: ThermalModelResult | list[ThermalModelResult] | None = None,
    u_values_path: Path = U_VALUES_PATH,
    seed: SeedLike | None = None,
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
    hints
        Points to sample at that you think are reasonable, these can be previous thermal model results.
    u_values_path
        Path to a JSON file of U values for the building's fabric

    Returns
    -------
    dict[str, float]
        kwarg parameters for `create_simple_structure` that provide the best fit to the gas data.
    """
    # This is the upper bound, assuming that all usage in a given period is DHW.
    total_days = (gas_df.end_ts - gas_df.start_ts).dt.total_seconds() / (pd.Timedelta(days=1).total_seconds())
    daily_dhw = gas_df.consumption / total_days

    pbounds = {
        "scale_factor": (0.1, 10.0),  # buildings are between 10m^2 and 1000M^2
        "ach": (1.0, 20.0),  # average air changes per hour is often 3
        "u_value": (0.1, 2.0),  # a reasonable range of U values from the table of best to worst material
        "boiler_power": (0, 60e3),  # Boiler Size in kW
        "setpoint": (16, 24),  # internal thermostat setpoint that the boiler targets
        "dhw_usage": (0, daily_dhw.mean()),  # Pick the average: DHW is probably closer to the min, but maybe holidays drop it?
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
            u_values_path=u_values_path,
            seed=seed,
        ),
        pbounds=pbounds,
        bounds_transformer=SequentialDomainReductionTransformer(),
        random_state=seed,
    )

    if hints is None:
        default_hint = ThermalModelResult(
            scale_factor=1,
            ach=3.0,
            u_value=2.0,
            boiler_power=24e3,  # Boiler Size in kW
            setpoint=21,
            dhw_usage=daily_dhw.min(),
        )
        hints = [default_hint]
    elif isinstance(hints, ThermalModelResult):
        # We only got a single hint, so wrap it into a
        # list for the next step.
        hints = [hints]

    for hint in hints:
        # Probe some reasonable points to get us started
        # TODO (2025-05-01 MHJB): This is a single hint for each one, so we could try
        # multiple slightly perturbed hints.
        dumped_hint = hint.model_dump()
        for key, val in dumped_hint.items():
            if key not in pbounds:
                continue
            # If we re-use a hint from before that's out of bounds,
            # then clamp it back into the bounds that we're using.
            # But stay just a touch within the bounds to avoid sampling right at the edges (which are often bad)
            clamped_val = max(pbounds[key][0] * 1.01, min(val, pbounds[key][1] * 0.99))
            dumped_hint[key] = clamped_val
        opt.probe(
            params={
                "scale_factor": float(hint.scale_factor),
                "ach": float(hint.ach),
                "u_value": float(hint.u_value),
                "boiler_power": float(hint.boiler_power),
                "setpoint": float(hint.setpoint),
                "dhw_usage": float(hint.dhw_usage),
            },
            lazy=False,
        )

    opt.maximize(init_points=int(np.ceil(n_iter / 10)), n_iter=n_iter)

    assert opt.max is not None, "Did not find an optimum for this fitting job"
    assert opt.max["params"] is not None, "Optimum had None in params for fitting job"
    r2_score = calculate_thermal_model_r2(
        ThermalModelResult.model_validate(opt.max["params"]),
        gas_df=gas_df,
        weather_df=weather_df,
        elec_df=elec_df,
        u_values_path=u_values_path,
        seed=seed,
    )
    return ThermalModelResult(
        scale_factor=opt.max["params"]["scale_factor"],
        ach=opt.max["params"]["ach"],
        u_value=opt.max["params"]["u_value"],
        boiler_power=opt.max["params"]["boiler_power"],
        setpoint=opt.max["params"]["setpoint"],
        dhw_usage=opt.max["params"]["dhw_usage"],
        r2_score=r2_score,
    )
