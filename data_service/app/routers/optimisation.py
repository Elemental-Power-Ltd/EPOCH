"""
Endpoints to store the requests and results of optimisation tasks.

Each optimisation task should start by filing the job config in the database,
and then later on add the results.
Each result is uniquely identified, and belongs to a set of results.
"""

import json

import asyncpg
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from ..dependencies import DatabaseDep
from ..models.core import ClientID, ResultID, TaskID
from ..models.optimisation import Objective, OptimisationResult, OptimisationTaskListEntry, ResultReproConfig, TaskConfig

router = APIRouter()


@router.post("/get-optimisation-results")
async def get_optimisation_results(task_id: TaskID, conn: DatabaseDep) -> list[OptimisationResult]:
    """
    Get all the optimisation results for a single task.

    This looks up for a specific task ID, which you filed in `/add-optimisation-job`.
    The set of task IDs for a given client can also be queried with /list-optimisation-tasks

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
            site_id,
            results_id AS result_id,
            portfolio_id,
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
            portfolio_id=item["portfolio_id"],
            site_id=item["site_id"],
            solution=json.loads(item["solutions"]),
            objective_values=Objective(
                carbon_cost=item["objective_values"]["carbon_cost"],
                cost_balance=item["objective_values"]["cost_balance"],
                capex=item["objective_values"]["capex"],
                payback_horizon=item["objective_values"]["payback_horizon"],
                annualised_cost=item["objective_values"]["annualised_cost"],
                carbon_balance_scope_1=item["objective_values"]["carbon_balance_scope_1"],
                carbon_balance_scope_2=item["objective_values"]["carbon_balance_scope_2"],
            ),
            completed_at=item["completed_at"],
        )
        for item in res
    ]


@router.post("/list-optimisation-tasks")
async def list_optimisation_tasks(conn: DatabaseDep, client_id: ClientID) -> list[OptimisationTaskListEntry]:
    """
    Get all the optimisation tasks for a given client.

    Parameters
    ----------
    client_id

    Returns
    -------
    results

    """
    res = await conn.fetch(
        """
        SELECT
            tc.task_id,
            tc.client_id,
            tc.task_name,
            MAX(r.n_evals) AS n_evals,
            MAX(r.exec_time) AS exec_time,
            tc.created_at,
            ARRAY_AGG(r.results_id) AS result_id
        FROM optimisation.task_config AS tc
        LEFT JOIN
            (SELECT task_id, results_id, n_evals, exec_time FROM optimisation.results) as r
        ON r.task_id = tc.task_id
        WHERE tc.client_id = $1
        GROUP BY
            tc.task_id
        ORDER BY tc.created_at ASC
        """,
        client_id.client_id,
    )

    return [
        OptimisationTaskListEntry(
            task_id=item["task_id"],
            task_name=item["task_name"],
            n_evals=item["n_evals"],
            exec_time=item["exec_time"],
            result_ids=list(set(item["result_id"])),
        )
        for item in res
        if item["result_id"] != [None]
    ]


@router.post("/add-optimisation-results")
async def add_optimisation_results(results_in: list[OptimisationResult], conn: DatabaseDep) -> None:
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
    try:
        await conn.executemany(
            """
            INSERT INTO
                optimisation.results (
                results_id,
                portfolio_id,
                task_id,
                solutions,
                objective_values,
                n_evals,
                exec_time,
                completed_at,
                site_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            zip(
                [item.result_id for item in results_in],
                [item.portfolio_id for item in results_in],
                [item.task_id for item in results_in],
                [json.dumps(item.solution) for item in results_in],
                [item.objective_values.model_dump() for item in results_in],
                [item.n_evals for item in results_in],
                [item.exec_time for item in results_in],
                [item.completed_at for item in results_in],
                [item.site_id for item in results_in],
                strict=True,
            ),
        )
    except asyncpg.exceptions.ForeignKeyViolationError as ex:
        raise HTTPException(
            400,
            f"task_id={results_in[0].task_id} does not have an associated task config."
            + "You should have added it via /add-optimisation-task beforehand.",
        ) from ex


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
                    client_id,
                    task_name,
                    objective_directions,
                    constraints_min,
                    constraints_max,
                    parameters,
                    input_data,
                    optimiser_type,
                    optimiser_hyperparameters,
                    created_at)
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
            task_config.client_id,
            task_config.task_name,
            task_config.objective_directions.model_dump(),
            task_config.constraints_min,
            task_config.constraints_max,
            json.dumps(jsonable_encoder(task_config.site_range)),  # we have nested pydantic objects in here...
            json.dumps(jsonable_encoder(task_config.site_data)),
            task_config.optimiser.name.value,
            json.dumps(jsonable_encoder(task_config.optimiser.hyperparameters)),
            task_config.created_at,
        )
    except asyncpg.exceptions.UniqueViolationError as ex:
        raise HTTPException(400, f"TaskID {task_config.task_id} already exists in the database.") from ex
    return task_config


@router.post("/get-result-configuration")
async def get_result_configuration(result_id: ResultID, conn: DatabaseDep) -> ResultReproConfig:
    """
    Return the configuration that was used to produce a given result.

    Parameters
    ----------
    result_id
        The result_id for a result in the database that you want to reproduce

    Returns
    -------
        All of the configuration data necessary to reproduce this simulation
    """
    task_info = await conn.fetchrow(
        """
        SELECT task_config.task_id, results.solutions, task_config.input_data, results.site_id
        FROM optimisation.task_config as task_config
        INNER JOIN optimisation.results as results
        ON task_config.task_id = results.task_id
        WHERE results.results_id = $1
        """,
        result_id.result_id,
    )

    if task_info is None:
        raise HTTPException(400, f"No task configuration exists for result with id {result_id.result_id}")

    task_id, task_data, portfolio_input_data, site_id = task_info
    input_data = json.loads(portfolio_input_data)[site_id]

    return ResultReproConfig(task_id=task_id, task_data=json.loads(task_data), site_data=input_data)
