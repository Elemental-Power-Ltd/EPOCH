"""Models for endpoints in heating_load.py, including DHW and heating load."""

# ruff: noqa: D101
import datetime
from enum import StrEnum
from typing import Self

import pydantic
from pydantic import Field

from .core import EpochEntry, RequestBase, dataset_id_t, site_id_field, site_id_t
from .thermal_model import SurveyedSizes


class ThermalModelResult(pydantic.BaseModel):
    scale_factor: pydantic.NonNegativeFloat = pydantic.Field(description="Multiplier of the floor area; 1.0 is 100m^2.")
    ach: pydantic.NonNegativeFloat = pydantic.Field(description="Air changes per hour; for a domestic building this is 1 - 4.")
    u_value: pydantic.NonNegativeFloat = pydantic.Field(description="U-value of the main wall building material.")
    boiler_power: pydantic.NonNegativeFloat = pydantic.Field(description="Heating output power of the boiler in W")
    setpoint: pydantic.NonNegativeFloat = pydantic.Field(description="Target temperature of the building thermostat in °C")
    dhw_usage: pydantic.NonNegativeFloat = pydantic.Field(description="Daily domestic hot water usage in kWh")
    r2_score: float | None = pydantic.Field(
        description="R^2 score of this thermal model against the original gas meter data." + ""
        "1.0 is the best possible score, but may be infinitely negative, or None if not calculated.",
        default=None,
    )


class InterventionEnum(StrEnum):
    Loft = "loft"
    DoubleGlazing = "double_glazing"
    Cladding = "cladding"


class HeatingLoadEntry(pydantic.BaseModel):
    timestamp: pydantic.AwareDatetime = pydantic.Field(
        examples=["2024-07-30T14:00:00Z"],
        description="Starting timestamp this reading covers."
        + "You can construct the usual (start_ts, end_ts) pairs by using the timedelta field.",
    )
    predicted: float | None = Field(examples=[0.512], description="Total predicted heating + DHW energy usage at this time.")
    dhw: float | None = Field(examples=[0.256], description="Predicted domestic hot water energy usage at this time.")
    heating: float | None = Field(examples=[0.256], description="Predicted heating usage at this time.")
    timedelta: datetime.timedelta = Field(
        examples=[1800.0],
        description="Length of time in seconds this reading covers, such that the"
        + "reading covers [timestamp, timestamp + timedelta]",
    )
    hdd: float | None = Field(examples=[0.01], description="Heating degree days due to external weather in this period.")


class FabricCostBreakdown(pydantic.BaseModel):
    name: str
    area: float | None
    cost: float


class FabricIntervention(pydantic.BaseModel):
    cost: float = pydantic.Field(description="Cost associated with this fabric intervention in £")
    cost_breakdown: list[FabricCostBreakdown] = pydantic.Field(
        default=[],
        description="Breakdown of costs in £ including the areas affected by each intervention."
        " If unknown, this is an empty list.",
    )
    reduced_hload: list[float] = pydantic.Field(
        examples=[[0.123, 4.56]], description="Heating demand in kWh th for this time period."
    )
    peak_hload: float = pydantic.Field(
        description="Peak heating demand from a survey in kWth", default_factory=lambda data: max(data["reduced_hload"])
    )


class EpochHeatingEntry(EpochEntry):
    data: list[FabricIntervention] = pydantic.Field(
        examples=[[0.123, 4.56]],
        description="List of heating loads representing various fabric interventions with corresponding cost.",
    )


class EpochAirTempEntry(EpochEntry):
    data: list[float] = pydantic.Field(
        examples=[[16.0, 15.5, 15.0, 14.7]], description="Air temperature for this time period in °C."
    )


class EpochDHWEntry(EpochEntry):
    data: list[float] = pydantic.Field(
        examples=[[0.123, 4.56]], description="Domestic hot water demand in kWh for this time period."
    )


class HeatingLoadModelEnum(StrEnum):
    Regression = "regression"
    ThermalModel = "thermal_model"
    PHPP = "phpp"
    Auto = "auto"


