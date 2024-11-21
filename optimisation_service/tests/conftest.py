import shutil
from collections.abc import Generator
from copy import deepcopy
from datetime import timedelta
from os import PathLike
from pathlib import Path

import numpy as np
import pytest

from app.internal.epoch_utils import PyTaskData
from app.internal.portfolio_simulator import combine_objective_values
from app.models.constraints import ConstraintDict
from app.models.core import Site
from app.models.objectives import _OBJECTIVES, Objectives
from app.models.parameters import ParameterDict, ParametersWORange, ParametersWRange, ParamRange, is_variable_paramrange
from app.models.result import BuildingSolution, OptimisationResult, PortfolioSolution
from app.models.site_data import FileLoc, LocalMetaData


@pytest.fixture
def default_parameters() -> ParameterDict:
    return ParameterDict(
        ESS_capacity=ParamRange(min=0, max=3, step=1),
        ESS_charge_power=ParamRange(min=0, max=3, step=1),
        ESS_discharge_power=ParamRange(min=0, max=3, step=1),
        ASHP_HPower=ParamRange(min=10, max=10, step=0),
        ASHP_HSource=ParamRange(min=1, max=1, step=0),
        ASHP_HotTemp=ParamRange(min=43, max=43, step=0),
        ASHP_RadTemp=ParamRange(min=60, max=60, step=0),
        ESS_charge_mode=ParamRange(min=1, max=1, step=0),
        ESS_discharge_mode=ParamRange(min=1, max=1, step=0),
        ESS_start_SoC=ParamRange(min=0, max=0, step=0),
        EV_flex=ParamRange(min=0, max=0, step=0),
        Export_headroom=ParamRange(min=0, max=0, step=0),
        Fixed_load1_scalar=ParamRange(min=1, max=1, step=0),
        Fixed_load2_scalar=ParamRange(min=0, max=0, step=0),
        Flex_load_max=ParamRange(min=0, max=0, step=0),
        GridExport=ParamRange(min=60, max=60, step=0),
        GridImport=ParamRange(min=60, max=60, step=0),
        Import_headroom=ParamRange(min=0.4, max=0.4, step=0),
        Min_power_factor=ParamRange(min=0.95, max=0.95, step=0),
        Mop_load_max=ParamRange(min=0, max=0, step=0),
        ScalarHL1=ParamRange(min=1, max=1, step=0),
        ScalarHYield=ParamRange(min=0.75, max=0.75, step=0),
        ScalarRG1=ParamRange(min=0, max=0, step=0),
        ScalarRG2=ParamRange(min=0, max=0, step=0),
        ScalarRG3=ParamRange(min=0, max=0, step=0),
        ScalarRG4=ParamRange(min=0, max=0, step=0),
        f22_EV_CP_number=ParamRange(min=3, max=3, step=0),
        r50_EV_CP_number=ParamRange(min=0, max=0, step=0),
        s7_EV_CP_number=ParamRange(min=0, max=0, step=0),
        u150_EV_CP_number=ParamRange(min=0, max=0, step=0),
        DHW_cylinder_volume=ParamRange(min=100, max=100, step=0),
        CAPEX_limit=500,
        Export_kWh_price=5,
        OPEX_limit=20,
        target_max_concurrency=44,
        time_budget_min=5,
        timestep_hours=1,
        timewindow=8760,
    )


@pytest.fixture
def default_input_dir() -> PathLike:
    return Path("tests", "data", "input_data")


@pytest.fixture
def default_site(default_parameters: ParameterDict, default_input_dir: PathLike) -> Site:
    site = Site(
        name="test_site",
        search_parameters=default_parameters,
        site_data=LocalMetaData(loc=FileLoc.local, site_id="demo_edinburgh", path=Path("tests", "data", "input_data")),
    )
    site._input_dir = default_input_dir
    return site


@pytest.fixture
def default_portfolio(default_site: Site) -> list[Site]:
    default_site_2 = deepcopy(default_site)
    default_site_2.name = "test_site_2"
    return [default_site, default_site_2]


@pytest.fixture
def default_constraints() -> ConstraintDict:
    return {}


@pytest.fixture
def default_objectives() -> list[Objectives]:
    return [Objectives.carbon_balance, Objectives.cost_balance]


@pytest.fixture(scope="module")
def temporary_directory(
    tmpdir_factory: pytest.TempdirFactory,
) -> Generator[PathLike, None, None]:
    my_tmpdir = tmpdir_factory.mktemp("tmp")
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


def dummy_site_solution(site: Site) -> BuildingSolution:
    solution = PyTaskData()
    rng = np.random.default_rng()
    for parameter in ParametersWRange:
        paramrange = getattr(site.search_parameters, parameter)
        if is_variable_paramrange(paramrange):
            solution[parameter] = rng.choice(
                np.arange(start=paramrange.min, stop=paramrange.max + paramrange.step, step=paramrange.step)
            )
        else:
            solution[parameter] = paramrange.min
    for parameter in ParametersWORange:
        solution[parameter] = getattr(site.search_parameters, parameter)

    objective_values = {objective: rng.random() * 100 for objective in _OBJECTIVES}
    return BuildingSolution(solution=solution, objective_values=objective_values)


def dummy_portfolio_results(portfolio: list[Site]) -> PortfolioSolution:
    solution = {}
    building_objective_values = []
    for site in portfolio:
        site_solution = dummy_site_solution(site)
        solution[site.name] = site_solution
        building_objective_values.append(site_solution.objective_values)
    objective_values = combine_objective_values(building_objective_values)
    return PortfolioSolution(solution=solution, objective_values=objective_values)


@pytest.fixture
def dummy_optimisation_result(default_portfolio) -> OptimisationResult:
    solutions = [dummy_portfolio_results(default_portfolio) for _ in range(10)]
    return OptimisationResult(solutions=solutions, n_evals=999, exec_time=timedelta(seconds=99))
