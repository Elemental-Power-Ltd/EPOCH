import datetime
import logging
import warnings
from typing import TypedDict, cast

import numpy as np
import numpy.typing as npt
import torch
from app.internal.bayesian.distributed_portfolio_optimiser import select_starting_solutions
from app.internal.ga_utils import Normaliser
from app.internal.NSGA2 import NSGA2
from app.internal.pareto_front import (
    merge_list_of_portfolio_solutions,
    portfolio_pareto_front,
)
from app.models.algorithms import Algorithm
from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.metrics import Metric, MetricDirection
from app.models.optimisers import NSGA2HyperParam
from app.models.result import OptimisationResult, PortfolioSolution
from botorch import fit_gpytorch_mll
from botorch.acquisition.multi_objective.logei import (
    qLogExpectedHypervolumeImprovement,
)
from botorch.exceptions import BadInitialCandidatesWarning
from botorch.exceptions.warnings import UserInputWarning
from botorch.models.gp_regression import SingleTaskGP
from botorch.models.gpytorch import GPyTorchModel
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.models.transforms.input import Normalize
from botorch.models.transforms.outcome import Standardize
from botorch.optim.optimize import optimize_acqf
from botorch.sampling.normal import IIDNormalSampler
from botorch.utils.multi_objective.box_decompositions.non_dominated import (
    FastNondominatedPartitioning,
)
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood  # type: ignore

logger = logging.getLogger("default")


class TKWARGS(TypedDict):
    """Torch keyword arguments which we need for optimisation."""

    dtype: torch.dtype
    device: torch.device


_TDEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_TKWARGS = TKWARGS(dtype=torch.double, device=_TDEVICE)


warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserInputWarning)


