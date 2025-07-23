"""Models for client and site metadata."""
# ruff: noqa: D101

import pydantic

from app.models import EpochRenewablesEntry
from app.models.air_source_heat_pump import ASHPCOPResponse
from app.models.carbon_intensity import EpochCarbonEntry
from app.models.electricity_load import EpochElectricityEntry
from app.models.epoch_types.task_data_type import TaskData
from app.models.heating_load import EpochAirTempEntry, EpochDHWEntry, EpochHeatingEntry
from app.models.import_tariffs import EpochTariffEntry
from app.models.renewables import PvgisTypeEnum


class SolarLocation(pydantic.BaseModel):
    site_id: str = pydantic.Field(description="Site ID this solar location is associated with")
    renewables_location_id: str = pydantic.Field(description="Database friendly name to refer to this solar panel location")
    name: str = pydantic.Field(description="Human readable name used to refer to this location in a GUI")
    azimuth: float | None = pydantic.Field(
        description="Azimuth of panels at this site, angle from true north in degrees (180 is South)", ge=0.0, le=360.0
    )
    tilt: float | None = pydantic.Field(
        description="Azimuth of panels at this site, angle from true north in degrees (180 is South)", ge=0.0, le=360.0
    )
    maxpower: float = pydantic.Field(description="Peak generation in kW of this array, assuming it's full of 1x2m 440W panels.")
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
