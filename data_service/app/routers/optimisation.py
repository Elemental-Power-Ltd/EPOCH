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
from ..models.optimisation import (
    OptimisationResultEntry,
    OptimisationTaskListEntry,
    PortfolioOptimisationResult,
    ResultReproConfig,
    SiteOptimisationResult,
    TaskConfig,
)

router = APIRouter()


@router.post("/get-optimisation-results")
async def get_optimisation_results(task_id: TaskID, conn: DatabaseDep) -> list[PortfolioOptimisationResult]:
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
            pr.task_id,
            pr.portfolio_id,
            MAX(pr.metric_carbon_balance_scope_1) AS metric_carbon_balance_scope_1,
            MAX(pr.metric_carbon_balance_scope_2) AS metric_carbon_balance_scope_2,
            MAX(pr.metric_capex) AS metric_capex,
            MAX(pr.metric_cost_balance) AS metric_cost_balance,
            MAX(pr.metric_payback_horizon) AS metric_payback_horizon,
            MAX(pr.metric_annualised_cost) AS metric_annualised_cost,
            ARRAY_AGG(sr.*) AS site_results
        FROM
            optimisation.portfolio_results AS pr
        LEFT JOIN
            optimisation.site_results AS sr
        ON pr.portfolio_id = sr.portfolio_id
        WHERE pr.task_id = $1
        GROUP BY (pr.task_id, pr.portfolio_id)
        """,
        task_id.task_id,
    )
    return [
        PortfolioOptimisationResult(
            task_id=item["task_id"],
            portfolio_id=item["portfolio_id"],
            metric_carbon_balance_scope_1=item["metric_carbon_balance_scope_1"],
            metric_carbon_balance_scope_2=item["metric_carbon_balance_scope_2"],
            metric_cost_balance=item["metric_cost_balance"],
            metric_payback_horizon=item["metric_payback_horizon"],
            metric_annualised_cost=item["metric_annualised_cost"],
            metric_capex=item["metric_capex"],
            site_results=[
                SiteOptimisationResult(
                    site_id=sub_item["site_id"],
                    portfolio_id=sub_item["portfolio_id"],
                    scenario=json.loads(sub_item["scenario"]),
                    metric_carbon_balance_scope_1=sub_item["metric_carbon_balance_scope_1"],
                    metric_carbon_balance_scope_2=sub_item["metric_carbon_balance_scope_2"],
                    metric_cost_balance=sub_item["metric_cost_balance"],
                    metric_payback_horizon=sub_item["metric_payback_horizon"],
                    metric_annualised_cost=sub_item["metric_annualised_cost"],
                    metric_capex=sub_item["metric_capex"],
                    metric_carbon_cost=sub_item["metric_carbon_cost"],
                )
                for sub_item in item["site_results"]
                if sub_item is not None
            ]
            if item["site_results"] != [None]
            else None,
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
            tr.n_evals,
            tr.exec_time,
            tc.created_at
        FROM optimisation.task_config AS tc
        LEFT JOIN
            optimisation.task_results as tr
        ON tr.task_id = tc.task_id
        WHERE client_id = $1
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
            result_ids=None,  # list(set(item["result_id"])),
        )
        for item in res
    ]


@router.post("/add-optimisation-results")
async def add_optimisation_results(conn: DatabaseDep, opt_result: OptimisationResultEntry) -> None:
    """
    Add a set of optimisation results into the database.

    This must include the ID of the task which you inserted earlier with `add-optimisation-task`.
    You may add multiple OptimisationResults in a single call, which might include the top N results
    for a specific task.
    This will allow you to insert multiple results with the same TaskID, so may result in duplicates (but this is
    specifically handy to insert results in batches if you'd like).

    Parameters
    ----------
    portfolio
        An OptimisationResult with objective values (capex, annualised_cost, etc.) bundled together,
        and solutions (EPOCH single run parameter dict e.g. `{ESS_Capacity: 100, ...}`). The solutions
        dictionary will be relatively large, and is stored as a JSONB object in the database.

    Raises
    ------
    HTTPException(400)
        If there's a problem with the task or portfolio results.

    Returns
    -------
    200, OK
        If all was uploaded correctly.
    """
    async with conn.transaction():
        if opt_result.portfolio:
            try:
                await conn.copy_records_to_table(
                    schema_name="optimisation",
                    table_name="portfolio_results",
                    records=zip(
                        [item.task_id for item in opt_result.portfolio],
                        [item.portfolio_id for item in opt_result.portfolio],
                        [item.metric_carbon_balance_scope_1 for item in opt_result.portfolio],
                        [item.metric_carbon_balance_scope_2 for item in opt_result.portfolio],
                        [item.metric_cost_balance for item in opt_result.portfolio],
                        [item.metric_capex for item in opt_result.portfolio],
                        [item.metric_payback_horizon for item in opt_result.portfolio],
                        [item.metric_annualised_cost for item in opt_result.portfolio],
                        [item.metric_carbon_cost for item in opt_result.portfolio],
                        strict=True,
                    ),
                    columns=[
                        "task_id",
                        "portfolio_id",
                        "metric_carbon_balance_scope_1",
                        "metric_carbon_balance_scope_2",
                        "metric_cost_balance",
                        "metric_capex",
                        "metric_payback_horizon",
                        "metric_annualised_cost",
                        "metric_carbon_cost",
                    ],
                )
            except asyncpg.exceptions.ForeignKeyViolationError as ex:
                raise HTTPException(
                    400,
                    f"task_id={opt_result.portfolio[0].task_id} does not have an associated task config."
                    + "You should have added it via /add-optimisation-task beforehand.",
                ) from ex

        if opt_result.sites and opt_result.portfolio:
            # We can only insert sites if there's at least one portfolio filed here
            if not all(item.portfolio_id in {item.portfolio_id for item in opt_result.portfolio} for item in opt_result.sites):
                raise HTTPException(400, "At least one site result has a portfolio ID that you're not currently inserting.")
            try:
                await conn.copy_records_to_table(
                    schema_name="optimisation",
                    table_name="site_results",
                    records=zip(
                        [item.site_id for item in opt_result.sites],
                        [item.portfolio_id for item in opt_result.sites],
                        [json.dumps(jsonable_encoder(item.scenario)) for item in opt_result.sites],
                        [item.metric_carbon_balance_scope_1 for item in opt_result.sites],
                        [item.metric_carbon_balance_scope_2 for item in opt_result.sites],
                        [item.metric_cost_balance for item in opt_result.sites],
                        [item.metric_capex for item in opt_result.sites],
                        [item.metric_payback_horizon for item in opt_result.sites],
                        [item.metric_annualised_cost for item in opt_result.sites],
                        [item.metric_carbon_cost for item in opt_result.portfolio],
                        strict=True,
                    ),
                    columns=[
                        "site_id",
                        "portfolio_id",
                        "scenario",
                        "metric_carbon_balance_scope_1",
                        "metric_carbon_balance_scope_2",
                        "metric_cost_balance",
                        "metric_capex",
                        "metric_payback_horizon",
                        "metric_annualised_cost",
                        "metric_carbon_cost",
                    ],
                )
            except asyncpg.exceptions.ForeignKeyViolationError as ex:
                raise HTTPException(
                    400,
                    f"task_id={opt_result.portfolio[0].task_id} does not have an associated task config."
                    + "You should have added it via /add-optimisation-task beforehand.",
                ) from ex
        if opt_result.tasks is not None:
            await conn.copy_records_to_table(
                table_name="task_results",
                schema_name="optimisation",
                records=zip(
                    [item.task_id for item in opt_result.tasks],
                    [item.n_evals for item in opt_result.tasks],
                    [item.exec_time for item in opt_result.tasks],
                    [item.completed_at for item in opt_result.tasks],
                    strict=True,
                ),
                columns=["task_id", "n_evals", "exec_time", "completed_at"],
            )


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
                    portfolio_range,
                    input_data,
                    optimiser_type,
                    optimiser_hyperparameters,
                    created_at,
                    objectives,
                    portfolio_constraints,
                    site_constraints)
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
            json.dumps(jsonable_encoder(task_config.portfolio_range)),
            json.dumps(jsonable_encoder(task_config.input_data)),
            task_config.optimiser.name,
            json.dumps(jsonable_encoder(task_config.optimiser.hyperparameters)),
            task_config.created_at,
            json.dumps(jsonable_encoder(task_config.objectives)),
            json.dumps(jsonable_encoder(task_config.portfolio_constraints)),
            json.dumps(jsonable_encoder(task_config.site_constraints)),
        )
    except asyncpg.exceptions.UniqueViolationError as ex:
        raise HTTPException(400, f"TaskID {task_config.task_id} already exists in the database.") from ex
    except asyncpg.PostgresSyntaxError as ex:
        raise HTTPException(400, f"TaskID {task_config.task_id} already had a syntax error {ex}") from ex
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
        SELECT
            cr.portfolio_id,
            cr.scenarios,
            cr.site_ids,
            tc.input_data
        FROM (
            SELECT
                pr.portfolio_id,
                pr.task_id,
                ARRAY_AGG(sr.scenario ORDER BY sr.site_id) AS scenarios,
                ARRAY_AGG(sr.site_id ORDER BY sr.site_id) AS site_ids
            FROM
                optimisation.portfolio_results AS pr
            LEFT JOIN
                optimisation.site_results AS sr
            ON pr.portfolio_id = sr.portfolio_id
            WHERE
                pr.portfolio_id = $1
            GROUP BY pr.portfolio_id, pr.task_id
        ) AS cr
        LEFT JOIN
            optimisation.task_config AS tc
        ON tc.task_id = cr.task_id
        """,
        result_id.result_id,
    )

    if task_info is None:
        raise HTTPException(400, f"No task configuration exists for result with id {result_id.result_id}")

    portfolio_id, scenarios, site_ids, portfolio_input_data = task_info
    return ResultReproConfig(
        portfolio_id=portfolio_id,
        task_data={site_id: json.loads(entry) for site_id, entry in zip(site_ids, scenarios, strict=False)},
        site_data=json.loads(portfolio_input_data),
    )