class Bayesian(Algorithm):
    """Optimise a multi objective portfolio problem by optimising the CAPEX allocations."""

    def __init__(
        self,
        n_per_sub_portfolio: int = 1,
        n_initialisation_points: int = 5,
        n_generations: int = 10,
        batch_size: int = 4,
        num_restarts: int = 10,
        raw_samples: int = 512,
        mc_samples: int = 128,
        NSGA2_param: NSGA2HyperParam | None = None,
    ):
        """
        Define Bayesian and NSGA-II hyperparameters.

        Parameters
        ----------
        n_per_sub_portfolio
            Number of sites in each sub-portfolio.
        n_generations
            Number of Bayesian optimisation generations to perform.
        batch_size
            Number of CAPEX allocations to test at each generation.
            Fitting the gaussian models and optimising the acquisition function can be compute intensive, selecting a larger
            batch_size can reduce the total number of generations.
        num_restarts
            Number of times to restart the acquisition function optimisation.
        raw_samples
            Number of samples to initialise the acquisition function optimisation with.
        mc_samples
            The size of each sample.
        NSGA2_param
            NSGA2 hyperparameter values.
        """
        self.n_per_sub_portfolio = n_per_sub_portfolio
        self.n_initialisation_points = n_initialisation_points
        self.num_restarts = num_restarts
        self.raw_samples = raw_samples
        self.n_generations = n_generations
        self.batch_size = batch_size
        self.mc_samples = mc_samples
        if NSGA2_param is None:
            NSGA2_param = NSGA2HyperParam()
        self.NSGA2_param = NSGA2_param
        self.NSGA2_param.return_least_infeasible = False
        self.n_evals = 0

    def run(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]) -> OptimisationResult:
        """
        Run the Bayesian optimiser.

        Parameters
        ----------
        objectives
            List of metrics to maximise or minimise
        constraints
            Limitations on which solutions are acceptable
        portfolio
            List of sites to optimise

        Returns
        -------
        OptimisationResult
            Optimised portfolio
        """
        start_time = datetime.datetime.now(datetime.UTC)

        assert len(portfolio) >= 2, "The portfolio must contain at least two sites."

        assert constraints.get(Metric.capex, None) is not None, "The constraints must define an upper CAPEX limit."
        assert constraints[Metric.capex].get("max", None) is not None, "The constraints must define an upper CAPEX limit."
        capex_limit = constraints[Metric.capex]["max"]

        self.sub_portfolios = split_into_sub_portfolios(portfolio, self.n_per_sub_portfolio)
        n_sub_portfolios = len(self.sub_portfolios)
        assert n_sub_portfolios > 1, "There must be at least two sub portfolios."

        n_objectives = len(objectives)
        assert n_sub_portfolios > 1, "There must be at least two objectives."

        self.normalisers_list = []
        for sub_portfolio in self.sub_portfolios:
            metrics = {objective: [] for objective in objectives}
            for objective in objectives:
                alg = NSGA2(**dict(self.NSGA2_param))
                res = alg.run(objectives=[objective], constraints=constraints, portfolio=sub_portfolio)
                for obj in objectives:
                    metrics[obj].append(res.solutions[0].metric_values[obj])
            normalisers = [
                Normaliser(min_value=min(metrics[objective]), max_value=max(metrics[objective])) for objective in objectives
            ]
            self.normalisers_list.append(normalisers)

        self.objectives = objectives
        self.sub_portfolio_solutions = [[]] * n_sub_portfolios
        sub_portfolio_site_ids = [[site.site_data.site_id for site in portfolio] for portfolio in self.sub_portfolios]

        candidates = generate_random_candidates(
            n=self.n_initialisation_points,
            capex_limit=capex_limit,
            n_sub_portfolios=n_sub_portfolios,
            n_objectives=n_objectives,
        )
        solutions = []
        train_x_list, train_y_list = [], []
        for k, candidate in enumerate(candidates):
            logger.debug(f"On random candidate {k + 1} / {self.n_initialisation_points}.")

            capexs, weights = convert_candidate_capexs_and_weights(
                candidate=candidate, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives, capex_limit=capex_limit
            )

            new_solution = self.evaluate(capex_limits=capexs, weights_list=weights)
            solutions.append(new_solution)

            new_train_x, new_train_y = convert_solution_to_tensors(
                candidate=candidate,
                solution=new_solution,
                n_sub_portfolios=n_sub_portfolios,
                sub_portfolio_site_ids=sub_portfolio_site_ids,
                objectives=objectives,
            )
            train_x_list.append(new_train_x)
            train_y_list.append(new_train_y)

        train_x = torch.cat(train_x_list)
        train_y = torch.cat(train_y_list)

        logger.debug(f"Currently have {len(train_x)} training points.")

        ref_point = create_reference_point(train_y)
        capex_bounds = create_capex_bounds(n_sub_portfolios=n_sub_portfolios, capex_limit=capex_limit)
        weight_bounds = create_objective_weight_bounds(n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives)
        bounds = torch.cat([capex_bounds, weight_bounds], dim=1)
        inequality_constraints = create_inequality_constraints(
            capex_limit=capex_limit, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives
        )

        mll, model = initialise_model(train_x, train_y, bounds)

        # run n_generations rounds of Bayesian optimisation after the initial random batch
        for j in range(0, self.n_generations):
            logger.debug(f"On generations {j + 1} / {self.n_generations}.")
            fit_gpytorch_mll(mll)
            state_dict = model.state_dict()

            candidates = optimize_acquisition_func_and_get_candidate(
                model=model,
                train_x=train_x,
                mc_samples=self.mc_samples,
                ref_point=ref_point,
                bounds=bounds,
                batch_size=self.batch_size,
                num_restarts=self.num_restarts,
                raw_samples=self.raw_samples,
                inequality_constraints=inequality_constraints,
            )

            for k, candidate in enumerate(candidates):
                logger.debug(f"On batch {k + 1} / {self.batch_size}.")
                capexs, weights = convert_candidate_capexs_and_weights(
                    candidate=candidate, n_sub_portfolios=n_sub_portfolios, n_objectives=n_objectives, capex_limit=capex_limit
                )
                new_solution = self.evaluate(capexs, weights)
                solutions.append(new_solution)

                new_train_x, new_train_y = convert_solution_to_tensors(
                    solution=new_solution,
                    candidate=candidate,
                    n_sub_portfolios=n_sub_portfolios,
                    sub_portfolio_site_ids=sub_portfolio_site_ids,
                    objectives=objectives,
                )
                train_x = torch.cat([train_x, new_train_x])
                train_y = torch.cat([train_y, new_train_y])

            logger.debug(f"Currently have {len(train_x)} training points.")

            ref_point = create_reference_point(train_y)

            mll, model = initialise_model(train_x, train_y, bounds)

            if state_dict is not None:
                model.load_state_dict(state_dict)

        solutions = portfolio_pareto_front(solutions, objectives)

        torch.cuda.empty_cache()

        total_exec_time = datetime.datetime.now(datetime.UTC) - start_time

        return OptimisationResult(solutions, self.n_evals, total_exec_time)

    def evaluate(self, capex_limits: list[float], weights_list: list[list[float]]) -> PortfolioSolution:
        """
        Evaluate a CAPEX allocation.

        Parameters
        ----------
        capex_limits
            A list of upper CAPEX bounds, one for each sub portfolio.

        Returns
        -------
        solutions
            A list of new (unseen before) optimal solutions.
        """
        sub_portfolio_solutions = []
        for i, (capex_limit, weights, normalisers) in enumerate(
            zip(capex_limits, weights_list, self.normalisers_list, strict=True)
        ):
            alg = NSGA2(**dict(self.NSGA2_param))
            constraints = {Metric.capex: Bounds(max=capex_limit)}

            selected_solutions = select_starting_solutions(
                existing_solutions=self.sub_portfolio_solutions[i], constraints=constraints
            )
            if len(selected_solutions) > alg.algorithm.pop_size * 0.9:
                pop_to_offspring = alg.algorithm.n_offsprings / alg.algorithm.pop_size
                alg.algorithm.pop_size = int(len(selected_solutions) * 1.1)
                alg.algorithm.n_offsprings = int(pop_to_offspring * alg.algorithm.pop_size)

            res = alg.run(
                objectives=self.objectives,
                constraints=constraints,
                portfolio=self.sub_portfolios[i],
                weights=weights,
                normalisers=normalisers,
                # existing_solutions=selected_solutions,
            )
            self.n_evals += res.n_evals

            sub_portfolio_solutions.append(res.solutions[0])
            self.sub_portfolio_solutions[i].append(res.solutions[0])

        return merge_list_of_portfolio_solutions(sub_portfolio_solutions)


