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


class LazyDict(dict):
    def __getitem__(self, item):
        value = dict.__getitem__(self, item)
        if callable(value):
            value = value()
            dict.__setitem__(self, item, value)
        return value


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
    dfs = LazyDict()
    dfs["heating_df"] = lambda: pd.read_csv(Path(input_dir, "CSVHload.csv"))
    dfs["ashp_input_df"] = lambda: pd.read_csv(Path(input_dir, "CSVASHPinput.csv"))
    dfs["ashp_output_df"] = lambda: pd.read_csv(Path(input_dir, "CSVASHPoutput.csv"))
    dfs["air_temp_df"] = lambda: pd.read_csv(Path(input_dir, "CSVAirtemp.csv"))
    dfs["elec_df"] = lambda: pd.read_csv(Path(input_dir, "CSVEload.csv"))
    dfs["solar_df"] = lambda: pd.read_csv(Path(input_dir, "CSVRGen.csv"))

    estimates = LazyDict()
    estimates["ASHP_HPower"] = lambda: estimate_ashp_hpower(
        heating_df=dfs["heating_df"],
        ashp_input_df=dfs["ashp_input_df"],
        ashp_output_df=dfs["ashp_output_df"],
        air_temp_df=dfs["air_temp_df"],
        ashp_mode=constant_param["ASHP_HSource"],
    )
    estimates["ESS_capacity"] = lambda: estimate_battery_capacity(elec_df=dfs["elec_df"])
    estimates["ScalarRG1"] = lambda: estimate_solar_pv(solar_df=dfs["solar_df"], elec_df=dfs["elec_df"])
    estimates["ESS_charge_power"] = lambda: estimate_battery_charge(
        solar_df=dfs["solar_df"], solar_scale=estimates["ScalarRG1"]
    )
    estimates["ESS_discharge_power"] = lambda: estimate_battery_discharge(elec_df=dfs["elec_df"])

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
    sampler_funcs["ASHP_HPower"] = lambda lo, hi, step: clipped_norm(estimates["ASHP_HPower"], lo, hi, step)
    sampler_funcs["ESS_capacity"] = lambda lo, hi, step: clipped_norm(estimates["ESS_capacity"], lo, hi, step)
    sampler_funcs["ESS_charge_power"] = lambda lo, hi, step: clipped_norm(estimates["ESS_charge_power"], lo, hi, step)
    sampler_funcs["ESS_discharge_power"] = lambda lo, hi, step: clipped_norm(estimates["ESS_discharge_power"], lo, hi, step)
    sampler_funcs["ScalarRG1"] = lambda lo, hi, step: clipped_norm(estimates["ScalarRG1"], lo, hi, step)

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
