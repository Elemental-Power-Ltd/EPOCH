import copy
from pathlib import Path

import pytest
from epoch_simulator import Building, Simulator, TaskData

from app.internal.epoch.converters import simulation_result_to_metric_dict
from app.internal.portfolio_simulator import PortfolioSimulator, simulate_scenario
from app.models.epoch_types.site_range_type import Config
from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import _METRICS
from app.models.result import PortfolioSolution
from app.models.site_data import EpochSiteData
from tests.conftest import _DATA_PATH

from .conftest import load_epoch_data_from_file


class TestPortfolioSimulator:
    def test_init(self, default_config: Config) -> None:
        epoch_data_ah = load_epoch_data_from_file(Path(_DATA_PATH, "amcott_house", "epoch_data.json"))
        epoch_data_blc = load_epoch_data_from_file(Path(_DATA_PATH, "bircotes_leisure_centre", "epoch_data.json"))
        PortfolioSimulator(
            epoch_data_dict={
                "amcott_house": epoch_data_ah,
                "bircotes_leisure_centre": epoch_data_blc,
            },
            epoch_config_dict={
                "amcott_house": default_config,
                "bircotes_leisure_centre": default_config,
            },
        )

    def test_simulate_portfolio(self, default_config: Config) -> None:
        epoch_data_ah = load_epoch_data_from_file(Path(_DATA_PATH, "amcott_house", "epoch_data.json"))
        epoch_data_blc = load_epoch_data_from_file(Path(_DATA_PATH, "bircotes_leisure_centre", "epoch_data.json"))
        ps = PortfolioSimulator(
            epoch_data_dict={
                "amcott_house": epoch_data_ah,
                "bircotes_leisure_centre": epoch_data_blc,
            },
            epoch_config_dict={
                "amcott_house": default_config,
                "bircotes_leisure_centre": default_config,
            },
        )
        atd = AnnotatedTaskData.model_validate_json(TaskData().to_json())
        portfolio_scenarios = {"amcott_house": atd, "bircotes_leisure_centre": atd}
        portfolio_solution = ps.simulate_portfolio(portfolio_scenarios)
        assert isinstance(portfolio_solution, PortfolioSolution)
        assert all(site_name in list(portfolio_solution.scenario.keys()) for site_name in portfolio_scenarios.keys())
        assert all(obj in list(portfolio_solution.metric_values.keys()) for obj in _METRICS)


class TestSimulateScenario:
    def test_good_inputs(self, default_config: Config) -> None:
        site_name = "amcott_house"
        epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site_name, "epoch_data.json"))
        sim = Simulator.from_json(epoch_data.model_dump_json(), default_config.model_dump_json())
        site_scenario = TaskData()
        res = simulate_scenario(sim, site_name, site_scenario)
        metrics = simulation_result_to_metric_dict(res)
        assert all(obj in list(metrics.keys()) for obj in _METRICS)

    def test_caching(self, default_config: Config) -> None:
        site_name = "amcott_house"
        epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site_name, "epoch_data.json"))
        sim = Simulator.from_json(epoch_data.model_dump_json(), default_config.model_dump_json())
        building_1 = Building()
        site_scenario = TaskData()
        site_scenario.building = building_1
        site_scenario_1a = site_scenario_1b = site_scenario

        simulate_scenario.cache_clear()

        res_1a = simulate_scenario(sim, site_name, site_scenario_1a)
        assert simulate_scenario.cache_info().misses == 1

        res_2a = simulate_scenario(sim, site_name, site_scenario_1b)
        assert res_1a == res_2a
        assert simulate_scenario.cache_info().hits == 1

        site_scenario_2 = site_scenario
        site_scenario_2.building.scalar_electrical_load = 2.0

        res_2 = simulate_scenario(sim, site_name, site_scenario_2)
        assert res_2 != res_1a
        assert simulate_scenario.cache_info().hits == 1
        assert simulate_scenario.cache_info().misses == 2
        assert simulate_scenario.cache_info().currsize == 2


class TestIsCopiable:
    @pytest.fixture
    def epoch_data_ah(self) -> EpochSiteData:
        return load_epoch_data_from_file(Path(_DATA_PATH, "amcott_house", "epoch_data.json"))

    def test_shallow_copy(self, default_config: Config, epoch_data_ah: EpochSiteData) -> None:
        """Test that we can shallow copy a simulator."""
        orig = PortfolioSimulator(
            epoch_data_dict={
                "amcott_house": epoch_data_ah,
            },
            epoch_config_dict={
                "amcott_house": default_config,
            },
        )
        # This should fail if we've got it wrong
        copy.copy(orig)

    def test_deep_copy(self, default_config: Config, epoch_data_ah: EpochSiteData) -> None:
        """Test that we can deepcopy a simulator and have it be unchanged."""
        orig = PortfolioSimulator(
            epoch_data_dict={
                "amcott_house": epoch_data_ah,
            },
            epoch_config_dict={
                "amcott_house": default_config,
            },
        )
        # This should fail if we've got it wrong
        copy.deepcopy(orig)
