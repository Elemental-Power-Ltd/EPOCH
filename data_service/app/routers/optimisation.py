"""
Endpoints to store the requests and results of optimisation tasks.

Each optimisation task should start by filing the job config in the database,
and then later on add the results.
Each result is uniquely identified, and belongs to a set of results.
"""

import functools
import json

import asyncpg
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from ..dependencies import DatabasePoolDep
from ..internal.optimisation import pick_highlighted_results
from ..models.core import ClientID, ResultID, TaskID
from ..models.optimisation import (
    Grade,
    OptimisationResultEntry,
    OptimisationResultsResponse,
    OptimisationTaskListEntry,
    PortfolioOptimisationResult,
    SimulationMetrics,
    SiteOptimisationResult,
    TaskConfig,
    result_repor_config_t,
)

router = APIRouter()


@router.post("/get-optimisation-results")
async def get_optimisation_results(task_id: TaskID, pool: DatabasePoolDep) -> OptimisationResultsResponse:
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
    res = await pool.fetch(
        """
        SELECT
            pr.task_id,
            pr.portfolio_id,
            ANY_VALUE(pr.metric_meter_balance) AS metric_meter_balance,
            ANY_VALUE(pr.metric_operating_balance) AS metric_operating_balance,
            ANY_VALUE(pr.metric_cost_balance) AS metric_cost_balance,
            ANY_VALUE(pr.metric_npv_balance) as metric_npv_balance,
            ANY_VALUE(pr.metric_payback_horizon) AS metric_payback_horizon,
            ANY_VALUE(pr.metric_carbon_balance_scope_1) AS metric_carbon_balance_scope_1,
            ANY_VALUE(pr.metric_carbon_balance_scope_2) AS metric_carbon_balance_scope_2,
            ANY_VALUE(pr.metric_combined_carbon_balance) AS metric_combined_carbon_balance,
            ANY_VALUE(pr.metric_carbon_cost) AS metric_carbon_cost,

            ANY_VALUE(pr.metric_total_gas_used) AS metric_total_gas_used,
            ANY_VALUE(pr.metric_total_electricity_imported) AS metric_total_electricity_imported,
            ANY_VALUE(pr.metric_total_electricity_generated) AS metric_total_electricity_generated,
            ANY_VALUE(pr.metric_total_electricity_exported) AS metric_total_electricity_exported,
            ANY_VALUE(pr.metric_total_electricity_curtailed) AS metric_total_electricity_curtailed,
            ANY_VALUE(pr.metric_total_electricity_used) AS metric_total_electricity_used,
            ANY_VALUE(pr.metric_total_electrical_shortfall) AS metric_total_electrical_shortfall,
            ANY_VALUE(pr.metric_total_heat_shortfall) AS metric_total_heat_shortfall,
            ANY_VALUE(pr.metric_total_ch_shortfall) AS metric_total_ch_shortfall,
            ANY_VALUE(pr.metric_total_dhw_shortfall) AS metric_total_dhw_shortfall,
            ANY_VALUE(pr.metric_capex) AS metric_capex,
            ANY_VALUE(pr.metric_total_gas_import_cost) AS metric_total_gas_import_cost,
            ANY_VALUE(pr.metric_total_electricity_import_cost) AS metric_total_electricity_import_cost,
            ANY_VALUE(pr.metric_total_electricity_export_gain) AS metric_total_electricity_export_gain,
            ANY_VALUE(pr.metric_total_meter_cost) AS metric_total_meter_cost,
            ANY_VALUE(pr.metric_total_operating_cost) AS metric_total_operating_cost,
            ANY_VALUE(pr.metric_annualised_cost) AS metric_annualised_cost,
            ANY_VALUE(pr.metric_total_net_present_value) AS metric_total_net_present_value,
            ANY_VALUE(pr.metric_total_scope_1_emissions) AS metric_total_scope_1_emissions,
            ANY_VALUE(pr.metric_total_scope_2_emissions) AS metric_total_scope_2_emissions,
            ANY_VALUE(pr.metric_total_combined_carbon_emissions) AS metric_total_combined_carbon_emissions,

            ANY_VALUE(pr.metric_baseline_gas_used) AS metric_baseline_gas_used,
            ANY_VALUE(pr.metric_baseline_electricity_imported) AS metric_baseline_electricity_imported,
            ANY_VALUE(pr.metric_baseline_electricity_generated) AS metric_baseline_electricity_generated,
            ANY_VALUE(pr.metric_baseline_electricity_exported) AS metric_baseline_electricity_exported,
            ANY_VALUE(pr.metric_baseline_electricity_curtailed) as metric_baseline_electricity_curtailed,
            ANY_VALUE(pr.metric_baseline_electricity_used) as metric_baseline_electricity_used,
            ANY_VALUE(pr.metric_baseline_electrical_shortfall) AS metric_baseline_electrical_shortfall,
            ANY_VALUE(pr.metric_baseline_heat_shortfall) AS metric_baseline_heat_shortfall,
            ANY_VALUE(pr.metric_baseline_ch_shortfall) as metric_baseline_ch_shortfall,
            ANY_VALUE(pr.metric_baseline_dhw_shortfall) as metric_baseline_dhw_shortfall,
            ANY_VALUE(pr.metric_baseline_gas_import_cost) AS metric_baseline_gas_import_cost,
            ANY_VALUE(pr.metric_baseline_electricity_import_cost) AS metric_baseline_electricity_import_cost,
            ANY_VALUE(pr.metric_baseline_electricity_export_gain) AS metric_baseline_electricity_export_gain,
            ANY_VALUE(pr.metric_baseline_meter_cost) AS metric_baseline_meter_cost,
            ANY_VALUE(pr.metric_baseline_operating_cost) AS metric_baseline_operating_cost,
            ANY_VALUE(pr.metric_baseline_net_present_value) AS metric_baseline_net_present_value,
            ANY_VALUE(pr.metric_baseline_scope_1_emissions) AS metric_baseline_scope_1_emissions,
            ANY_VALUE(pr.metric_baseline_scope_2_emissions) AS metric_baseline_scope_2_emissions,
            ANY_VALUE(pr.metric_baseline_combined_carbon_emissions) as metric_baseline_combined_carbon_emissions,

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

    # Bind a local NaN to num with the defaults set reasonably, just in case
    # any have slipped through.
    nan_to_num = functools.partial(
        np.nan_to_num,
        nan=np.finfo(np.float32).max,  # be careful of this one!
        posinf=np.finfo(np.float32).max,
        neginf=np.finfo(np.float32).min,
    )
    portfolio_results = [
        PortfolioOptimisationResult(
            task_id=item["task_id"],
            portfolio_id=item["portfolio_id"],
            metrics=SimulationMetrics(
                meter_balance=nan_to_num(item["metric_meter_balance"]),
                operating_balance=nan_to_num(item["metric_operating_balance"]),
                cost_balance=nan_to_num(item["metric_cost_balance"]),
                npv_balance=nan_to_num(item["metric_npv_balance"]),
                payback_horizon=nan_to_num(item["metric_payback_horizon"]),
                carbon_balance_scope_1=nan_to_num(item["metric_carbon_balance_scope_1"]),
                carbon_balance_scope_2=nan_to_num(item["metric_carbon_balance_scope_2"]),
                carbon_balance_total=nan_to_num(item["metric_combined_carbon_balance"]),
                carbon_cost=nan_to_num(item["metric_carbon_cost"]),
                # total metrics
                total_gas_used=nan_to_num(item["metric_total_gas_used"]),
                total_electricity_imported=nan_to_num(item["metric_total_electricity_imported"]),
                total_electricity_generated=nan_to_num(item["metric_total_electricity_generated"]),
                total_electricity_exported=nan_to_num(item["metric_total_electricity_exported"]),
                total_electricity_curtailed=nan_to_num(item["metric_total_electricity_curtailed"]),
                total_electricity_used=nan_to_num(item["metric_total_electricity_used"]),
                total_electrical_shortfall=nan_to_num(item["metric_total_electrical_shortfall"]),
                total_heat_shortfall=nan_to_num(item["metric_total_heat_shortfall"]),
                total_ch_shortfall=nan_to_num(item["metric_total_ch_shortfall"]),
                total_dhw_shortfall=nan_to_num(item["metric_total_dhw_shortfall"]),
                capex=nan_to_num(item["metric_capex"]),
                total_gas_import_cost=nan_to_num(item["metric_total_gas_import_cost"]),
                total_electricity_import_cost=nan_to_num(item["metric_total_electricity_import_cost"]),
                total_electricity_export_gain=nan_to_num(item["metric_total_electricity_export_gain"]),
                total_meter_cost=nan_to_num(item["metric_total_meter_cost"]),
                total_operating_cost=nan_to_num(item["metric_total_operating_cost"]),
                annualised_cost=nan_to_num(item["metric_annualised_cost"]),
                total_net_present_value=nan_to_num(item["metric_total_net_present_value"]),
                total_scope_1_emissions=nan_to_num(item["metric_total_scope_1_emissions"]),
                total_scope_2_emissions=nan_to_num(item["metric_total_scope_2_emissions"]),
                total_combined_carbon_emissions=nan_to_num(item["metric_total_combined_carbon_emissions"]),
                # quirk of Portfolio vs Site results,
                # these columns don't exist in the portfolio table
                scenario_environmental_impact_score=None,
                scenario_environmental_impact_grade=None,
                # baseline metrics
                baseline_gas_used=nan_to_num(item["metric_baseline_gas_used"]),
                baseline_electricity_imported=nan_to_num(item["metric_baseline_electricity_imported"]),
                baseline_electricity_generated=nan_to_num(item["metric_baseline_electricity_generated"]),
                baseline_electricity_exported=nan_to_num(item["metric_baseline_electricity_exported"]),
                baseline_electricity_curtailed=nan_to_num(item["metric_baseline_electricity_curtailed"]),
                baseline_electricity_used=nan_to_num(item["metric_baseline_electricity_used"]),
                baseline_electrical_shortfall=nan_to_num(item["metric_baseline_electrical_shortfall"]),
                baseline_heat_shortfall=nan_to_num(item["metric_baseline_heat_shortfall"]),
                baseline_ch_shortfall=nan_to_num(item["metric_baseline_ch_shortfall"]),
                baseline_dhw_shortfall=nan_to_num(item["metric_baseline_dhw_shortfall"]),
                baseline_gas_import_cost=nan_to_num(item["metric_baseline_gas_import_cost"]),
                baseline_electricity_import_cost=nan_to_num(item["metric_baseline_electricity_import_cost"]),
                baseline_electricity_export_gain=nan_to_num(item["metric_baseline_electricity_export_gain"]),
                baseline_meter_cost=nan_to_num(item["metric_baseline_meter_cost"]),
                baseline_operating_cost=nan_to_num(item["metric_baseline_operating_cost"]),
                baseline_net_present_value=nan_to_num(item["metric_baseline_net_present_value"]),
                baseline_scope_1_emissions=nan_to_num(item["metric_baseline_scope_1_emissions"]),
                baseline_scope_2_emissions=nan_to_num(item["metric_baseline_scope_2_emissions"]),
                baseline_combined_carbon_emissions=nan_to_num(item["metric_baseline_combined_carbon_emissions"]),
                # quirk of Portfolio vs Site results,
                # these columns don't exist in the portfolio table
                baseline_environmental_impact_score=None,
                baseline_environmental_impact_grade=None,
            ),
            site_results=[
                SiteOptimisationResult(
                    site_id=sub_item["site_id"],
                    portfolio_id=sub_item["portfolio_id"],
                    scenario=json.loads(sub_item["scenario"]),
                    metrics=SimulationMetrics(
                        meter_balance=nan_to_num(sub_item["metric_meter_balance"]),
                        operating_balance=nan_to_num(sub_item["metric_operating_balance"]),
                        cost_balance=nan_to_num(sub_item["metric_cost_balance"]),
                        npv_balance=nan_to_num(sub_item["metric_npv_balance"]),
                        payback_horizon=nan_to_num(sub_item["metric_payback_horizon"]),
                        carbon_balance_scope_1=nan_to_num(sub_item["metric_carbon_balance_scope_1"]),
                        carbon_balance_scope_2=nan_to_num(sub_item["metric_carbon_balance_scope_2"]),
                        carbon_balance_total=nan_to_num(sub_item["metric_combined_carbon_balance"]),
                        carbon_cost=nan_to_num(sub_item["metric_carbon_cost"]),
                        # total metrics
                        total_gas_used=nan_to_num(sub_item["metric_total_gas_used"]),
                        total_electricity_imported=nan_to_num(sub_item["metric_total_electricity_imported"]),
                        total_electricity_generated=nan_to_num(sub_item["metric_total_electricity_generated"]),
                        total_electricity_exported=nan_to_num(sub_item["metric_total_electricity_exported"]),
                        total_electricity_curtailed=nan_to_num(sub_item["metric_total_electricity_curtailed"]),
                        total_electricity_used=nan_to_num(sub_item["metric_total_electricity_used"]),
                        total_electrical_shortfall=nan_to_num(sub_item["metric_total_electrical_shortfall"]),
                        total_heat_shortfall=nan_to_num(sub_item["metric_total_heat_shortfall"]),
                        total_ch_shortfall=nan_to_num(sub_item["metric_total_ch_shortfall"]),
                        total_dhw_shortfall=nan_to_num(sub_item["metric_total_dhw_shortfall"]),
                        capex=nan_to_num(sub_item["metric_capex"]),
                        total_gas_import_cost=nan_to_num(sub_item["metric_total_gas_import_cost"]),
                        total_electricity_import_cost=nan_to_num(sub_item["metric_total_electricity_import_cost"]),
                        total_electricity_export_gain=nan_to_num(sub_item["metric_total_electricity_export_gain"]),
                        total_meter_cost=nan_to_num(sub_item["metric_total_meter_cost"]),
                        total_operating_cost=nan_to_num(sub_item["metric_total_operating_cost"]),
                        annualised_cost=nan_to_num(sub_item["metric_annualised_cost"]),
                        total_net_present_value=nan_to_num(sub_item["metric_total_net_present_value"]),
                        total_scope_1_emissions=nan_to_num(sub_item["metric_total_scope_1_emissions"]),
                        total_scope_2_emissions=nan_to_num(sub_item["metric_total_scope_2_emissions"]),
                        total_combined_carbon_emissions=nan_to_num(sub_item["metric_total_combined_carbon_emissions"]),
                        scenario_environmental_impact_score=nan_to_num(sub_item["metric_scenario_environmental_impact_score"]),
                        scenario_environmental_impact_grade=Grade[sub_item["metric_scenario_environmental_impact_grade"]]
                        if sub_item["metric_scenario_environmental_impact_grade"]
                        else None,
                        # baseline metrics
                        baseline_gas_used=nan_to_num(sub_item["metric_baseline_gas_used"]),
                        baseline_electricity_imported=nan_to_num(sub_item["metric_baseline_electricity_imported"]),
                        baseline_electricity_generated=nan_to_num(sub_item["metric_baseline_electricity_generated"]),
                        baseline_electricity_exported=nan_to_num(sub_item["metric_baseline_electricity_exported"]),
                        baseline_electricity_curtailed=nan_to_num(sub_item["metric_baseline_electricity_curtailed"]),
                        baseline_electricity_used=nan_to_num(sub_item["metric_baseline_electricity_used"]),
                        baseline_electrical_shortfall=nan_to_num(sub_item["metric_baseline_electrical_shortfall"]),
                        baseline_heat_shortfall=nan_to_num(sub_item["metric_baseline_heat_shortfall"]),
                        baseline_ch_shortfall=nan_to_num(sub_item["metric_baseline_ch_shortfall"]),
                        baseline_dhw_shortfall=nan_to_num(sub_item["metric_baseline_dhw_shortfall"]),
                        baseline_gas_import_cost=nan_to_num(sub_item["metric_baseline_gas_import_cost"]),
                        baseline_electricity_import_cost=nan_to_num(sub_item["metric_baseline_electricity_import_cost"]),
                        baseline_electricity_export_gain=nan_to_num(sub_item["metric_baseline_electricity_export_gain"]),
                        baseline_meter_cost=nan_to_num(sub_item["metric_baseline_meter_cost"]),
                        baseline_operating_cost=nan_to_num(sub_item["metric_baseline_operating_cost"]),
                        baseline_net_present_value=nan_to_num(sub_item["metric_baseline_net_present_value"]),
                        baseline_scope_1_emissions=nan_to_num(sub_item["metric_baseline_scope_1_emissions"]),
                        baseline_scope_2_emissions=nan_to_num(sub_item["metric_baseline_scope_2_emissions"]),
                        baseline_combined_carbon_emissions=nan_to_num(sub_item["metric_baseline_combined_carbon_emissions"]),
                        baseline_environmental_impact_score=nan_to_num(sub_item["metric_baseline_environmental_impact_score"]),
                        baseline_environmental_impact_grade=Grade[sub_item["metric_baseline_environmental_impact_grade"]]
                        if sub_item["metric_baseline_environmental_impact_grade"]
                        else None,
                    ),
                )
                for sub_item in item["site_results"]
                if sub_item is not None
            ]
            if item["site_results"] != [None]
            else None,
        )
        for item in res
    ]

    highlighted_results = pick_highlighted_results(portfolio_results)

    return OptimisationResultsResponse(portfolio_results=portfolio_results, highlighted_results=highlighted_results)


@router.post("/list-optimisation-tasks")
async def list_optimisation_tasks(pool: DatabasePoolDep, client_id: ClientID) -> list[OptimisationTaskListEntry]:
    """
    Get all the optimisation tasks for a given client.

    Parameters
    ----------
    client_id

    Returns
    -------
    results

    """
    res = await pool.fetch(
        """
        SELECT
            tc.task_id,
            tc.client_id,
            tc.task_name,
            ANY_VALUE(tr.n_evals)   AS n_evals,
            COUNT(pr.task_id)       AS n_saved,
            ANY_VALUE(tr.exec_time) AS exec_time,
            ANY_VALUE(tc.created_at) AS created_at
        FROM optimisation.task_config AS tc
        LEFT JOIN optimisation.task_results AS tr
            ON tr.task_id = tc.task_id
        LEFT JOIN optimisation.portfolio_results AS pr
            ON tc.task_id = pr.task_id
        WHERE tc.client_id = $1
        GROUP BY
            tc.task_id,
            tc.client_id,
            tc.task_name
        ORDER BY
            created_at ASC;
        """,
        client_id.client_id,
    )

    return [
        OptimisationTaskListEntry(
            task_id=item["task_id"],
            task_name=item["task_name"],
            n_evals=item["n_evals"],
            n_saved=item["n_saved"],
            exec_time=item["exec_time"],
        )
        for item in res
    ]


@router.post("/add-optimisation-results")
async def add_optimisation_results(pool: DatabasePoolDep, opt_result: OptimisationResultEntry) -> None:
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
    async with pool.acquire() as conn:
        async with conn.transaction():
            if opt_result.portfolio:
                # Note that we don't add the specific site results here;
                # those are stored in a separate table.
                try:
                    await conn.copy_records_to_table(
                        schema_name="optimisation",
                        table_name="portfolio_results",
                        records=zip(
                            [item.task_id for item in opt_result.portfolio],
                            [item.portfolio_id for item in opt_result.portfolio],
                            [item.metrics.meter_balance for item in opt_result.portfolio],
                            [item.metrics.operating_balance for item in opt_result.portfolio],
                            [item.metrics.cost_balance for item in opt_result.portfolio],
                            [item.metrics.npv_balance for item in opt_result.portfolio],
                            [item.metrics.payback_horizon for item in opt_result.portfolio],
                            [item.metrics.carbon_balance_scope_1 for item in opt_result.portfolio],
                            [item.metrics.carbon_balance_scope_2 for item in opt_result.portfolio],
                            [item.metrics.carbon_balance_total for item in opt_result.portfolio],
                            [item.metrics.carbon_cost for item in opt_result.portfolio],
                            [item.metrics.total_gas_used for item in opt_result.portfolio],
                            [item.metrics.total_electricity_imported for item in opt_result.portfolio],
                            [item.metrics.total_electricity_generated for item in opt_result.portfolio],
                            [item.metrics.total_electricity_exported for item in opt_result.portfolio],
                            [item.metrics.total_electricity_curtailed for item in opt_result.portfolio],
                            [item.metrics.total_electricity_used for item in opt_result.portfolio],
                            [item.metrics.total_electrical_shortfall for item in opt_result.portfolio],
                            [item.metrics.total_heat_shortfall for item in opt_result.portfolio],
                            [item.metrics.total_ch_shortfall for item in opt_result.portfolio],
                            [item.metrics.total_dhw_shortfall for item in opt_result.portfolio],
                            [item.metrics.capex for item in opt_result.portfolio],
                            [item.metrics.total_gas_import_cost for item in opt_result.portfolio],
                            [item.metrics.total_electricity_import_cost for item in opt_result.portfolio],
                            [item.metrics.total_electricity_export_gain for item in opt_result.portfolio],
                            [item.metrics.total_meter_cost for item in opt_result.portfolio],
                            [item.metrics.annualised_cost for item in opt_result.portfolio],
                            [item.metrics.total_net_present_value for item in opt_result.portfolio],
                            [item.metrics.total_operating_cost for item in opt_result.portfolio],
                            [item.metrics.total_scope_1_emissions for item in opt_result.portfolio],
                            [item.metrics.total_scope_2_emissions for item in opt_result.portfolio],
                            [item.metrics.total_combined_carbon_emissions for item in opt_result.portfolio],
                            [item.metrics.baseline_gas_used for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_imported for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_generated for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_exported for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_curtailed for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_used for item in opt_result.portfolio],
                            [item.metrics.baseline_electrical_shortfall for item in opt_result.portfolio],
                            [item.metrics.baseline_heat_shortfall for item in opt_result.portfolio],
                            [item.metrics.baseline_ch_shortfall for item in opt_result.portfolio],
                            [item.metrics.baseline_dhw_shortfall for item in opt_result.portfolio],
                            [item.metrics.baseline_gas_import_cost for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_import_cost for item in opt_result.portfolio],
                            [item.metrics.baseline_electricity_export_gain for item in opt_result.portfolio],
                            [item.metrics.baseline_meter_cost for item in opt_result.portfolio],
                            [item.metrics.baseline_operating_cost for item in opt_result.portfolio],
                            [item.metrics.baseline_net_present_value for item in opt_result.portfolio],
                            [item.metrics.baseline_scope_1_emissions for item in opt_result.portfolio],
                            [item.metrics.baseline_scope_2_emissions for item in opt_result.portfolio],
                            [item.metrics.baseline_combined_carbon_emissions for item in opt_result.portfolio],
                            strict=True,
                        ),
                        columns=[
                            "task_id",
                            "portfolio_id",
                            "metric_meter_balance",
                            "metric_operating_balance",
                            "metric_cost_balance",
                            "metric_npv_balance",
                            "metric_payback_horizon",
                            "metric_carbon_balance_scope_1",
                            "metric_carbon_balance_scope_2",
                            "metric_combined_carbon_balance",
                            "metric_carbon_cost",
                            "metric_total_gas_used",
                            "metric_total_electricity_imported",
                            "metric_total_electricity_generated",
                            "metric_total_electricity_exported",
                            "metric_total_electricity_curtailed",
                            "metric_total_electricity_used",
                            "metric_total_electrical_shortfall",
                            "metric_total_heat_shortfall",
                            "metric_total_ch_shortfall",
                            "metric_total_dhw_shortfall",
                            "metric_capex",
                            "metric_total_gas_import_cost",
                            "metric_total_electricity_import_cost",
                            "metric_total_electricity_export_gain",
                            "metric_total_meter_cost",
                            "metric_total_operating_cost",
                            "metric_annualised_cost",
                            "metric_total_net_present_value",
                            "metric_total_scope_1_emissions",
                            "metric_total_scope_2_emissions",
                            "metric_total_combined_carbon_emissions",
                            "metric_baseline_gas_used",
                            "metric_baseline_electricity_imported",
                            "metric_baseline_electricity_generated",
                            "metric_baseline_electricity_exported",
                            "metric_baseline_electricity_curtailed",
                            "metric_baseline_electricity_used",
                            "metric_baseline_electrical_shortfall",
                            "metric_baseline_heat_shortfall",
                            "metric_baseline_ch_shortfall",
                            "metric_baseline_dhw_shortfall",
                            "metric_baseline_gas_import_cost",
                            "metric_baseline_electricity_import_cost",
                            "metric_baseline_electricity_export_gain",
                            "metric_baseline_meter_cost",
                            "metric_baseline_operating_cost",
                            "metric_baseline_net_present_value",
                            "metric_baseline_scope_1_emissions",
                            "metric_baseline_scope_2_emissions",
                            "metric_baseline_combined_carbon_emissions",
                        ],
                    )
                except asyncpg.exceptions.ForeignKeyViolationError as ex:
                    raise HTTPException(
                        400,
                        f"task_id={opt_result.portfolio[0].task_id} does not have an associated task config."
                        + "You should have added it via /add-optimisation-task beforehand.",
                    ) from ex

                for pf in opt_result.portfolio:
                    if not pf.site_results:
                        # No site results here, so skip it.
                        continue
                    await conn.copy_records_to_table(
                        schema_name="optimisation",
                        table_name="site_results",
                        records=zip(
                            [item.site_id for item in pf.site_results],
                            [item.portfolio_id for item in pf.site_results],
                            [json.dumps(jsonable_encoder(item.scenario)) for item in pf.site_results],
                            [item.metrics.meter_balance for item in pf.site_results],
                            [item.metrics.operating_balance for item in pf.site_results],
                            [item.metrics.cost_balance for item in pf.site_results],
                            [item.metrics.npv_balance for item in pf.site_results],
                            [item.metrics.payback_horizon for item in pf.site_results],
                            [item.metrics.carbon_balance_scope_1 for item in pf.site_results],
                            [item.metrics.carbon_balance_scope_2 for item in pf.site_results],
                            [item.metrics.carbon_balance_total for item in pf.site_results],
                            [item.metrics.carbon_cost for item in pf.site_results],
                            [item.metrics.total_gas_used for item in pf.site_results],
                            [item.metrics.total_electricity_imported for item in pf.site_results],
                            [item.metrics.total_electricity_generated for item in pf.site_results],
                            [item.metrics.total_electricity_exported for item in pf.site_results],
                            [item.metrics.total_electricity_curtailed for item in pf.site_results],
                            [item.metrics.total_electricity_used for item in pf.site_results],
                            [item.metrics.total_electrical_shortfall for item in pf.site_results],
                            [item.metrics.total_heat_shortfall for item in pf.site_results],
                            [item.metrics.total_ch_shortfall for item in pf.site_results],
                            [item.metrics.total_dhw_shortfall for item in pf.site_results],
                            [item.metrics.capex for item in pf.site_results],
                            [item.metrics.total_gas_import_cost for item in pf.site_results],
                            [item.metrics.total_electricity_import_cost for item in pf.site_results],
                            [item.metrics.total_electricity_export_gain for item in pf.site_results],
                            [item.metrics.total_meter_cost for item in pf.site_results],
                            [item.metrics.annualised_cost for item in pf.site_results],
                            [item.metrics.total_net_present_value for item in pf.site_results],
                            [item.metrics.total_operating_cost for item in pf.site_results],
                            [item.metrics.total_scope_1_emissions for item in pf.site_results],
                            [item.metrics.total_scope_2_emissions for item in pf.site_results],
                            [item.metrics.total_combined_carbon_emissions for item in pf.site_results],
                            [item.metrics.scenario_environmental_impact_score for item in pf.site_results],
                            [item.metrics.scenario_environmental_impact_grade for item in pf.site_results],
                            [item.metrics.baseline_gas_used for item in pf.site_results],
                            [item.metrics.baseline_electricity_imported for item in pf.site_results],
                            [item.metrics.baseline_electricity_generated for item in pf.site_results],
                            [item.metrics.baseline_electricity_exported for item in pf.site_results],
                            [item.metrics.baseline_electricity_curtailed for item in pf.site_results],
                            [item.metrics.baseline_electricity_used for item in pf.site_results],
                            [item.metrics.baseline_electrical_shortfall for item in pf.site_results],
                            [item.metrics.baseline_heat_shortfall for item in pf.site_results],
                            [item.metrics.baseline_ch_shortfall for item in pf.site_results],
                            [item.metrics.baseline_dhw_shortfall for item in pf.site_results],
                            [item.metrics.baseline_gas_import_cost for item in pf.site_results],
                            [item.metrics.baseline_electricity_import_cost for item in pf.site_results],
                            [item.metrics.baseline_electricity_export_gain for item in pf.site_results],
                            [item.metrics.baseline_meter_cost for item in pf.site_results],
                            [item.metrics.baseline_operating_cost for item in pf.site_results],
                            [item.metrics.baseline_net_present_value for item in pf.site_results],
                            [item.metrics.baseline_scope_1_emissions for item in pf.site_results],
                            [item.metrics.baseline_scope_2_emissions for item in pf.site_results],
                            [item.metrics.baseline_combined_carbon_emissions for item in pf.site_results],
                            [item.metrics.baseline_environmental_impact_score for item in pf.site_results],
                            [item.metrics.baseline_environmental_impact_grade for item in pf.site_results],
                            strict=True,
                        ),
                        columns=[
                            "site_id",
                            "portfolio_id",
                            "scenario",
                            "metric_meter_balance",
                            "metric_operating_balance",
                            "metric_cost_balance",
                            "metric_npv_balance",
                            "metric_payback_horizon",
                            "metric_carbon_balance_scope_1",
                            "metric_carbon_balance_scope_2",
                            "metric_combined_carbon_balance",
                            "metric_carbon_cost",
                            "metric_total_gas_used",
                            "metric_total_electricity_imported",
                            "metric_total_electricity_generated",
                            "metric_total_electricity_exported",
                            "metric_total_electricity_curtailed",
                            "metric_total_electricity_used",
                            "metric_total_electrical_shortfall",
                            "metric_total_heat_shortfall",
                            "metric_total_ch_shortfall",
                            "metric_total_dhw_shortfall",
                            "metric_capex",
                            "metric_total_gas_import_cost",
                            "metric_total_electricity_import_cost",
                            "metric_total_electricity_export_gain",
                            "metric_total_meter_cost",
                            "metric_total_operating_cost",
                            "metric_annualised_cost",
                            "metric_total_net_present_value",
                            "metric_total_scope_1_emissions",
                            "metric_total_scope_2_emissions",
                            "metric_total_combined_carbon_emissions",
                            "metric_scenario_environmental_impact_score",
                            "metric_scenario_environmental_impact_grade",
                            "metric_baseline_gas_used",
                            "metric_baseline_electricity_imported",
                            "metric_baseline_electricity_generated",
                            "metric_baseline_electricity_exported",
                            "metric_baseline_electricity_curtailed",
                            "metric_baseline_electricity_used",
                            "metric_baseline_electrical_shortfall",
                            "metric_baseline_heat_shortfall",
                            "metric_baseline_ch_shortfall",
                            "metric_baseline_dhw_shortfall",
                            "metric_baseline_gas_import_cost",
                            "metric_baseline_electricity_import_cost",
                            "metric_baseline_electricity_export_gain",
                            "metric_baseline_meter_cost",
                            "metric_baseline_operating_cost",
                            "metric_baseline_net_present_value",
                            "metric_baseline_scope_1_emissions",
                            "metric_baseline_scope_2_emissions",
                            "metric_baseline_combined_carbon_emissions",
                            "metric_baseline_environmental_impact_score",
                            "metric_baseline_environmental_impact_grade",
                        ],
                    )

            if opt_result.tasks:
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
async def add_optimisation_task(task_config: TaskConfig, pool: DatabasePoolDep) -> TaskConfig:
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
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                await conn.execute(
                    """
                    INSERT INTO
                        optimisation.task_config (
                            task_id,
                            client_id,
                            task_name,
                            optimiser_type,
                            optimiser_hyperparameters,
                            created_at,
                            objectives,
                            portfolio_constraints,
                            epoch_version)
                        VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        $7,
                        $8,
                        $9)""",
                    task_config.task_id,
                    task_config.client_id,
                    task_config.task_name,
                    task_config.optimiser.name,
                    json.dumps(jsonable_encoder(task_config.optimiser.hyperparameters)),
                    task_config.created_at,
                    json.dumps(jsonable_encoder(task_config.objectives)),
                    json.dumps(jsonable_encoder(task_config.portfolio_constraints)),
                    task_config.epoch_version,
                )

            except asyncpg.exceptions.UniqueViolationError as ex:
                raise HTTPException(400, f"TaskID {task_config.task_id} already exists in the database.") from ex
            except asyncpg.PostgresSyntaxError as ex:
                raise HTTPException(400, f"TaskID {task_config.task_id} had a syntax error {ex}") from ex

            try:
                await conn.copy_records_to_table(
                    schema_name="optimisation",
                    table_name="site_task_config",
                    records=[
                        (
                            task_config.task_id,
                            site_id,
                            bundle_id,
                            task_config.site_constraints[site_id],
                            task_config.portfolio_range[site_id],
                        )
                        for site_id, bundle_id in task_config.bundle_ids.items()
                    ],
                    columns=["task_id", "site_id", "bundle_id", "site_constraints", "site_range"],
                )
            except asyncpg.PostgresSyntaxError as ex:
                raise HTTPException(400, f"TaskID {task_config.task_id} had a syntax error {ex}") from ex

    return task_config


@router.post("/get-result-configuration")
async def get_result_configuration(result_id: ResultID, pool: DatabasePoolDep) -> result_repor_config_t:
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
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                stc.site_data,
                stc.site_id,
                stc.bundle_id,
                sr.scenario
            FROM
                optimisation.site_results sr
            JOIN
                optimisation.portfolio_results pr ON sr.portfolio_id = pr.portfolio_id
            JOIN
                optimisation.site_task_config stc ON pr.task_id = stc.task_id
            WHERE
                sr.portfolio_id = $1
            """,
            result_id.result_id,
        )

    if rows is None:
        raise HTTPException(400, f"No task configuration exists for result with id {result_id.result_id}")

    site_datas = {}
    bundle_ids = {}
    scenarios = {}

    for row in rows:
        site_id = row["site_id"]
        site_datas[site_id] = row["site_data"]
        bundle_ids[site_id] = row["bundle_id"]
        scenarios[site_id] = row["scenario"]

    if any(value is None for value in bundle_ids.values()):
        return LegacyResultReproConfig(portfolio_id=result_id.result_id, task_data=scenarios, site_data=site_datas)

    return NewResultReproConfig(portfolio_id=result_id.result_id, task_data=scenarios, bundle_ids=bundle_ids)
