from copy import deepcopy

import numpy as np
import pytest

from app.internal.epoch_utils import convert_TaskData_to_dictionary
from app.internal.ga_utils import ProblemInstance, RoundingAndDegenerateRepair, SimpleIntMutation
from app.internal.site_range import SiteRange, count_parameters_to_optimise
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import _METRICS, Metric, MetricValues
from app.models.site_range import Building, Config, DomesticHotWater, Grid, HeatPump, HeatSourceEnum, Renewables, SiteRange

from .conftest import site_generator


class TestProblemInstance:
    def test_init(self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]):
        ProblemInstance(default_objectives, default_constraints, default_portfolio)

    def test_split_solution(self, default_problem_instance: ProblemInstance) -> None:
        splits = {}
        for site in default_problem_instance.portfolio:
            splits[site.name] = np.arange(count_parameters_to_optimise(site.site_range))
        x = np.concatenate(list(splits.values()))
        res = default_problem_instance.split_solution(x)
        assert [x == y for x, y in zip(splits, res)]

    @pytest.mark.parametrize("x_value", [0, 1])
    def test_convert_solution(self, x_value: int, default_problem_instance: ProblemInstance) -> None:
        for site in default_problem_instance.portfolio:
            x = np.array([x_value] * count_parameters_to_optimise(site.site_range))
            res = default_problem_instance.convert_solution(x, site.name)
            td_dict = convert_TaskData_to_dictionary(res)
            for asset_name, asset in site.site_range.model_dump(exclude_none=True).items():
                if not x_value and asset_name != "config" and not asset["COMPONENT_IS_MANDATORY"]:
                    assert asset_name not in td_dict.keys()
                else:
                    assert asset_name in td_dict.keys()

    @pytest.mark.parametrize("x_value", [0, 1])
    def test_simulate_portfolio(self, x_value: int, default_problem_instance: ProblemInstance) -> None:
        portfolio = default_problem_instance.portfolio
        x = np.array([x_value] * sum(count_parameters_to_optimise(site.site_range) for site in portfolio))
        res = default_problem_instance.simulate_portfolio(x)
        for site in portfolio:
            td_dict = convert_TaskData_to_dictionary(res.scenario[site.name].scenario)
            for asset_name, asset in site.site_range.model_dump(exclude_none=True).items():
                if not x_value and asset_name != "config" and not asset["COMPONENT_IS_MANDATORY"]:
                    assert asset_name not in td_dict.keys()
                else:
                    assert asset_name in td_dict.keys()

    def test_apply_directions(self, default_problem_instance: ProblemInstance):
        metric_values: MetricValues = dict.fromkeys(_METRICS, 10)
        res = default_problem_instance.apply_directions(deepcopy(metric_values))
        assert res[Metric.annualised_cost] == metric_values[Metric.annualised_cost]
        assert res[Metric.capex] == metric_values[Metric.capex]
        assert res[Metric.carbon_cost] == metric_values[Metric.carbon_cost]
        assert res[Metric.payback_horizon] == metric_values[Metric.payback_horizon]
        assert res[Metric.carbon_balance_scope_1] == -metric_values[Metric.carbon_balance_scope_1]
        assert res[Metric.carbon_balance_scope_2] == -metric_values[Metric.carbon_balance_scope_2]
        assert res[Metric.cost_balance] == -metric_values[Metric.cost_balance]

    def test_calculate_infeasibility(self, default_problem_instance: ProblemInstance):
        constraints = default_problem_instance.constraints
        metric_values: MetricValues = dict.fromkeys(_METRICS, 10)
        excess = []
        for metric, bounds in constraints.items():
            min_value = bounds.get("min", None)
            max_value = bounds.get("max", None)

            if min_value is not None:
                metric_values[metric] = min_value - 1
                excess.append(1)
            if max_value is not None:
                metric_values[metric] = max_value + 1
                excess.append(1)

        assert default_problem_instance.calculate_infeasibility(metric_values) == excess


class TestSimpleIntMutation:
    def test_mut_simple_int_works(self):
        """
        Test mut_simple_int works with good inputs.
        """
        X = np.array([[1, 1], [2, 2], [0, 2]])
        xl = np.array([0, 0])
        xu = np.array([2, 2])
        prob = np.array([1, 0.5, 0])
        Xp = SimpleIntMutation.mut_simple_int(X, xl, xu, prob)
        assert np.min(Xp) >= 0
        assert np.max(Xp) <= 2
        assert not np.array_equal(X, Xp)


