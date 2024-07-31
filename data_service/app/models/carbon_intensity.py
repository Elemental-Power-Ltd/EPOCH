import pydantic

from .core import site_id_field, site_id_t


class CarbonIntensityMetadata(pydantic.BaseModel):
    dataset_id: pydantic.UUID4
    created_at: pydantic.AwareDatetime
    data_source: str
    is_regional: bool
    site_id: site_id_t = site_id_field


class CarbonIntensityEntry(pydantic.BaseModel):
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    forecast: float | None
    actual: float | None
    gas: float | None
    coal: float | None
    biomass: float | None
    nuclear: float | None
    hydro: float | None
    imports: float | None
    other: float | None
    wind: float | None
    solar: float | None
