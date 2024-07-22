import os
import pathlib
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd


def typename(x: Any) -> str:
    """
    Get a string representation of the name of a class.

    Parameters
    ----------
    x
        Any python object

    Returns
    -------
        String of the name, e.g. typename(1) == "int"
    """
    return type(x).__name__


class BoundedStepSize:
    """
    Basin Hopping utility class to only take steps that are within some bounds.
    """

    def __init__(
        self,
        lbs: npt.NDArray[np.floating],
        ubs: npt.NDArray[np.floating],
        stepsize: float = 0.1,
        rng: np.random.Generator | None = None,
    ):
        """
        Set up the step sizes and bounds for BasinHopping.

        Parameters
        ----------
        lbs
            Lower bounds for each potential parameter
        ubs
            Upper bounds for each potential parameter
        stepsize
            Fraction of (ub - lb) to take, will be scaled dynamically by scipy
        """
        self.stepsize = stepsize
        if rng is None:
            self.rng = np.random.default_rng()
        else:
            self.rng = rng
        self.lbs = lbs
        self.ubs = ubs

    def __call__(self, x: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        """
        Take a scaled step.

        This will calculate a step for each variable randomly between
        [-stepsize * (upper - lower), +stepsize * (upper-lower)] for each
        variable.
        They will also be clamped to the be no lower than the lower bound,
        and no higher than the higher bound.

        Parameters
        ----------
        x
            Parameter vector to take a step from (same size as bounds)

        Returns
        -------
            stepped parameter vector
        """
        s = self.stepsize * np.abs(self.ubs - self.lbs)
        step = self.rng.uniform(-s, s)
        x = np.clip(self.lbs, x + step, self.ubs)
        return x


def hour_of_year(ts: pd.Timestamp) -> int:
    """
    Convert a given timestamp to being the indexed hour of year (starting at 1).

    YYYY-01-01 00:00 is hour 1 (to mimic Excel numbering).
    Watch out for varying timezones and DST as you go through the year.

    Parameters
    ----------
    ts
        Pandas timestamp or datetime, with a timezone

    Returns
    -------
        one-indexed hour of year
    """
    soy_ts = pd.Timestamp(year=ts.year, month=1, day=1, hour=0, minute=0, tzinfo=ts.tzinfo)
    # watch out for this off-by-one error!
    return 1 + (int((ts - soy_ts).total_seconds()) // 3600)


def load_dotenv(fname: os.PathLike = pathlib.Path(".env")) -> dict[str, str]:
    """
    Load a set of environment variables from an .env file.

    Mutates the environment variables for this python process, and
    returns them as a dictionary just in case.

    Parameters
    ----------
    fname
        Path to the environment file to load (it's probably ".env")

    Returns
    -------
        environment dictionary, with new keys added.
    """
    fpath = pathlib.Path(fname).resolve()
    if not fpath.is_file():
        file_name = fpath.name
        for parent in fpath.parents:
            parent_path = parent.joinpath(file_name)
            if parent_path.is_file():
                fpath = parent_path
                break
        else:
            raise FileNotFoundError(f"Could not find {fname} in the specified location {fpath} or its parents.")

    with open(fpath) as fi:
        for line in fi:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value
    # turn this into a dict to prevent any trouble with weird types
    return dict(os.environ.items())
