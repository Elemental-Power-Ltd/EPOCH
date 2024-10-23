import numpy as np
from paretoset import paretoset  # typing : ignore

from app.models.objectives import _OBJECTIVES, _OBJECTIVES_DIRECTION, Objectives
from app.models.result import PortfolioSolution


def portfolio_pareto_front(portfolio_solutions: list[PortfolioSolution], objectives: list[Objectives]):
    objective_values = np.array([list(solution.objective_values.values()) for solution in portfolio_solutions])
    objective_mask = [_OBJECTIVES.index(col) for col in objectives]
    objective_values = objective_values[:, objective_mask]

    objective_direct = ["max" if _OBJECTIVES_DIRECTION[objective] == -1 else "min" for objective in objectives]
    pareto_efficient = paretoset(costs=objective_values, sense=objective_direct, distinct=True)

    return portfolio_solutions[pareto_efficient]
