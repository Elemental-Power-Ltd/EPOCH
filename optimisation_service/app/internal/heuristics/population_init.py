import numpy as np
import numpy.typing as npt

from app.models.site_data import EpochSiteData
from app.models.site_range import SiteRange

from .asset_heuristics import EnergyStorageSystem, HeatPump, Renewables


def generate_building_initial_population(site_range: SiteRange, epoch_data: EpochSiteData, pop_size: int) -> npt.NDArray:
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
    rng = np.random.default_rng()

    N = len(epoch_data.building_eload)
    timestamps = [epoch_data.start_ts + (epoch_data.end_ts - epoch_data.start_ts) * i / (N - 1) for i in range(N)]

    def normal_choice(est: float | int, attribute_values: list[float | int]) -> npt.NDArray:
        lo, hi = attribute_values[0], attribute_values[-1]
        std_dev = np.abs(hi - lo) / 4
        probabilities = np.exp(-0.5 * ((np.array(attribute_values) - est) / std_dev) ** 2)
        probabilities /= probabilities.sum()
        return rng.choice(a=range(len(attribute_values)), size=pop_size, p=probabilities)

    estimates: dict[str, dict[str, int | float]] = {}
    estimates["heat_pump"] = {}
    estimates["heat_pump"]["heat_power"] = HeatPump.heat_power(
        building_hload=epoch_data.building_hload,
        ashp_input_table=epoch_data.ashp_input_table,
        ashp_output_table=epoch_data.ashp_output_table,
        air_temperature=epoch_data.air_temperature,
        timestamps=timestamps,
        ashp_mode=2.0,
    )
    estimates["energy_storage_system"] = {}
    estimates["energy_storage_system"]["capacity"] = EnergyStorageSystem.capacity(
        building_eload=epoch_data.building_eload, timestamps=timestamps
    )
    solar_yield_sum = [sum(values) for values in zip(*epoch_data.solar_yields)]
    estimates["energy_storage_system"]["charge_power"] = EnergyStorageSystem.charge_power(
        solar_yield=solar_yield_sum,
        timestamps=timestamps,
        solar_scale=Renewables.yield_scalars(solar_yield=solar_yield_sum, building_eload=epoch_data.building_eload),
    )
    estimates["energy_storage_system"]["discharge_power"] = EnergyStorageSystem.discharge_power(
        building_eload=epoch_data.building_eload, timestamps=timestamps
    )
    estimates["renewables"] = {}
    yield_scalars_estimates = [
        Renewables.yield_scalars(solar_yield=solar_yield, building_eload=epoch_data.building_eload)
        for solar_yield in epoch_data.solar_yields
    ]

    pop = []
    for asset_name, asset_range in site_range.model_dump().items():
        if asset_name == "config":
            pass
        if asset_name == "renewables":
            if not asset_range["COMPONENT_IS_MANDATORY"]:
                pop.append(rng.choice(a=[0, 1], size=pop_size))
            for estimate, yield_scalar_values in zip(yield_scalars_estimates, asset_range["yield_scalars"]):
                if len(yield_scalar_values) > 1:
                    chosen_value = normal_choice(estimate, yield_scalar_values)
                    pop.append(yield_scalar_values.index(chosen_value))
        else:
            for attrbute_name, attribute_values in asset_range.items():
                if attrbute_name == "COMPONENT_IS_MANDATORY":
                    if not attribute_values:
                        pop.append(rng.choice(a=[0, 1], size=pop_size))
                elif (
                    asset_name in estimates.keys()
                    and attrbute_name in estimates[asset_name].keys()
                    and len(attribute_values) > 1
                ):
                    estimate = estimates[asset_name][attrbute_name]
                    chosen_value = normal_choice(estimate, attribute_values)
                    pop.append(attribute_values.index(chosen_value))
                else:
                    pop.append(rng.choice(a=range(len(attribute_values)), size=pop_size))
    # TODO: check CAPEX of values
    return np.array(pop).transpose()
