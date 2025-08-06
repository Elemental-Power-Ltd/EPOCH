import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from epoch_simulator import SimulationResult, aggregate_site_results

from app.internal.datamanager import load_epoch_data_from_file
from app.internal.epoch_utils import simulation_result_to_metric_dict
from app.internal.ga_utils import ProblemInstance
from app.internal.site_range import REPEAT_COMPONENTS
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.epoch_types.site_range_type import (
    BatteryModeEnum,
    Building,
    Config,
    DomesticHotWater,
    EnergyStorageSystem,
    GasHeater,
    GasTypeEnum,
    Grid,
    HeatPump,
    HeatSourceEnum,
    SiteRange,
    SolarPanel,
)
from app.models.ga_utils import AnnotatedTaskData, asset_t, value_t
from app.models.metrics import Metric
from app.models.result import OptimisationResult, PortfolioSolution, SiteSolution
from app.models.site_data import EpochSiteData, SiteMetaData

_DATA_PATH = Path("tests", "data")

# set a few fields in the SimulationResult with random values
_METRICS = ["total_capex", "total_electricity_used", "total_ch_shortfall"]
_COMPARISON = ["operating_balance", "npv_balance", "combined_carbon_balance"]


@pytest.fixture
def default_siterange() -> SiteRange:
    building = Building(
        COMPONENT_IS_MANDATORY=True,
        scalar_heat_load=[1],
        scalar_electrical_load=[1],
        fabric_intervention_index=[0],
        incumbent=False,
        age=0,
        lifetime=30,
    )
    domestic_hot_water = DomesticHotWater(
        COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200], incumbent=False, age=0, lifetime=12
    )
    energy_storage_system = EnergyStorageSystem(
        COMPONENT_IS_MANDATORY=False,
        capacity=[100, 200],
        charge_power=[100],
        discharge_power=[100],
        battery_mode=[BatteryModeEnum.CONSUME],
        initial_charge=[0],
        incumbent=False,
        age=0,
        lifetime=15,
    )
    gas_heater = GasHeater(
        COMPONENT_IS_MANDATORY=True,
        maximum_output=[40],
        boiler_efficiency=[0.9],
        gas_type=[GasTypeEnum.NATURAL_GAS, GasTypeEnum.LIQUID_PETROLEUM_GAS],
        incumbent=True,
        age=0,
        lifetime=10,
    )
    grid = Grid(
        COMPONENT_IS_MANDATORY=True,
        grid_export=[60],
        grid_import=[60],
        import_headroom=[0.5],
        tariff_index=[0, 1, 2, 3],
        export_tariff=[0.05],
        incumbent=False,
        age=0,
        lifetime=25,
    )
    heat_pump = HeatPump(
        COMPONENT_IS_MANDATORY=False,
        heat_power=[100, 200],
        heat_source=[HeatSourceEnum.AMBIENT_AIR],
        send_temp=[70],
        incumbent=False,
        age=0,
        lifetime=10,
    )
    panel = SolarPanel(
        COMPONENT_IS_MANDATORY=False, yield_scalar=[100, 200], yield_index=[0], incumbent=False, age=0, lifetime=25
    )
    config = Config(
        capex_limit=99999999999,
        use_boiler_upgrade_scheme=False,
        general_grant_funding=0,
        npv_time_horizon=10,
        npv_discount_factor=0.0,
    )

    return SiteRange(
        building=building,
        domestic_hot_water=domestic_hot_water,
        energy_storage_system=energy_storage_system,
        gas_heater=gas_heater,
        grid=grid,
        heat_pump=heat_pump,
        solar_panels=[panel],
        config=config,
    )


def site_generator(site_name: str, site_range: SiteRange) -> Site:
    start_ts = datetime(year=2022, month=1, day=1, hour=0).astimezone(UTC)
    end_ts = datetime(year=2023, month=1, day=1, hour=0).astimezone(UTC)
    site_data = SiteMetaData(site_id=site_name, start_ts=start_ts, end_ts=end_ts)
    site = Site(
        name=site_data.site_id,
        site_range=site_range,
        site_data=site_data,
    )
    site._epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site_name, "epoch_data.json"))
    return site


@pytest.fixture
def default_epoch_data() -> EpochSiteData:
    return load_epoch_data_from_file(Path(_DATA_PATH, "amcott_house", "epoch_data.json"))


