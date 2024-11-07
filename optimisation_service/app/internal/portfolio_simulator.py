from itertools import product
from os import PathLike

from app.internal.task_data_wrapper import PySimulationResult, PyTaskData, Simulator
from app.models.objectives import _OBJECTIVES, Objectives
from app.models.result import BuildingSolution, ObjectiveValues, PortfolioSolution


class PortfolioSimulator:
    """
    Provides portfolio simulation by initialising multiple EPOCH simulator's.
    """

    def __init__(self, input_dirs: dict[str, PathLike]) -> None:
        """
        Initialise the various EPOCH simulators.

        Parameters
        ----------
        input_dirs
            Dictionary of building names and directories containing input data.

        Returns
        -------
        None
        """
        self.sims = {name: Simulator(inputDir=str(input_dir)) for name, input_dir in input_dirs.items()}

    def simulate_portfolio(self, portfolio_tasks: dict[str, PyTaskData]) -> PortfolioSolution:
        """
        Simulate a portfolio.

        Parameters
        ----------
        portfolio_tasks
            Dictionary of building names and task data.

        Returns
        -------
        PortfolioSolution
            solution: dictionary of buildings names and evaluated candidate building solutions.
            objective_values: objective values of the portfolio.
        """
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


def combine_objective_values(
    objective_values_list: list[PySimulationResult] | list[ObjectiveValues] | list[PySimulationResult | ObjectiveValues],
) -> list[PySimulationResult] | list[ObjectiveValues] | list[PySimulationResult | ObjectiveValues]:
    """
    Combine a list of objective values into a single list of objective values.
    Most objectives can be summed, but some require more complex functions.

    Parameters
    ----------
    objective_values_list
        List of objective value dictionaries.

    Returns
    -------
    combined
        Dictionary of objective values.
    """
    combined = {objective: sum(obj_vals[objective] for obj_vals in objective_values_list) for objective in _OBJECTIVES}
    combined[Objectives.payback_horizon] = combined[Objectives.capex] / combined[Objectives.cost_balance]
    return combined


def gen_all_building_combinations(building_solutions_dict: dict[str, list[BuildingSolution]]) -> list[PortfolioSolution]:  # type: ignore
    """
    Generate a list of all possible portfolio solutions for a group of buildings and there multiple building solutions.

    Parameters
    ----------
    building_solutions_dict
        Dictionary of building names and list of building solutions.

    Returns
    -------
    portfolio_solutions
        List of portfolio solutions.
    """
    building_names = list(building_solutions_dict.keys())
    all_combinations = product(*building_solutions_dict.values())

    portfolio_solutions = []
    for combination in all_combinations:
        solution_dict = dict(zip(building_names, combination))
        objective_values = [building.objective_values for building in combination]
        portfolio_objective_values = combine_objective_values(objective_values)

        portfolio_solution = PortfolioSolution(solution=solution_dict, objective_values=portfolio_objective_values)

        portfolio_solutions.append(portfolio_solution)

    return portfolio_solutions
