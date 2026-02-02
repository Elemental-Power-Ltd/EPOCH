import pytest

from app.internal.result import get_baseline_portfolio_solution
from app.models.core import Site
from app.models.result import OptimisationResult


class TestGetBaselinePortfolioSolution:
    def test_good_inputs(self, default_portfolio: list[Site]) -> None:
        res = get_baseline_portfolio_solution(portfolio=default_portfolio)
        assert all(site.site_data.site_id in res.scenario.keys() for site in default_portfolio)


class TestResult:
    def test_negative_n_evals(self, dummy_optimisation_result: OptimisationResult) -> None:
        """
        Test we can't set negative n_evals.
        """
        result = dummy_optimisation_result
        solutions = result.solutions
        n_evals = -result.n_evals
        exec_time = result.exec_time
        with pytest.raises(ValueError):
            OptimisationResult(solutions=solutions, n_evals=n_evals, exec_time=exec_time)

    def test_negative_exec_time(self, dummy_optimisation_result: OptimisationResult) -> None:
        """
        Test we can't set negative exec_time.
        """
        result = dummy_optimisation_result
        solutions = result.solutions
        n_evals = result.n_evals
        exec_time = -result.exec_time
        with pytest.raises(ValueError):
            OptimisationResult(solutions=solutions, n_evals=n_evals, exec_time=exec_time)
