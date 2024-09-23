import json
import os
import tempfile
import time
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from paretoset import paretoset  # type: ignore

from .opt_algorithm import Algorithm
from .problem import _OBJECTIVES, _OBJECTIVES_DIRECTION, Problem, convert_param
from .result import Result
from .task_data_wrapper import run_headless

_EPOCH_CONFIG = {"optimiser": {"leagueTableCapacity": 1, "produceExhaustiveOutput": True}}


class GridSearch(Algorithm):
    """
    Optimise a multi-objective EPOCH problem using grid search.
    """

    def __init__(
        self,
        keep_degenerate: bool = False,
    ) -> None:
        """
        Define grid search parameters.

        Parameters
        ----------
        keep_degenerate
            Whether or not to keep degenerate solutions in solutions
        """
        self.keep_degenerate = keep_degenerate

    def run(self, problem: Problem) -> Result:
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
        temp_dir = tempfile.TemporaryDirectory()

        output_dir = Path(temp_dir.name, "tmp_outputs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        config_dir = Path(temp_dir.name, "Config")
        Path(temp_dir.name, "Config").mkdir(parents=False, exist_ok=False)

        with open(Path(config_dir, "EpochConfig.json"), "w") as f:
            json.dump(_EPOCH_CONFIG, f)

        with open(Path(problem.input_dir, "inputParameters.json"), "w") as f:
            json.dump(convert_param(problem.parameters), f)

        t0 = time.perf_counter()
        run_headless(
            project_path=str(os.environ.get("EPOCH_DIR", "../Epoch")),
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

        temp_dir.cleanup()

        return Result(solutions=solutions, objective_values=objective_values, exec_time=exec_time, n_evals=problem.size())
