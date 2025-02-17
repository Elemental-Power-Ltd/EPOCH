import json
import logging
import os
import pathlib
import platform
import shutil
import subprocess
import tempfile
import time
from datetime import timedelta
from itertools import islice, product
from pathlib import Path

import numpy as np
import pandas as pd
from paretoset import paretoset  # type: ignore

from app.internal.epoch_utils import TaskData
from app.internal.portfolio_simulator import combine_metric_values
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import _METRICS, Metric, MetricDirection
from app.models.result import OptimisationResult, PortfolioSolution, SiteSolution

from ..models.algorithms import Algorithm

logger = logging.getLogger("default")

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

    def run(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]) -> OptimisationResult:
        """
        Run grid search optimisation.

        Parameters
        ----------
        objectives
            List of metrics to optimise for.
        portfolio
            List of buidlings to find optimise scenarios.
        constraints
            Constraints to apply to metrics.

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        site_solutions = {}
        n_evals = 0
        for site in portfolio:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir, "tmp_outputs")
                os.makedirs(output_dir, exist_ok=True)

                config_dir = Path(temp_dir, "Config")
                Path(temp_dir, "Config").mkdir(parents=False, exist_ok=False)

                with open(Path(config_dir, "EpochConfig.json"), "w") as f:
                    json.dump(_EPOCH_CONFIG, f)

                with open(Path(site._input_dir, "inputParameters.json"), "w") as f:
                    json.dump(site.site_range, f)

                t0 = time.perf_counter()
                run_headless(
                    config_dir=str(config_dir),
                    input_dir=str(site._input_dir),
                    output_dir=str(output_dir),
                )
                exec_time = timedelta(seconds=(time.perf_counter() - t0))

                df_res = pd.read_csv(Path(output_dir, "ExhaustiveResults.csv"), encoding="cp1252", dtype=np.float32)
                df_res = df_res.drop(columns=["Parameter index"])
                df_res[Metric.carbon_cost] = df_res[Metric.capex] / df_res[Metric.carbon_balance_scope_1]

                n_evals += len(df_res)

                # Avoid maintaining all solutions from each building by keeping only the best solutions for each CAPEX.
                if len(portfolio) > 1:  # Only required if there is more than 1 building.
                    df_res = pareto_front_but_preserve(df_res, objectives, Metric.capex)

                for objective, bounds in constraints.items():
                    min_value = bounds.get("min", -np.inf)
                    max_value = bounds.get("max", np.inf)
                    df_res = df_res[(df_res[objective] >= min_value) & (df_res[objective] <= max_value)]

                scenarios_list: list[dict] = df_res.drop(columns=_METRICS).to_dict("records")
                scenarios = [TaskData.from_json(json.dumps(scenario)) for scenario in scenarios_list]
                objective_values: list[dict] = df_res[_METRICS].to_dict("records")

                site_solutions[site.name] = [SiteSolution(*sol) for sol in zip(scenarios, objective_values)]  # type: ignore

        solutions = pareto_optimise(site_solutions, objectives, constraints)

        return OptimisationResult(solutions=solutions, exec_time=exec_time, n_evals=n_evals)


def pareto_optimise(
    building_solutions_dict: dict[str, list[SiteSolution]], objectives: list[Metric], constraints: Constraints
) -> list[PortfolioSolution]:
    logger.debug(f"Number of Sites: {[len(scenario_list) for scenario_list in building_solutions_dict.values()]}")
    all_combinations = product(*building_solutions_dict.values())
    objective_mask = [_METRICS.index(col) for col in objectives]
    objective_direct = ["max" if MetricDirection[objective] == -1 else "min" for objective in objectives]
    pareto_optimal_subsets = []
    n = 0
    while True:
        subset = np.array(list(islice(all_combinations, 50000000)))  # type: ignore
        logger.debug(f"optimising subset {n}.")
        n += 1
        if subset.size > 1:
            subset_costs = []
            is_feasible = np.ones(len(subset), dtype=bool)
            for i, combination in enumerate(subset):
                objective_values = combine_metric_values([building.objective_values for building in combination])
                for objective, bounds in constraints.items():
                    min_value = bounds.get("min", None)
                    max_value = bounds.get("max", None)
                    is_feasible[i] = not (min_value is not None and objective_values[objective] < min_value)
                    is_feasible[i] = not (max_value is not None and objective_values[objective] > max_value)
                if is_feasible[i]:
                    subset_costs.append(list(objective_values.values()))
            subset_costs_req = np.array(subset_costs)[:, objective_mask]
            is_pareto_efficient = paretoset(costs=subset_costs_req, sense=objective_direct, distinct=True)
            pareto_optimal_subsets.append(subset[is_feasible][is_pareto_efficient])
        else:
            break
    reduced_set = np.vstack(pareto_optimal_subsets)
    costs = np.array(
        [list(combine_metric_values([site.objective_values for site in combination]).values()) for combination in reduced_set]
    )[:, objective_mask]
    is_pareto_efficient = paretoset(costs=costs, sense=objective_direct, distinct=True)
    front = reduced_set[is_pareto_efficient].tolist()

    site_names = building_solutions_dict.keys()
    portfolio_solutions = []
    for combination in front:
        solution_dict = dict(zip(site_names, combination))
        objective_values = [site.objective_values for site in combination]  # type: ignore
        portfolio_objective_values = combine_metric_values(objective_values)  # type: ignore

        portfolio_solution = PortfolioSolution(scenario=solution_dict, metric_values=portfolio_objective_values)

        portfolio_solutions.append(portfolio_solution)

    return portfolio_solutions


def pareto_front_but_preserve(df: pd.DataFrame, objectives: list[Metric], preserved_objective: Metric) -> pd.DataFrame:
    """
    Find the optimal Pareto front while maintaining at least one solution for each value encountered of the preserved objective.

    Parameters
    ----------
    df
        Pandas dataframe.
    objectives
        Objective(s) to optimise for (must be a subset of the dataframe's columns).
    preserved_objective
        Objective to preserve values of (must be a column of the dataframe).

    Returns
    -------
    df
        Pandas dataframe of optimal Pareto front.
    """
    grouped = df.groupby(by=[preserved_objective])
    optimal_res = []
    for _, group in grouped:
        obj_values = group[objectives]
        objective_direct = ["max" if MetricDirection[objective] == -1 else "min" for objective in objectives]
        pareto_efficient = paretoset(costs=obj_values, sense=objective_direct, distinct=True)
        optimal_res.append(group[pareto_efficient])
    return pd.concat(optimal_res)


def run_headless(
    input_dir: os.PathLike | str,
    output_dir: os.PathLike | str,
    config_dir: os.PathLike | str,
) -> dict[str, float]:
    """
    Run the headless version of Epoch as a subprocess

    Parameters
    ----------
    input_dir
        A directory containing input data for Epoch.
    output_dir
         The directory to write the output to.
    config_dir
        A directory containing the config file(s) for Epoch.

    Returns
    -------
        A dictionary containing the best value for each of the five objectives
    """
    logger.debug("Running run_headless.")

    epoch_path = get_epoch_path()

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
            epoch_path,
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


def get_epoch_path() -> str:
    """
    Find the Epoch executable

    This tries a number of options in the following order:
    1. Epoch is in the system PATH
    2. There is a release build of Epoch within the EPOCH_DIRECTORY path
    3. There is a debug build of Epoch within the EPOCH_DIRECTORY path

    Returns
    -------
        A valid path to supply to subprocess.run
    """

    # When using Docker, we expect to find Epoch in the PATH
    system_path_epoch = shutil.which("Epoch")
    if system_path_epoch:
        logger.debug(f"Found Epoch in the PATH - {system_path_epoch}")
        return "Epoch"

    # Epoch is not in the system PATH, try looking in the build folder of EPOCH_DIR
    epoch_dir = str(os.environ.get("EPOCH_DIR", "./Epoch"))

    if platform.system() == "Windows":
        # Windows places Release and Debug builds in separate folders
        # We prioritise Release builds (we currently only support RelWithDebInfo and Debug)
        exe_name = "Epoch.exe"

        suffixes = [
            pathlib.Path("build", "headless", "epoch_main", "RelWithDebInfo"),
            pathlib.Path("build", "headless", "epoch_main", "Debug"),
        ]
    else:
        # Linux places the executable in build/epoch_main
        exe_name = "Epoch"

        suffixes = [pathlib.Path("build", "epoch_main")]

    project_path = pathlib.Path(epoch_dir)

    for suffix in suffixes:
        full_path_to_exe = project_path / suffix / exe_name
        if os.path.isfile(full_path_to_exe):
            logger.debug(f"Found Epoch at {full_path_to_exe}")
            return str(full_path_to_exe)

    raise FileNotFoundError("Failed to find Epoch executable")
