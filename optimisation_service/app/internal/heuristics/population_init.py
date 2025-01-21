from os import PathLike
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd

from app.models.site_range import SiteRange

from .asset_heuristics import energy_storage_system, heat_pump, renewables


def generate_building_initial_population(site_range: SiteRange, input_dir: PathLike, pop_size: int) -> npt.NDArray:
    """
    Generate a population of solutions by estimating some parameter values from data.

    For some parameters, estimates can be generated from the input data.
    We can then set these as the mu to truncated normal distributions.
    We then sample these distributions to generate parameter values.
    For parameters that can't be estimated from the data, parameter values are sampled from a uniform distribution.

    Parameters
    ----------
    site_range
        Problem site range.
    input_dir
        Path to folder containing data files.
    pop_size
        Number of solutions generated in population.

    Returns
    -------
    pop
        Generated population, prepared for pymoo (in range [0, number of asset values])
    """
    heating_df = pd.read_csv(Path(input_dir, "CSVHload.csv"))
    ashp_input_df = pd.read_csv(Path(input_dir, "CSVASHPinput.csv"))
    ashp_output_df = pd.read_csv(Path(input_dir, "CSVASHPoutput.csv"))
    air_temp_df = pd.read_csv(Path(input_dir, "CSVAirtemp.csv"))
    elec_df = pd.read_csv(Path(input_dir, "CSVEload.csv"))
    solar_df = pd.read_csv(Path(input_dir, "CSVRGen.csv"))

    rng = np.random.default_rng()

    def normal_choice(est: float | int, attribute_values: list[float | int]) -> npt.NDArray:
        lo, hi = attribute_values[0], attribute_values[-1]
        std_dev = np.abs(hi - lo) / 4
        probabilities = np.exp(-0.5 * ((np.array(attribute_values) - est) / std_dev) ** 2)
        probabilities /= probabilities.sum()
        return rng.choice(a=range(len(attribute_values)), size=pop_size, p=probabilities)

    estimates: dict[str, dict[str, int | float]] = {}
    estimates["heat_pump"] = {}
    estimates["heat_pump"]["heat_power"] = heat_pump.heat_power(
        heating_df=heating_df,
        ashp_input_df=ashp_input_df,
        ashp_output_df=ashp_output_df,
        air_temp_df=air_temp_df,
        ashp_mode=2.0,
    )
    estimates["energy_storage_system"] = {}
    estimates["energy_storage_system"]["capacity"] = energy_storage_system.capacity(elec_df=elec_df)
    estimates["energy_storage_system"]["charge_power"] = energy_storage_system.charge_power(
        solar_df=solar_df, solar_scale=renewables.yield_scalars(solar_df=solar_df, elec_df=elec_df)
    )
    estimates["energy_storage_system"]["discharge_power"] = energy_storage_system.discharge_power(elec_df=elec_df)
    estimates["renewables"] = {}
    estimates["renewables"]["yield_scalars"] = renewables.yield_scalars(solar_df=solar_df, elec_df=elec_df)

    pop = []
    for asset_name, asset_range in site_range.model_dump().items():
        if asset_name == "config":
            pass
        else:
            for attrbute_name, attribute_values in asset_range.items():
                if attrbute_name == "COMPONENT_IS_MANDATORY":
                    if not attribute_values:
                        generated_indeces = rng.choice(a=[0, 1], size=pop_size)
                elif (
                    asset_name in estimates.keys()
                    and attrbute_name in estimates[asset_name].keys()
                    and len(attribute_values) > 1
                ):
                    estimate = estimates[asset_name][attrbute_name]
                    generated_indeces = normal_choice(estimate, attribute_values)
                else:
                    generated_indeces = rng.choice(a=range(len(attribute_values)), size=pop_size)
        pop.append(generated_indeces)
    # TODO: check CAPEX of values
    return np.array(pop).transpose()
