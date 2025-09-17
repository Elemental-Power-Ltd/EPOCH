"""Models for client and site metadata."""
# ruff: noqa: D101

import pydantic

from app.internal.epl_typing import Jsonable
from app.models.air_source_heat_pump import ASHPCOPResponse
from app.models.carbon_intensity import EpochCarbonEntry
from app.models.core import dataset_id_t
from app.models.electricity_load import EpochElectricityEntry
from app.models.epoch_types.task_data_type import TaskData
from app.models.heating_load import EpochAirTempEntry, EpochDHWEntry, EpochHeatingEntry
from app.models.import_tariffs import EpochTariffEntry
from app.models.renewables import EpochRenewablesEntry, PvgisTypeEnum


class SolarLocation(pydantic.BaseModel):
    site_id: str = pydantic.Field(description="Site ID this solar location is associated with")
    renewables_location_id: str | None = pydantic.Field(
        description="Database friendly name to refer to this solar panel location"
    )
    name: str | None = pydantic.Field(description="Human readable name used to refer to this location in a GUI")
    azimuth: float | None = pydantic.Field(
        description="Azimuth of panels at this site, angle from true north in degrees (180 is South)", ge=0.0, le=360.0
    )
    tilt: float | None = pydantic.Field(
        description="Azimuth of panels at this site, angle from true north in degrees (180 is South)", ge=0.0, le=360.0
    )
    maxpower: float | None = pydantic.Field(
        description="Peak generation in kW of this array, assuming it's full of 1x2m 440W panels."
    )
    mounting_type: PvgisTypeEnum = pydantic.Field(default=PvgisTypeEnum.building_integrated)


class SiteDataEntries(pydantic.BaseModel):
    baseline: TaskData

    dhw: EpochDHWEntry | None
    air_temp: EpochAirTempEntry | None
    eload: EpochElectricityEntry | None
    heat: EpochHeatingEntry | None
    rgen: EpochRenewablesEntry | None
    import_tariffs: EpochTariffEntry | None
    grid_co2: EpochCarbonEntry | None

    ashp_input: ASHPCOPResponse | None
    ashp_output: ASHPCOPResponse | None


class BaselineMetadata(pydantic.BaseModel):
    baseline_id: dataset_id_t = pydantic.Field(description="Unique ID for this baseline.")
    created_at: pydantic.AwareDatetime = pydantic.Field(description="The time this baseline was created.")
    baseline: dict[str, Jsonable] = pydantic.Field(
        description="Un-parsed JSON of what the baseline for this site will be."
        " This means you can list old baselines that might be potentially unparseable now."
    )
    tariff_id: dataset_id_t = pydantic.Field(description="Dataset ID for the baseline tariff associated with this baseline.")
