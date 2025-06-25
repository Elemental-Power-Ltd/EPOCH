"""Models for the Thermal Model fitting and generating process."""

# ruff: noqa: D101

import pydantic

# watch out for cicular imports!
from ..internal.thermal_model.rdsap import estimate_window_area
from .core import DatasetID, SiteIDWithTime


class ThermalModelRequest(SiteIDWithTime):
    n_iter: pydantic.PositiveInt = pydantic.Field(
        default=10,
        description="Number of Bayesian optimisation iterations to try in the fitting process",
        examples=[10, 100, 500],
    )


class ThermalModelHeatingLoadRequest(SiteIDWithTime, DatasetID):
    pass


class SurveyedSizes(pydantic.BaseModel):
    n_floors: int = pydantic.Field(default=2, description="Number of floors, including the ground.")
    total_floor_area: float = pydantic.Field(description="Total interior floor area across all floors in m^2")
    exterior_wall_area: float = pydantic.Field(description="Exterior surface area of the walls in m^2")
    ceiling_area: float = pydantic.Field(
        default_factory=lambda data: data["total_floor_area"] / data["n_floors"],
        description="Flat interior surface area of the ceilings in m^2 where we could insulate,"
        + "assumed to be the same as a single floor area if not provided.",
    )
    window_area: float = pydantic.Field(
        default_factory=lambda data: estimate_window_area(data["total_floor_area"]),
        description="Exterior surface area of windows in m^2; will estimate from floor area if not provided.",
    )
    boiler_power: float = pydantic.Field(
        default_factory=lambda data: 100 * data["total_floor_area"],
        description="Power of the boiler in W; assumed to be 100 W / m^2 if not specified.",
    )
    ach: float = pydantic.Field(
        description="Air changes per hour as measured by the survey"
        + " (you may have to calculate this from the reading in litres per hour)",
        default=2.0,
    )
