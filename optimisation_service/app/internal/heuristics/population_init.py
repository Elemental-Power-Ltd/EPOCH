from collections import defaultdict
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
    Generate a population of solutions by estimating some parameter values from data.

    For some parameters, estimates can be generated from the input data.
    We can then set these as the mu to truncated normal distributions.
    We then sample these distributions to generate parameter values.
    For parameters that can't be estimated from the data, parameter values are sampled from a uniform distribution.

    Parameters
    ----------
    variable_param
        dictionary of optimisable parameters with corresponding range.
    constant_param
        dictionary of non-optimisable parameters with their corresponding value.
    input_dir
        path to folder containing data files.
    pop_size
        number of solutions generated in population.

    Returns
    -------
    scaled_pop
        Generated population, scaled for consumption by pymoo (in range [0, parameter value upper bound])
    """
    heating_df = pd.read_csv(Path(input_dir, "CSVHload.csv"))
    ashp_input_df = pd.read_csv(Path(input_dir, "CSVASHPinput.csv"))
    ashp_output_df = pd.read_csv(Path(input_dir, "CSVASHPoutput.csv"))
    air_temp_df = pd.read_csv(Path(input_dir, "CSVAirtemp.csv"))
    elec_df = pd.read_csv(Path(input_dir, "CSVEload.csv"))
    solar_df = pd.read_csv(Path(input_dir, "CSVRGen.csv"))

    rng = np.random.default_rng()

    def clipped_rand(lo, hi, step):
        x = rng.choice(a=np.arange(lo, hi), size=pop_size)
        return round_to_search_space(x, lo, hi, step)

    def clipped_norm(est, lo, hi, step):
        sigma = np.abs(hi - lo) / 4
        a = (lo - est) / sigma
        b = (hi - est) / sigma
        x = np.clip(truncnorm.rvs(a=a, b=b, loc=est, scale=sigma, size=pop_size), lo, hi)
        return round_to_search_space(x, lo, hi, step)

    sampler_funcs = defaultdict(lambda: lambda lo, hi, step: clipped_rand(lo, hi, step))
    sampler_funcs["ASHP_HPower"] = lambda lo, hi, step: clipped_norm(
        estimate_ashp_hpower(
            heating_df=heating_df,
            ashp_input_df=ashp_input_df,
            ashp_output_df=ashp_output_df,
            air_temp_df=air_temp_df,
            ashp_mode=constant_param["ASHP_HSource"],
        ),
        lo,
        hi,
        step,
    )
    sampler_funcs["ESS_capacity"] = lambda lo, hi, step: clipped_norm(estimate_battery_capacity(elec_df=elec_df), lo, hi, step)
    sampler_funcs["ESS_charge_power"] = lambda lo, hi, step: clipped_norm(
        estimate_battery_charge(solar_df=solar_df, solar_scale=estimate_solar_pv(solar_df=solar_df, elec_df=elec_df)),
        lo,
        hi,
        step,
    )
    sampler_funcs["ESS_discharge_power"] = lambda lo, hi, step: clipped_norm(
        estimate_battery_discharge(elec_df=elec_df), lo, hi, step
    )
    sampler_funcs["ScalarRG1"] = lambda lo, hi, step: clipped_norm(
        estimate_solar_pv(solar_df=solar_df, elec_df=elec_df), lo, hi, step
    )

    pop, lbs, steps = [], np.array([]), np.array([])
    for parameter, param_range in variable_param.items():
        lo, hi, step = param_range["min"], param_range["max"], param_range["step"]
        generated_values = sampler_funcs[parameter](lo, hi, step)
        pop.append(generated_values)
        lbs, steps = np.append(lbs, lo), np.append(steps, step)
    pop = np.array(pop)
    pop = pop.transpose()
    scaled_pop = (pop - lbs) / steps
    # TODO: check CAPEX of values
    return scaled_pop
