from copy import deepcopy

import numpy as np
import pytest

from app.internal.constraints import count_constraints
from app.internal.ga_utils import (
    ProblemInstance,
    RoundingAndDegenerateRepair,
    SimpleIntMutation,
    evaluate_constraints,
    evaluate_peak_hload,
)
from app.internal.site_range import REPEAT_COMPONENTS, count_parameters_to_optimise
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.epoch_types.site_range_type import (
    Building as BuildingRange,
)
from app.models.epoch_types.site_range_type import (
    Config as ConfigRange,
)
from app.models.epoch_types.site_range_type import (
    DomesticHotWater as DomesticHotWaterRange,
)
from app.models.epoch_types.site_range_type import (
    Grid as GridRange,
)
from app.models.epoch_types.site_range_type import (
    HeatPump as HeatPumpRange,
)
from app.models.epoch_types.site_range_type import (
    HeatSourceEnum as HeatSourceEnumRange,
)
from app.models.epoch_types.site_range_type import (
    SiteRange,
)
from app.models.epoch_types.site_range_type import (
    SolarPanel as SolarPanelRange,
)
from app.models.epoch_types.task_data_type import Building, GasHeater, HeatPump
from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import _METRICS, _OBJECTIVES, Metric, MetricValues
from app.models.result import PortfolioSolution, SiteSolution
from app.models.site_data import EpochSiteData

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
    def test_convert_chromosome_to_site_scenario(self, x_value: int, default_problem_instance: ProblemInstance) -> None:
        for site in default_problem_instance.portfolio:
            x = np.array([x_value] * count_parameters_to_optimise(site.site_range))
            td_pydantic = default_problem_instance.convert_chromosome_to_site_scenario(x, site.name)
            for asset_name, asset in site.site_range.model_dump(exclude_none=True).items():
                if asset_name == "config":
                    pass
                elif asset_name in REPEAT_COMPONENTS:
                    # for repeat components, we count how many subcomponents we expect to find then check this matches
                    repeat_count = 0
                    for sub_asset in asset:
                        if x_value or sub_asset["COMPONENT_IS_MANDATORY"]:
                            repeat_count += 1
                    assert (hasattr(td_pydantic, asset_name) and len(getattr(td_pydantic, asset_name)) == repeat_count) or (
                        repeat_count == 0 and not hasattr(td_pydantic, asset_name)
                    )
                else:
                    # for singleton components, we check whether the component should be present or not
                    if not x_value and not asset["COMPONENT_IS_MANDATORY"]:
                        assert not hasattr(td_pydantic, asset_name) or getattr(td_pydantic, asset_name) is None
                    else:
                        assert hasattr(td_pydantic, asset_name)

    @pytest.mark.parametrize("x_value", [0, 1])
    def test_convert_site_scenario_to_chromosome(self, x_value: int, default_problem_instance: ProblemInstance):
        for site in default_problem_instance.portfolio:
            x = np.array([x_value] * count_parameters_to_optimise(site.site_range))
            site_scenario = default_problem_instance.convert_chromosome_to_site_scenario(x, site.name)
            chromosome = default_problem_instance.convert_site_scenario_to_chromosome(site_scenario, site.name)
            assert all(chromosome == x)

    @pytest.mark.parametrize("x_value", [0, 1])
    def test_simulate_portfolio(self, x_value: int, default_problem_instance: ProblemInstance) -> None:
        portfolio = default_problem_instance.portfolio
        x = np.array([x_value] * sum(count_parameters_to_optimise(site.site_range) for site in portfolio))
        res = default_problem_instance.simulate_portfolio(x)
        for site in portfolio:
            td_pydantic: AnnotatedTaskData = res.scenario[site.name].scenario
            for asset_name, asset in site.site_range.model_dump(exclude_none=True).items():
                if asset_name == "config":
                    pass
                elif asset_name in REPEAT_COMPONENTS:
                    repeat_count = 0
                    for sub_asset in asset:
                        if x_value or sub_asset["COMPONENT_IS_MANDATORY"]:
                            repeat_count += 1
                    assert (hasattr(td_pydantic, asset_name) and len(getattr(td_pydantic, asset_name)) == repeat_count) or (
                        repeat_count == 0 and not hasattr(td_pydantic, asset_name)
                    )
                else:
                    if not x_value and not asset["COMPONENT_IS_MANDATORY"]:
                        assert not hasattr(td_pydantic, asset_name) or getattr(td_pydantic, asset_name) is None
                    else:
                        assert hasattr(td_pydantic, asset_name)

    def test_apply_directions(self, default_problem_instance: ProblemInstance):
        metric_values: MetricValues = dict.fromkeys(_OBJECTIVES, 10)
        res = default_problem_instance.apply_directions(deepcopy(metric_values))
        assert res[Metric.annualised_cost] == metric_values[Metric.annualised_cost]
        assert res[Metric.capex] == metric_values[Metric.capex]
        assert res[Metric.carbon_cost] == metric_values[Metric.carbon_cost]
        assert res[Metric.payback_horizon] == metric_values[Metric.payback_horizon]
        assert res[Metric.carbon_balance_scope_1] == -metric_values[Metric.carbon_balance_scope_1]
        assert res[Metric.carbon_balance_scope_2] == -metric_values[Metric.carbon_balance_scope_2]
        assert res[Metric.cost_balance] == -metric_values[Metric.cost_balance]

    def test_evaluate_constraint_violations(
        self, default_problem_instance: ProblemInstance, dummy_portfolio_solution: PortfolioSolution
    ):
        n_constraints = count_constraints(default_problem_instance.constraints)
        for site in default_problem_instance.portfolio:
            n_constraints += count_constraints(site.constraints)

        assert len(default_problem_instance.evaluate_constraint_violations(dummy_portfolio_solution)) == n_constraints


