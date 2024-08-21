"""
Endpoints to store the requests and results of optimisation tasks.

Each optimisation task should start by filing the job config in the database,
and then later on add the results.
Each result is uniquely identified, and belongs to a set of results.
"""

import json
import uuid

import asyncpg
import pydantic
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from ..dependencies import DatabaseDep
from ..models.core import SiteID, TaskID, ResultID
from ..models.optimisation import OptimisationResult, TaskConfig, OptimisationResultListEntry, Objective

router = APIRouter()


@router.post("/get-optimisation-result")
async def get_optimisation_result(result_id: ResultID, conn: DatabaseDep) -> OptimisationResult:
    """
    Get a single set of optimisation results.

    This looks up for a single specific result, which is one row from the database.

    Parameters
    ----------
    result_id
        ID of a single result row

    Returns
    -------
    results
        A single optimisation result, including the EPOCH parameters under 'solutions'
    """
    res = await conn.fetchrow(
        """
            SELECT
                task_id,
                results_id AS result_id,
                solutions,
                objective_values,
                completed_at
            FROM optimisation.results
            WHERE results_id = $1""",
        result_id.result_id,
    )
    print(res)
    return  OptimisationResult(
            task_id=res["task_id"],
            result_id=res["result_id"],
            solution=json.loads(res["solutions"]),
            objective_values=Objective(
                carbon_balance=res["objective_values"]["carbon_balance"],
                cost_balance=res["objective_values"]["cost_balance"],
                capex=res["objective_values"]["capex"],
                payback_horizon=res["objective_values"]["payback_horizon"],
                annualised_cost=res["objective_values"]["annualised_cost"],
            ),
            completed_at=res["completed_at"],
        )


@router.post("/get-optimisation-task-results")
async def get_optimisation_task_results(task_id: TaskID, conn: DatabaseDep) -> list[OptimisationResult]:
    """
    Get all the optimisation results for a single task.

    This looks up for a specific task ID, which you filed in `/add-optimisation-job`.
    If you want to refer to use a single result, try `/get-optimisation-result` with the result UUID
    (which you were given as a result of `add-optimisation-results`, or can look up here).

    Parameters
    ----------
    task_id
        ID of a specific optimisation task that was run

    Returns
    -------
    results
        List of optimisation results, including the EPOCH parameters under 'solutions'
    """
    res = await conn.fetch(
        """
        SELECT
            task_id,
            results_id AS result_id,
            solutions,
            objective_values,
            completed_at
        FROM optimisation.results
        WHERE task_id = $1""",
        task_id.task_id,
    )
    return [
        OptimisationResult(
            task_id=item["task_id"],
            result_id=item["result_id"],
            solution=json.loads(item["solutions"]),
            objective_values=Objective(
                carbon_balance=item["objective_values"]["carbon_balance"],
                cost_balance=item["objective_values"]["cost_balance"],
                capex=item["objective_values"]["capex"],
                payback_horizon=item["objective_values"]["payback_horizon"],
                annualised_cost=item["objective_values"]["annualised_cost"],
            ),
            completed_at=item["completed_at"],
        )
        for item in res
    ]


@router.post("/list-optimisation-results")
async def list_optimisation_results(conn: DatabaseDep, site_id: SiteID | None = None) -> list[OptimisationResultListEntry]:
    """
    Get all the optimisation results for a single task.

    This looks up for a specific task ID, which you filed in `/add-optimisation-job`.
    If you want to refer to use a single result, try `/get-optimisation-result` with the result UUID
    (which you were given as a result of `add-optimisation-results`, or can look up here).

    Parameters
    ----------
    task_id
        ID of a specific optimisation task that was run

    Returns
    -------
    results

    """
    if site_id is None:
        res = await conn.fetch(
            """
            SELECT
                tc.task_id,
                tc.site_id,
                MAX(r.n_evals) AS n_evals,
                MAX(r.exec_time) AS exec_time,
                tc.created_at,
                ARRAY_AGG(r.results_id) AS result_id
            FROM optimisation.task_config AS tc
            LEFT JOIN
                (SELECT task_id, results_id, n_evals, exec_time FROM optimisation.results) as r
            ON r.task_id = tc.task_id
            GROUP BY
                tc.task_id
            ORDER BY tc.created_at ASC
            """
        )
    else:
        res = await conn.fetch(
            """
            SELECT
                tc.task_id,
                tc.site_id,
                MAX(r.n_evals) AS n_evals,
                MAX(exec_time) AS exec_time,
                tc.created_at,
                ARRAY_AGG(r.results_id) AS result_id
            FROM optimisation.task_config AS tc
            LEFT JOIN
                (SELECT task_id, results_id, n_evals, exec_time FROM optimisation.results) as r
            ON r.task_id = tc.task_id
            WHERE tc.site_id = $1
            GROUP BY
                tc.task_id
            ORDER BY tc.created_at ASC
            """,
            site_id.site_id,
        )
    return [
        {
            "task_id": item["task_id"],
            "site_id": item["site_id"],
            "n_evals": item["n_evals"],
            "exec_time": item["exec_time"],
            "result_ids": [subitem for subitem in item["result_id"]],
        }
        for item in res
        if item["result_id"] != [None]
    ]


