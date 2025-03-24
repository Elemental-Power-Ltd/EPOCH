import numpy as np
import pytest
import torch
from epoch_simulator import TaskData

from app.internal.bayesian.bayesian import (
    _TKWARGS,
    Bayesian,
    convert_solution_list_to_tensor,
    create_capex_allocation_bounds,
    create_reference_point,
    extract_sub_portfolio_capex_allocations,
    generate_random_capex_allocations,
    initialise_model,
    optimize_acquisition_func_and_get_candidate,
)
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.result import OptimisationResult, PortfolioSolution, SiteSolution


class TestBayesian:
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
        alg = Bayesian(pop_size=512, n_offsprings=256, n_max_gen=50, n_generations=20, period=10)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)


class TestCreateReferencePoint:
    def test_good_inputs(self, default_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]):
        n_sub_portfolios = len(default_portfolio_solutions[0].scenario)
        _, train_y = convert_solution_list_to_tensor(
            solutions=default_portfolio_solutions,
            n_per_sub_portfolio=1,
            n_sub_portfolios=n_sub_portfolios,
            objectives=default_objectives,
        )
        ref_point = create_reference_point(train_y)
        assert len(ref_point) == train_y.shape[1]


class TestCreateCapexAllocationBounds:
    def test_good_inputs(self):
        capex_limit = 10000
        n_sub_portfolios = 2
        bounds = create_capex_allocation_bounds(n_sub_portfolios, capex_limit)
        assert bounds.shape == (2, n_sub_portfolios - 1)
        assert bounds[0].sum() == 0
        assert bounds[1].sum() == capex_limit * (n_sub_portfolios - 1)


class TestInitializeModel:
    def test_good_inputs(self, default_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]):
        capex_limit = 10000
        n_sub_portfolios = len(default_portfolio_solutions[0].scenario)
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=default_portfolio_solutions,
            n_per_sub_portfolio=1,
            n_sub_portfolios=n_sub_portfolios,
            objectives=default_objectives,
        )
        bounds = create_capex_allocation_bounds(n_sub_portfolios, capex_limit)
        initialise_model(train_x, train_y, bounds)


class TestGenerateRandomCapexAllocations:
    def test_good_inputs(self):
        n_portfolios = 2
        n_initial = 4
        capex_limit = 10000
        capex_allocations = generate_random_capex_allocations(
            n_portfolios=n_portfolios, n_initial=n_initial, capex_limit=capex_limit
        )
        assert capex_allocations.shape == (n_initial, n_portfolios)
        assert all(np.isclose(np.sum(capex_allocations, axis=1), capex_limit))


class TestOptimizeAcquisitionFuncAndGetCandidate:
    def test_good_inputs(self, default_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]):
        capex_limit = 10000
        batch_size = 2
        n_sub_portfolios = len(default_portfolio_solutions[0].scenario)
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=default_portfolio_solutions,
            n_per_sub_portfolio=1,
            n_sub_portfolios=n_sub_portfolios,
            objectives=default_objectives,
        )
        bounds = create_capex_allocation_bounds(n_sub_portfolios, capex_limit)
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
            n_sub_portfolios=n_sub_portfolios,
            num_restarts=2,
            raw_samples=2,
        )
        assert candidates_arr.shape[0] == batch_size
        assert candidates_arr.shape[1] == n_sub_portfolios


class TestExtractSubPortfolioCapexAllocations:
    def test_good_inputs(self):
        n_sub_portfolios = 3
        n_per_sub_portfolio = 2
        capex_a, capex_b, capex_c, capex_d, capex_e = 10, 20, 30, 40, 50
        solution = PortfolioSolution(
            scenario={
                "a": SiteSolution(TaskData, {"capex": capex_a}),
                "b": SiteSolution(TaskData, {"capex": capex_b}),
                "c": SiteSolution(TaskData, {"capex": capex_c}),
                "d": SiteSolution(TaskData, {"capex": capex_d}),
                "e": SiteSolution(TaskData, {"capex": capex_e}),
            },
            metric_values={},
        )
        capex_allocations = extract_sub_portfolio_capex_allocations(solution, n_per_sub_portfolio, n_sub_portfolios)
        assert capex_allocations == [capex_a + capex_b, capex_c + capex_d]


class TestConvertSolutionListToTensor:
    def test_good_inputs(self):
        n_sub_portfolios = 3
        n_per_sub_portfolio = 2
        capex_a, capex_b, capex_c, capex_d, capex_e = 10, 20, 30, 40, 50
        objectives = [Metric.cost_balance, Metric.carbon_balance_scope_1]
        cost_balance = 99
        carbon_balance_scope_1 = 66
        solution = PortfolioSolution(
            scenario={
                "a": SiteSolution(TaskData, {"capex": capex_a}),
                "b": SiteSolution(TaskData, {"capex": capex_b}),
                "c": SiteSolution(TaskData, {"capex": capex_c}),
                "d": SiteSolution(TaskData, {"capex": capex_d}),
                "e": SiteSolution(TaskData, {"capex": capex_e}),
            },
            metric_values={Metric.cost_balance: cost_balance, Metric.carbon_balance_scope_1: carbon_balance_scope_1},
        )
        train_x, train_y = convert_solution_list_to_tensor([solution], n_per_sub_portfolio, n_sub_portfolios, objectives)
        assert all(train_x[0] == torch.tensor([capex_a + capex_b, capex_c + capex_d], **_TKWARGS))
        assert all(train_y[0] == torch.tensor([cost_balance, carbon_balance_scope_1], **_TKWARGS))

    def test_good_inputs_2(self, default_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]):
        n_sub_portfolios = len(default_portfolio_solutions[0].scenario)
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=default_portfolio_solutions,
            n_per_sub_portfolio=1,
            n_sub_portfolios=n_sub_portfolios,
            objectives=default_objectives,
        )
        assert len(train_x) == len(train_y)
        assert train_x.dim() == 2
        assert train_y.dim() == 2
