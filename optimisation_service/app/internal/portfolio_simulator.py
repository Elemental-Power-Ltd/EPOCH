from os import PathLike

from app.internal.task_data_wrapper import PySimulationResult, PyTaskData, Simulator
from app.models.objectives import _OBJECTIVES
from app.models.result import BuildingSolution, ObjectiveValues, PortfolioSolution


class PortfolioSimulator:
    def __init__(self, input_dirs: dict[str, PathLike]) -> None:
        self.sims = {name: Simulator(inputDir=str(input_dir)) for name, input_dir in input_dirs.items()}

    def simulate_portfolio(self, portfolio_tasks: dict[str, PyTaskData]) -> PortfolioSolution:
        solution = {}
        objective_values_list = []
        for name in portfolio_tasks.keys():
            task = portfolio_tasks[name]
            sim = self.sims[name]
            result = PySimulationResult(sim.simulate_scenario(task))
            solution[name] = BuildingSolution(solution=task, objective_values=result)  # TODO:Solution doesn't require taskdata
            objective_values_list.append(result)
        objective_values = combine_objective_values(objective_values_list)
        return PortfolioSolution(solution=solution, objective_values=objective_values)  # TODO:Solution doesn't require taskdata


def combine_objective_values(objective_values_list: list[ObjectiveValues]):
    combined = {objective: sum(obj_vals[objective] for obj_vals in objective_values_list) for objective in _OBJECTIVES}
    combined["payback_horizon"] = combined["capex"] / combined["cost_balance"]
    return combined
