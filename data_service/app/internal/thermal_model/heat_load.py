"""Generate an EPOCH-friendly heat load using the thermal model."""

import pandas as pd

from ...models.heating_load import InterventionEnum, ThermalModelResult
from .integrator import simulate
from .network import HeatNetwork

type FabricParameters = dict[str, float]


def generate_heat_load(structure: HeatNetwork, weather_df: pd.DataFrame, elec_df: pd.DataFrame | None = None) -> pd.Series:
    """
    Generate a heating load given a structure and some weather data.

    Parameters
    ----------
    structure

    weather_df

    elec_df

    Returns
    -------
    just the heat load
    """
    start_ts = weather_df.timestamp.min()
    end_ts = weather_df.timestamp.max() + pd.Timedelta(hours=1)
    sim_df = simulate(
        structure, external_df=weather_df, elec_df=elec_df, start_ts=start_ts, end_ts=end_ts, dt=pd.Timedelta(minutes=3)
    )

    return sim_df["heating_usage"].resample(pd.Timedelta(minutes=30)).sum()


def apply_fabric_intervention_to_parameters(params: ThermalModelResult, intervention: InterventionEnum) -> ThermalModelResult:
    """
    Apply a given fabric intervention to a pre-fitted thermal model to get a new one.

    Parameters
    ----------
    params

    intervention

    Returns
    -------
    ThermalModelResult
    """
    # these numbers are nonsense
    match intervention:
        case InterventionEnum.Loft:
            params.u_value *= 0.8
        case InterventionEnum.DoubleGlazing:
            params.u_value *= 0.8
        case InterventionEnum.Cladding:
            params.u_value = 1.0
    return params