class TestRoundingAndDegenerateRepair:
    def test_rounding(self, default_objectives: list[Metric], default_constraints: Constraints):
        building = Building(
            COMPONENT_IS_MANDATORY=True, scalar_heat_load=[1], scalar_electrical_load=[1], fabric_intervention_index=[0]
        )
        domestic_hot_water = DomesticHotWater(COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200])
        grid = Grid(
            COMPONENT_IS_MANDATORY=True,
            export_headroom=[0.5],
            grid_export=[60],
            grid_import=[60],
            import_headroom=[0.5],
            min_power_factor=[1],
            tariff_index=[0, 1, 2, 3],
        )
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=False, heat_power=[100, 200], heat_source=[HeatSourceEnum.AMBIENT_AIR], send_temp=[70]
        )
        config = Config(capex_limit=99999999999)
        site_range = SiteRange(
            building=building, domestic_hot_water=domestic_hot_water, grid=grid, heat_pump=heat_pump, config=config
        )
        portfolio = [site_generator("amcott_house", site_range)]
        pi = ProblemInstance(default_objectives, default_constraints, portfolio)

        rdr = RoundingAndDegenerateRepair()

        X = np.array([[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 1, 0, 1, 0]])

        res = rdr._do(pi, X)
        assert res.dtype == int
        assert res.shape == X.shape

    def test_degeneracy(self, default_objectives: list[Metric], default_constraints: Constraints):
        building = Building(
            COMPONENT_IS_MANDATORY=True, scalar_heat_load=[1], scalar_electrical_load=[1], fabric_intervention_index=[0]
        )
        domestic_hot_water = DomesticHotWater(COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200])
        grid = Grid(
            COMPONENT_IS_MANDATORY=True,
            export_headroom=[0.5],
            grid_export=[60],
            grid_import=[60],
            import_headroom=[0.5],
            min_power_factor=[1],
            tariff_index=[0, 1, 2, 3],
        )
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=False, heat_power=[100, 200], heat_source=[HeatSourceEnum.AMBIENT_AIR], send_temp=[70]
        )
        config = Config(capex_limit=99999999999)
        site_range = SiteRange(
            building=building, domestic_hot_water=domestic_hot_water, grid=grid, heat_pump=heat_pump, config=config
        )
        portfolio = [site_generator("amcott_house", site_range)]
        pi = ProblemInstance(default_objectives, default_constraints, portfolio)

        rdr = RoundingAndDegenerateRepair()

        X = np.array([[0, 1, 1, 1, 1], [1, 0, 1, 1, 1], [1, 1, 0, 1, 1], [1, 1, 1, 0, 1], [1, 1, 1, 1, 0]])

        res = rdr._do(pi, X)
        assert res.shape == X.shape
        assert all(res == np.array([[0, 0, 1, 1, 1], [1, 0, 1, 1, 1], [1, 1, 0, 1, 1], [1, 1, 1, 0, 0], [1, 1, 1, 1, 0]]))

    def test_degeneracy_with_renewables(self, default_objectives: list[Metric], default_constraints: Constraints):
        building = Building(
            COMPONENT_IS_MANDATORY=True, scalar_heat_load=[1], scalar_electrical_load=[1], fabric_intervention_index=[0, 1]
        )
        domestic_hot_water = DomesticHotWater(COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200])
        grid = Grid(
            COMPONENT_IS_MANDATORY=True,
            export_headroom=[0.5],
            grid_export=[60],
            grid_import=[60],
            import_headroom=[0.5],
            min_power_factor=[1],
            tariff_index=[0, 1, 2, 3],
        )
        config = Config(capex_limit=99999999999)
        renewables = Renewables(COMPONENT_IS_MANDATORY=False, yield_scalars=[[100, 200]])
        site_range = SiteRange(
            building=building,
            domestic_hot_water=domestic_hot_water,
            grid=grid,
            config=config,
            renewables=renewables,
        )
        portfolio = [site_generator("amcott_house", site_range)]
        pi = ProblemInstance(default_objectives, default_constraints, portfolio)

        rdr = RoundingAndDegenerateRepair()

        X = np.array(
            [
                [0, 1, 1, 1, 1, 1],
                [1, 0, 1, 1, 1, 1],
                [1, 1, 0, 1, 1, 1],
                [1, 1, 1, 0, 1, 1],
                [1, 1, 1, 1, 0, 1],
                [1, 1, 1, 1, 1, 0],
            ]
        )

        res = rdr._do(pi, X)
        assert res.shape == X.shape
        assert (
            res
            == np.array(
                [
                    [0, 0, 1, 1, 1, 1],
                    [1, 0, 1, 1, 1, 1],
                    [1, 1, 0, 1, 1, 1],
                    [1, 1, 1, 0, 0, 1],
                    [1, 1, 1, 1, 0, 1],
                    [1, 1, 1, 1, 1, 0],
                ]
            )
        ).all
