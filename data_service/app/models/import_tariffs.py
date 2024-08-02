import datetime
import enum

import pydantic

from .core import dataset_id_field, dataset_id_t, site_id_field, site_id_t


class EpochTariffEntry(pydantic.BaseModel):
    Date: str = pydantic.Field(examples=["Jan-01", "Dec-31"], pattern=r"[0-9][0-9]-[A-Za-z]*")
    StartTime: datetime.time = pydantic.Field(examples=["00:00", "13:30"])
    HourOfYear: float = pydantic.Field(examples=[1, 24 * 365 - 1])
    Tariff: float = pydantic.Field(examples=[32.4, 14.6], description="Import costs for this time period in p / kWh")


class TariffRequest(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    tariff_name: str = pydantic.Field(
        examples=["E-1R-AGILE-24-04-03-A", "E-1R-COOP-FIX-12M-24-07-25-B"],
        description="The specific region-containing tariff code for this tariff.",
    )
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime


class TariffProviderEnum(enum.Enum):
    octopus = "octopus"


class TariffMetadata(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    site_id: site_id_t = site_id_field
    created_at: pydantic.AwareDatetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    provider: TariffProviderEnum = pydantic.Field(description="The source of this tariff data")
    product_name: str = pydantic.Field(
        description="The overall product name (not necessarily human readable) for this group of tariffs.",
        examples=["AGILE-24-04-03", "COOP-FIX-12M-24-07-25"],
    )
    tariff_name: str = pydantic.Field(
        description="The specific region-containing tariff code for this tariff.",
        examples=["E-1R-AGILE-24-04-03-A", "E-1R-COOP-FIX-12M-24-07-25-B"],
    )
    valid_from: pydantic.AwareDatetime | None
    valid_to: pydantic.AwareDatetime | None
