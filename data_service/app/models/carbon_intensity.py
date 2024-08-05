"""Models for carbon intensity endpoints."""

# ruff: noqa: D101
import datetime

import pydantic

from .core import site_id_field, site_id_t


class CarbonIntensityMetadata(pydantic.BaseModel):
    dataset_id: pydantic.UUID4 = pydantic.Field(description="Unique database ID for the carbon intensity readings.")
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC), description="The time this dataset was created"
    )
    data_source: str = pydantic.Field(
        examples=["api.carbonintensity.org.uk"], description="The API or other data source that we got these readings from."
    )
    is_regional: bool = pydantic.Field(
        examples=[True, False],
        description="Whether the carbon intensity data is for a specific UK region, or the" + "entire country.",
    )
    site_id: site_id_t = site_id_field


class CarbonIntensityEntry(pydantic.BaseModel):
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=[datetime.datetime(year=2024, month=8, day=5, hour=16, minute=30, tzinfo=datetime.UTC)],
        description="The starting time of the period this CI applies for (inclusive)",
    )
    end_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=[datetime.datetime(year=2024, month=8, day=5, hour=17, minute=0, tzinfo=datetime.UTC)],
        description="The ending time of the period this CI applies for (exclusive)",
    )
    forecast: float | None = pydantic.Field(description="Forecast carbon intensity during this time period in g CO2 / kWh.")
    actual: float | None = pydantic.Field(
        description="Actual carbon intensity during this time period in g CO2 / kWh." + "Not provided for regional samples (?)"
    )
    gas: float | None = pydantic.Field(description="Fraction of grid power provided by gas power plants (bad!)")
    coal: float | None = pydantic.Field(description="Fraction of grid power provided by coal power plants (very bad!)")
    biomass: float | None = pydantic.Field(description="Fraction of grid power provided by biomass power plants")
    nuclear: float | None = pydantic.Field(description="Fraction of grid power provided by nuclear power plants")
    hydro: float | None = pydantic.Field(description="Fraction of grid power provided by hydroeletric power plants (bad!)")
    imports: float | None = pydantic.Field(description="Fraction of grid power imported.")
    other: float | None = pydantic.Field(description="Fraction of grid power from unknown sources.")
    wind: float | None = pydantic.Field(description="Fraction of grid power provided by wind turbines (good!)")
    solar: float | None = pydantic.Field(description="Fraction of grid power provided by solar PV (good!)")
