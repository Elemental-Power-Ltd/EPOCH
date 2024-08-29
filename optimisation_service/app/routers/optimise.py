import datetime
import logging
import os
import typing
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import UUID4

from ..internal.models.algorithms import Optimiser
from ..internal.models.problem import ParameterDict
from ..internal.problem import _OBJECTIVES, Problem
from ..internal.result import Result
from .models.core import EndpointResult, EndpointTask, TaskWithUUID, TaskResponse, ObjectiveValues, OptimisationSolution
from .models.tasks import Task
from .queue import IQueue
from .utils.datamanager import DataManager

router = APIRouter()
logger = logging.getLogger("default")
database_url = os.environ.get("DB_API_URL", "http://localhost:8000")


def convert_task(task: TaskWithUUID, data_manager: DataManager) -> Task:
    """
    Convert json optimisation tasks into corresponding python objects.

    Parameters
    ----------
    task
        Optimisation task to convert

    Returns
    -------
    problem
        Problem.
    optimiser
        Initialised optimiser.
    """
    logger.info(f"Converting {task.task_id}.")
    optimiser_func = Optimiser[task.optimiser.name].value
    optimiser = optimiser_func(**task.optimiser.hyperparameters.model_dump(mode="python"))
    search_parameters: ParameterDict = task.search_parameters.model_dump(mode="python")
    problem = Problem(
        objectives=task.objectives,
        constraints={},
        parameters=search_parameters,
        input_dir=data_manager.temp_data_dir,
    )
    return Task(task_id=task.task_id, problem=problem, optimiser=optimiser, data_manager=data_manager)


def postprocess_results(task: Task, results: Result, completed_at: datetime.datetime) -> list[EndpointResult]:
    logger.info(f"Postprocessing results of {task.task_id}.")
    Optimisation_Results = []
    for solutions, objective_values in zip(results.solutions, results.objective_values):
        solution_dict = task.problem.constant_param() | dict(zip(task.problem.variable_param().keys(), solutions))
        solution: OptimisationSolution = solution_dict
        objective_values: ObjectiveValues = dict(zip(_OBJECTIVES, objective_values))
        OptRes = EndpointResult(
            task_id=str(task.task_id),
            result_id=str(uuid.uuid4()),  # generate a uuid to refer back to later
            solution=solution,
            objective_values=objective_values,
            n_evals=results.n_evals,
            exec_time=results.exec_time,
            completed_at=str(completed_at),
        )
        Optimisation_Results.append(OptRes)
    return Optimisation_Results


async def process_requests(q: IQueue):
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    q
        Queue to process.
    """
    logger.info("Initialising worker loop.")
    while True:
        logger.info("Awaiting next task from queue.")
        task = await q.get()
        try:
            logger.info(f"Optimising {task.task_id}.")
            results = await task.optimiser.run(task.problem)
            logger.info(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            payload = postprocess_results(task, results, completed_at)
            await task.data_manager.transmit_results(payload)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        q.mark_task_done(task)


DataManagerDep = typing.Annotated[DataManager, Depends(DataManager)]


@router.post("/submit-task")
async def submit_task(request: Request, endpoint_task: EndpointTask, data_manager: DataManagerDep) -> TaskResponse:
    """
    Add optimisation task to queue.

    Parameters
    ----------
    Task
        Optimisation task to be added to queue.
    """
    task_id: UUID4 = uuid.uuid4()
    logger.info(f"Received task - assigning id: {task_id}.")
    task = TaskWithUUID(**endpoint_task.model_dump(), task_id=task_id)

    q: IQueue = request.app.state.q
    if q.full():
        logger.warning("Queue full.")
        raise HTTPException(status_code=503, detail="Task queue is full.")
    if task.task_id in q.q.keys():
        logger.warning(f"{task.task_id} already in queue.")
        raise HTTPException(status_code=400, detail="Task already in queue.")
    else:
        try:
            await data_manager.process_site_data(task.site_data, task.task_id)
            pytask = convert_task(task, data_manager)
            await data_manager.transmit_task(task)
            await q.put(pytask)
            return TaskResponse(task_id=task.task_id)
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to add task to database: {str(e.response.text)}")
            raise HTTPException(status_code=500, detail=f"Failed to add task to database: {str(e.response.text)}") from e
        except Exception as e:
            logger.warning(f"Failed to add task to queue: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add task to queue: {str(e)}") from e
