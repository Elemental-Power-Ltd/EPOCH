import datetime
import logging
import warnings
from typing import TypedDict

import numpy as np
import numpy.typing as npt
import torch
from botorch import fit_gpytorch_mll  # type: ignore
from botorch.acquisition.multi_objective.logei import (  # type: ignore
    qLogExpectedHypervolumeImprovement,  # type: ignore
)
from botorch.exceptions import BadInitialCandidatesWarning  # type: ignore
from botorch.exceptions.warnings import UserInputWarning  # type: ignore
from botorch.models.gp_regression import SingleTaskGP  # type: ignore
from botorch.models.gpytorch import GPyTorchModel  # type: ignore
from botorch.models.model_list_gp_regression import ModelListGP  # type: ignore
from botorch.models.transforms.input import Normalize  # type: ignore
from botorch.models.transforms.outcome import Standardize  # type: ignore
from botorch.optim.optimize import optimize_acqf  # type: ignore
from botorch.sampling.normal import IIDNormalSampler  # type: ignore
from botorch.utils.multi_objective.box_decompositions.non_dominated import (  # type: ignore
    FastNondominatedPartitioning,  # type: ignore
)
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood  # type: ignore

from app.internal.bayesian.distributed_portfolio_optimiser import DistributedPortfolioOptimiser
from app.internal.pareto_front import portfolio_pareto_front
from app.models.algorithms import Algorithm
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric, MetricDirection
from app.models.optimisers import NSGA2HyperParam
from app.models.result import OptimisationResult, PortfolioSolution

logger = logging.getLogger("default")


class TKWARGS(TypedDict):
    dtype: torch.dtype
    device: torch.device


_TDEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_TKWARGS = TKWARGS(dtype=torch.double, device=_TDEVICE)


warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserInputWarning)