class HeatingLoadRequest(RequestBase):
    dataset_id: dataset_id_t
    interventions: list[InterventionEnum] | list[str] = Field(
        examples=[[InterventionEnum.Loft], [], ["Internal Insulation to external solid wall", "Secondary Glazing"]],
        default=[],
        description="List of energy saving intervention to make for this site.  "
        "Either a InterventionEnum for the thermal model or a THIRD_PARTY title for survey results; "
        + " THIRD_PARTY interventions can be found in costs.py."
        + " If an empty list, apply no interventions.",
    )
    apply_bait: bool = True
    dhw_fraction: float = Field(
        default=1.0,
        description="What fraction of the non-varying load is due to DHW."
        + "For most buildings this should be 1, unless there is an unusually inefficient heating system.",
    )
    model_type: HeatingLoadModelEnum = Field(
        description=(
            "Which type of underyling heating load model to use."
            + "By default, will try to use a thermal model if there's one available, and regression if not."
        ),
        default=HeatingLoadModelEnum.Auto,
    )
    site_id: site_id_t | None = pydantic.Field(description="The site ID you want to analyse", default=None)
    structure_id: dataset_id_t | None = Field(
        description="Which underlying thermal model to use if in thermal model mode", default=None
    )
    savings_fraction: float = Field(
        examples=[0.0, 1.0, 0.15],
        default=0.0,
        description="Fraction of savings on the hetaing due to this interventions (leave as 0 if using estimated fabric).",
    )

    surveyed_sizes: SurveyedSizes | None = pydantic.Field(description="Surveyed sizes of the building in m2", default=None)
    seed: int | None = pydantic.Field(default=None, description="Random seed used to ensure reproducibility")

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self

    @pydantic.field_validator("interventions", mode="after")
    @classmethod
    def check_all_enum_interventions(
        cls, interventions: list[str] | list[InterventionEnum]
    ) -> list[str] | list[InterventionEnum]:
        """Check if all the interventions are generic or specific.

        If all the interventions are specific (given as a str), then return the list of strings.
        If they're all generic (given as an entry in InterventionEnum) then pydantic might misread them as strings
        because that's how they come over the wire. We have to manually convert them here.

        If there's a mixture of generic and specific interventions, then error out -- we assume that everything is
        the same type elsewhere.

        Parameters
        ----------
        cls
            HeatingLoadRequest or similar
        interventions
            List of interventions, likely a list of generic or specific strings

        Returns
        -------
        list[str]
            If all the entries are specific interventions
        list[InterventionEnum]
            If all the entries are generic interventions

        Raises
        ------
        ValueError
            If there's a mix of generic and specific
        """
        converted = [InterventionEnum(item) for item in interventions if item in InterventionEnum]
        if not converted:
            # We couldn't convert any of them, so they're all strings
            return interventions
        if len(converted) == len(interventions):
            # We converted all of them
            return converted
        raise ValueError(f"Got mixed specific interventions and generic interventions in {interventions}")


class HeatingLoadMetadata(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    dataset_id: dataset_id_t = Field(description="UUID for heating load")
    created_at: pydantic.AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        examples=["2024-07-30T14:13:00Z"],
        description="The time this dataset was created",
    )
    params: pydantic.Json = Field(
        examples=["{'source_dataset': '...'}"],
        description="Parameters used to generate this dataset, for example the original dataset.",
    )
    interventions: list[InterventionEnum] | list[str] = Field(
        examples=["Loft"],
        default=[],
        description="List of interventions to apply, either generic ones for us to estimate or THIRD_PARTY-provided names",
    )
    generation_method: HeatingLoadModelEnum = Field(
        examples=[HeatingLoadModelEnum.Regression, HeatingLoadModelEnum.PHPP],
        description="Which method was used to generate this heating load",
    )
    peak_hload: float | None = Field(
        default=None,
        description="Peak heating load in kW associated with this set of interventions."
        " May be higher than that actually experienced during the dataset.",
    )


class PhppMetadata(pydantic.BaseModel):
    """Metadata for a PHPP, including the file it came from and some non-element data that might be useful."""

    filename: str | None
    site_id: site_id_t
    internal_volume: float = pydantic.Field(description="Air volume in m3 within the envelope of this building.")
    air_changes: float = pydantic.Field(description="Air changes per hour in this building as estimated during survey.")
    floor_area: float
    structure_id: dataset_id_t
    created_at: pydantic.AwareDatetime


class IsInterventionFeasible(pydantic.BaseModel):
    name: str = pydantic.Field(description="Name of this intervention.")
    is_feasible: bool = pydantic.Field(description="Whether this intervention is feasible on this site.")