class TestEvaluateExcess:
    def test_it_works(self, default_constraints: Constraints):
        metric_values: MetricValues = dict.fromkeys(_METRICS, 10)

        excess = []
        for metric, bounds in default_constraints.items():
            min_value = bounds.get("min", None)
            max_value = bounds.get("max", None)

            if min_value is not None and max_value is not None:
                metric_values[metric] = min_value - 1
                excess.append(1.0)
                excess.append(-max_value)
            elif min_value is not None:
                metric_values[metric] = min_value - 1
                excess.append(1.0)
            elif max_value is not None:
                metric_values[metric] = max_value + 1
                excess.append(1.0)

        assert evaluate_constraints(metric_values=metric_values, constraints=default_constraints) == excess


class TestEvaluatePeakHload:
    def test_it_works(self, default_epoch_data: EpochSiteData, dummy_site_solution: SiteSolution):
        evaluate_peak_hload(site_scenario=dummy_site_solution.scenario, site_data=default_epoch_data)

    def test_undersized_heat_pump(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()

        peak_hload = default_epoch_data.peak_hload

        scenario.heat_pump = HeatPump(heat_power=peak_hload - 1)

        assert evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data) == 1

    def test_undersized_gas_heater(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()

        peak_hload = default_epoch_data.peak_hload

        scenario.gas_heater = GasHeater(maximum_output=peak_hload - 1)

        assert evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data) == 1

    def test_undersized_gas_heater_and_heat_pump(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()

        peak_hload = default_epoch_data.peak_hload

        scenario.gas_heater = GasHeater(maximum_output=peak_hload / 2 - 1)
        scenario.heat_pump = HeatPump(heat_power=peak_hload / 2 - 1)

        assert evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data) == 2

    def test_oversized_heat_pump(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()

        peak_hload = default_epoch_data.peak_hload

        scenario.heat_pump = HeatPump(heat_power=peak_hload + 1)

        assert evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data) == -1

    def test_oversized_gas_heater(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()

        peak_hload = default_epoch_data.peak_hload

        scenario.gas_heater = GasHeater(maximum_output=peak_hload + 1)

        assert evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data) == -1

    def test_oversized_gas_heater_and_heat_pump(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()

        peak_hload = default_epoch_data.peak_hload

        scenario.gas_heater = GasHeater(maximum_output=peak_hload / 2 + 1)
        scenario.heat_pump = HeatPump(heat_power=peak_hload / 2 + 1)

        assert evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data) == -2

    def test_fabric_intervention_peak_hload(self, default_epoch_data: EpochSiteData):
        scenario = AnnotatedTaskData()
        scenario.building = Building()
        scenario.heat_pump = HeatPump(heat_power=50)

        scenario.building.fabric_intervention_index = 1
        res_w_fabric = evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data)

        scenario.building.fabric_intervention_index = 0
        res_wo_fabric = evaluate_peak_hload(site_scenario=scenario, site_data=default_epoch_data)
        assert res_w_fabric <= res_wo_fabric


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
        building = BuildingRange(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1],
            scalar_electrical_load=[1],
            fabric_intervention_index=[0],
            incumbent=False,
            age=0,
            lifetime=30,
        )
        domestic_hot_water = DomesticHotWaterRange(
            COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200], incumbent=False, age=0, lifetime=12
        )
        grid = GridRange(
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
        heat_pump = HeatPumpRange(
            COMPONENT_IS_MANDATORY=False,
            heat_power=[100, 200],
            heat_source=[HeatSourceEnumRange.AMBIENT_AIR],
            send_temp=[70],
            incumbent=False,
            age=0,
            lifetime=10,
        )
        config = ConfigRange(
            capex_limit=99999999999,
            use_boiler_upgrade_scheme=False,
            general_grant_funding=0,
            npv_time_horizon=10,
            npv_discount_factor=0.0,
        )
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
        building = BuildingRange(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1],
            scalar_electrical_load=[1],
            fabric_intervention_index=[0],
            incumbent=False,
            age=0,
            lifetime=30,
        )
        domestic_hot_water = DomesticHotWaterRange(
            COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200], incumbent=False, age=0, lifetime=12
        )
        grid = GridRange(
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
        heat_pump = HeatPumpRange(
            COMPONENT_IS_MANDATORY=False,
            heat_power=[100, 200],
            heat_source=[HeatSourceEnumRange.AMBIENT_AIR],
            send_temp=[70],
            incumbent=False,
            age=0,
            lifetime=10,
        )
        config = ConfigRange(
            capex_limit=99999999999,
            use_boiler_upgrade_scheme=False,
            general_grant_funding=0,
            npv_time_horizon=10,
            npv_discount_factor=0.0,
        )
        site_range = SiteRange(
            building=building, domestic_hot_water=domestic_hot_water, grid=grid, heat_pump=heat_pump, config=config
        )
        portfolio = [site_generator("amcott_house", site_range)]
        pi = ProblemInstance(default_objectives, default_constraints, portfolio)

        rdr = RoundingAndDegenerateRepair()

        X = np.array([[0, 1, 1, 1, 1], [1, 0, 1, 1, 1], [1, 1, 0, 1, 1], [1, 1, 1, 0, 1], [1, 1, 1, 1, 0]])

        res = rdr._do(pi, X)
        assert res.shape == X.shape
        assert (res == np.array([[0, 0, 1, 1, 1], [1, 0, 1, 1, 1], [1, 1, 0, 1, 1], [1, 1, 1, 0, 0], [1, 1, 1, 1, 0]])).all

    def test_degeneracy_with_renewables(self, default_objectives: list[Metric], default_constraints: Constraints):
        building = BuildingRange(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1],
            scalar_electrical_load=[1],
            fabric_intervention_index=[0, 1],
            incumbent=False,
            age=0,
            lifetime=30,
        )
        domestic_hot_water = DomesticHotWaterRange(
            COMPONENT_IS_MANDATORY=False, cylinder_volume=[100, 200], incumbent=False, age=0, lifetime=12
        )
        grid = GridRange(
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
        config = ConfigRange(capex_limit=99999999999, use_boiler_upgrade_scheme=False, general_grant_funding=0)
        panel = SolarPanelRange(
            COMPONENT_IS_MANDATORY=False, yield_scalar=[100, 200], yield_index=[0], incumbent=False, age=0, lifetime=25
        )

        site_range = SiteRange(
            building=building,
            domestic_hot_water=domestic_hot_water,
            grid=grid,
            config=config,
            solar_panels=[panel],
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