@router.post("/add-optimisation-results")
async def add_optimisation_results(
    results_in: list[OptimisationResult], conn: DatabaseDep
) -> list[pydantic.UUID4 | pydantic.UUID1]:
    """
    Add a set of optimisation results into the database.

    This must include the ID of the task which you inserted earlier with `add-optimisation-task`.
    You may add multiple OptimisationResults in a single call, which might include the top N results
    for a specific task.
    This will allow you to insert multiple results with the same TaskID, so may result in duplicates (but this is
    specifically handy to insert results in batches if you'd like).

    Parameters
    ----------
    results_in
        An OptimisationResult with objective values (capex, annualised_cost, etc.) bundled together,
        and solutions (EPOCH single run parameter dict e.g. `{ESS_Capacity: 100, ...}`). The solutions
        dictionary will be relatively large, and is stored as a JSONB object in the database.

    Returns
    -------
    results_uuids
        Unique database IDs of each set of results in case you want to refer back to them later.
    """
    results_uuids = [uuid.uuid4() for _ in results_in]
    try:
        await conn.executemany(
            """
            INSERT INTO
                optimisation.results (
                results_id,
                task_id,
                solutions,
                objective_values,
                n_evals,
                exec_time,
                completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            zip(
                results_uuids,
                [item.task_id for item in results_in],
                [json.dumps(item.solution) for item in results_in],
                [item.objective_values.model_dump() for item in results_in],
                [item.n_evals for item in results_in],
                [item.exec_time for item in results_in],
                [item.completed_at for item in results_in],
                strict=True,
            ),
        )
    except asyncpg.exceptions.ForeignKeyViolationError as ex:
        raise HTTPException(
            400,
            f"task_id={results_in[0].task_id} does not have an associated task config."
            + "You should have added it via /add-optimisation-task beforehand.",
        ) from ex
    return results_uuids


@router.post("/add-optimisation-task")
async def add_optimisation_task(task_config: TaskConfig, conn: DatabaseDep) -> TaskConfig:
    """
    Add the details of an optimisation task into the database.

    You should do this when a task enters the queue (or potentially when it starts executing),
    and describe the parameters put in to the task here.

    Parameters
    ----------
    *request*
        Internal FastAPI request object, not needed for external callers
    *task_config*
        Task configuration, featuring a unique ID, search space information (in `parameters`),
        and constraints (ideally split into `constraints_min` and `constraints_max`)

    Returns
    -------
    *task_config*
        A copy of the task config you just sent, after being put into the database.

    Raises
    ------
    *HTTPException*
        If the key already exists in the database.
    """

    try:
        await conn.execute(
            """
            INSERT INTO
                optimisation.task_config (
                    task_id,
                    task_name,
                    objective_directions,
                    constraints_min,
                    constraints_max,
                    parameters,
                    input_data,
                    optimiser_type,
                    optimiser_hyperparameters,
                    created_at,
                    site_id)
                VALUES (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6,
                $7,
                $8,
                $9,
                $10,
                $11)""",
            task_config.task_id,
            task_config.task_name,
            task_config.objective_directions.model_dump(),
            task_config.constraints_min,
            task_config.constraints_max,
            json.dumps(jsonable_encoder(task_config.search_parameters)),  # we have nested pydantic objects in here...
            json.dumps(jsonable_encoder(task_config.site_data)),
            task_config.optimiser.name.value,
            json.dumps(jsonable_encoder(task_config.optimiser.hyperparameters)),
            task_config.created_at,
            task_config.site_id,
        )
    except asyncpg.exceptions.UniqueViolationError as ex:
        raise HTTPException(400, f"TaskID {task_config.task_id} already exists in the database.") from ex
    return task_config
