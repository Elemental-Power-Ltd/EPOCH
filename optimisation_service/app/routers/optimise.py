import asyncio
import datetime
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict

from fastapi import APIRouter, HTTPException, Request
from pydantic import UUID1

from ..internal.genetic_algorithm import NSGA2, GeneticAlgorithm
from ..internal.grid_search import GridSearch
from ..internal.opt_algorithm import Algorithm
from ..internal.problem import Problem, convert_objectives, convert_parameters
from ..internal.result import Result

router = APIRouter()


# def transmit(problem: Problem, results: Result, completed_at: datetime.UTC):
#     df_objective_values = pd.DataFrame(data=results.objective_values, columns=problem.objectives.keys())
#     df_solutions = pd.DataFrame(data=results.solutions, columns=problem.variable_param().keys())
#     constant_param = problem.constant_param()
#     constant_param_values = np.repeat([list(problem.constant_param().values())], results.solutions.shape[0], axis=0)
#     df_constants = pd.DataFrame(data=constant_param_values, columns=constant_param.keys())

#     records[problem.name] = pd.concat([df_objective_values, df_solutions, df_constants], axis=1).to_json(orient="records")


class ParamRange(TypedDict):
    min: int | float
    max: int | float
    step: int | float


@dataclass
class Task:
    UUID: UUID1
    optimiser: str
    optimiserConfig: dict[str, str | int | float]
    parameters: dict[str, ParamRange | int | float]
    objectives: list
    site: str


class Optimiser(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


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
    optimiser = Optimiser[task.optimiser].value(**task.optimiserConfig)
    problem = Problem(
        name=task.UUID,
        objectives=convert_objectives(task.objectives),
        constraints={
            "annualised_cost": [None, None],
            "capex": [None, None],
            "carbon_balance": [None, None],
            "cost_balance": [None, None],
            "payback_horizon": [None, None],
        },
        parameters=convert_parameters(task.parameters),
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
async def add_task(request: Request, task: Task):
    """
    Add optimisation tasks to queue.

    Parameters
    ----------
    Task
        Optimisation task to be added to queue.
        Must contain task:
        - UUID
        - Optimiser
        - Optimiser Configuration
        - Objectives
        - Parameters
        - Input Data UUID
    """
    q = request.app.state.q
    if q.full():
        raise HTTPException(status_code=503, detail="Task queue is full.")
    else:
        await q.put(task)
        return "Added task to queue."
