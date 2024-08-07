import json
import os
import tempfile
import time
from datetime import timedelta
from os import PathLike
from pathlib import Path

import numpy as np
import pandas as pd
from paretoset import paretoset  # type: ignore

from .opt_algorithm import Algorithm
from .problem import _OBJECTIVES, _OBJECTIVES_DIRECTION, Problem, convert_param
from .result import Result
from .task_data_wrapper import run_headless
from .utils import typename

_EPOCH_CONFIG = {"optimiser": {"leagueTableCapacity": 1, "produceExhaustiveOutput": True}}


class GridSearch(Algorithm):
    """
    Optimise a multi-objective EPOCH problem using grid search.
    """

    def __init__(
        self,
        project_path: str | PathLike | None = None,
        output_dir: str | PathLike | None = None,
        config_dir: str | PathLike | None = None,
        keep_degenerate: bool = False,
    ) -> None:
        """
        Define grid search parameters.

        Parameters
        ----------
        output_dir
            Path to directory to save outputs of EPOCH.
            Defaults to a temporary directory that is deleted after completion of optimisation.
        project_path
            Path to EPOCH directory
        config_dir
            Path to EPOCH config directory
            Defaults to a temporary directory with the necessary config file that is deleted after completion of optimisation.
        keep_degenerate
            Whether or not to keep degenerate solutions in solutions
        """
        if project_path is None:
            project_path = os.environ.get("EPOCH_DIR", "../EPOCH")
        self.project_path = project_path
        self.config_dir = config_dir
        self.output_dir = output_dir
        self.keep_degenerate = keep_degenerate

    async def run(self, problem: Problem) -> Result:
        """
        Run grid search optimisation.

        Parameters
        ----------
        problem
            Problem instance to optimise.

        Returns
        -------
        solutions
            Optimal solutions.
        objective_values
            objective_values of optimal solutions.
        """
        if self.output_dir is None or self.config_dir is None:
            has_temp_dir = True
            temp_dir = tempfile.TemporaryDirectory()
        else:
            has_temp_dir = False

        if self.output_dir is None:
            output_dir = Path(temp_dir.name, "tmp_outputs")
        else:
            output_dir = Path(self.output_dir, typename(self))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if self.config_dir is None:
            config_dir = Path(temp_dir.name, "Config")
            Path(temp_dir.name, "Config").mkdir(parents=False, exist_ok=False)
            with open(Path(config_dir, "EpochConfig.json"), "w") as f:
                json.dump(_EPOCH_CONFIG, f)

        with open(Path(problem.input_dir, "inputParameters.json"), "w") as f:
            json.dump(convert_param(problem.parameters), f)

        t0 = time.perf_counter()
        await run_headless(
            project_path=str(self.project_path),
            config_dir=str(config_dir),
            input_dir=str(problem.input_dir),
            output_dir=str(output_dir),
        )
        exec_time = timedelta(seconds=(time.perf_counter() - t0))

        os.remove(Path(problem.input_dir, "inputParameters.json"))

        variable_param = list(problem.variable_param().keys())
        usecols = problem.objectives + variable_param

        df_res = pd.read_csv(Path(output_dir, "ExhaustiveResults.csv"), encoding="cp1252", dtype=np.float32, usecols=usecols)

        for constraint, bounds in problem.constraints.items():
            df_res = df_res[df_res[constraint] >= bounds.get("min", -np.inf)]
            df_res = df_res[df_res[constraint] <= bounds.get("max", -np.inf)]

        solutions = df_res[variable_param].to_numpy()
        obj_direct = ["max" if _OBJECTIVES_DIRECTION[objective] == -1 else "min" for objective in problem.objectives]
        pareto_efficient = paretoset(df_res[problem.objectives].to_numpy(), obj_direct, distinct=not self.keep_degenerate)
        solutions = solutions[pareto_efficient]
        objective_values = df_res[_OBJECTIVES].to_numpy()[pareto_efficient]

        if has_temp_dir:
            temp_dir.cleanup()

        return Result(solutions=solutions, objective_values=objective_values, exec_time=exec_time, n_evals=problem.size())
