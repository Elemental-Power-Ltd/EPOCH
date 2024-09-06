"""Models for client and site metadata."""
# ruff: noqa: D101

import pydantic

from app.models import EpochHeatingEntry, EpochRenewablesEntry
from app.models.air_source_heat_pump import ASHPCOPResponse
from app.models.carbon_intensity import EpochCarbonEntry
from app.models.import_tariffs import EpochTariffEntry
from app.models.meter_data import EpochElectricityEntry


class SiteDataEntries(pydantic.BaseModel):
    eload: list[EpochElectricityEntry]
    heat: list[EpochHeatingEntry]
    rgen: list[EpochRenewablesEntry]
    import_tariffs: list[EpochTariffEntry]
    grid_co2: list[EpochCarbonEntry]

    ashp_input: ASHPCOPResponse
    ashp_output: ASHPCOPResponse