def convert_candidate_capexs_and_weights(
    candidate: npt.NDArray, n_sub_portfolios: int, n_objectives: int, capex_limit: float
) -> tuple[list[float], list[list[float]]]:
    capexs = candidate[: n_sub_portfolios - 1].tolist()
    capexs.append(capex_limit - sum(capexs))
    weights = candidate[n_sub_portfolios - 1 :].reshape(n_sub_portfolios, (n_objectives - 1)).tolist()
    for i in range(n_sub_portfolios):
        weights[i].append(1 - sum(weights[i]))

    return capexs, weights


def split_into_sub_portfolios(portfolio: list[Site], n_per_sub_portfolio: int) -> list[list[Site]]:
    """
    Split a portfolio into sub portfolios each containing n_per_sub_portfolio sites.

    This excludes the last sub portfolio if the number of sites isn't divisible by n_per_sub_portfolio.

    Parameters
    ----------
    portfolio
        List of Sites to split into sub portfolios.
    n_per_sub_portfolio
        The number of sites per sub portfolio.

    Returns
    -------
    sub_portfolios
        A list of portfolios.
    """
    return [portfolio[i : i + n_per_sub_portfolio] for i in range(0, len(portfolio), n_per_sub_portfolio)]


def generate_random_candidates(
    n: int, capex_limit: float, n_sub_portfolios: int, n_objectives: int
) -> npt.NDArray[np.floating]:
    """
    Generate n CAPEX allocation splits randomly.

    Parameters
    ----------
    n
        Number of training points to generate.
    capex_limit
        Upper CAPEX limit for the whole portfolio.

    Returns
    -------
    candidates
        An 2D array of training points
    """
    rng = np.random.default_rng()
    candidates = []
    for _ in range(n):
        # get capex splits
        capex_splits = rng.dirichlet(np.ones(n_sub_portfolios))[:-1] * capex_limit

        # get objective weights
        obj_weights = []
        for _ in range(n_sub_portfolios):
            obj_weights.extend(rng.dirichlet(np.ones(n_objectives))[:-1])

        candidate = np.concatenate([capex_splits, np.array(obj_weights)])
        candidates.append(candidate)

    return np.array(candidates)


