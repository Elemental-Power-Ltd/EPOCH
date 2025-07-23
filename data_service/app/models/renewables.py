"""Models for endpoints in renewables.py, mostly solar PV generation."""

# ruff: noqa: D101
import datetime
from enum import StrEnum

import pydantic

from .core import EpochEntry, RequestBase, dataset_id_field, site_id_field, site_id_t


class RenewablesRequest(RequestBase):
    site_id: site_id_t = site_id_field
    renewables_location_id: str | None = pydantic.Field(
        default=None,
        examples=["demo_matts_house_southroof"],
        description="Database ID of the site-associated solar location e.g. southroof",
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
    renewables_location_id: str | None = pydantic.Field(
        description="Database ID for the on-site location of this installation", default=None
    )


class EpochRenewablesEntry(EpochEntry):
    data: list[list[float]] = pydantic.Field(
        examples=[[0.123, 4.56], [5.4, 6.7]],
        description="""A list of renewable array generations.
        Each renewable array generation is a list of renewable generations in kW / kWp for this array for this time period.""",
    )


class PvgisDataSourceEnum(StrEnum):
    NSRDB = "PVGIS-NSRDB"
    ERA5 = "PVGIS-ERA5"
    COSMO = "PVGIS-COSMO"
    CMSAF = "PVGIS-CMSAF"
    SARAH = "PVGIS-SARAH"
    SARAH2 = "PVGIS-SARAH2"
    SARAH3 = "PVGIS-SARAH3"


class PvgisMountingSystemEnum(StrEnum):
    fixed = "fixed"


class PvgisTypeEnum(StrEnum):
    """
    Type of solar installation (where is mounted).

    PVGIS uses "building-integrated" to mean roof mounted
    and "free" to mean ground mounted, so we adopt that convention.
    """

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
