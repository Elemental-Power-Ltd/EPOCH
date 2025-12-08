"""Models for client and site metadata."""
# ruff: noqa: D101

from typing import Self

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

    @pydantic.model_validator(mode="after")
    def check_all_same_length(self) -> Self:
        """Check all timeseries inputs are of same length."""
        lengths = {}
        if self.dhw:
            lengths["dhw"] = len(self.dhw.data)
        if self.air_temp:
            lengths["air_temp"] = len(self.air_temp.data)
        if self.eload:
            lengths["eload"] = len(self.eload.data)
        if self.grid_co2:
            lengths["grid_co2"] = len(self.grid_co2.data)
        if self.rgen:
            for i, solar in enumerate(self.rgen.data):
                lengths[f"rgen_{i}"] = len(solar)
        if self.import_tariffs:
            for i, import_tariff in enumerate(self.import_tariffs.data):
                lengths[f"import_tariff_{i}"] = len(import_tariff)
        if self.heat:
            for i, fabric_int in enumerate(self.heat.data):
                lengths[f"fabric_intervention_{i}"] = len(fabric_int.reduced_hload)

        if len(set(lengths.values())) > 1:
            raise ValueError(f"Expected all timeseries inputs to have the same length, got: {lengths}")

        return self


class BaselineMetadata(pydantic.BaseModel):
    baseline_id: dataset_id_t = pydantic.Field(description="Unique ID for this baseline.")
    created_at: pydantic.AwareDatetime = pydantic.Field(description="The time this baseline was created.")
    baseline: dict[str, Jsonable] = pydantic.Field(
        description="Un-parsed JSON of what the baseline for this site will be."
        " This means you can list old baselines that might be potentially unparseable now."
    )
    tariff_id: dataset_id_t | None = pydantic.Field(
        default=None,
        description="Dataset ID for the baseline tariff associated with this baseline."
        " If None, we'll get a sensible fixed tariff 0 from Octopus.",
    )
