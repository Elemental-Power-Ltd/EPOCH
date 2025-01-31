import pytest

from app.internal.NSGA2 import NSGA2
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.objectives import Objectives
from app.models.result import OptimisationResult


class TestNSGA2:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        NSGA2()

    @pytest.mark.slow
    def test_run(
        self, default_objectives: list[Objectives], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = NSGA2(pop_size=256)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)