@pytest.fixture
def default_site(default_siterange: SiteRange) -> Site:
    return site_generator("amcott_house", default_siterange)


@pytest.fixture
def default_portfolio(default_siterange: SiteRange) -> list[Site]:
    return [site_generator("amcott_house", default_siterange), site_generator("bircotes_leisure_centre", default_siterange)]


@pytest.fixture
def default_constraints() -> Constraints:
    return {Metric.capex: {"max": 999999, "min": 1}, Metric.payback_horizon: {"max": 25}}


@pytest.fixture
def default_objectives() -> list[Metric]:
    return [Metric.carbon_balance_scope_1, Metric.cost_balance]


@pytest.fixture
def default_problem_instance(
    default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
) -> ProblemInstance:
    return ProblemInstance(default_objectives, default_constraints, default_portfolio)


@pytest.fixture
def default_config() -> Config:
    return Config()


def gen_dummy_site_solution(site: Site) -> SiteSolution:
    site_scenario = {}
    site_range = site.site_range
    for asset_name, asset in site_range.model_dump(exclude_none=True).items():
        if asset_name == "config":
            site_scenario[asset_name] = asset
        elif asset_name in REPEAT_COMPONENTS:
            site_scenario[asset_name] = []
            for i, sub_asset in enumerate(asset):
                sub_asset_instance = choose_random_values_for_asset(sub_asset)
                sub_asset_instance["index_tracker"] = i
                site_scenario[asset_name].append(sub_asset_instance)
        else:
            site_scenario[asset_name] = choose_random_values_for_asset(asset)
    scenario = AnnotatedTaskData.model_validate(site_scenario)

    # construct a pybind SimulationResult and populate a few of the fields
    sim_result = SimulationResult()
    for metric in _METRICS:
        setattr(sim_result.metrics, metric, random.random() * 100)

    for metric in _COMPARISON:
        setattr(sim_result.comparison, metric, random.random() * 100)

    metric_values = simulation_result_to_metric_dict(sim_result)

    return SiteSolution(scenario=scenario, metric_values=metric_values, simulation_result=sim_result)


def choose_random_values_for_asset(asset: asset_t) -> dict[str, value_t]:
    """
    Reduce a SiteRange asset into a TaskData asset by selecting a random element in each list.

    Parameters
    ----------
    asset
        a SiteRange asset containing lists of possible values for parameters

    Returns
    -------
    a TaskData asset with randomly chosen values

    """
    chosen_asset = {}
    asset.pop("COMPONENT_IS_MANDATORY")
    for attribute_name, attribute_value in asset.items():
        if isinstance(attribute_value, list):
            chosen_asset[attribute_name] = random.choice(attribute_value)
        else:
            chosen_asset[attribute_name] = attribute_value
    return chosen_asset


def gen_dummy_portfolio_solution(portfolio: list[Site]) -> PortfolioSolution:
    solution = {}
    site_results = []

    for site in portfolio:
        site_solution = gen_dummy_site_solution(site)
        solution[site.site_data.site_id] = site_solution
        site_results.append(site_solution.simulation_result)

    portfolio_result = aggregate_site_results(site_results)
    metric_values = simulation_result_to_metric_dict(portfolio_result)
    return PortfolioSolution(scenario=solution, metric_values=metric_values, simulation_result=portfolio_result)


def gen_dummy_portfolio_solutions(portfolio: list[Site]) -> list[PortfolioSolution]:
    return [gen_dummy_portfolio_solution(portfolio) for _ in range(10)]


@pytest.fixture
def dummy_site_solution(default_site: Site) -> SiteSolution:
    return gen_dummy_site_solution(default_site)


@pytest.fixture
def dummy_portfolio_solution(default_portfolio: list[Site]) -> PortfolioSolution:
    return gen_dummy_portfolio_solution(default_portfolio)


@pytest.fixture
def dummy_portfolio_solutions(default_portfolio: list[Site]) -> list[PortfolioSolution]:
    return gen_dummy_portfolio_solutions(default_portfolio)


@pytest.fixture
def dummy_optimisation_result(dummy_portfolio_solutions: list[PortfolioSolution]) -> OptimisationResult:
    return OptimisationResult(solutions=dummy_portfolio_solutions, n_evals=999, exec_time=timedelta(seconds=99))
