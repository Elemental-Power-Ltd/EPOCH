import datetime
import logging
import warnings
from typing import TypedDict

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
from botorch.models.transforms.outcome import Standardize  # type: ignore
from botorch.optim.optimize import optimize_acqf  # type: ignore
from botorch.sampling.normal import IIDNormalSampler  # type: ignore
from botorch.utils.multi_objective.box_decompositions.non_dominated import (  # type: ignore
    FastNondominatedPartitioning,  # type: ignore
)
from botorch.utils.transforms import normalize  # type: ignore
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood  # type: ignore

from app.internal.bayesian.distributed_portfolio_optimiser import DistributedPortfolioOptimiser
from app.internal.NSGA2 import NSGA2
from app.internal.pareto_front import portfolio_pareto_front
from app.models.algorithms import Algorithm
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric, MetricDirection
from app.models.result import OptimisationResult, PortfolioSolution

logger = logging.getLogger("default")


class TKWARGS(TypedDict):
    dtype: torch.dtype
    device: torch.device


_TDEVICE = torch.device("cpu")
_TKWARGS = TKWARGS(dtype=torch.double, device=_TDEVICE)


warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserInputWarning)


class Bayesian(Algorithm):
    def __init__(
        self,
        n_per_sub_portfolio: int = 1,
        n_generations: int = 10,
        batch_size: int = 4,
        num_restarts: int = 10,
        raw_samples: int = 512,
        mc_samples: int = 128,
        **kwargs,
    ):
        self.n_per_sub_portfolio = n_per_sub_portfolio
        self.num_restarts = num_restarts
        self.raw_samples = raw_samples
        self.n_generations = n_generations
        self.batch_size = batch_size
        self.mc_samples = mc_samples
        self.NSGA2 = NSGA2(**kwargs)

    def run(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]):
        start_time = datetime.datetime.now(datetime.UTC)

        assert len(portfolio) >= 2, "The portfolio must contain at least two sites."

        assert constraints.get(Metric.capex, None) is not None, "The constraints must define an upper CAPEX limit."
        assert constraints[Metric.capex].get("max", None) is not None, "The constraints must define an upper CAPEX limit."
        capex_limit = constraints[Metric.capex]["max"]

        sub_portfolios = split_into_sub_portfolios(portfolio, self.n_per_sub_portfolio)
        n_sub_portfolios = len(sub_portfolios)
        assert n_sub_portfolios > 1, "There must be at least two sub portfolios."

        # Initilise dpo
        dpo = DistributedPortfolioOptimiser(sub_portfolios, objectives, self.NSGA2, constraints)
        solutions = dpo.init_solutions

        # convert to tensors
        train_x, train_y = convert_solution_list_to_tensor(solutions, self.n_per_sub_portfolio, n_sub_portfolios, objectives)

        # initialise model
        bounds = create_capex_allocation_bounds(n_sub_portfolios, dpo.max_capexs)
        mll, model = initialise_model(train_x, train_y, bounds)

        # run n_generations rounds of Bayesian optimisation after the initial random batch
        for j in range(0, self.n_generations):
            logger.debug(f"On generations {j + 1} / {self.n_generations}.")

            # create reference point. TODO: Improve Reference point selection
            ref_point = create_reference_point(train_y)

            # fit the model
            fit_gpytorch_mll(mll)
            state_dict = model.state_dict()

            # optimize acquisition functions and get new candidates
            candidates = optimize_acquisition_func_and_get_candidate(
                model=model,
                train_x=train_x,
                mc_samples=self.mc_samples,
                ref_point=ref_point,
                bounds=bounds,
                batch_size=self.batch_size,
                capex_limit=capex_limit,
                n_sub_portfolios=n_sub_portfolios,
                num_restarts=self.num_restarts,
                raw_samples=self.raw_samples,
            )
            print(f"Candidates: {candidates}")

            # evaluate candidates
            new_solutions = []
            for k, candidate in enumerate(candidates):
                logger.debug(f"On batch {k + 1} / {self.batch_size}.")
                new = dpo.evaluate(candidate)
                logger.debug(f"Found {len(new)} solutions.")
                new_solutions.extend(new)

            if len(new_solutions) > 0:  # if new solutions have been found
                # convert to tensors
                new_train_x, new_train_y = convert_solution_list_to_tensor(
                    new_solutions, self.n_per_sub_portfolio, n_sub_portfolios, objectives
                )

                # update training points
                train_x = torch.cat([train_x, new_train_x])
                train_y = torch.cat([train_y, new_train_y])

            # initialise model for next gen
            mll, model = initialise_model(train_x, train_y, bounds)

            # Should be able to load old model dict. TODO: Fix model load bug.
            if state_dict is not None:
                model.load_state_dict(state_dict)

            solutions = portfolio_pareto_front(solutions + new_solutions, objectives)

            logger.debug(f"Currently have {len(solutions)} Pareto-optimal solutions.")

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
    print(f"Initialising model with {len(train_x)} training points.")
    train_x = normalize(train_x, bounds)
    models = []
    for i in range(train_y.shape[-1]):
        train_y_i = train_y[..., i : i + 1]
        train_yvar = torch.full_like(train_y_i, 1e-6)
        models.append(SingleTaskGP(train_x, train_y_i, train_yvar, outcome_transform=Standardize(m=1)))
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
    ref_point, _ = torch.max(train_y, dim=0)
    ref_point = ref_point * 0.9 - 1

    return ref_point


