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
