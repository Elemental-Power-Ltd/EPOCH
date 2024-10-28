import pytest

from app.internal.genetic_algorithm import GeneticAlgorithm
from app.internal.problem import PortfolioProblem
from app.models.result import OptimisationResult


class TestGeneticAlgorithm:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        GeneticAlgorithm()

    @pytest.mark.slow
    def test_run(self, default_portfolio_problem: PortfolioProblem) -> None:
        """
        Test output of algorithm.
        """
        alg = GeneticAlgorithm(pop_size=256)
        res = alg.run(default_portfolio_problem)
        assert isinstance(res, OptimisationResult)
