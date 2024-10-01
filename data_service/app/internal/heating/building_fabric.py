"""
Functions for a simple model of building fabric.

Here, we apply a simple % saving to the total kwh per HDD number.
"""

import copy

from ...models.heating_load import InterventionEnum
from ...models.weather import BaitAndModelCoefs

# FABRIC_SAVINGS = {
#    InterventionEnum.Loft: 1 - (2.4 / 100),  # via NEED 2021
#    InterventionEnum.Cladding: 1 - (8.8 / 100),  # via NEED 2021
#    InterventionEnum.DoubleGlazing: 1 - (4.4 / 100),
#    # via https://www.sciencedirect.com/science/article/abs/pii/S0378778819312782
# }

# These numbers are made up!
FABRIC_SAVINGS = {
    InterventionEnum.Loft: 1 - 0.1,
    InterventionEnum.Cladding: 1 - 0.2,
    InterventionEnum.DoubleGlazing: 1 - 0.15,
}

FABRIC_WINDCHILL = {InterventionEnum.Loft: 1.00, InterventionEnum.Cladding: 0.95, InterventionEnum.DoubleGlazing: 0.90}


def apply_fabric_interventions(bait_coefs: BaitAndModelCoefs, interventions: list[InterventionEnum]) -> BaitAndModelCoefs:
    """
    Apply some fabric interventions to the BAIT and model coefficients to mimic energy savings.

    This is currently a filthy hack -- be wary! It just drops the heating kWh per HDD by
    a flat savings percentage, and for some interventions will also affect the BAIT windchill
    coefficient.
    You can get the costs of each intervention from `/get-intervention-costs`.

    Parameters
    ----------
    bait_coefs
        Fitted BAIT and heating model coefficients, calculated from gas meter data.
    interventions
        Some building fabric interventions you would like to do.
        Currently assumes that these are multiplicative
        (e.g. two interventions with 10% saving lead to 19% total saving)

    Returns
    -------
    modified BAIT and heating model coefficients, mostly changed in `heating_kwh`
    """
    # make sure we don't mutate the original
    new_coefs = copy.deepcopy(bait_coefs)
    for intervention in interventions:
        new_coefs.heating_kwh *= FABRIC_SAVINGS[intervention]
        new_coefs.wind_chill *= FABRIC_WINDCHILL[intervention]
    return new_coefs
