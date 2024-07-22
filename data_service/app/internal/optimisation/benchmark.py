import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from ..utils import typename
from ..visualise import search_space_fitness_plot
from .grid_search import GridSearch
from .opt_algorithm import Algorithm
from .pf_eval import (
    InvertedGenDistPlus,
    MatchingIndividuals,
    MaxParetoFrontError,
    NonDominatedIndividuals,
    SingleObjectiveAccuracy,
    Spacing,
)
from .problem import Problem, load_problem
from .result import (
    BenchmarkScoring,
    Result,
    load_optimisation_results,
    save_optimisation_results,
)

_BENCH_PATH = Path("..", "benchmarks")


@dataclass(frozen=True)
class Benchmark:
    problem: Problem
    ref_result: Result


def load_benchmark(name: str, bench_path: os.PathLike = _BENCH_PATH) -> Benchmark:
    """
    Load benchmark with given name from benchmarking dir.

    Parameters
    ----------
    name
        Name of benchmark to load.

    Returns
    -------
        Benchmarking object.
    """
    problem = load_problem(name, bench_path)
    reference_results = load_optimisation_results(Path(bench_path, name))

    return Benchmark(problem, reference_results)


def ss_fitness_plot_grid_search(problem: Problem, bench_path: os.PathLike = _BENCH_PATH) -> Figure:
    """
    Creates a search space fitness plot by using the results from applying grid search to a given problem.

    Parameters
    ----------
    problem
        Problem instance to create the visual for.
    """
    file_path = Path(bench_path, problem.name, "GridSearch", "ExhaustiveResults.csv")
    assert Path(file_path).exists(), "No grid search results to plot."

    objectives = list(problem.objectives.keys())
    variable_param_names = list(problem.variable_param().keys())
    usecols = objectives + variable_param_names
    GS_df = pd.read_csv(file_path, encoding="cp1252", dtype="float", usecols=usecols)

    fitnesses = GS_df[objectives].to_numpy()
    solutions = GS_df[variable_param_names].to_numpy()

    return search_space_fitness_plot(problem.objectives, fitnesses, problem.variable_param(), solutions)


def populate_benchmark(name: str, algorithm: Algorithm | None = None, bench_path: os.PathLike = _BENCH_PATH) -> None:
    """
    Populates benchmark directory using the parsed reference algorithm.
    ref_result pickle file is added to the benchmark directory.

    Parameters
    ----------
    problem
        Problem to use as benchmark.
    algorithm
        Algorithm to use to populate benchmark.
        Default is Grid Search.
    """
    if algorithm is None:
        algorithm = GridSearch(
            project_path=Path("..", "..", "Epoch"),
            config_dir=None,
            output_dir=None,
            keep_degenerate=True,
        )

    problem = load_problem(name, bench_path)

    ref_result = algorithm.run(problem)

    alg_dir = Path(bench_path, problem.name)

    save_optimisation_results(ref_result, alg_dir)
    save_optimisation_results(ref_result, Path(alg_dir, typename(algorithm) + algorithm.paramstr))


def measure_optimisation_results(expected: Result, obtained: Result, problem: Problem) -> BenchmarkScoring:
    """
    Measures obtaineds results against expected results for a given problem.

    Parameters
    ----------
    expected
        Expected results
    obtained
        Obtained results
    problem
        Optimisation Problem that the results seak to solve

    Returns
    -------
    Dictionary of metrics
    """
    exec_time_r = obtained.exec_time / expected.exec_time
    n_eval_r = obtained.n_evals / expected.n_evals

    senses = np.array(list(problem.objectives.values()))  # get direction of optimisation if maximising or minimising
    expected_pf = np.unique(expected.fitnesses, axis=0) * senses  # apply optimisation direction & remove degenarates
    obtained_pf = np.unique(obtained.fitnesses, axis=0) * senses  # apply optimisation direction & remove degenarates

    igdp = InvertedGenDistPlus(expected_pf, obtained_pf)
    mpfe = MaxParetoFrontError(expected_pf, obtained_pf)
    n_matching_r = MatchingIndividuals(expected_pf, obtained_pf) / expected_pf.shape[0]
    n_non_domiated_r = NonDominatedIndividuals(expected_pf, obtained_pf) / expected_pf.shape[0]
    spacing_r = Spacing(obtained_pf) / Spacing(expected_pf)
    soo = [bool(i) for i in SingleObjectiveAccuracy(expected_pf, obtained_pf)]
    soo_success = dict(zip(problem.objectives.keys(), soo, strict=False))
    nsoor = sum(soo) / expected_pf.shape[1]

    return {
        "ExecTimeRatio": float(exec_time_r),
        "NumEvalRatio": float(n_eval_r),
        "InvertedGenDistPlus": float(igdp),
        "MaxParetoFrontError": float(mpfe),
        "NumMatchingRatio": float(n_matching_r),
        "NumNonDominatedRatio": float(n_non_domiated_r),
        "SpacingRatio": float(spacing_r),
        "SOOSuccess": soo_success,
        "SOOAccuracy": float(nsoor),
    }


def benchmark_algorithm(algorithm: Algorithm, benchmark: Benchmark, path_to_bench: os.PathLike = _BENCH_PATH) -> None:
    """
    Benchmarks an optimisation algorithm on a benchmark problem.

    Parameters
    ----------
    algorithm
        Algorithm to benchmark.
    benchmark
        Populated benchmark problem.
    """
    algorithm_name = typename(algorithm) + algorithm.paramstr
    if Path(
        path_to_bench,
        benchmark.problem.name,
        algorithm_name,
        "optimisation_results.pkl",
    ).exists():
        optimisation_results = load_optimisation_results(Path(path_to_bench, benchmark.problem.name, algorithm_name))
    else:
        optimisation_results = algorithm.run(benchmark.problem)
        save_optimisation_results(
            optimisation_results,
            Path(path_to_bench, benchmark.problem.name, algorithm_name),
        )

    benchmarking_results = measure_optimisation_results(benchmark.ref_result, optimisation_results, benchmark.problem)

    alg_dir = Path(path_to_bench, benchmark.problem.name, algorithm_name)

    save_benchmarking_results(benchmarking_results, alg_dir)


def save_benchmarking_results(results: Result | BenchmarkScoring, save_dir: str | os.PathLike) -> None:
    """
    Save benchmarking results to a directory.

    Parameters
    ----------
    results
        Result instance to save
    save_dir
        Directory to save to
    """
    Path(save_dir).mkdir(parents=False, exist_ok=True)
    with open(Path(save_dir, "benchmarking_results.json"), "w") as f:
        json.dump(results, f, indent=4)


def load_benchmarking_results(save_dir: str | os.PathLike) -> None:
    """
    Load benchmarking results from a directory.

    Parameters
    ----------
    save_dir
        Directory to load from

    Returns
    -------
    Benchmarking results
    """
    with open(Path(save_dir, "benchmarking_results.json")) as f:
        results = json.load(f)
    return results
