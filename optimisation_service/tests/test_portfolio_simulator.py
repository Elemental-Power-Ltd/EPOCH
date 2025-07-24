from pathlib import Path

import numpy as np
import pytest
from epoch_simulator import Building, Simulator, TaskData

from app.internal.datamanager import load_epoch_data_from_file
from app.internal.metrics import calculate_carbon_cost, calculate_payback_horizon
from app.internal.portfolio_simulator import PortfolioSimulator, combine_metric_values, simulate_scenario
from app.models.epoch_types.site_range_type import Config
from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import _METRICS, _SUMMABLE_METRICS, Metric, MetricValues
from app.models.result import PortfolioSolution
from tests.conftest import _DATA_PATH


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
        assert all(obj in list(res.keys()) for obj in _METRICS)

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


class TestCombineMetricValues:
    def test_good_inputs(self):
        metric_values: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.carbon_balance_total: 20,
            Metric.meter_balance: 10,
            Metric.operating_balance: 10,
            Metric.cost_balance: 10,
            Metric.npv_balance: 10,
            Metric.carbon_cost: 10,
            Metric.total_gas_used: 10,
            Metric.total_electricity_imported: 10,
            Metric.total_electricity_generated: 10,
            Metric.total_electricity_exported: 10,
            Metric.total_electrical_shortfall: 10,
            Metric.total_heat_shortfall: 10,
            Metric.total_ch_shortfall: 10,
            Metric.total_dhw_shortfall: 10,
            Metric.total_gas_import_cost: 10,
            Metric.total_electricity_import_cost: 10,
            Metric.total_electricity_export_gain: 10,
            Metric.total_meter_cost: 10,
            Metric.total_operating_cost: 10,
            Metric.total_net_present_value: 10,
            Metric.baseline_gas_used: 10,
            Metric.baseline_electricity_imported: 10,
            Metric.baseline_electricity_generated: 10,
            Metric.baseline_electricity_exported: 10,
            Metric.baseline_electrical_shortfall: 10,
            Metric.baseline_heat_shortfall: 10,
            Metric.baseline_ch_shortfall: 10,
            Metric.baseline_dhw_shortfall: 10,
            Metric.baseline_gas_import_cost: 10,
            Metric.baseline_electricity_import_cost: 10,
            Metric.baseline_electricity_export_gain: 10,
            Metric.baseline_meter_cost: 10,
            Metric.baseline_operating_cost: 10,
            Metric.baseline_net_present_value: 10,
        }
        metric_values[Metric.payback_horizon] = calculate_payback_horizon(
            capex=metric_values[Metric.capex], cost_balance=metric_values[Metric.cost_balance]
        )
        metric_values[Metric.carbon_cost] = calculate_carbon_cost(
            capex=metric_values[Metric.capex], carbon_balance_scope_1=metric_values[Metric.carbon_balance_scope_1]
        )
        res = combine_metric_values([metric_values])
        assert res == metric_values
        res = combine_metric_values([metric_values, metric_values])
        # check this test contains every metric
        assert all(obj in list(res.keys()) for obj in _METRICS)
        # check every summable metric is 10 * 2
        for metric in _SUMMABLE_METRICS:
            assert res[metric] == metric_values[metric] * 2
        assert res[Metric.cost_balance] == metric_values[Metric.cost_balance] * 2
        assert res[Metric.payback_horizon] == calculate_payback_horizon(
            capex=metric_values[Metric.capex] * 2, cost_balance=metric_values[Metric.cost_balance] * 2
        )
        assert res[Metric.carbon_cost] == calculate_carbon_cost(
            capex=metric_values[Metric.capex] * 2,
            carbon_balance_scope_1=metric_values[Metric.carbon_balance_scope_1] * 2,
        )

    @pytest.mark.parametrize("carbon_balance_scope_1", [0, -10])
    def test_null_and_negative_carbon_scope_1(self, carbon_balance_scope_1):
        metric_values_1: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: carbon_balance_scope_1,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        metric_values_2: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        res = combine_metric_values([metric_values_1, metric_values_1])
        assert res[Metric.carbon_cost] == float(np.finfo(np.float32).max)
        res = combine_metric_values([metric_values_1, metric_values_2])
        assert res[Metric.carbon_cost] == calculate_carbon_cost(
            capex=metric_values_1[Metric.capex] + metric_values_2[Metric.capex],
            carbon_balance_scope_1=metric_values_1[Metric.carbon_balance_scope_1]
            + metric_values_2[Metric.carbon_balance_scope_1],
        )

    @pytest.mark.parametrize("cost_balance", [0, -10])
    def test_null_and_negative_cost_balance(self, cost_balance):
        metric_values_1: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: cost_balance,
        }
        metric_values_2: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        res = combine_metric_values([metric_values_1, metric_values_1])
        assert res[Metric.payback_horizon] < 0
        res = combine_metric_values([metric_values_1, metric_values_2])
        assert res[Metric.payback_horizon] == calculate_payback_horizon(
            capex=metric_values_1[Metric.capex] + metric_values_2[Metric.capex],
            cost_balance=metric_values_1[Metric.cost_balance] + metric_values_2[Metric.cost_balance],
        )

    @pytest.mark.parametrize("capex", [0, -10])
    def test_null_and_negative_capex(self, capex):
        metric_values_1: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: capex,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        metric_values_2: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        res = combine_metric_values([metric_values_1, metric_values_1])
        assert res[Metric.payback_horizon] == 0
        assert res[Metric.carbon_cost] == 0
        res = combine_metric_values([metric_values_1, metric_values_2])
        assert res[Metric.payback_horizon] == calculate_payback_horizon(
            capex=metric_values_1[Metric.capex] + metric_values_2[Metric.capex],
            cost_balance=metric_values_1[Metric.cost_balance] + metric_values_2[Metric.cost_balance],
        )
        assert res[Metric.carbon_cost] == calculate_carbon_cost(
            capex=metric_values_1[Metric.capex] + metric_values_2[Metric.capex],
            carbon_balance_scope_1=metric_values_1[Metric.carbon_balance_scope_1]
            + metric_values_2[Metric.carbon_balance_scope_1],
        )

    def test_missing_metrics(self):
        metric_values_1: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_1: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        metric_values_no_scope_1: MetricValues = {
            Metric.annualised_cost: 10,
            Metric.capex: 10,
            Metric.carbon_balance_scope_2: 10,
            Metric.cost_balance: 10,
        }
        res = combine_metric_values([metric_values_1, metric_values_no_scope_1])

        # metrics present in both results should be combine-able
        assert Metric.annualised_cost in res
        assert Metric.capex in res
        assert Metric.carbon_balance_scope_2

        # a metric missing from either should not be present
        assert Metric.carbon_balance_scope_1 not in res

        # we can't derive a carbon cost without scope_1 being present in both
        assert Metric.carbon_cost not in res
