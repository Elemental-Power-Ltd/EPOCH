import os

import pytest

from app.internal.grid_search import GridSearch
from app.models.constraints import ConstraintDict
from app.models.core import Site
from app.models.objectives import Objectives
from app.models.result import OptimisationResult


class TestGridSearch:
    def test_initialisation(self, temporary_directory: os.PathLike) -> None:
        """
        Test algorithm initialisation.
        """
        GridSearch(keep_degenerate=False)

    @pytest.mark.requires_epoch
    def test_run(
        self, default_objectives: list[Objectives], default_constraints: ConstraintDict, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = GridSearch(keep_degenerate=False)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)
