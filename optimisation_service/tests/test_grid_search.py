import os

import pytest

from app.internal.grid_search import GridSearch
from app.internal.problem import PortfolioProblem
from app.models.result import OptimisationResult


class TestGridSearch:
    def test_initialisation(self, temporary_directory: os.PathLike) -> None:
        """
        Test algorithm initialisation.
        """
        GridSearch(keep_degenerate=False)

    @pytest.mark.requires_epoch
    def test_run(self, default_portfolio_problem: PortfolioProblem) -> None:
        """
        Test output of algorithm.
        """
        alg = GridSearch(keep_degenerate=False)
        res = alg.run(default_portfolio_problem)
        assert isinstance(res, OptimisationResult)
