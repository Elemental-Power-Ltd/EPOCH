"""Logic for highlighting specific results from within the pareto front."""
from app.models import PortfolioOptimisationResult
from app.models.optimisation import HighlightedResult, HighlightReason


def pick_highlighted_results(portfolio_results: list[PortfolioOptimisationResult]) -> list[HighlightedResult]:
    """
    Pick highlighted results out of the portfolio results.

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A list of Highlighted Results

    """
    if len(portfolio_results) == 0:
        return []

    results = []

    # negative paybacks are not valid, we filter them first
    # for each of these, we filter out any None values (we then do or 0 to keep mypy happy)
    valid_paybacks = [
        result for result in portfolio_results
        if result.metrics.payback_horizon is not None and result.metrics.payback_horizon >= 0]
    if valid_paybacks:
        best_payback = min(valid_paybacks, key=lambda payback: payback.metrics.payback_horizon or 0.0)
        results.append(HighlightedResult(portfolio_id=best_payback.portfolio_id, reason=HighlightReason.BestPaybackHorizon))

    valid_carbon = [
        result for result in portfolio_results
        if result.metrics.carbon_balance_scope_1 is not None and result.metrics.carbon_balance_scope_2 is not None
    ]
    if valid_carbon:
        best_carbon_balance = max(
            valid_carbon,
            key=lambda result: (result.metrics.carbon_balance_scope_1 or 0.0) + (result.metrics.carbon_balance_scope_2 or 0.0)
        )
        results.append(
            HighlightedResult(portfolio_id=best_carbon_balance.portfolio_id, reason=HighlightReason.BestCarbonBalance)
        )

    valid_cost = [result for result in portfolio_results if result.metrics.cost_balance is not None]
    if valid_cost:
        best_cost_balance = max(valid_cost, key=lambda result: result.metrics.cost_balance or 0.0)
        results.append(HighlightedResult(portfolio_id=best_cost_balance.portfolio_id, reason=HighlightReason.BestCostBalance))

    return results
