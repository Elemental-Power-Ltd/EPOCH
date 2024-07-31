import datetime

import pydantic

from .core import site_id_field, site_id_t


class EpochTariffEntry(pydantic.BaseModel):
    Date: str = pydantic.Field(examples=["Jan-01", "Dec-31"], pattern=r"[0-9][0-9]-[A-Za-z]*")
    StartTime: datetime.time = pydantic.Field(examples=["00:00", "13:30"])
    HourOfYear: float = pydantic.Field(examples=[1, 24 * 365 - 1])
    Tariff: float = pydantic.Field(examples=[0.123, 4.56])


class TariffRequest(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    tariff_name: str = pydantic.Field(examples=[], description="Octopus tariff group code.")
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