def initialise_model(
    train_x: torch.Tensor, train_y: torch.Tensor, bounds: torch.Tensor
) -> tuple[SumMarginalLogLikelihood, ModelListGP]:
    """
    Initialise Gaussian process models with training features and observations.

    Parameters
    ----------
    train_x
        A n x d tensor of training features (CAPEX allocations).
    train_y
        A n x m tensor of training observations (Portfolio objective values).
    bounds
        A 2 x d tensor of lower and upper bounds for each of the train_x's d columns (Bounds on the sites' CAPEX allocations).

    Returns
    -------
    mll
        A SumMarginalLogLikelihood.
    model
        A collection of Gaussian Process models.
    """
    models = []
    for i in range(train_y.shape[-1]):
        train_y_i = train_y[..., i : i + 1]
        train_y_noise = torch.full_like(train_y_i, 1e-06)
        models.append(
            SingleTaskGP(
                train_x,
                train_y_i,
                train_y_noise,
                outcome_transform=Standardize(m=1),
                input_transform=Normalize(d=train_x.shape[-1], bounds=bounds),
            )
        )
    model = ModelListGP(*models)
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    return mll, model


def create_reference_point(train_y: torch.Tensor) -> torch.Tensor:
    """
    Create a reference point for the hypervolume by taking the worst value for each objective.

    Parameters
    ----------
    train_y
        A n x m tensor of training observations (Portfolio objective values adjusted for maximisation).

    Returns
    -------
    ref_point
        A reference point in the outcome space (Objective values).
    """
    ref_point, _ = torch.min(train_y, dim=0)

    return ref_point


def create_capex_bounds(n_sub_portfolios: int, capex_limit: float) -> torch.Tensor:
    """
    Create a tensor representation of the bounds on the capex allocations.

    The capex allocations are bound to [0, capex_limit].

    Parameters
    ----------
    n_sub_portfolios
        Number of sub portfolios.
    capex_limit
        Upper CAPEX limit for the portfolio.

    Returns
    -------
    bounds
        A 2 x d tensor of lower and upper bounds for each of the train_x's capex columns (Bounds on the sites' CAPEX allocations).
    """
    return torch.tensor([[0], [capex_limit]], **_TKWARGS).repeat(1, n_sub_portfolios - 1)


def create_objective_weight_bounds(n_sub_portfolios: int, n_objectives: int) -> torch.Tensor:
    """
    Create a tensor representation of the bounds on the capex allocations.

    The capex allocations are bound to [0, capex_limit].

    Parameters
    ----------
    n_sub_portfolios
        Number of sub portfolios.
    n_objectives
        Number of objectives.

    Returns
    -------
    bounds
        A 2 x d tensor of lower and upper bounds for each of the train_x's  columns (Bounds on the sites' CAPEX allocations).
    """
    return torch.tensor([[0], [1]], **_TKWARGS).repeat(1, n_sub_portfolios * (n_objectives - 1))


def create_inequality_constraints(capex_limit: float, n_sub_portfolios: int, n_objectives: int) -> list[torch.Tensor]:
    inequality_constraints = []

    indexes = list(range((n_sub_portfolios - 1) + n_sub_portfolios * (n_objectives - 1)))
    # Define constraints on the CAPEX allocations.
    # The sum of the allocations must be smaller than the CAPEX limit.
    capex_indeces = indexes[: (n_sub_portfolios - 1)]
    indeces = torch.tensor(capex_indeces, dtype=torch.int, device=_TDEVICE)
    coefficients = torch.tensor([-1.0] * (n_sub_portfolios - 1), **_TKWARGS)
    inequality_constraints.append((indeces, coefficients, -capex_limit))

    # Define constraints on the objective weights.
    # The sum of the weights must be smaller than 1 for each sub portfolio.
    weight_indeces = indexes[(n_sub_portfolios - 1) :]
    for i in range(n_sub_portfolios):
        portfolio_weight_idx = weight_indeces[i * (n_objectives - 1) : i * (n_objectives - 1) + (n_objectives - 1)]
        indeces = torch.tensor(portfolio_weight_idx, dtype=torch.int, device=_TDEVICE)
        coefficients = torch.tensor([-1.0] * (n_objectives - 1), **_TKWARGS)
        inequality_constraints.append((indeces, coefficients, -1.0))

    return inequality_constraints


