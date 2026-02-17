from app.internal.bayesian.common import extract_sub_portfolio_capex_allocations, initialise_model
from app.internal.bayesian.research_algorithm import convert_solution_list_to_tensor, create_capex_allocation_bounds
from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import Metric
from app.models.result import PortfolioSolution, SiteSolution

from epoch_simulator import SimulationResult


class TestInitializeModel:
    def test_good_inputs(self, dummy_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]) -> None:
        sub_portfolio_site_ids = [[site_id] for site_id in dummy_portfolio_solutions[0].scenario.keys()]
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=dummy_portfolio_solutions,
            sub_portfolio_site_ids=sub_portfolio_site_ids,
            objectives=default_objectives,
        )
        max_capexs = [1000.0, 500.0]
        min_capexs = [0.0] * len(max_capexs)
        bounds = create_capex_allocation_bounds(min_capexs, max_capexs)
        initialise_model(train_x, train_y, bounds)


class TestExtractSubPortfolioCapexAllocations:
    def test_good_inputs(self) -> None:
        sub_portfolio_site_ids = [["a", "b"], ["c", "d"], ["e"]]
        capex_a, capex_b, capex_c, capex_d, capex_e = 10, 20, 30, 40, 50
        solution = PortfolioSolution(
            scenario={
                "a": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_a}, SimulationResult()),
                "b": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_b}, SimulationResult()),
                "c": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_c}, SimulationResult()),
                "d": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_d}, SimulationResult()),
                "e": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_e}, SimulationResult()),
            },
            metric_values={},
            simulation_result=SimulationResult(),
        )
        capex_allocations = extract_sub_portfolio_capex_allocations(solution, sub_portfolio_site_ids)
        assert capex_allocations == [capex_a + capex_b, capex_c + capex_d, capex_e]
