"""Logic for highlighting specific results from within the pareto front."""

from app.dependencies import DatabasePoolDep
from app.models import PortfolioOptimisationResult
from app.models.core import dataset_id_t
from app.models.optimisation import CuratedResult, HighlightedResult, HighlightReason


async def get_curated_results(task_id: dataset_id_t | None, pool: DatabasePoolDep) -> list[CuratedResult]:
    """
    Retrieve all curated results, optionally filtered by a task_id.

    Results are sorted by submission time. Most recent first.

    Parameters
    ----------
    task_id
        a task_id to filter by. Use None to retrieve all curated results.
    pool

    Returns
    -------
    A list of curated results.
    """
    if task_id is not None:
        res = await pool.fetch(
            """
            SELECT
                cr.highlight_id,
                cr.task_id,
                cr.portfolio_id,
                cr.submitted_at,
                cr.display_name
            FROM optimisation.curated_results AS cr
            WHERE cr.task_id = $1
            ORDER BY cr.submitted_at DESC
            """,
            task_id,
        )
    else:
        res = await pool.fetch(
            """
            SELECT
                cr.highlight_id,
                cr.task_id,
                cr.portfolio_id,
                cr.submitted_at,
                cr.display_name
            FROM optimisation.curated_results AS cr
            ORDER BY cr.submitted_at DESC
            """
        )

    return [
        CuratedResult(
            highlight_id=cr["highlight_id"],
            task_id=cr["task_id"],
            portfolio_id=cr["portfolio_id"],
            submitted_at=cr["submitted_at"],
            display_name=cr["display_name"],
        )
        for cr in res
    ]


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

        return HighlightedResult(
            portfolio_id=best_payback.portfolio_id,
            reason=HighlightReason.BestPaybackHorizon,
            display_name="Payback Horizon",
            suggested_metric="payback_horizon",
        )
    return None


def find_best_carbon_savings(portfolio_results: list[PortfolioOptimisationResult]) -> HighlightedResult | None:
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
    valid_carbon = [result for result in portfolio_results if result.metrics.carbon_balance_total is not None]
    if valid_carbon:
        best_carbon_balance = max(valid_carbon, key=lambda r: r.metrics.carbon_balance_total)  # type: ignore
        return HighlightedResult(
            portfolio_id=best_carbon_balance.portfolio_id,
            reason=HighlightReason.BestCarbonBalance,
            display_name="Carbon Savings",
            suggested_metric="carbon_balance_total",
        )
    return None


def find_best_cost_savings(portfolio_results: list[PortfolioOptimisationResult]) -> HighlightedResult | None:
    """
    Find the result with the best operating balance from the portfolio results.

    Returns None if there are no results with a valid cost balance.

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A HighlightedResult or None
    """
    valid_cost = [result for result in portfolio_results if result.metrics.operating_balance is not None]
    if valid_cost:
        best_operating_balance = max(valid_cost, key=lambda r: r.metrics.operating_balance)  # type: ignore
        return HighlightedResult(
            portfolio_id=best_operating_balance.portfolio_id,
            reason=HighlightReason.BestCostBalance,
            display_name="Cost Savings",
            suggested_metric="operating_balance",
        )
    return None


def find_best_return_on_investment(portfolio_results: list[PortfolioOptimisationResult]) -> HighlightedResult | None:
    """
    Find the result with the best return_on_investment from the portfolio results.

    Returns None if there are no results with a valid ROI.

    Parameters
    ----------
    portfolio_results

    Returns
    -------
        A HighlightedResult or None
    """
    valid_roi = [result for result in portfolio_results if result.metrics.return_on_investment is not None]
    if valid_roi:
        best_roi = max(valid_roi, key=lambda r: r.metrics.return_on_investment)  # type: ignore
        return HighlightedResult(
            portfolio_id=best_roi.portfolio_id,
            reason=HighlightReason.BestReturnOnInvestment,
            display_name="Return on Investment",
            suggested_metric="return_on_investment",
        )
    return None


def pick_highlighted_results(
    portfolio_results: list[PortfolioOptimisationResult], curated_results: list[CuratedResult]
) -> list[HighlightedResult]:
    """
    Pick highlighted results out of the portfolio results.

    This returns a list of portfolio_id, HighlightReason pairs.
    - the same result may be highlighted for multiple different reasons
    - it is possible for no results to be highlighted
    - if any results have been 'curated' the most recent of those will be returned

    Parameters
    ----------
    portfolio_results
        the full set of portfolio results for this task
    curated_results
        any results that have been 'curated' by the user

    Returns
    -------
        A list of Highlighted Results

    """
    if len(portfolio_results) == 0:
        return []

    results: list[HighlightedResult] = []

    if best_carbon_balance := find_best_carbon_savings(portfolio_results):
        results.append(best_carbon_balance)

    if best_roi := find_best_return_on_investment(portfolio_results):
        results.append(best_roi)

    # if there are curated results, return the most recent one
    # otherwise, highlight the result with the best operating balance
    if len(curated_results) > 0:
        # these are sorted by submission time, take the first result
        curated = curated_results[0]

        results.append(
            HighlightedResult(
                portfolio_id=curated.portfolio_id,
                reason=HighlightReason.UserCurated,
                display_name=curated.display_name,
                suggested_metric=None,
            )
        )

    elif best_cost_balance := find_best_cost_savings(portfolio_results):
        results.append(best_cost_balance)

    return results
