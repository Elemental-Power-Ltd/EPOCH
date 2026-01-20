"""Utilities for fetching cost models.

A cost model is a set of piecewise linear functions used by EPOCH to estimate costs as a function of size by component.
"""

import json

from fastapi import APIRouter, HTTPException

from app.dependencies import DatabasePoolDep
from app.models.core import dataset_id_t
from app.models.cost_model import CostModelResponse

router = APIRouter()


@router.post("/list-cost-models", tags=["list", "cost_model"])
async def list_cost_models(pool: DatabasePoolDep) -> list[CostModelResponse]:
    """
    List all the cost models in the database.

    A cost model comes with a capex model and and opex model.

    Parameters
    ----------
    pool
        Database pool to interrogate

    Returns
    -------
    list[CostModelResponse]
        All the cost models in the database in increasing recency.
    """
    values = await pool.fetch("""
        SELECT
            cost_model_id,
            model_name,
            capex_model,
            opex_model,
            created_at
        FROM
            optimisation.cost_models
        ORDER BY created_at ASC""")
    return [
        CostModelResponse(
            cost_model_id=item["cost_model_id"],
            model_name=item["model_name"],
            capex_model=item["capex_model"],
            opex_model=item["opex_model"],
            created_at=item["created_at"],
        )
        for item in values
    ]


@router.post("/add-cost-model", tags=["add", "cost_model"])
async def add_cost_model(model: CostModelResponse, pool: DatabasePoolDep) -> CostModelResponse:
    """
    Add a cost model to the database.

    The CAPEX and OPEX models are just blobs of JSON, and your created_at is ignored and replaced by the database.

    Parameters
    ----------
    model
        Cost model to insert; will generate a UUID7 and created_at if not provided.

    Returns
    -------
    CostModelResponse
        the inserted model
    """
    await pool.execute(
        """INSERT INTO optimisation.cost_models (cost_model_id, model_name, capex_model, opex_model) VALUES ($1, $2, $3, $4)""",
        model.cost_model_id,
        model.model_name,
        json.dumps(model.capex_model),
        json.dumps(model.opex_model),
    )
    return model


@router.post("/get-cost-model", tags=["get", "cost_model"])
async def get_cost_model(cost_model_id: dataset_id_t, pool: DatabasePoolDep) -> CostModelResponse:
    """
    Get a given cost model from the database.

    This comes with the metadata as well.

    Parameters
    ----------
    cost_model_id
        ID of the cost model to get

    Raises
    ------
    HTTPException(400)
        If we can't find it

    Returns
    -------
    CostModelResponse
        CAPEX, OPEX and gubbins
    """
    resp = await pool.fetchrow(
        """
        SELECT
            cost_model_id,
            model_name,
            capex_model,
            opex_model,
            created_at
        FROM
            optimisation.cost_models
        WHERE cost_model_id = $1
        LIMIT 1""",
        cost_model_id,
    )
    if resp is None:
        raise HTTPException(400, f"Couldn't find a cost model for {cost_model_id}")
    return CostModelResponse(
        cost_model_id=cost_model_id,
        model_name=resp["model_name"],
        capex_model=json.loads(resp["capex_model"]),
        opex_model=json.loads(resp["opex_model"]),
        created_at=resp["created_at"],
    )
