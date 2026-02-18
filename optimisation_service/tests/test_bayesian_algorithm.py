import numpy as np
import pytest
import torch
from app.internal.bayesian import Bayesian
from app.internal.bayesian.algorithm import (
    create_capex_bounds,
    create_inequality_constraints,
    create_objective_weight_bounds,
    generate_random_candidates,
    optimize_acquisition_func_and_get_candidate,
    split_candidate_capexs_and_weights,
)
from app.internal.bayesian.common import create_reference_point, initialise_model
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.optimisers import NSGA2HyperParam
from app.models.result import OptimisationResult, PortfolioSolution


class TestGenerateRandomCandidates:
    def test_good_inputs(self) -> None:
        n = 2
        n_sub_portfolios = 2
        n_objectives = 2
        capex_limit = 100.0
        candidates = generate_random_candidates(
            n=n, capex_limit=capex_limit, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives
        )
        assert len(candidates) == n
        for candidate in candidates:
            assert sum(candidate[:n_sub_portfolios]) == capex_limit
            for i in range(n_sub_portfolios):
                assert sum(candidate[n_sub_portfolios + i * n_objectives :]) == 1.0


class TestSplitCandidateCapexsAndWeights:
    def test_good_inputs(self) -> None:
        split_candidate_capexs_and_weights()
        n = 2
        n_sub_portfolios = 2
        n_objectives = 2
        capex_limit = 100.0
        candidates = generate_random_candidates(
            n=n, capex_limit=capex_limit, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives
        )
        assert len(candidates) == n
        for candidate in candidates:
            capexs, weights_lists = split_candidate_capexs_and_weights(
                candidate=candidate, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives, capex_limit=capex_limit
            )
            assert len(capexs) == n_sub_portfolios - 1
            assert sum(capexs) <= capex_limit
            assert sum(capexs) >= 0
            assert len(weights_lists) == n_sub_portfolios
            for weights in weights_lists:
                assert len(weights) == n_objectives - 1
                assert sum(weights) <= 1
                assert sum(weights) >= 0


class TestCreateCapexBounds:
    def test_basic_bounds(self) -> None:
        n_sub_portfolios = 3
        capex_limit = 100.0
        bounds = create_capex_bounds(n_sub_portfolios=n_sub_portfolios, capex_limit=capex_limit)

        assert bounds.shape == (2, n_sub_portfolios - 1)
        assert torch.all(bounds[0, :] == 0)
        assert torch.all(bounds[1, :] == capex_limit)


class TestCreateObjectiveWeightBounds:
    def test_basic_bounds(self) -> None:
        n_sub_portfolios = 3
        n_objectives = 2
        bounds = create_objective_weight_bounds(n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives)

        # Check shape
        expected_shape = (2, n_sub_portfolios * (n_objectives - 1))
        assert bounds.shape == expected_shape

        # Check lower bounds are all 0
        assert torch.all(bounds[0, :] == 0)

        # Check upper bounds are all 1
        assert torch.all(bounds[1, :] == 1)


class TestCreateInequalityConstraints:
    def test_basic_constraints(self) -> None:
        n_sub_portfolios = 3
        n_objectives = 2
        capex_limit = 100.0

        constraints = create_inequality_constraints(
            capex_limit=capex_limit, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives
        )

        # Total constraints: 1 CAPEX + n_sub_portfolios weight constraints
        assert len(constraints) == 1 + n_sub_portfolios

        # Check CAPEX constraint
        capex_indices, capex_coeffs, capex_value = constraints[0]
        assert capex_indices.shape[0] == n_sub_portfolios - 1
        assert torch.all(capex_coeffs == -1.0)
        assert capex_value == -capex_limit

        # Check weight constraints for each sub-portfolio
        for _, (indices, coeffs, value) in enumerate(constraints[1:]):
            assert indices.shape[0] == n_objectives - 1
            assert torch.all(coeffs == -1.0)
            assert value == -1.0


class TestOptimizeAcquisitionFuncAndGetCandidate:
    def test_basic_optimization(self) -> None:
        # Problem setup
        n_sub_portfolios = 2
        n_objectives = 2
        capex_limit = 100.0

        batch_size = 1
        mc_samples = 16
        num_restarts = 2
        raw_samples = 16

        # Dummy training data
        train_x = torch.rand(5, (n_sub_portfolios - 1) + n_sub_portfolios * (n_objectives - 1))
        train_y = torch.rand(5, n_objectives)

        # Build required inputs
        ref_point = create_reference_point(train_y)
        capex_bounds = create_capex_bounds(
            n_sub_portfolios=n_sub_portfolios,
            capex_limit=capex_limit,
        )
        weight_bounds = create_objective_weight_bounds(
            n_sub_portfolios=n_sub_portfolios,
            n_objectives=n_objectives,
        )
        bounds = torch.cat([capex_bounds, weight_bounds], dim=1)

        inequality_constraints = create_inequality_constraints(
            capex_limit=capex_limit,
            n_sub_portfolios=n_sub_portfolios,
            n_objectives=n_objectives,
        )

        # Initialise model
        _, model = initialise_model(train_x, train_y, bounds)

        # Run optimization
        candidates = optimize_acquisition_func_and_get_candidate(
            model=model,
            train_x=train_x,
            mc_samples=mc_samples,
            ref_point=ref_point,
            bounds=bounds,
            batch_size=batch_size,
            num_restarts=num_restarts,
            raw_samples=raw_samples,
            inequality_constraints=inequality_constraints,
        )

        # Assertions
        assert isinstance(candidates, np.ndarray)
        assert candidates.shape == (batch_size, bounds.shape[1])
        assert np.isfinite(candidates).all()


class TestBayesian:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        Bayesian()

    def test_init_evaluator(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test initialisation of evaluator.
        """
        alg = Bayesian(n_generations=2, NSGA2_param=NSGA2HyperParam(pop_size=512, n_offsprings=256, n_max_gen=2, period=10))
        n_sub_portfolios = alg.init_evaluator(
            objectives=default_objectives, constraints=default_constraints, portfolio=default_portfolio
        )
        assert n_sub_portfolios == 2

    def test_evaluate(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = Bayesian(n_generations=2, NSGA2_param=NSGA2HyperParam(pop_size=512, n_offsprings=256, n_max_gen=2, period=10))
        n_sub_portfolios = alg.init_evaluator(
            objectives=default_objectives, constraints=default_constraints, portfolio=default_portfolio
        )
        capex_limit = 99999
        candidates = generate_random_candidates(
            n=1, capex_limit=capex_limit, n_sub_portfolios=n_sub_portfolios, n_objectives=len(default_objectives)
        )
        capexs, weights = split_candidate_capexs_and_weights(
            candidate=candidates[0],
            n_sub_portfolios=n_sub_portfolios,
            n_objectives=len(default_objectives),
            capex_limit=capex_limit,
        )
        solution = alg.evaluate(capex_limits=capexs, weights_list=weights)
        assert isinstance(solution, PortfolioSolution)

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
