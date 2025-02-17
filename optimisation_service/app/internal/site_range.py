from app.models.site_range import SiteRange


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
    site_range_dict.pop("config")

    if "renewables" in site_range_dict.keys():
        n += not site_range_dict["renewables"]["COMPONENT_IS_MANDATORY"]
        for scalars in site_range_dict["renewables"]["yield_scalars"]:
            if len(scalars) > 1:
                n += 1
        site_range_dict.pop("renewables")

    for asset in site_range_dict.values():
        n += not asset["COMPONENT_IS_MANDATORY"]
        asset.pop("COMPONENT_IS_MANDATORY")
        for attr_values in asset.values():
            if len(attr_values) > 1:
                n += 1

    return n
