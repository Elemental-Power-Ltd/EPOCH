import pytest

from app.internal.NSGA2 import NSGA2
from app.internal.problem import PortfolioProblem
from app.models.result import OptimisationResult


class TestNSGA2:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        NSGA2()

    @pytest.mark.slow
    def test_run(self, default_portfolio_problem: PortfolioProblem) -> None:
        """
        Test output of algorithm.
        """
        alg = NSGA2(pop_size=256)
        res = alg.run(default_portfolio_problem)
        assert isinstance(res, OptimisationResult)
