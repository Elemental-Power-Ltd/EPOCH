from pathlib import Path
from time import perf_counter

import pytest

from app.internal.genetic_algorithm import (
    NSGA2,
    GeneticAlgorithm,
    ProblemInstance,
    SamplingMethod,
)
from app.internal.problem import Problem, load_problem
from app.internal.result import Result


@pytest.fixture(scope="session")
def example_problem() -> Problem:
    return load_problem(name="var-3", save_dir=Path("tests", "data", "benchmarks"))


class TestNSGA2:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        NSGA2()

    def test_good_sampling_method(self) -> None:
        """
        Test sampling_method initialisation parameter with good values.
        """
        NSGA2(sampling_method=SamplingMethod.LHS)
        NSGA2(sampling_method=SamplingMethod.RS)

    def test_bad_sampling_method(self) -> None:
        """
        Test sampling_method initialisation parameter with bad values.
        """
        with pytest.raises(KeyError):
            NSGA2(sampling_method=1)  # type: ignore

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_run(self, example_problem: Problem) -> None:
        """
        Test algorithm run.
        """
        alg = NSGA2()
        t0 = perf_counter()
        await alg.run(example_problem)
        exec_time = perf_counter() - t0
        assert exec_time < 60

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_res(self, example_problem: Problem) -> None:
        """
        Test output of algorithm.
        """
        alg = NSGA2()
        res = await alg.run(example_problem)
        assert isinstance(res, Result)


class TestGeneticAlgorithm:
    def test_initialisation(self) -> None:
        """
        Test default algorithm initialisation.
        """
        GeneticAlgorithm()

    def test_good_sampling_method(self) -> None:
        """
        Test sampling_method initialisation parameter with good values.
        """
        GeneticAlgorithm(sampling_method=SamplingMethod.LHS)
        GeneticAlgorithm(sampling_method=SamplingMethod.RS)

    def test_bad_sampling_method(self) -> None:
        """
        Test sampling_method initialisation parameter with bad values.
        """
        with pytest.raises(KeyError):
            GeneticAlgorithm(sampling_method=1)  # type: ignore

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_run(self, example_problem: Problem) -> None:
        """
        Test algorithm run.
        """
        alg = GeneticAlgorithm()
        t0 = perf_counter()
        await alg.run(example_problem)
        exec_time = perf_counter() - t0
        assert exec_time < 60

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_res(self, example_problem: Problem) -> None:
        """
        Test output of algorithm.
        """
        alg = GeneticAlgorithm()
        res = await alg.run(example_problem)
        assert isinstance(res, Result)


class TestProblemInstance:
    def test_initialisation(self, example_problem: Problem) -> None:
        """
        Test initialisation with test problem.
        """
        ProblemInstance(example_problem)
