import uuid

import pydantic
from fastapi import APIRouter, Request

from ..models.optimisation import JobConfig, OptimisationResult

router = APIRouter()


@router.post("/get-optimisation-job-results")
async def get_optimisation_result(request: Request, result_id: pydantic.UUID4) -> OptimisationResult:
    """
    Get a single set of optimisation results.

    This looks up for a single specific result.

    Parameters
    ----------
    job_id
        ID of a specific optimisation job that was run

    Returns
    -------
    results
        A single optimisation result, including the EPOCH parameters under 'solutions'
    """
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetchval(
            """
                SELECT
                    job_id,
                    solutions,
                    objective_values,
                    n_evals,
                    exec_time,
                    completed_at
                FROM optimisation.results
                WHERE result_id = $1""",
            result_id,
        )
    return OptimisationResult(**res)


@router.post("/get-optimisation-job-results")
async def get_optimisation_job_results(request: Request, job_id: pydantic.UUID4) -> list[OptimisationResult]:
    """
    Get all the optimisation results for a single job.

    This looks up for a specific job ID, which you filed in `/add-optimisation-job`.
    If you want to refer to use a single result, try `/get-optimisation-result` with the result UUID
    (which you were given as a result of `add-optimisation-results`, or can look up here).

    Parameters
    ----------
    job_id
        ID of a specific optimisation job that was run

    Returns
    -------
    results
        List of optimisation results, including the EPOCH parameters under 'solutions'
    """
    async with request.state.pgpool.acquire() as conn:
        res = await conn.fetch(
            """
                SELECT
                    job_id,
                    solutions,
                    objective_values,
                    n_evals,
                    exec_time,
                    completed_at
                FROM optimisation.results
                WHERE job_id = $1""",
            job_id,
        )
    return [OptimisationResult(**item) for item in res]


@router.post("/add-optimisation-results")
async def add_optimisation_results(request: Request, results_in: list[OptimisationResult]) -> list[pydantic.UUID4]:
    """
    Add a set of optimisation results into the database.

    This must include the ID of the job which you inserted earlier with `add-optimisation-job`.
    You may add multiple OptimisationResults in a single call, which might include the top N results
    for a specific job.

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
    async with request.state.pgpool.acquire() as conn:
        results_uuids = [uuid.uuid4() for _ in results_in]
        await conn.executemany(
            """
            INSERT INTO
                optimisation.results (
                results_id,
                id,
                solutions,
                objective_values,
                n_evals,
                exec_time,
                completed_at)
            VALUES ($1, $2, $3, $4, $5, $6)""",
            zip(
                [results_uuids],
                [item.job_id for item in results_in],
                [item.solutions for item in results_in],
                [item.objective_values for item in results_in],
                [item.n_evals for item in results_in],
                [item.exec_time for item in results_in],
                [item.completed_at for item in results_in],
                strict=False,
            ),
        )
    return results_uuids


@router.post("/add-optimisation-job")
async def add_optimisation_job(request: Request, job_config: JobConfig) -> JobConfig:
    async with request.state.pgpool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO
                optimisation.jobs (
                    job_id,
                    job_name,
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
                $10)""",
            job_config.job_id,
            job_config.job_name,
            job_config.objective_directions,
            job_config.constraints_min,
            job_config.constraints_max,
            job_config.parameters,
            job_config.input_data,
            job_config.optimiser_type,
            job_config.optimiser_hyperparameters,
            job_config.created_at,
        )
    return job_config
