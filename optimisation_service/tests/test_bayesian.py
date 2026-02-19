import pytest
import torch
from app.internal.bayesian.bayesian import (
    Bayesian,
    convert_solution_list_to_tensor,
    create_capex_allocation_bounds,
    generate_random_candidates,
    optimize_acquisition_func_and_get_candidate,
)
from app.internal.bayesian.common import _TKWARGS, create_reference_point, initialise_model, split_into_sub_portfolios
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import Metric
from app.models.optimisers import NSGA2HyperParam
from app.models.result import OptimisationResult, PortfolioSolution, SiteSolution
from epoch_simulator import SimulationResult


class TestBayesianResearch:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        Bayesian()

    @pytest.mark.slow
    def test_run(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = Bayesian(n_generations=2, NSGA2_param=NSGA2HyperParam(pop_size=512, n_offsprings=256, n_max_gen=2, period=10))
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)


class TestCreateCapexAllocationBounds:
    def test_good_inputs(self) -> None:
        max_capexs = [1000.0, 500.0]
        min_capexs = [0.0] * len(max_capexs)
        bounds = create_capex_allocation_bounds(min_capexs, max_capexs)
        assert bounds.shape == (2, len(max_capexs))
        assert bounds[0].sum() == 0
        assert all(bounds[1] == torch.tensor(max_capexs, **_TKWARGS))


class TestOptimizeAcquisitionFuncAndGetCandidate:
    def test_good_inputs(
        self,
        default_portfolio: list[Site],
        dummy_portfolio_solutions: list[PortfolioSolution],
        default_objectives: list[Metric],
    ) -> None:
        capex_limit = 10000
        max_capexs = [1000.0, 500.0]
        min_capexs = [0.0] * len(max_capexs)
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        sub_portfolio_site_ids = [[site.site_data.site_id for site in portfolio] for portfolio in sub_portfolios]
        batch_size = 2
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=dummy_portfolio_solutions,
            sub_portfolio_site_ids=sub_portfolio_site_ids,
            objectives=default_objectives,
        )
        bounds = create_capex_allocation_bounds(min_capexs, max_capexs)
        ref_point = create_reference_point(train_y)
        _, model = initialise_model(train_x, train_y, bounds)
        candidates_arr = optimize_acquisition_func_and_get_candidate(
            model=model,
            train_x=train_x,
            mc_samples=2,
            ref_point=ref_point,
            bounds=bounds,
            batch_size=batch_size,
            capex_limit=capex_limit,
            num_restarts=2,
            raw_samples=2,
        )
        assert candidates_arr.shape[0] == batch_size
        assert candidates_arr.shape[1] == len(sub_portfolios)


class TestConvertSolutionListToTensor:
    def test_good_inputs(self) -> None:
        capex_a, capex_b, capex_c, capex_d, capex_e = 10, 20, 30, 40, 50
        objectives = [Metric.cost_balance, Metric.carbon_balance_scope_1]
        sub_portfolio_site_ids = [["a", "b"], ["c", "d"], ["e"]]
        cost_balance = 99
        carbon_balance_scope_1 = 66
        solution = PortfolioSolution(
            scenario={
                "a": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_a}, SimulationResult()),
                "b": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_b}, SimulationResult()),
                "c": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_c}, SimulationResult()),
                "d": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_d}, SimulationResult()),
                "e": SiteSolution(AnnotatedTaskData(), {Metric.capex: capex_e}, SimulationResult()),
            },
            metric_values={Metric.cost_balance: cost_balance, Metric.carbon_balance_scope_1: carbon_balance_scope_1},
            simulation_result=SimulationResult(),
        )
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=[solution], sub_portfolio_site_ids=sub_portfolio_site_ids, objectives=objectives
        )
        assert all(train_x[0] == torch.tensor([capex_a + capex_b, capex_c + capex_d, capex_e], **_TKWARGS))
        assert all(train_y[0] == torch.tensor([cost_balance, carbon_balance_scope_1], **_TKWARGS))

    def test_good_inputs_2(self, dummy_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]) -> None:
        sub_portfolio_site_ids = [[site_id] for site_id in dummy_portfolio_solutions[0].scenario.keys()]
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=dummy_portfolio_solutions,
            sub_portfolio_site_ids=sub_portfolio_site_ids,
            objectives=default_objectives,
        )
        assert len(train_x) == len(train_y)
        assert train_x.dim() == 2
        assert train_y.dim() == 2


class TestGenerateRandomCandidates:
    def test_good_inputs(self) -> None:
        n = 10
        max_capexs = [100.0, 200.0, 50.0]
        capex_limit = 150.0
        res = generate_random_candidates(n=n, max_capexs=max_capexs, capex_limit=capex_limit)
        assert res.shape == (n, len(max_capexs))
        assert all(sum(candidate) <= capex_limit for candidate in res)
        assert all(all(candidate <= max_capexs) for candidate in res)
