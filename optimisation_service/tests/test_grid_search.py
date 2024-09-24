import os
import shutil
from pathlib import Path
from time import perf_counter
from typing import Generator

import pytest

from app.internal.grid_search import GridSearch
from app.internal.problem import Problem, load_problem
from app.internal.result import Result


@pytest.fixture(scope="module")
def temporary_directory(
    tmpdir_factory: pytest.TempdirFactory,
) -> Generator[os.PathLike, None, None]:
    my_tmpdir = tmpdir_factory.mktemp("tmp")
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


@pytest.fixture(scope="session")
def example_problem() -> Problem:
    return load_problem(name="var-3", save_dir=Path("tests", "data", "benchmarks"))


@pytest.mark.requires_epoch
class TestGridSearch:
    def test_initialisation(self, temporary_directory: os.PathLike) -> None:
        """
        Test algorithm initialisation.
        """
        GridSearch(keep_degenerate=False)

    def test_run(self, example_problem: Problem) -> None:
        """
        Test algorithm run.
        """
        alg = GridSearch(keep_degenerate=False)
        t0 = perf_counter()
        alg.run(example_problem)
        exec_time = perf_counter() - t0
        assert exec_time < 60

    def test_res(self, example_problem: Problem) -> None:
        """
        Test output of algorithm.
        """
        alg = GridSearch(keep_degenerate=False)
        res = alg.run(example_problem)
        assert isinstance(res, Result)
