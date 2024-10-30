import json
import logging
import os
import pathlib
import platform
import subprocess
import tempfile
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from paretoset import paretoset  # type: ignore

from app.internal.pareto_front import portfolio_pareto_front
from app.internal.portfolio_simulator import gen_all_building_combinations
from app.internal.problem import PortfolioProblem
from app.models.objectives import _OBJECTIVES, _OBJECTIVES_DIRECTION
from app.models.result import BuildingSolution, OptimisationResult

from ..models.algorithms import Algorithm
from ..models.parameters import EndpointParameterDict, OldParameterDict, ParameterDict, ParametersWORange, ParametersWRange

logger = logging.getLogger("default")

_EPOCH_CONFIG = {"optimiser": {"leagueTableCapacity": 1, "produceExhaustiveOutput": True}}


def convert_param(parameters: ParameterDict | EndpointParameterDict | dict[str, Any]) -> OldParameterDict:
    """
    Converts dictionary of parameters from dict of dicts to dict of lists.
    ex: {"param1":{"min":0, "max":10, "step":1}, "param2":123} -> {"param1":[0, 10, 1], "param2":123}

    Parameters
    ----------
    parameters
        Dictionary of parameters with values in the format {"min":min, "max":max, "step":step} or int or float.

    Returns
    -------
    ParameterDict
        Dictionary of parameters with values in the format [min, max, step] or int or float.
    """
    if isinstance(parameters, EndpointParameterDict):
        parameters = parameters.model_dump()
    new_dict = {}
    for param_name in ParametersWRange:
        value = parameters[param_name]  # type: ignore
        new_dict[param_name] = [value["min"], value["max"], value["step"]]
    for param_name in ParametersWORange:
        new_dict[param_name] = parameters[param_name]  # type: ignore
    return new_dict


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

    def run(self, portfolio: PortfolioProblem) -> OptimisationResult:
        """
        Run grid search optimisation.

        Parameters
        ----------
        portfolio
            Portfolio problem instance to optimise.

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        building_solutions = {}
        for building_name, building in portfolio.buildings.items():
            temp_dir = tempfile.TemporaryDirectory()

            output_dir = Path(temp_dir.name, "tmp_outputs")
            os.makedirs(output_dir, exist_ok=True)

            config_dir = Path(temp_dir.name, "Config")
            Path(temp_dir.name, "Config").mkdir(parents=False, exist_ok=False)

            with open(Path(config_dir, "EpochConfig.json"), "w") as f:
                json.dump(_EPOCH_CONFIG, f)

            with open(Path(building.input_dir, "inputParameters.json"), "w") as f:
                json.dump(convert_param(building.parameters), f)

            t0 = time.perf_counter()
            run_headless(
                project_path=str(os.environ.get("EPOCH_DIR", "./Epoch")),
                config_dir=str(config_dir),
                input_dir=str(building.input_dir),
                output_dir=str(output_dir),
            )
            exec_time = timedelta(seconds=(time.perf_counter() - t0))

            os.remove(Path(building.input_dir, "inputParameters.json"))

            df_res = pd.read_csv(Path(output_dir, "ExhaustiveResults.csv"), encoding="cp1252", dtype=np.float32)

            if len(portfolio.buildings.keys()) > 1:
                grouped = df_res.groupby(by=["capex"])
                optimal_res = []
                for _, group in grouped:
                    obj_values = group[portfolio.objectives]
                    objective_direct = [
                        "max" if _OBJECTIVES_DIRECTION[objective] == -1 else "min" for objective in portfolio.objectives
                    ]
                    pareto_efficient = paretoset(costs=obj_values, sense=objective_direct, distinct=True)
                    optimal_res.append(group[pareto_efficient])
                df_res = pd.concat(optimal_res)

            solutions = df_res.drop(columns=_OBJECTIVES).to_dict("records")
            objective_values = df_res[_OBJECTIVES].to_dict("records")

            building_solutions[building_name] = np.array([BuildingSolution(*sol) for sol in zip(solutions, objective_values)])

            temp_dir.cleanup()

        portfolio_sol = gen_all_building_combinations(building_solutions)

        portfolio_sol_pf = portfolio_pareto_front(portfolio_sol, portfolio.objectives)

        # TODO: Apply portfolio constraints

        return OptimisationResult(solutions=portfolio_sol_pf, exec_time=exec_time, n_evals=building.size())


def run_headless(
    project_path: os.PathLike | str,
    input_dir: os.PathLike | str | None = None,
    output_dir: os.PathLike | str | None = None,
    config_dir: os.PathLike | str | None = None,
) -> dict[str, float]:
    """
    Run the headless version of Epoch as a subprocess

    Parameters
    ----------
    project_path
        The path to the root of the Epoch repository
    input_dir
        A directory containing input data for Epoch. Defaults to $project_path$/InputData
    output_dir
         The directory to write the output to. Defaults to ./Data/OutputData
    config_dir
        A directory containing the config file(s) for Epoch. Defaults to $project_path$/Config

    Returns
    -------
        A dictionary containing the best value for each of the five objectives
    """
    logger.debug("Running run_headless.")

    if platform.system() == "Windows":
        exe_name = "Epoch.exe"
    else:
        exe_name = "Epoch"

    project_path = pathlib.Path(project_path)

    full_path_to_exe = pathlib.Path(exe_name)
    if not full_path_to_exe.is_file():
        suffix = pathlib.Path("build", "epoch_main")
        full_path_to_exe = project_path / suffix / exe_name
    assert pathlib.Path(full_path_to_exe).exists(), f"Could not find an EPOCH executable at {full_path_to_exe}"

    # input_dir, output_dir and config_dir can all be None
    # in which case we default to the following:
    #   input_dir   - the InputData directory in the Epoch root directory
    #   output_dir  - Data/OutputData within this project
    #   config_dir  - the Config directory in the Epoch root directory

    if input_dir is None:
        input_dir = pathlib.Path(project_path) / "InputData"

    if output_dir is None:
        output_dir = pathlib.Path("Data", "OutputData")

    if config_dir is None:
        config_dir = pathlib.Path(project_path) / "Config"

    input_dir, output_dir, config_dir = pathlib.Path(input_dir), pathlib.Path(output_dir), pathlib.Path(config_dir)
    # check these directories exist
    assert input_dir.is_dir(), f"Could not find {input_dir}"
    assert output_dir.is_dir(), f"Could not find {output_dir}"
    assert config_dir.is_dir(), f"Could not find {config_dir}"

    # check for required files within the directories
    assert (input_dir / "inputParameters.json").is_file(), f"Could not find {input_dir / "inputParameters.json"} is not a file"
    assert (config_dir / "EpochConfig.json").is_file(), f"Could not find {input_dir / "EpochConfig.json"} is not a file"

    result = subprocess.run(
        [
            str(full_path_to_exe),
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
            "--config",
            str(config_dir),
        ]
    )

    assert result.returncode == 0, result

    output_json = output_dir / "outputParameters.json"

    with open(output_json) as f:
        full_output = json.load(f)

    minimal_output = {
        "annualised": full_output["annualised"],
        "scenario_cost_balance": full_output["scenario_cost_balance"],
        "scenario_carbon_balance": full_output["scenario_carbon_balance"],
        "payback_horizon": full_output["payback_horizon"],
        "CAPEX": full_output["CAPEX"],
        "time_taken": full_output["time_taken"],
    }
    return minimal_output