def optimize_acquisition_func_and_get_candidate(
    model: GPyTorchModel,
    train_x: torch.Tensor,
    mc_samples: int,
    ref_point: torch.Tensor,
    bounds: torch.Tensor,
    batch_size: int,
    num_restarts: int,
    raw_samples: int,
    inequality_constraints: list[torch.Tensor],
) -> npt.NDArray[np.floating]:
    """
    Optimise the acquisition function and returns a new candidate.

    Parameters
    ----------
    model
        The Gaussian process models.
    train_x
        A n x d tensor of observed features (CAPEX allocations).
    mc_samples
        The number of samples to generate at each call of the sampler.
    ref_point
        A reference point in the outcome space (Objective values).
    bounds
        A 2 x d tensor of lower and upper bounds for each of the train_x's d columns (Bounds on the sites' CAPEX allocations).
    batch_size
        The number of candidates to generate.
    capex_limit
        Upper CAPEX limit for the portfolio.
    num_restarts
        The number of restarts of the acquisition function optimisation.
    raw_samples
        The number of samples to initilise the acquisition function optimisation with.

    Returns
    -------
    candidates_arr
        A numpy array of candidate CAPEX allocations to evaluate.
    """
    sampler = IIDNormalSampler(sample_shape=torch.Size([mc_samples]))
    with torch.no_grad():
        pred = model.posterior(train_x).mean
    partitioning = FastNondominatedPartitioning(
        ref_point=ref_point,
        Y=pred,
    )
    acq_func = qLogExpectedHypervolumeImprovement(
        model=model,
        ref_point=ref_point,
        partitioning=partitioning,  # type: ignore
        sampler=sampler,
    )

    # optimize
    candidates, _ = optimize_acqf(
        acq_function=acq_func,
        bounds=bounds,
        q=batch_size,
        inequality_constraints=inequality_constraints,
        # https://botorch.readthedocs.io/en/stable/optim.html#module-botorch.optim.parameter_constraints
        num_restarts=num_restarts,
        raw_samples=raw_samples,  # used for intialization heuristic
        options={"batch_limit": 5, "maxiter": 200},
        sequential=True,
    )

    candidates_arr = candidates.cpu().detach().numpy()

    return cast(npt.NDArray[np.floating], candidates_arr)


def extract_sub_portfolio_capex_allocations(
    solution: PortfolioSolution, sub_portfolio_site_ids: list[list[str]]
) -> list[float]:
    """
    Extract the sub portfolio CAPEX allocations from a portfolio solution.

    Parameters
    ----------
    solution
        The PortfolioSolution.
    sub_portfolio_site_ids
        A list of lists of site_ids defining the sites in each sub portfolio.

    Returns
    -------
    capex_allocations_per_sub
        A list of the sub portfolio CAPEX allocations.
    """
    return [
        sum(solution.scenario[site_id].metric_values[Metric.capex] for site_id in portfolio)
        for portfolio in sub_portfolio_site_ids
    ]


def convert_solution_to_tensors(
    candidate: list[float],
    solution: PortfolioSolution,
    n_sub_portfolios: int,
    sub_portfolio_site_ids: list[list[str]],
    objectives: list[Metric],
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Convert a PortfolioSolutions into two feature (CAPEX allocations and objective wights) and observation (Objective values) tensors.
    One is created from the proposed CAPEX limits, the second is generated from the actual CAPEX spends.

    Parameters
    ----------
    solutions
        A list of N PortfolioSolutions.
    sub_portfolio_site_ids
        A list of lists of site_ids defining the sub portfolios.
    objectives
        The objectives to extract from the metrics.

    Returns
    -------
    train_x
        Tensor of N feature vectors (CAPEX allocations).
    train_y
        Tensor of N observation vectors (Objective values).
    """
    train_x, train_y = [], []
    candidate = list(candidate)

    # Botorch maximises
    obj_values = [solution.metric_values[objective] * -MetricDirection[objective] for objective in objectives]

    # Create one point from capex limits
    train_x.append(candidate)
    train_y.append(obj_values)

    # create one point from capex spends
    capex_spends = extract_sub_portfolio_capex_allocations(solution, sub_portfolio_site_ids)[:-1]
    obj_weights = candidate[n_sub_portfolios - 1 :]
    train_x.append(capex_spends + obj_weights)
    train_y.append(obj_values)

    train_x_t = torch.tensor(train_x, **_TKWARGS)
    train_y_t = torch.tensor(train_y, **_TKWARGS)

    return train_x_t, train_y_t
