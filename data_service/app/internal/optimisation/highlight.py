"""Logic for highlighting specific results from within the pareto front."""

from app.models import PortfolioOptimisationResult
from app.models.optimisation import HighlightedResult, HighlightReason


def find_best_payback_horizon(portfolio_results: list[PortfolioOptimisationResult]) -> HighlightedResult | None:
    """
    Find the result with the best payback horizon from the portfolio results.

    Returns None if there are no results with a valid payback horizon.

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A HighlightedResult or None
    """
    # negative paybacks are not valid, we filter them out along with any None values
    valid_paybacks = [
        result
        for result in portfolio_results
        if result.metrics.payback_horizon is not None and result.metrics.payback_horizon >= 0
    ]

    if valid_paybacks:
        best_payback = min(valid_paybacks, key=lambda payback: payback.metrics.payback_horizon)  # type: ignore

        return HighlightedResult(portfolio_id=best_payback.portfolio_id,
                                 reason=HighlightReason.BestPaybackHorizon, display_name="Best payback horizon")
    return None


def find_best_carbon_balance(portfolio_results: list[PortfolioOptimisationResult]) -> HighlightedResult | None:
    """
    Find the result with the best combined scope 1 and scope 2 carbon balance from the portfolio results.

    Returns None if there are no results with valid carbon balances.

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A HighlightedResult or None
    """
    valid_carbon = [
        result
        for result in portfolio_results
        if result.metrics.carbon_balance_scope_1 is not None and result.metrics.carbon_balance_scope_2 is not None
    ]
    if valid_carbon:
        best_carbon_balance = max(
            valid_carbon,
            key=lambda r: (r.metrics.carbon_balance_scope_1 + r.metrics.carbon_balance_scope_2),  # type: ignore
        )
        return HighlightedResult(portfolio_id=best_carbon_balance.portfolio_id,
                                 reason=HighlightReason.BestCarbonBalance, display_name="Best carbon savings")
    return None


def find_best_cost_balance(portfolio_results: list[PortfolioOptimisationResult]) -> HighlightedResult | None:
    """
    Find the result with the best cost balance from the portfolio results.

    Returns None if there are no results with a valid cost balance.

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A HighlightedResult or None
    """
    valid_cost = [result for result in portfolio_results if result.metrics.cost_balance is not None]
    if valid_cost:
        best_cost_balance = max(valid_cost, key=lambda r: r.metrics.cost_balance)  # type: ignore
        return HighlightedResult(portfolio_id=best_cost_balance.portfolio_id,
                                 reason=HighlightReason.BestCostBalance, display_name="Best cost savings")
    return None


def pick_highlighted_results(portfolio_results: list[PortfolioOptimisationResult]) -> list[HighlightedResult]:
    """
    Pick highlighted results out of the portfolio results.

    This returns a list of portfolio_id, HighlightReason pairs.
    - the same result may be highlighted for multiple different reasons
    - it is possible for no results to be highlighted

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A list of Highlighted Results

    """
    if len(portfolio_results) == 0:
        return []

    results: list[HighlightedResult] = []

    if best_payback := find_best_payback_horizon(portfolio_results):
        results.append(best_payback)

    if best_carbon_balance := find_best_carbon_balance(portfolio_results):
        results.append(best_carbon_balance)

    if best_cost_balance := find_best_cost_balance(portfolio_results):
        results.append(best_cost_balance)

    return results
