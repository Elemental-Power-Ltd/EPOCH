import pytest

from app.internal.genetic_algorithm import GeneticAlgorithm
from app.models.constraints import ConstraintDict
from app.models.core import Site
from app.models.objectives import Objectives
from app.models.result import OptimisationResult


class TestGeneticAlgorithm:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        GeneticAlgorithm()

    @pytest.mark.slow
    def test_run(
        self, default_objectives: list[Objectives], default_constraints: ConstraintDict, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = GeneticAlgorithm(pop_size=256)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)
