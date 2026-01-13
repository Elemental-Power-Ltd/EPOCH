import random  # Use random instead of numpy.random to avoid numpy types that aren't json serialisable
from typing import cast

import numpy as np

from app.internal.heuristics.asset_heuristics import get_all_estimates
from app.internal.site_range import FIXED_PARAMETERS, REPEAT_COMPONENTS
from app.models.epoch_types import SiteRange
from app.models.ga_utils import AnnotatedTaskData, asset_t
from app.models.site_data import EpochSiteData


def generate_site_scenarios_from_heuristics(
    site_range: SiteRange, epoch_data: EpochSiteData, pop_size: int
) -> list[AnnotatedTaskData]:
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

    td_pop = []
    for _ in range(pop_size):
        # Each individual can be an arbitrary type of asset;
        # if it's a repeated asset then we can have many.

        individual: dict[str, asset_t | list[asset_t]] = {}
        for asset_name, asset_range in site_range_dict.items():
            if asset_name in REPEAT_COMPONENTS:
                individual[asset_name] = []
                for i, sub_asset in enumerate(asset_range):
                    if is_mandatory_or_random(sub_asset):
                        repeat_asset = generate_asset_from_heuristics(asset_name, sub_asset, estimates)
                        # associate this asset with the index in the SiteRange
                        repeat_asset["index_tracker"] = i
                        cast(list[asset_t], individual[asset_name]).append(repeat_asset)
            elif is_mandatory_or_random(asset_range):
                individual[asset_name] = generate_asset_from_heuristics(asset_name, asset_range, estimates)

        td_pop.append(AnnotatedTaskData.model_validate(individual))
    # TODO: check CAPEX of values
    return td_pop


def is_mandatory_or_random(asset: dict[str, bool]) -> bool:
    """
    Decide if an asset should be included in this individual.

    Returns True if the asset is mandatory and a random choice otherwise.

    Parameters
    ----------
    asset
        A subset of the SiteRange for an individual component.

    Returns
    -------
        Whether this component should be included or not.
    """
    return asset["COMPONENT_IS_MANDATORY"] or random.choice([True, False])


def generate_asset_from_heuristics(asset_name: str, asset: asset_t, estimates: dict[str, asset_t]) -> asset_t:
    """
    Create an instance of this asset type using the heuristically derived values for this site.

    Parameters
    ----------
    asset_name
        The name of the asset.
    asset
        The subset of the SiteRange for this component.
    estimates
        The heuristics for this site

    Returns
    -------
    The subset of the TaskRange for this component with appropriate estimates.
    """
    task_data_asset = {}
    for attribute_name, attribute_values in asset.items():
        if attribute_name == "COMPONENT_IS_MANDATORY":
            pass
        elif attribute_name in FIXED_PARAMETERS:
            # fixed_parameters are forwarded as is, there's no choice to make
            task_data_asset[attribute_name] = attribute_values
        elif (
            asset_name in estimates.keys()
            and attribute_name in estimates[asset_name].keys()
            and isinstance(attribute_values, list)
            and len(attribute_values) > 1
        ):
            estimate = cast(float | int, estimates[asset_name][attribute_name])
            task_data_asset[attribute_name] = normal_choice(estimate, cast(list[float] | list[int], attribute_values))
        else:
            task_data_asset[attribute_name] = random.choice(cast(list[float] | list[int], attribute_values))

    return task_data_asset


def normal_choice(estimate: float | int, attribute_values: list[float] | list[int], std_dev_scale: float = 0.1) -> int | float:
    """
    Randomly select a value from the attribute values list with probabilties from a truncated normal distribution.

    This has mu equal to the estimate and with the standard deviation equal to std_dev_scale times the difference
    between the minimum and maximum attribute value.

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
