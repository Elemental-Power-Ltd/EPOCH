import asyncio
import datetime
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
from os import PathLike

from fastapi import APIRouter, HTTPException, Request
from pydantic import UUID1, BaseModel

from ..internal.epl_typing import ConstraintDict, ParameterDict
from ..internal.genetic_algorithm import NSGA2, GeneticAlgorithm
from ..internal.grid_search import GridSearch
from ..internal.opt_algorithm import Algorithm
from ..internal.problem import Problem
from ..internal.result import Result

router = APIRouter()


# def transmit(problem: Problem, results: Result, completed_at: datetime.UTC):
#     df_objective_values = pd.DataFrame(data=results.objective_values, columns=problem.objectives.keys())
#     df_solutions = pd.DataFrame(data=results.solutions, columns=problem.variable_param().keys())
#     constant_param = problem.constant_param()
#     constant_param_values = np.repeat([list(problem.constant_param().values())], results.solutions.shape[0], axis=0)
#     df_constants = pd.DataFrame(data=constant_param_values, columns=constant_param.keys())

#     records[problem.name] = pd.concat([df_objective_values, df_solutions, df_constants], axis=1).to_json(orient="records")


class JSONOptimiser(BaseModel):
    type: str
    hyperparameters: dict[str, str | int | float]


class JSONProblem(BaseModel):
    id: str
    objectives: dict[str, int]
    constraints: ConstraintDict
    parameters: ParameterDict
    input_type: str
    input_path: str | PathLike


class Optimiser(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


@dataclass()
class Task:
    UUID: UUID1
    problem: JSONProblem
    optimiser: JSONOptimiser


def convert_task(task: Task) -> tuple[Problem, Optimiser]:
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
    # input_data = fetch_inputdata(task.problem.input_path)
    # input_path = save_inputdata(input_data)
    optimiser = Optimiser[task.optimiser.type].value(**task.optimiser.hyperparameters)
    problem = Problem(
        name=task.problem.id,
        objectives=task.problem.objectives,
        constraints=task.problem.constraints,
        parameters=task.problem.parameters,
        input_dir="C:/Users/willi/Documents/GitHub/optimisation_elemental/tests/data/benchmarks/var-3/InputData",  # input_path
    )
    return problem, optimiser


def fetch_inputdata(input_data_details):
    """
    Fetch input data from database.

    Parameters
    ----------
    input_data_details
        details of input data to fetch

    Returns
    input_data
        Input data
    """
    pass


def save_inputdata(input_data):
    """
    Save input data to data folder.

    Parameters
    ----------
    input_data
        Input data to save.

    Returns
    input_data_path
        Path to input data.
    """
    pass
    # return input_data_path


def optimise(problem: Problem, optimiser: Algorithm) -> tuple[Result, datetime.datetime]:
    """
    Apply optimisation algorithm to problem.

    Parameters
    ----------
    problem
        Problem to optimise.
    optimiser
        Optimiser to solve problem.

    Returns
    -------
    Result
        Optimisation results.
    completed_at
        Completion time of optimiser.
    """
    return optimiser.run(problem), datetime.datetime.now(datetime.UTC)


async def process_requests(q: asyncio.Queue, pool: ProcessPoolExecutor):
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    q
        Queue to process.
    pool
        Process Pool Executor to run tasks.
    """
    while True:
        task = await q.get()
        loop = asyncio.get_running_loop()
        problem, optimiser = convert_task(task)
        results, completed_at = await loop.run_in_executor(pool, optimise, *(problem, optimiser))
        # transmit(problem, results, completed_at)
        q.task_done(task)


@router.post("/add/")
async def add_task(request: Request, UUID: UUID1, problem: JSONProblem, optimiser: JSONOptimiser):
    """
    Add tasks to queue.

    Parameters
    ----------
    UUID
        Task UUID.
    problem
        Task problem.
    optimiser
        Task optimiser.
    """
    q = request.app.state.q
    if q.full():
        raise HTTPException(status_code=503, detail="Task queue is full.")
    else:
        await q.put(Task(UUID, problem, optimiser))
        return "Added task to queue."
