import pytest

from app.models.result import OptimisationResult


class TestResult:
    def test_negative_n_evals(self, default_optimisation_result: OptimisationResult) -> None:
        """
        Test we can't set negative n_evals.
        """
        result = default_optimisation_result
        solutions = result.solutions
        n_evals = -result.n_evals
        exec_time = result.exec_time
        with pytest.raises(ValueError):
            OptimisationResult(solutions=solutions, n_evals=n_evals, exec_time=exec_time)

    def test_negative_exec_time(self, default_optimisation_result: OptimisationResult) -> None:
        """
        Test we can't set negative exec_time.
        """
        result = default_optimisation_result
        solutions = result.solutions
        n_evals = result.n_evals
        exec_time = -result.exec_time
        with pytest.raises(ValueError):
            OptimisationResult(solutions=solutions, n_evals=n_evals, exec_time=exec_time)
