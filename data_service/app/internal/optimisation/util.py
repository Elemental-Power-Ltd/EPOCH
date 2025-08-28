"""Utility functions for handling Optimisation types."""
import json

from app.models.optimisation import CostInfo


def capex_breakdown_to_json(breakdown: list[CostInfo] | None) -> str | None:
    """
    Convert an (optional) capex breakdown into json.

    Parameters
    ----------
    breakdown
        The pydantic definition for a list of Cost Information (or None)

    Returns
    -------
        A json string or None
    """
    if breakdown is None:
        return None

    return json.dumps([cost.model_dump() for cost in breakdown])


def capex_breakdown_from_json(capex_json: str | None) -> list[CostInfo] | None:
    """
    Convert the JSON written to the database back into a list[CostInfo] (or None).

    Parameters
    ----------
    capex_json
        A json string or None, as written to the database

    Returns
    -------
        list[CostInfo] or None

    """
    if capex_json is None:
        return None

    cost_list = json.loads(capex_json)
    return [CostInfo.model_validate(cost) for cost in cost_list]
