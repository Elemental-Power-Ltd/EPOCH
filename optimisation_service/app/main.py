import asyncio
import datetime
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from os import PathLike

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from src.epl_typing import ConstraintDict, ParameterDict
from src.genetic_algorithm import NSGA2, GeneticAlgorithm
from src.grid_search import GridSearch
from src.opt_algorithm import Algorithm
from src.problem import Problem
from src.result import Result


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
    Problem instance.
    Optimiser instance.
    """
    optimiser = Optimiser[task.optimiser.type].value(**task.optimiser.hyperparameters)
    problem = Problem(
        name=task.problem.id,
        objectives=task.problem.objectives,
        constraints=task.problem.constraints,
        parameters=task.problem.parameters,
        input_dir=task.problem.input_path,
    )
    return problem, optimiser


def optimise(problem: Problem, optimiser: Algorithm) -> tuple[Result, datetime.UTC]:
    return optimiser.run(problem), datetime.datetime.now(datetime.UTC)


records = {}


def transmit(problem: Problem, results: Result, completed_at: datetime.UTC):
    df_objective_values = pd.DataFrame(data=results.objective_values, columns=problem.objectives.keys())
    df_solutions = pd.DataFrame(data=results.solutions, columns=problem.variable_param().keys())
    constant_param = problem.constant_param()
    constant_param_values = np.repeat([list(problem.constant_param().values())], results.solutions.shape[0], axis=0)
    df_constants = pd.DataFrame(data=constant_param_values, columns=constant_param.keys())

    records[problem.name] = pd.concat([df_objective_values, df_solutions, df_constants], axis=1).to_json(orient="records")


async def process_requests(q: asyncio.Queue, pool: ProcessPoolExecutor):
    while True:
        task = await q.get()
        loop = asyncio.get_running_loop()
        problem, optimiser = convert_task(task)
        results, completed_at = await loop.run_in_executor(pool, optimise, *(problem, optimiser))
        transmit(problem, results, completed_at)
        q.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    queue = asyncio.Queue(maxsize=5)
    pool = ProcessPoolExecutor()
    app.state.queue = queue
    app.state.pool = pool
    asyncio.create_task(process_requests(queue, pool))
    yield
    pool.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/add")
async def add_task(request: Request, problem: JSONProblem, optimiser: JSONOptimiser):
    queue = request.app.state.queue
    if queue.full():
        raise HTTPException(status_code=503, detail="Task queue is full.")
    else:
        await queue.put(Task(problem, optimiser))
        return "Added task to queue."


@app.get("/records")
async def get_records():
    return records
