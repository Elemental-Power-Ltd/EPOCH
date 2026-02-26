import pytest
from app.internal.ga_utils import ProblemInstance
from app.internal.NSGA2 import NSGA2, SeparatedNSGA2, SeparatedNSGA2xNSGA2
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.optimisers import NSGA2HyperParam
from app.models.result import OptimisationResult, PortfolioSolution


class TestNSGA2:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        NSGA2()

    def test_load_existing_solutions(
        self,
        default_objectives: list[Metric],
        default_constraints: Constraints,
        default_portfolio: list[Site],
        dummy_portfolio_solutions: list[PortfolioSolution],
    ) -> None:
        alg = NSGA2()
        problem_instance = ProblemInstance(default_objectives, default_constraints, default_portfolio)
        alg._load_existing_solutions(dummy_portfolio_solutions, problem_instance)

    @pytest.mark.slow
    def test_run(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = NSGA2(pop_size=512, n_offsprings=256, n_max_gen=10)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)

    @pytest.mark.slow
    def test_run_with_existing_solutions(
        self,
        default_objectives: list[Metric],
        default_constraints: Constraints,
        default_portfolio: list[Site],
        dummy_portfolio_solutions: list[PortfolioSolution],
    ) -> None:
        alg = NSGA2(pop_size=512, n_offsprings=256, n_max_gen=10)
        res = alg.run(
            objectives=default_objectives,
            constraints=default_constraints,
            portfolio=default_portfolio,
            existing_solutions=dummy_portfolio_solutions,
        )
        assert isinstance(res, OptimisationResult)


class TestSeperatedNSGA2:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        SeparatedNSGA2()

    @pytest.mark.slow
    def test_run(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = SeparatedNSGA2(pop_size=512, n_offsprings=256, n_max_gen=10)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)


class TestSeperatedNSGA2xNSGA2:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        SeparatedNSGA2xNSGA2()

    @pytest.mark.slow
    def test_run(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = SeparatedNSGA2xNSGA2(
            SeparatedNSGA2_param=NSGA2HyperParam(n_max_gen=10), NSGA2_param=NSGA2HyperParam(n_max_gen=10)
        )
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)
