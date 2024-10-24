from os import PathLike
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.stats import truncnorm

from app.models.problem import ParamRange

from .population_heuristics import (
    estimate_ashp_hpower,
    estimate_battery_capacity,
    estimate_battery_charge,
    estimate_battery_discharge,
    estimate_solar_pv,
    round_to_search_space,
)


def generate_initial_population(
    variable_param: dict[str, ParamRange], constant_param: dict[str, float], input_dir: PathLike, pop_size: int
) -> npt.NDArray:
    """
    Generate a population of solutions by estimating parameter values from data.

    Values for individual solutions are sampled from truncated normal distributions which mu is estimated from data.

    Parameters
    ----------
    variable_param
        dictionary of optimisable parameters with corresponding range.
    constant_param
        dictionary of non-optimisable parameter with their corresponding value.
    input_dir
        path to folder containing data files.
    pop_size
        number of solutions generated in population.
    """
    heating_df = pd.read_csv(Path(input_dir, "CSVHload.csv"))
    ashp_input_df = pd.read_csv(Path(input_dir, "CSVASHPinput.csv"))
    ashp_output_df = pd.read_csv(Path(input_dir, "CSVASHPoutput.csv"))
    air_temp_df = pd.read_csv(Path(input_dir, "CSVAirtemp.csv"))
    elec_df = pd.read_csv(Path(input_dir, "CSVEload.csv"))
    solar_df = pd.read_csv(Path(input_dir, "CSVRGen.csv"))

    pop, lbs, steps = [], np.array([]), np.array([])
    estimatable = ["ASHP_HPower", "ESS_capacity", "ESS_charge_power", "ESS_discharge_power", "ScalarRG1"]
    for parameter, param_range in variable_param.items():
        lower, upper, step = param_range["min"], param_range["max"], param_range["step"]
        if parameter in estimatable:
            if parameter == "ASHP_HPower":
                ashp_mode = constant_param["ASHP_HSource"]
                estimate = estimate_ashp_hpower(
                    heating_df=heating_df,
                    ashp_input_df=ashp_input_df,
                    ashp_output_df=ashp_output_df,
                    air_temp_df=air_temp_df,
                    ashp_mode=ashp_mode,
                )
            if parameter == "ESS_capacity":
                estimate = estimate_battery_capacity(elec_df=elec_df)
            if parameter == "ESS_charge_power":
                solar_scale = estimate_solar_pv(solar_df=solar_df, elec_df=elec_df)
                estimate = estimate_battery_charge(solar_df=solar_df, solar_scale=solar_scale)
            if parameter == "ESS_discharge_power":
                estimate = estimate_battery_discharge(elec_df=elec_df)
            if parameter == "ScalarRG1":
                estimate = estimate_solar_pv(solar_df=solar_df, elec_df=elec_df)

            sigma = (upper - lower) / 4
            a = (lower - estimate) / sigma
            b = (upper - estimate) / sigma
            non_clipped_values = truncnorm.rvs(a=a, b=b, loc=estimate, scale=sigma, size=pop_size)
            generated_values = round_to_search_space(x=non_clipped_values, start=lower, stop=upper, step=step)
        else:
            possible_values = np.arange(lower, upper + step, step)
            generated_values = np.random.choice(possible_values, size=pop_size)

        pop.append(generated_values)
        lbs, steps = np.append(lbs, lower), np.append(steps, step)
    pop = np.array(pop)
    pop = pop.transpose()
    scaled_pop = (pop - lbs) / steps
    # TODO: check CAPEX of values
    return scaled_pop