class Bayesian(Algorithm):
    """
    Optimise a single or multi objective portfolio problem by optimising the CAPEX allocations accross the portfolio with a
    Bayesian optimiser as follows:
        1. Split the portfolio into N sub-portfolios
        2. Initialise the optimiser by optimising each sub-portfolio individually with NSGA-II for maximum CAPEX, recombining
           the sub-portfolio solutions into feasible portfolio solutions.
        3. Convert the portfolio solutions into input (sub-portfolio CAPEX allocations) / output (objective values) pairs to fit
           Gaussian process models to.
        4. Optimise the acquisition function and get new CAPEX allocations to test.
        5. Optimise each sub-portfolio individually with NSGA-II for the new CAPEX allocations, recombining
           the sub-portfolio solutions into feasible portfolio solutions.
        6. Repeat steps 3-5 until algorithm terminates.
    """

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

    def run(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]):
        start_time = datetime.datetime.now(datetime.UTC)
        rng = np.random.default_rng()

        assert len(portfolio) >= 2, "The portfolio must contain at least two sites."

        assert constraints.get(Metric.capex, None) is not None, "The constraints must define an upper CAPEX limit."
        assert constraints[Metric.capex].get("max", None) is not None, "The constraints must define an upper CAPEX limit."
        capex_limit = constraints[Metric.capex]["max"]

        sub_portfolios = split_into_sub_portfolios(portfolio, self.n_per_sub_portfolio)
        n_sub_portfolios = len(sub_portfolios)
        assert n_sub_portfolios > 1, "There must be at least two sub portfolios."

        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios, objectives=objectives, constraints=constraints, NSGA2_param=self.NSGA2_param
        )
        solutions = dpo.init_solutions

        if len(solutions) == 0:  # If initialisation found no solutions then no point in continuing.
            total_exec_time = datetime.datetime.now(datetime.UTC) - start_time
            total_n_evals = dpo.n_evals
            return OptimisationResult(solutions, total_n_evals, total_exec_time)

        max_capexs = [1.25 * val for val in dpo.max_capexs]  # Add 25% extra CAPEX in case initialisation didn't converge

        sub_portfolio_site_ids = [[site.site_data.site_id for site in portfolio] for portfolio in sub_portfolios]

        # We select a random subset of the solutions since they usually are all quite similar which leads to bad model fitting.
        # TODO: Make the sampler less random, ex: Sobol sampling
        train_x, train_y = convert_solution_list_to_tensor(
            solutions=list(rng.choice(a=solutions, size=max(1, int(0.25 * len(solutions))), replace=False)),  # type: ignore
            sub_portfolio_site_ids=sub_portfolio_site_ids,
            objectives=objectives,
        )

        logger.debug(f"Currently have {len(solutions)} Pareto-optimal solutions.")
        logger.debug(f"Currently have {len(train_x)} training points.")

        candidates = generate_random_train_x(n=self.n_initialisation_points, max_capexs=max_capexs, capex_limit=capex_limit)
        for k, candidate in enumerate(candidates):
            logger.debug(f"On random candidate {k + 1} / {self.n_initialisation_points}.")
            new_solutions = dpo.evaluate(candidate)

            if len(new_solutions) > 0:
                solutions = portfolio_pareto_front(solutions + new_solutions, objectives)

                # TODO: Improve the sampling of the new solutions, ex: Sobol sampling.
                # Converting all new solutions into training points would be best, but increasing the number of points makes
                # the fitting process slower.
                new_train_x, new_train_y = convert_solution_list_to_tensor(
                    solutions=list(rng.choice(a=new_solutions, size=max(1, int(0.25 * len(new_solutions))), replace=False)),  # type: ignore
                    sub_portfolio_site_ids=sub_portfolio_site_ids,
                    objectives=objectives,
                )
                train_x = torch.cat([train_x, new_train_x])
                train_y = torch.cat([train_y, new_train_y])

        logger.debug(f"Currently have {len(solutions)} Pareto-optimal solutions.")
        logger.debug(f"Currently have {len(train_x)} training points.")

        ref_point = create_reference_point(train_y)
        bounds = create_capex_allocation_bounds([0] * n_sub_portfolios, max_capexs)
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
                capex_limit=capex_limit,
                num_restarts=self.num_restarts,
                raw_samples=self.raw_samples,
            )

            for k, candidate in enumerate(candidates):
                logger.debug(f"On batch {k + 1} / {self.batch_size}.")
                new_solutions = dpo.evaluate(candidate)

                if len(new_solutions) > 0:
                    solutions = portfolio_pareto_front(solutions + new_solutions, objectives)

                    # TODO: Improve the sampling of the new solutions, ex: Sobol sampling.
                    # Converting all new solutions into training points would be best, but increasing the number of points makes
                    # the fitting process slower and if too many points are near identical, can lead to failed fits.
                    new_train_x, new_train_y = convert_solution_list_to_tensor(
                        solutions=list(rng.choice(a=new_solutions, size=max(1, int(0.25 * len(new_solutions))), replace=False)),  # type: ignore
                        sub_portfolio_site_ids=sub_portfolio_site_ids,
                        objectives=objectives,
                    )
                    train_x = torch.cat([train_x, new_train_x])
                    train_y = torch.cat([train_y, new_train_y])

            logger.debug(f"Currently have {len(solutions)} Pareto-optimal solutions.")
            logger.debug(f"Currently have {len(train_x)} training points.")

            ref_point = create_reference_point(train_y)

            mll, model = initialise_model(train_x, train_y, bounds)

            if state_dict is not None:
                model.load_state_dict(state_dict)

        torch.cuda.empty_cache()

        total_exec_time = datetime.datetime.now(datetime.UTC) - start_time
        total_n_evals = dpo.n_evals

        return OptimisationResult(solutions, total_n_evals, total_exec_time)


