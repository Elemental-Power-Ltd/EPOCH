import pytest

from app.internal.grid_search import GridSearch
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.result import OptimisationResult


class TestGridSearch:
    def test_initialisation(self) -> None:
        """
        Test algorithm initialisation.
        """
        GridSearch(keep_degenerate=False)

    @pytest.mark.requires_epoch
    @pytest.mark.skip(reason="Awaiting Grid Search fix.")
    def test_run(
        self, default_objectives: list[Metric], default_constraints: Constraints, default_portfolio: list[Site]
    ) -> None:
        """
        Test output of algorithm.
        """
        alg = GridSearch(keep_degenerate=False)
        res = alg.run(default_objectives, default_constraints, default_portfolio)
        assert isinstance(res, OptimisationResult)
