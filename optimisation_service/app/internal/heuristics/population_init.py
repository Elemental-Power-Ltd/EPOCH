import json
import random  # Use random instead of numpy.random to avoid numpy types that aren't json serialisable

import numpy as np
from epoch_simulator import TaskData

from app.models.site_data import EpochSiteData
from app.models.site_range import SiteRange

from .asset_heuristics import get_all_estimates


def generate_site_scenarios_from_heuristics(site_range: SiteRange, epoch_data: EpochSiteData, pop_size: int) -> list[TaskData]:
    """
    Generate a population of site scenarios by estimating some parameter values from data.

    For some parameters, estimates can be generated from the input data.
    We can then set these as the mu to truncated normal distributions.
    We then sample these distributions to generate parameter values.
    For parameters that can't be estimated from the data, parameter values are sampled from a uniform distribution.

    Parameters
    ----------
    site_range
        Problem site range.
    epoch_data
        Site data to generate estimates from.
    pop_size
        Number of scenarios generated in population.

    Returns
    -------
    pop
        Population of site scenarios.
    """
    estimates = get_all_estimates(epoch_data)

    site_range_dict = site_range.model_dump(exclude_none=True)
    config = site_range_dict["config"]
    site_range_dict.pop("config")

    td_pop = []
    for _ in range(pop_size):
        individual = {"config": config}
        for asset_name, asset_range in site_range_dict.items():
            if (not asset_range["COMPONENT_IS_MANDATORY"] and random.choice([True, False])) or asset_range[
                "COMPONENT_IS_MANDATORY"
            ]:
                if asset_name == "renewables":
                    individual["renewables"] = {
                        "yield_scalars": [
                            normal_choice(estimate, yield_scalar_values)
                            for estimate, yield_scalar_values in zip(
                                estimates["renewables"]["yield_scalars"], asset_range["yield_scalars"]
                            )
                        ]
                    }
                else:
                    individual[asset_name] = {}
                    for attribute_name, attribute_values in asset_range.items():
                        if attribute_name == "COMPONENT_IS_MANDATORY":
                            pass
                        elif (
                            asset_name in estimates.keys()
                            and attribute_name in estimates[asset_name].keys()
                            and len(attribute_values) > 1
                        ):
                            estimate = estimates[asset_name][attribute_name]
                            individual[asset_name][attribute_name] = normal_choice(estimate, attribute_values)
                        else:
                            individual[asset_name][attribute_name] = random.choice(attribute_values)
        td_pop.append(TaskData.from_json(json.dumps(individual)))
    # TODO: check CAPEX of values
    return td_pop


def normal_choice(estimate: float | int, attribute_values: list[float] | list[int], std_dev_scale: float = 0.1) -> int | float:
    """
    Randomly select a value from the attribute values list with probabilties from a truncated normal distribution with mu equal
    to the estimate and with the standard deviation equal to std_dev_scale times the difference between the minimum and maximum
    attribute value.

    Parameters
    ----------
    estimate
        Estimate value for the attribute to center distribution on.
    attribute_values
        Candidate attribute values to select from.
    std_dev_scale
        Scaler to modify distribution standard deviation.

    Returns
    -------
    selected
        The selected attribute value.
    """
    max_attr = max(attribute_values)
    if estimate > max_attr * 2:  # For cases where the estimate is much greater than any attribute value
        return max_attr

    min_attr = min(attribute_values)
    if estimate < min_attr / 2:  # For cases where the estimate is much smaller than any attribute value
        return min_attr

    std_dev = np.abs(max_attr - min_attr) * std_dev_scale
    probabilities = np.exp(-0.5 * ((np.array(attribute_values) - estimate) / std_dev) ** 2)
    probabilities /= probabilities.sum()

    selected = random.choices(population=attribute_values, weights=probabilities)[0]

    return selected
