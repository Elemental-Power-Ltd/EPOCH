"""
Heating intervention cost API endpoints.

This module provides FastAPI endpoints to calculate the costs of building
fabric interventions, such as insulation or glazing upgrades. It offers:
- Cost calculations based on thermal models
- Retrieval of intervention costs from a database for specific sites
- Breakdown of costs by intervention type
"""

from ...dependencies import DatabaseDep, DatabasePoolDep
from ...internal.thermal_model.costs import calculate_intervention_costs_params
from ...models.heating_load import InterventionCostRequest, InterventionCostResult, InterventionEnum, ThermalModelResult
from .router import api_router


async def get_heating_cost_thermal_model(
    thermal_model: ThermalModelResult, interventions: list[InterventionEnum], pool: DatabasePoolDep
) -> float:
    """
    Get the intervention costs for interventions applied to a building described by a thermal model.

    Parameters
    ----------
    thermal_model_id
        The ID of the relevant thermal model stored in the database
    interventions
        The interventions you want to apply e.g. Cladding, DoubleGlazing
    pool
        Database with thermal models in it

    Returns
    -------
    float
        Cost in GBP of applying interventions to this building.
    """
    costs = calculate_intervention_costs_params(thermal_model, interventions=interventions)
    return costs


@api_router.post("/get-intervention-cost", tags=["get", "heating"])
async def get_intervention_cost(params: InterventionCostRequest, conn: DatabaseDep) -> InterventionCostResult:
    """
    Get the costs of interventions for a given site.

    This will only return the interventions that are both stored in the database and are in your request.
    For example, if you request ["Loft", "DoubleGlazing"] and we only have ["Loft"] in the database, you'll
    only get a cost and corresponding total for the loft.

    Parameters
    ----------
    params
        A list of interventions (can be the empty list) that you are interested in for a site, and the site id

    Returns
    -------
    Broken-down costs by intervention type (check that they're all there!), and a total cost for those interventions.
    """
    if not params.interventions:
        return InterventionCostResult(
            breakdown={},
            total=0.0,
        )
    res = await conn.fetch(
        """
        SELECT
            intervention,
            cost
        FROM
            heating.interventions
        WHERE
            site_id = $1
        AND intervention = ANY($2::text[])
        """,
        params.site_id,
        tuple(params.interventions),
    )
    return InterventionCostResult(
        breakdown={InterventionEnum(intervention): float(cost) for intervention, cost in res},
        total=sum(float(cost) for _, cost in res),
    )
