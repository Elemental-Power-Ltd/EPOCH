import shutil
from collections.abc import Generator
from datetime import timedelta
from os import PathLike
from pathlib import Path

import numpy as np
import pytest

from app.internal.portfolio_simulator import combine_objective_values
from app.internal.problem import Building, PortfolioProblem
from app.internal.task_data_wrapper import PyTaskData
from app.models.constraints import ConstraintDict
from app.models.objectives import Objectives
from app.models.parameters import ParameterDict
from app.models.result import BuildingSolution, OptimisationResult, PortfolioSolution


@pytest.fixture
def default_parameters() -> ParameterDict:
    return {
        "ESS_capacity": {"min": 1, "max": 3, "step": 1},
        "ESS_charge_power": {"min": 1, "max": 3, "step": 1},
        "ESS_discharge_power": {"min": 1, "max": 3, "step": 1},
        "ASHP_HPower": {"min": 10, "max": 10, "step": 0},
        "ASHP_HSource": {"min": 1, "max": 1, "step": 0},
        "ASHP_HotTemp": {"min": 43, "max": 43, "step": 0},
        "ASHP_RadTemp": {"min": 60, "max": 60, "step": 0},
        "ESS_charge_mode": {"min": 1, "max": 1, "step": 0},
        "ESS_discharge_mode": {"min": 1, "max": 1, "step": 0},
        "ESS_start_SoC": {"min": 0.5, "max": 0.5, "step": 0},
        "EV_flex": {"min": 0, "max": 0, "step": 0},
        "Export_headroom": {"min": 0, "max": 0, "step": 0},
        "Fixed_load1_scalar": {"min": 1, "max": 1, "step": 0},
        "Fixed_load2_scalar": {"min": 0, "max": 0, "step": 0},
        "Flex_load_max": {"min": 0, "max": 0, "step": 0},
        "GridExport": {"min": 95, "max": 95, "step": 0},
        "GridImport": {"min": 95, "max": 95, "step": 0},
        "Import_headroom": {"min": 0, "max": 0, "step": 0},
        "Min_power_factor": {"min": 0.95, "max": 0.95, "step": 0},
        "Mop_load_max": {"min": 0, "max": 0, "step": 0},
        "ScalarHL1": {"min": 1, "max": 1, "step": 0},
        "ScalarHYield": {"min": 0.75, "max": 0.75, "step": 0},
        "ScalarRG1": {"min": 0, "max": 0, "step": 0},
        "ScalarRG2": {"min": 0, "max": 0, "step": 0},
        "ScalarRG3": {"min": 0, "max": 0, "step": 0},
        "ScalarRG4": {"min": 0, "max": 0, "step": 0},
        "f22_EV_CP_number": {"min": 0, "max": 0, "step": 0},
        "r50_EV_CP_number": {"min": 0, "max": 0, "step": 0},
        "s7_EV_CP_number": {"min": 0, "max": 0, "step": 0},
        "u150_EV_CP_number": {"min": 0, "max": 0, "step": 0},
        "DHW_cylinder_volume": {"min": 0.001, "max": 0.001, "step": 0},
        "OPEX_limit": 20.0,
        "Export_kWh_price": 5.0,
        "target_max_concurrency": 44,
        "time_budget_min": 1.0,
        "timestep_hours": 1.0,
        "CAPEX_limit": 500.0,
        "timewindow": 8760,
    }


@pytest.fixture
def default_input_dir() -> PathLike:
    return Path("tests", "data", "input_data")


@pytest.fixture
def default_building(default_parameters, default_input_dir) -> Building:
    return Building(parameters=default_parameters, input_dir=default_input_dir)


@pytest.fixture
def default_buildings(default_building) -> dict[str, Building]:
    return {"hotel_1": default_building, "hotel_2": default_building}


@pytest.fixture
def default_constraints() -> ConstraintDict:
    return {Objectives.capex: {"min": 100}}  # type: ignore


@pytest.fixture
def default_objectives() -> list[Objectives]:
    return [
        Objectives.carbon_balance,
        Objectives.cost_balance,
        Objectives.capex,
        Objectives.payback_horizon,
        Objectives.annualised_cost,
    ]


@pytest.fixture
def default_portfolio_problem(default_objectives, default_constraints, default_buildings) -> PortfolioProblem:
    return PortfolioProblem(objectives=default_objectives, constraints=default_constraints, buildings=default_buildings)


@pytest.fixture(scope="module")
def temporary_directory(
    tmpdir_factory: pytest.TempdirFactory,
) -> Generator[PathLike, None, None]:
    my_tmpdir = tmpdir_factory.mktemp("tmp")
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


def dummy_building_solution(building: Building, objectives: list[Objectives]) -> BuildingSolution:
    solution = PyTaskData(**building.constant_param())
    rng = np.random.default_rng()
    for name, value in building.variable_param().items():
        solution[name] = rng.choice(np.arange(start=value["min"], stop=value["max"], step=value["step"]))
    objective_values = {objective: rng.random() * 100 for objective in objectives}
    return BuildingSolution(solution=solution, objective_values=objective_values)


def dummy_portfolio_results(portfolio_problem: PortfolioProblem) -> PortfolioSolution:
    solution = {}
    building_objective_values = []
    for building_name, building in portfolio_problem.buildings.items():
        building_solution = dummy_building_solution(building, portfolio_problem.objectives)
        solution[building_name] = building_solution
        building_objective_values.append(building_solution.objective_values)
    objective_values = combine_objective_values(building_objective_values)
    return PortfolioSolution(solution=solution, objective_values=objective_values)


@pytest.fixture
def dummy_optimisation_result(default_portfolio_problem) -> OptimisationResult:
    solutions = [dummy_portfolio_results(default_portfolio_problem) for _ in range(10)]
    return OptimisationResult(solutions=solutions, n_evals=999, exec_time=timedelta(seconds=99))
