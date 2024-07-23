import numpy as np
import pytest

from app.internal.result import Result


class TestResult:
    def test_good_inputs(self) -> None:
        """
        Test we can initialise Result with valid inputs.
        """
        solutions = np.array([[0, 1], [2, 0]])
        fitnesses = np.array([[12, 5.0, 3], [16, 4.0, 2]])
        n_evals = 200
        exec_time = 100
        Result(solutions, fitnesses, n_evals, exec_time)

    def test_bad_sol_fit_dims(self) -> None:
        """
        Test we can't set solutions and fitnesses that aren't 2d arrays.
        """
        solutions = np.array([2, 0])
        fitnesses = np.array([12, 5.0, 3])
        n_evals = 200
        exec_time = 100
        with pytest.raises(ValueError):
            Result(solutions, fitnesses, n_evals, exec_time)

    def test_diff_dim_sizes(self) -> None:
        """
        Test we can't set solutions and fitnesses with different first dimension sizes.
        """
        solutions = np.array([[2, 0], [1, 0]])
        fitnesses = np.array([[12, 5.0, 3]])
        n_evals = 200
        exec_time = 100
        with pytest.raises(ValueError):
            Result(solutions, fitnesses, n_evals, exec_time)

    def test_negative_n_evals(self) -> None:
        """
        Test we can't set negative n_evals.
        """
        solutions = np.array([[2, 0], [1, 0]])
        fitnesses = np.array([[12, 5.0, 3]])
        n_evals = -200
        exec_time = 100
        with pytest.raises(ValueError):
            Result(solutions, fitnesses, n_evals, exec_time)

    def test_negative_exec_time(self) -> None:
        """
        Test we can't set negative n_evals.
        """
        solutions = np.array([[2, 0], [1, 0]])
        fitnesses = np.array([[12, 5.0, 3]])
        n_evals = 200
        exec_time = -100
        with pytest.raises(ValueError):
            Result(solutions, fitnesses, n_evals, exec_time)
