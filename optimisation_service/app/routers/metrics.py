"""Endpoints for information about optimisation metrics."""

from typing import Literal

from fastapi import APIRouter

from app.models.metrics import MetricDirection

router = APIRouter()


@router.get("/get-metric-directions", tags=["metric"])
async def get_metric_directions() -> dict[str, Literal[1] | Literal[-1]]:
    """
    Get the directions for the metrics, which means whether we want to maximise or minimise them.

    This returns 1 for objectives we want to minimise, -1 for objectives we want to maximise.
    Use these numbers by multiplying the metrics by this number and then minimising them.

    If you're using these results to sort, then:
        - Any metrics with "+1" should have the lowest value first (sort ascending)
        - Any metrics with "-1" should have the highest value first (sort descending)

    Generally the balance metrics are to be maximised (a positive balance is a greater saving against the baseline,
    a negative balance is doing worse against the baseline) and absolute metrics are to be minimised.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, +/- 1]
        Dictionary with metric names, +1 for each metric to minimise, -1 for each metric to maximise.
    """
    return {m.name: m.value for m in MetricDirection}
