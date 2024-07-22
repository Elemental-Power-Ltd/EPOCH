import numba  # type: ignore
import numpy as np
import numpy.typing as npt


@numba.jit(nopython=True, fastmath=True)
def dominates(a: list | npt.NDArray, b: list | npt.NDArray, length: int) -> bool:
    """Does a dominate b?"""
    better = False
    for i in range(length):
        a_i, b_i = a[i], b[i]

        # Worse in one dimension -> does not dominate
        # This is faster than computing `at least as good` in every dimension
        if a_i > b_i:
            return False

        # Better in at least one dimension
        if a_i < b_i:
            better = True
    return better


@numba.jit(nopython=True, fastmath=True)
def window_dominates_cost(
    window: list[list] | npt.NDArray,
    cost: list | npt.NDArray,
    window_rows: int,
    window_cols: int,
) -> int:
    for i in range(window_rows):
        if dominates(window[i], cost, window_cols):
            return i
    return -1


@numba.jit(nopython=True, fastmath=True)
def cost_dominates_window(
    window: list[list] | npt.NDArray,
    cost: list | npt.NDArray,
    window_rows: int,
    window_cols: int,
) -> list[int]:
    return [i for i in range(window_rows) if dominates(cost, window[i], window_cols)]


@numba.jit(nopython=True)
def BNL(costs: npt.NDArray[np.floating]) -> npt.NDArray[np.bool_]:
    """
    Block nested loops algorithm.
    """

    is_efficient = np.arange(costs.shape[0])
    n_costs, n_objectives = costs.shape
    num_efficient = 1  # Always put the first row in the window

    window_changed = True

    for i in range(1, n_costs):  # Skip the first row, since it's in the window
        # Get the cost for this row
        this_cost = costs[i]

        # If the window indices changed in the last iteration, get window again
        if window_changed:
            window = costs[is_efficient[:num_efficient]]
            window_rows, window_cols = window.shape
            window_changed = False

        # CASE 1 : DOES ANYTHING IN THE WINDOW DOMINATE THIS COST?
        # --------------------------------------------------------

        dom_index = window_dominates_cost(window, this_cost, window_rows, window_cols)
        # `dom_index` is the index of the first window element that dominates
        # the cost. If no window elements dominate the cost, -1 is returned.
        if dom_index >= 0:
            continue  # Window dominates cost, move on.

        # CASE 2 : DOES THIS COST DOMINATE ANYTHING IN THE WINDOW?
        # --------------------------------------------------------

        # Check if anything in the window is dominated by the point in question
        dominated_inds_window = cost_dominates_window(window, this_cost, window_rows, window_cols)
        # A point in the window is dominated, remove it
        if len(dominated_inds_window) != 0:
            # Get the original indices to remove
            to_removes = [is_efficient[k] for k in dominated_inds_window]
            for to_remove in to_removes:
                # Original indices of elements in the window
                for j, efficient in enumerate(is_efficient):
                    # Found a match, remove it
                    if efficient == to_remove:
                        # Move one to the left and decrement
                        is_efficient[j:num_efficient] = is_efficient[j + 1 : num_efficient + 1]
                        num_efficient -= 1
                        break  # Break out here

        # CASE 3 : ADD THE NEW COST TO THE WINDOW
        # ---------------------------------------

        # Insert the index value of the point in the last position
        is_efficient[num_efficient] = i
        # Increment the number of efficient points
        num_efficient += 1
        window_changed = True

    bools = np.zeros(costs.shape[0], dtype=np.bool_)
    bools[is_efficient[:num_efficient]] = 1
    return bools


def paretoset(costs: npt.NDArray[np.floating], sense: npt.NDArray) -> npt.NDArray:
    """Return boolean mask indicating the Pareto set of (non-NaN) numerical data.

    Parameters
    ----------
    costs
        Array or DataFrame of shape (observations, objectives).
    sense
        List with strings for each column (objective). The value `min` (default)
        indicates minimization, `max` indicates maximization and `diff` indicates
        different values. Using `diff` is equivalent to a group-by operation
        over the columns marked with `diff`. If None, minimization is assumed.
    distinct : bool
        How to treat duplicate rows. If `True`, only the first duplicate is returned.
        If `False`, every identical observation is returned instead.

    Returns
    -------
    mask : np.ndarray
        Boolean mask with `True` for observations in the Pareto set.
    """
    conv_costs = costs * sense

    return BNL(conv_costs)