def create_capex_allocation_bounds(n_sub_portfolios: int, max_capexs: list[float]) -> torch.Tensor:
    """
    Creates a tensor representation of the bounds on the capex allocations.
    The capex allocations are bound to [0, max_capex].

    Parameters
    ----------
    n_sub_portfolios
        The number of sub portfolios.
    max_capexs
        Upper CAPEX limit for each portfolio.

    Returns
    -------
    bounds
        A 2 x d tensor of lower and upper bounds for each of the train_x's d columns (Bounds on the sites' CAPEX allocations).
    """
    bounds = torch.tensor([[0.0] * n_sub_portfolios, max_capexs], **_TKWARGS)
    return bounds


def optimize_acquisition_func_and_get_candidate(
    model: GPyTorchModel,
    train_x: torch.Tensor,
    mc_samples: int,
    ref_point: torch.Tensor,
    bounds: torch.Tensor,
    batch_size: int,
    capex_limit: float,
    n_sub_portfolios: int,
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
    n_sub_portfolios
        The number of sub portfolios.
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
        pred = model.posterior(normalize(train_x, bounds)).mean
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
    # Define constraints on the features (CAPEX allocations). The sum of the allocations must be smaller than the CAPEX limit.
    indeces = torch.tensor(list(range(n_sub_portfolios)), dtype=torch.int, device=_TDEVICE)
    coefficients = torch.tensor([-1.0] * n_sub_portfolios, **_TKWARGS)
    inequality_constraints = [(indeces, coefficients, -capex_limit)]

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
    # add capex allocation for last sub portfolio
    candidates_arr = candidates.cpu().detach().numpy()

    return candidates_arr


def extract_sub_portfolio_capex_allocations(
    solution: PortfolioSolution, n_per_sub_portfolio: int, n_sub_portfolios: int
) -> list[float]:
    """
    Extracts the sub portfolio CAPEX allocations from a portfolio solution.

    Parameters
    ----------
    solution
        The PortfolioSolution.
    n_per_sub_portfolio
        The number of sites per sub portfolio.
    n_portfolios
        The number of sub portfolios.

    Returns
    -------
    capex_allocations_per_sub
        A list of the sub portfolio CAPEX allocations.
    """
    capex_allocations_per_site = [site.metric_values[Metric.capex] for site in solution.scenario.values()]
    capex_allocations_per_sub = [
        sum(capex_allocations_per_site[i * n_per_sub_portfolio : (i + 1) * n_per_sub_portfolio])
        for i in range(n_sub_portfolios)
    ]
    return capex_allocations_per_sub


def convert_solution_list_to_tensor(
    solutions: list[PortfolioSolution],
    n_per_sub_portfolio: int,
    n_sub_portfolios: int,
    objectives: list[Metric],
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Convert a list of PortfolioSolutions into a feature (CAPEX allocations) and observation (Objective values) tensors.

    Parameters
    ----------
    solutions
        A list of N PortfolioSolutions.
    n_per_sub_portfolio
        The number of sites per sub portfolio.
    n_portfolios
        The number of sub portfolios.
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
        train_x.append(extract_sub_portfolio_capex_allocations(solution, n_per_sub_portfolio, n_sub_portfolios))
        # Botorch maximises
        train_y.append([solution.metric_values[objective] * -MetricDirection[objective] for objective in objectives])

    train_x_t, train_y_t = torch.tensor(train_x, **_TKWARGS), torch.tensor(train_y, **_TKWARGS)
    return train_x_t, train_y_t
