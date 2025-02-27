"""Models for the Thermal Model fitting and generating process."""

# ruff: noqa: D101

import pydantic

from .core import DatasetID, SiteIDWithTime


class ThermalModelRequest(SiteIDWithTime):
    n_iter: pydantic.PositiveInt = pydantic.Field(
        default=10,
        description="Number of Bayesian optimisation iterations to try in the fitting process",
        examples=[10, 100, 500],
    )

class ThermalModelHeatingLoadRequest(SiteIDWithTime, DatasetID):
    pass
