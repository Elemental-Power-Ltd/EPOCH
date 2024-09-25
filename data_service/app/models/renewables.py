"""Models for endpoints in renewables.py, mostly solar PV generation."""

# ruff: noqa: D101
import datetime
from enum import StrEnum
from typing import Self

import pydantic

from .core import EpochEntry, dataset_id_field, site_id_field, site_id_t


class RenewablesRequest(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2020-01-01T00:00:00Z"], description="The starting time to run the renewables calculation, should be <2021."
    )
    end_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=["2021-01-01T00:00:00Z"],
        description="The ending time to run the renewables calculation, should be one year on from start_ts",
    )
    azimuth: float | None = pydantic.Field(
        default=None,
        examples=[178.0, 182.0, None],
        description="Angle from compass north, 180° is due south. For None, use the optimum azimuth.",
    )
    tilt: float | None = pydantic.Field(
        default=None,
        examples=[30.0, 40.0, None],
        description="Tilt from the horizontal, 90° is vertical. For None, use the optimum tilt.",
    )
    tracking: bool = pydantic.Field(
        default=False, examples=[False, True], description="Whether these panels use single axis tracking."
    )

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self


class RenewablesMetadata(pydantic.BaseModel):
    data_source: str = pydantic.Field(
        examples=["renewables.ninja", "PVGIS"], description="The data source we used to generate this."
    )
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC), description="The time we generated this dataset at"
    )
    dataset_id: pydantic.UUID4 = dataset_id_field
    site_id: site_id_t = site_id_field
    parameters: pydantic.Json = pydantic.Field(description="The parameters we sent to the data source in generating this.")


class EpochRenewablesEntry(EpochEntry):
    RGen1: float = pydantic.Field(examples=[0.123, 4.56], description="The renewables generation in kW / kWp for this array.")
    RGen2: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="The renewables generation in kW / kWp for this array."
    )
    RGen3: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="The renewables generation in kW / kWp for this array."
    )
    RGen4: float | None = pydantic.Field(
        default=None, examples=[0.123, 4.56], description="The renewables generation in kW / kWp for this array."
    )


class PvgisDataSourceEnum(StrEnum):
    SARAH = "PVGIS-SARAH"
    NSRDB = "PVGIS-NSRDB"
    ERA5 = "PVGIS-ERA5"
    COSMO = "PVGIS-COSMO"
    CMSAF = "PVGIS-CMSAF"
    SARAH2 = "PVGIS-SARAH2"


class PvgisMountingSystemEnum(StrEnum):
    fixed = "fixed"


class PvgisTypeEnum(StrEnum):
    building_integrated = "building-integrated"
    freestanding = "free"


class PvgisTechnologyEnum(StrEnum):
    cryst_si = "c-Si"
    cis = "CIS"
    CdTe = "CdTe"
    unknown = "Unknown"


class PVOptimaResult(pydantic.BaseModel):
    azimuth: float = pydantic.Field(
        examples=[178, 182], description="Optimal azimuth for these panels in °, with 180° being due South.", ge=-180, le=360
    )
    tilt: float = pydantic.Field(
        examples=[40.0, 75.0], description="Optimum tilt angle for fixed panels in ° from the horizontal"
    )
    altitude: float = pydantic.Field(
        examples=[5, 253.4], description="Height in m above mean sea level this was calculated for."
    )
    mounting_system: PvgisMountingSystemEnum = pydantic.Field(
        examples=["fixed"], description="Whether the PV system is fixed angle (more common) or single-axis"
    )
    type: PvgisTypeEnum = pydantic.Field(
        examples=["building-integrated", "free"], description="Whether the PV system is building integrated or freestanding."
    )
    technology: PvgisTechnologyEnum = pydantic.Field(
        examples=["c-Si", "CdTe"], description="Main panel technology, e.g. crystalline silicon"
    )
    data_source: PvgisDataSourceEnum = pydantic.Field(description="Radiation database used to calculate these optima.")
