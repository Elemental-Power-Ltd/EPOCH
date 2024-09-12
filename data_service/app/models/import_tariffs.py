"""Models associated with import_tariffs.py, mostly Octopus Agile."""

# ruff: noqa: D101
import datetime
import enum
from typing import Self

import pydantic

from .core import EpochEntry, dataset_id_field, dataset_id_t, site_id_field, site_id_t


class GSPEnum(str, enum.Enum):
    A = "_A"
    B = "_B"
    C = "_C"
    D = "_D"
    E = "_E"
    F = "_F"
    G = "_G"
    H = "_H"
    J = "_J"
    K = "_K"
    L = "_L"
    M = "_M"
    N = "_N"
    P = "_P"


class GSPCodeResponse(pydantic.BaseModel):
    ci_region_id: int | None = pydantic.Field(
        description="Region ID used by the National Grid ESO Carbon Intensity API", examples=[13]
    )
    dno_region_id: int | None = pydantic.Field(
        description="Distribution Network Operator ID used by tariff providers. Not the same as CI Region ID.", examples=[12]
    )
    region_code: GSPEnum = pydantic.Field(
        description="Letter code used by Octopus and other providers for a given region", examples=["_C"]
    )
    dno_region: str = pydantic.Field(
        description="Human readable name of the Distribution Network Operator region.", examples=["London"]
    )


class EpochTariffEntry(EpochEntry):
    Tariff: float = pydantic.Field(examples=[32.4, 14.6], description="Import costs for this time period in p / kWh")


class TariffRequest(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    tariff_name: str = pydantic.Field(
        examples=["E-1R-AGILE-24-04-03-A", "E-1R-COOP-FIX-12M-24-07-25-B"],
        description="The specific region-containing tariff code for this tariff.",
    )
    start_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=[datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.UTC)],
        description="The earliest timestamp to get this tariff for"
        + "(but note that it may not be provided too far in the past).",
    )
    end_ts: pydantic.AwareDatetime = pydantic.Field(
        examples=[datetime.datetime(year=2024, month=12, day=1, tzinfo=datetime.UTC)],
        description="The latest timestamp to get this tariff for"
        + "(but note that it may not be provided too far in the future).",
    )

    @pydantic.model_validator(mode="after")
    def check_timestamps_valid(self) -> Self:
        """Check that the start timestamp is before the end timestamp, and that neither of them is in the future."""
        assert self.start_ts < self.end_ts, f"Start timestamp {self.start_ts} must be before end timestamp {self.end_ts}"
        assert self.start_ts <= datetime.datetime.now(datetime.UTC), f"Start timestamp {self.start_ts} must be in the past."
        assert self.end_ts <= datetime.datetime.now(datetime.UTC), f"End timestamp {self.end_ts} must be in the past."
        return self


class TariffProviderEnum(str, enum.Enum):
    octopus = "octopus"


class TariffListEntry(pydantic.BaseModel):
    tariff_name: str = pydantic.Field(
        description="The Octopus name (code-like) for this tariff, without region added.",
        examples=["BUS-36M-FIXED-ELX-BAND4-21-12-14"],
    )
    valid_from: pydantic.AwareDatetime | None
    valid_to: pydantic.AwareDatetime | None
    provider: TariffProviderEnum
    is_tracker: bool = pydantic.Field(description="Whether this is a tracker / agile tariff or not")
    is_prepay: bool = pydantic.Field(description="Whether this is a pre-paid tariff or not")
    is_variable: bool = pydantic.Field(description="Whether this is a variable rate tariff or not")


class TariffMetadata(pydantic.BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    site_id: site_id_t = site_id_field
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC), description="The time we retrieved this tariff data at."
    )
    provider: TariffProviderEnum = pydantic.Field(description="The source of this tariff data, currently just Octopus.")
    product_name: str = pydantic.Field(
        description="The overall product name (not necessarily human readable) for this group of tariffs.",
        examples=["AGILE-24-04-03", "COOP-FIX-12M-24-07-25"],
    )
    tariff_name: str = pydantic.Field(
        description="The specific region-containing tariff code for this tariff.",
        examples=["E-1R-AGILE-24-04-03-A", "E-1R-COOP-FIX-12M-24-07-25-B"],
    )
    valid_from: pydantic.AwareDatetime | None = pydantic.Field(
        default=None,
        examples=[None, "2024-07-24T00:00:00Z"],
        description="The first time this tariff is valid for. May be None if we don't know.",
    )
    valid_to: pydantic.AwareDatetime | None = pydantic.Field(
        default=None,
        examples=[None, "2024-09-01T00:00:00Z"],
        description="The last time this tariff is valid for. May be None if we don't know.",
    )
