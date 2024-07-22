import matplotlib.pyplot as plt
import numpy.typing as npt
import pandas as pd
from matplotlib.figure import Figure


def search_space_fitness_plot(
    objectives: dict[str, int],
    fitnesses: npt.NDArray,
    search_space_variables: dict,
    solutions: npt.NDArray,
) -> Figure:
    """
    Creates a figure that summarises the objectives fitness values for a search space.
    The figure contains a plot for each pair of (objective, search space variable) which indicates the optimal objective values
    for each parameter value for any combination of other search space variables.
    Example: For a set of search space variables [X, Y, Z] and objectives [A, B, C], the plot of parameter X on objective A
    details the optimal objective values achieved for each value of X for any combination of Y and Z.

    Parameters
    ----------
    objectives
        Dictionary of objectives with corresponding optimisation direction.
    fitnesses
        Array of objective fitness values.
    search_space_variables
        Dictionary of search space varaibles with corresponding list of lower and upper bounds and step.
    solutions
        Array of parameter values for fitnesses.

    Returns
    -------
    Fig
        Figure containing plots.
    """
    ss_var_names = list(search_space_variables.keys())
    object_names = list(objectives.keys())
    df_fit = pd.DataFrame(fitnesses, columns=object_names)
    df_sol = pd.DataFrame(solutions, columns=ss_var_names)
    df = pd.concat([df_fit, df_sol], axis=1)
    n_objectives = len(objectives.keys())

    fig, ax = plt.subplots(nrows=len(ss_var_names), ncols=n_objectives, figsize=(20, 3 * len(ss_var_names)))  # type: ignore

    for i, parameter in enumerate(ss_var_names):
        for j, (objective, sense) in enumerate(objectives.items()):
            if sense == -1:
                df.groupby(parameter)[objective].max().plot(
                    ax=ax[i, j],  # type: ignore
                    color="green",
                    linestyle="--",
                    marker="o",
                )
            elif sense == 1:
                df.groupby(parameter)[objective].min().plot(
                    ax=ax[i, j],  # type: ignore
                    color="red",
                    linestyle="--",
                    marker="o",
                )

            df.groupby(parameter)[objective].mean().plot(
                ax=ax[i, j],  # type: ignore
                color="black",
                linestyle="--",
                marker="o",
                secondary_y=True,
                alpha=0.5,
                grid=True,
            )

        ax[i, j].xaxis.grid(True, which="minor", linestyle="-", linewidth=0.25)  # type: ignore

    for j, (objective, sense) in enumerate(objectives.items()):
        if sense == -1:
            fig.text(
                j / n_objectives + 0.1,
                1,
                objective,
                ha="center",
                bbox={"facecolor": "green", "alpha": 0.5},
            )
        elif sense == 1:
            fig.text(
                j / n_objectives + 0.1,
                1,
                objective,
                ha="center",
                bbox={"facecolor": "red", "alpha": 0.5},
            )

    fig.tight_layout()
    return fig
