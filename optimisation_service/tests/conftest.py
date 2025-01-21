import json
import shutil
from collections.abc import Generator
from datetime import timedelta
from os import PathLike
from pathlib import Path

import numpy as np
import pytest

from app.internal.epoch_utils import TaskData
from app.internal.portfolio_simulator import combine_objective_values
from app.models.constraints import ConstraintDict
from app.models.core import Site
from app.models.objectives import _OBJECTIVES, Objectives
from app.models.result import OptimisationResult, PortfolioSolution, SiteSolution
from app.models.site_data import FileLoc, LocalMetaData
from app.models.site_range import (
    BatteryModeEnum,
    Building,
    Config,
    DataCentre,
    DomesticHotWater,
    ElectricVehicles,
    EnergyStorageSystem,
    Grid,
    HeatPump,
    HeatSourceEnum,
    Mop,
    Renewables,
    SiteRange,
)


@pytest.fixture
def default_siterange() -> SiteRange:
    building = Building(
        COMPONENT_IS_MANDATORY=True, scalar_heat_load=[1], scalar_electrical_load=[1], fabric_intervention_index=[0]
    )
    data_centre = DataCentre(COMPONENT_IS_MANDATORY=False, maximum_load=[100], hotroom_temp=[30])
    domestic_hot_water = DomesticHotWater(COMPONENT_IS_MANDATORY=False, cylinder_volume=[100])
    electric_vehicles = ElectricVehicles(
        COMPONENT_IS_MANDATORY=False,
        flexible_load_ratio=[0.5],
        small_chargers=[0],
        fast_chargers=[0],
        rapid_chargers=[0],
        ultra_chargers=[0],
        scalar_electrical_load=[0],
    )
    energy_storage_system = EnergyStorageSystem(
        COMPONENT_IS_MANDATORY=False,
        capacity=[100],
        charge_power=[100],
        discharge_power=[100],
        battery_mode=[BatteryModeEnum.CONSUME],
        initial_charge=[0],
    )
    grid = Grid(
        COMPONENT_IS_MANDATORY=True,
        export_headroom=[0.5],
        grid_export=[60],
        grid_import=[60],
        import_headroom=[0.5],
        min_power_factor=[1],
        tariff_index=[0],
    )
    heat_pump = HeatPump(
        COMPONENT_IS_MANDATORY=False, heat_power=[100], heat_source=[HeatSourceEnum.AMBIENT_AIR], send_temp=[70]
    )
    mop = Mop(COMPONENT_IS_MANDATORY=False, maximum_load=[100])
    renewables = Renewables(COMPONENT_IS_MANDATORY=False, yield_scalars=[[100]])
    config = Config(capex_limit=99999999999)

    return SiteRange(
        building=building,
        data_centre=data_centre,
        domestic_hot_water=domestic_hot_water,
        electric_vehicles=electric_vehicles,
        energy_storage_system=energy_storage_system,
        grid=grid,
        heat_pump=heat_pump,
        mop=mop,
        renewables=renewables,
        config=config,
    )


@pytest.fixture
def default_input_dir() -> PathLike:
    return Path("tests", "data", "demo_edinburgh")


@pytest.fixture
def default_site(default_siterange: SiteRange, default_input_dir: PathLike) -> Site:
    site = Site(
        name="test_site",
        site_range=default_siterange,
        site_data=LocalMetaData(loc=FileLoc.local, site_id="demo_edinburgh", path=Path("tests", "data", "demo_edinburgh")),
    )
    site._input_dir = default_input_dir
    return site


@pytest.fixture
def default_site_2(default_siterange: SiteRange, default_input_dir: PathLike) -> Site:
    site = Site(
        name="test_site_2",
        site_range=default_siterange,
        site_data=LocalMetaData(loc=FileLoc.local, site_id="amcott_house", path=Path("tests", "data", "amcott_house")),
    )
    site._input_dir = Path("tests", "data", "amcott_house")
    return site


@pytest.fixture
def default_portfolio(default_site: Site, default_site_2: Site) -> list[Site]:
    return [default_site, default_site_2]


@pytest.fixture
def default_constraints() -> ConstraintDict:
    return {}


@pytest.fixture
def default_objectives() -> list[Objectives]:
    return [Objectives.carbon_cost, Objectives.cost_balance]


@pytest.fixture(scope="module")
def temporary_directory(
    tmpdir_factory: pytest.TempdirFactory,
) -> Generator[PathLike, None, None]:
    my_tmpdir = tmpdir_factory.mktemp("tmp")
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


def dummy_site_solution(site: Site) -> SiteSolution:
    site_scenario = {}
    rng = np.random.default_rng()
    site_range = site.site_range
    for asset_name, asset in site_range.model_dump().items():
        if asset_name == "config":
            site_scenario[asset_name] = asset
        elif asset["COMPONENT_IS_MANDATORY"]:
            asset.pop("COMPONENT_IS_MANDATORY")
            site_scenario[asset_name] = asset
        else:
            site_scenario[asset_name] = {}
            asset.pop("COMPONENT_IS_MANDATORY")
            for attribute_name, attribute_values in asset.items():
                if len(attribute_values) > 1:
                    site_scenario[asset_name][attribute_name] = rng.choice(a=attribute_values)
                else:
                    site_scenario[asset_name][attribute_name] = attribute_values[0]
    scenario = TaskData.from_json(json.dumps(site_scenario))
    objective_values = {objective: rng.random() * 100 for objective in _OBJECTIVES}

    return SiteSolution(scenario=scenario, objective_values=objective_values)


def dummy_portfolio_results(portfolio: list[Site]) -> PortfolioSolution:
    solution = {}
    building_objective_values = []
    for site in portfolio:
        site_solution = dummy_site_solution(site)
        solution[site.site_data.site_id] = site_solution
        building_objective_values.append(site_solution.objective_values)
    objective_values = combine_objective_values(building_objective_values)
    return PortfolioSolution(scenario=solution, objective_values=objective_values)


@pytest.fixture
def dummy_optimisation_result(default_portfolio) -> OptimisationResult:
    solutions = [dummy_portfolio_results(default_portfolio) for _ in range(10)]
    return OptimisationResult(solutions=solutions, n_evals=999, exec_time=timedelta(seconds=99))