def split_into_sub_portfolios(portfolio: list[Site], n_per_sub_portfolio: int) -> list[list[Site]]:
    """
    Split a portfolio into sub portfolios each containing n_per_sub_portfolio sites,
    except the last sub portfolio if the number of sites isn't divisible by n_per_sub_portfolio.

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
    sub_portfolios = [portfolio[i : i + n_per_sub_portfolio] for i in range(0, len(portfolio), n_per_sub_portfolio)]
    return sub_portfolios


def generate_random_train_x(n: int, max_capexs: list[float], capex_limit: float):
    """
    Generate n CAPEX allocation splits randomly.

    Parameters
    ----------
    n
        Number of training points to generate.
    max_capexs
        List of upper CAPEX limits, one for each site.
    capex_limit
        Upper CAPEX limit for the whole portfolio.

    Returns
    -------
    candidates
        An 2D array of training points
    """
    candidates = []
    for _ in range(n):
        candidate = np.zeros(len(max_capexs))
        remaining = capex_limit
        for i, max_capex in enumerate(max_capexs):
            high = min(max_capex, remaining)
            point = np.random.uniform(0, high)
            candidate[i] = point
            remaining -= point
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


# TODO: improve reference point creation
def create_reference_point(train_y: torch.Tensor) -> torch.Tensor:
    """
    Creates a reference point for the hypervolume by taking the best value for each objective, reducing it by 10%
    and taking away one.

    Parameters
    ----------
    train_y
        A n x m tensor of training observations (Portfolio objective values).

    Returns
    -------
    ref_point
        A reference point in the outcome space (Objective values).
    """
    ref_point, _ = torch.min(train_y, dim=0)

    return ref_point


def create_capex_allocation_bounds(min_capexs: list[float], max_capexs: list[float]) -> torch.Tensor:
    """
    Creates a tensor representation of the bounds on the capex allocations.
    The capex allocations are bound to [min_capex, max_capex].

    Parameters
    ----------
    min_capexs
        Lower CAPEX limit for each portfolio.
    max_capexs
        Upper CAPEX limit for each portfolio.

    Returns
    -------
    bounds
        A 2 x d tensor of lower and upper bounds for each of the train_x's d columns (Bounds on the sites' CAPEX allocations).
    """
    bounds = torch.tensor(np.array([min_capexs, max_capexs]), **_TKWARGS)
    return bounds


def optimize_acquisition_func_and_get_candidate(
    model: GPyTorchModel,
    train_x: torch.Tensor,
    mc_samples: int,
    ref_point: torch.Tensor,
    bounds: torch.Tensor,
    batch_size: int,
    capex_limit: float,
    num_restarts: int,
    raw_samples: int,
) -> npt.NDArray:
    """
    Optimises the acquisition function and returns a new candidate.

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
        partitioning=partitioning,
        sampler=sampler,
    )
    n_sub_portfolios = train_x.shape[-1]
    # Define constraints on the features (CAPEX allocations).
    # The sum of the allocations must be smaller than the CAPEX limit.
    indeces = torch.tensor(list(range(n_sub_portfolios)), dtype=torch.int, device=_TDEVICE)
    coefficients = torch.tensor([-1.0] * n_sub_portfolios, **_TKWARGS)
    inequality_constraints = [(indeces, coefficients, -capex_limit)]
    # The sum of the allocations must be greater than 0.
    indeces = torch.tensor(list(range(n_sub_portfolios)), dtype=torch.int, device=_TDEVICE)
    coefficients = torch.tensor([1.0] * n_sub_portfolios, **_TKWARGS)
    inequality_constraints.append((indeces, coefficients, 0))

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

    return candidates_arr


def extract_sub_portfolio_capex_allocations(
    solution: PortfolioSolution, sub_portfolio_site_ids: list[list[str]]
) -> list[float]:
    """
    Extracts the sub portfolio CAPEX allocations from a portfolio solution.

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
    capex_allocations_per_sub = [
        sum(solution.scenario[site_id].metric_values[Metric.capex] for site_id in portfolio)
        for portfolio in sub_portfolio_site_ids
    ]
    return capex_allocations_per_sub


def convert_solution_list_to_tensor(
    solutions: list[PortfolioSolution],
    sub_portfolio_site_ids: list[list[str]],
    objectives: list[Metric],
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Convert a list of PortfolioSolutions into a feature (CAPEX allocations) and observation (Objective values) tensors.

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
    for solution in solutions:
        train_x.append(extract_sub_portfolio_capex_allocations(solution, sub_portfolio_site_ids))
        # Botorch maximises
        train_y.append([solution.metric_values[objective] * -MetricDirection[objective] for objective in objectives])

    train_x_t, train_y_t = torch.tensor(train_x, **_TKWARGS), torch.tensor(train_y, **_TKWARGS)
    return train_x_t, train_y_t
