"""Models for endpoints in heating_load.py, including DHW and heating load."""

# ruff: noqa: D101
import datetime
from enum import StrEnum
from typing import Self

import pydantic
from pydantic import Field

from .core import DatasetIDWithTime, EpochEntry, dataset_id_t, site_id_field, site_id_t
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


class FabricIntervention(pydantic.BaseModel):
    cost: float
    reduced_hload: list[float] = pydantic.Field(
        examples=[[0.123, 4.56]], description="heating demand in kWh for this time period."
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
    Auto = "auto"


class HeatingLoadRequest(DatasetIDWithTime):
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
    thermal_model_dataset_id: dataset_id_t | None = Field(
        description="Which underlying thermal model to use if in thermal model mode", default=None
    )
    savings_fraction: float = Field(
        examples=[0.0, 1.0, 0.15],
        default=0.0,
        description="Fraction of savings on the hetaing due to this interventions (leave as 0 if using estimated fabric).",
    )

    surveyed_sizes: SurveyedSizes | None = pydantic.Field(description="Surveyed sizes of the building in m2", default=None)

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


class InterventionCostRequest(pydantic.BaseModel):
    interventions: list[InterventionEnum] = pydantic.Field(default=[])
    site_id: site_id_t = site_id_field
    thermal_model_dataset_id: dataset_id_t | None = pydantic.Field(
        description="ID of the thermal model you want to use for cost calculation, defaults to None", default=None
    )


class InterventionCostResult(pydantic.BaseModel):
    breakdown: dict[InterventionEnum, float]
    total: float
