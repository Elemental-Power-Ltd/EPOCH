from app.models.epoch_types import SiteRange

REPEAT_COMPONENTS = {"solar_panels"}
FIXED_PARAMETERS = {"incumbent", "age", "lifetime", "floor_area", "fixed_gas_price"}


def count_parameters_to_optimise(site_range: SiteRange) -> int:
    """
    Count the number of parameters in a site range to optimise.

    Parameters
    ----------
    site_range
        Site range to analyse.

    Returns
    -------
    n
        Number of parameters to optimise
    """
    n = 0

    site_range_dict = site_range.model_dump(exclude_none=True)

    for asset_name, asset in site_range_dict.items():
        if asset_name in REPEAT_COMPONENTS:
            for sub_asset in asset:
                n += count_parameters_in_asset(sub_asset)
        else:
            n += count_parameters_in_asset(asset)

    return n


def count_parameters_in_asset(asset: dict[str, list[float]]) -> int:
    """
    Count the number of parameters to optimise in an individual component.

    Parameters
    ----------
    asset
        An individual component within the SiteRange.

    Returns
    -------
    n
        Number of parameters to optimise

    """
    n = 0
    n += not asset["COMPONENT_IS_MANDATORY"]
    for attribute in asset.values():
        # each list in the asset is a varying parameter
        if isinstance(attribute, list) and len(attribute) > 1:
            n += 1

    return n


def site_range_size(site_range: SiteRange) -> int:
    """
    Count the total number of combinations of a site range.

    Parameters
    ----------
    site_range
        Site range to analyse.

    Returns
    -------
    n
        Number of combinations
    """
    n = 1

    site_range_dict = site_range.model_dump(exclude_none=True)

    for asset_name, asset in site_range_dict.items():
        if asset_name in REPEAT_COMPONENTS:
            for sub_asset in asset:
                n *= asset_range_size(sub_asset)
        else:
            n *= asset_range_size(asset)

    return n


def asset_range_size(asset: dict[str, list[float]]) -> int:
    """
    Count the number of combinations of an individual asset.

    Parameters
    ----------
    asset
        An individual component within the SiteRange.

    Returns
    -------
    n
        Number of combinations
    """
    n = 1
    if not asset["COMPONENT_IS_MANDATORY"]:
        n *= 2
    for attribute in asset.values():
        # each list in the asset is a varying parameter
        if isinstance(attribute, list):
            n *= len(attribute)

    return n
