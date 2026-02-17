import torch
from botorch.models.gp_regression import SingleTaskGP
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.models.transforms.input import Normalize
from botorch.models.transforms.outcome import Standardize
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood  # type: ignore

from app.models.core import Site
from app.models.metrics import Metric
from app.models.result import PortfolioSolution


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
