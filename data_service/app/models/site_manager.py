"""Models for site manager, handling requesting datasets."""

# ruff: noqa: D101

import pydantic

from .core import site_id_t


class DatasetRequest(pydantic.BaseModel):
    site_id: site_id_t
    start_ts: pydantic.AwareDatetime
    HeatingLoad: pydantic.UUID4 | None = pydantic.Field(default=None)
    ASHPData: pydantic.UUID4 | None = pydantic.Field(default=None)
    CarbonIntensity: pydantic.UUID4 | None = pydantic.Field(default=None)
    ElectricityMeterData: pydantic.UUID4 | None = pydantic.Field(default=None)
    ElectricityMeterDataSynthesised: pydantic.UUID4 | None = pydantic.Field(default=None)
    ImportTariff: pydantic.UUID4 | None = pydantic.Field(default=None)
    Weather: pydantic.UUID4 | None = pydantic.Field(default=None)
