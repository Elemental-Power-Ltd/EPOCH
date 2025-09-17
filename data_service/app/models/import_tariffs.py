"""Models associated with import_tariffs.py, mostly Octopus Agile."""

# ruff: noqa: D101
import datetime
from enum import StrEnum
from typing import Self

import pydantic

from .core import EpochEntry, RequestBase, dataset_id_field, dataset_id_t, site_id_field, site_id_t


class GSPEnum(StrEnum):
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
    data: list[list[float]] = pydantic.Field(
        examples=[[[0.324, 0.146], [0.163, 0.208]]],
        description="List of import tariffs. Each import tariff is a list of Import costs for this time period in £ / kWh.",
    )


class SyntheticTariffEnum(StrEnum):
    # This ordering matters -- Fixed must be the first entry.
    Fixed = "fixed"
    Agile = "agile"
    Overnight = "overnight"
    Peak = "peak"
    ShapeShifter = "shapeshifter"
    PowerPurchaseAgreement = "power_purchase_agreement"


class TariffRequest(RequestBase):
    site_id: site_id_t = site_id_field
    tariff_name: SyntheticTariffEnum | str = pydantic.Field(
        examples=["E-1R-AGILE-24-04-03-A", "E-1R-COOP-FIX-12M-24-07-25-B"],
        description="Either a synthetic tariff type like `fixed`, `agile`, `overnight` which will cause"
        " synthetic tariff generation, or a specific Octopus region-containing tariff code for this tariff.",
    )
    day_cost: float | None = pydantic.Field(
        default=None,
        examples=[23.7, 25.9, 14.0],
        description="For a synthetic tariff, the fixed cost for 'day' periods in p/kWh."
        " If None, will look up an Octopus tariff.",
    )
    night_cost: float | None = pydantic.Field(
        default=None,
        examples=[20.7, 22.9, 12.0],
        description="For a synthetic tariff, the fixed cost for 'night' periods in p/kWh."
        " Will most commonly be lower than 'day'."
        " If None, will look up an Octopus tariff.",
    )
    peak_cost: float | None = pydantic.Field(
        default=None,
        examples=[33.7, 35.9, 24.0],
        description="For a synthetic tariff, the fixed cost for 'peak' periods in p/kWh."
        " Will most commonly be higher than 'day'."
        " If None, will look up an Octopus tariff.",
    )

    @pydantic.field_validator("tariff_name", mode="before")
    @classmethod
    def check_tariff_type(cls, v: str) -> str | SyntheticTariffEnum:
        """Check if this tariff is a specific name, or a generic type like 'fixed'."""
        try:
            return SyntheticTariffEnum(v)
        except ValueError:
            return v

    @pydantic.model_validator(mode="after")
    def check_day_night_costs(self) -> Self:
        """Check if the provided day/night costs make sense with the tariff option."""
        if not isinstance(self.tariff_name, SyntheticTariffEnum):
            if self.day_cost is not None:
                raise ValueError(f"Specified an Octopus tariff {self.tariff_name} but also a day cost {self.day_cost}.")
            if self.night_cost is not None:
                raise ValueError(f"Specified an Octopus tariff {self.tariff_name} but also a night cost {self.night_cost}.")

        if self.tariff_name == SyntheticTariffEnum.Fixed and self.night_cost is not None:
            raise ValueError(f"Specified a synthetic Fixed tariff but also a night cost {self.night_cost}.")
        if self.tariff_name == SyntheticTariffEnum.Fixed and self.peak_cost is not None:
            raise ValueError(f"Specified a synthetic Fixed tariff but also a peak cost {self.peak_cost}.")

        if self.tariff_name == SyntheticTariffEnum.Overnight and self.peak_cost is not None:
            raise ValueError(f"Specified a synthetic Overnight tariff but also a peak cost {self.peak_cost}.")

        if self.tariff_name == SyntheticTariffEnum.Agile and self.day_cost is not None:
            raise ValueError(f"Specified a synthetic Agile tariff but also a day cost {self.day_cost}.")
        if self.tariff_name == SyntheticTariffEnum.Agile and self.night_cost is not None:
            raise ValueError(f"Specified a synthetic Agile tariff but also a night cost {self.night_cost}.")

        return self

    @pydantic.model_validator(mode="after")
    def check_costs_right_units(self) -> Self:
        """Check if the provided day/night costs are in p / kWh."""
        if self.day_cost is not None and self.day_cost < 1.0:
            raise ValueError("Got suspiciously low day_cost: {self.day_cost}. It should be in p / kWh.")
        if self.day_cost is not None and self.day_cost > 100.0:
            raise ValueError("Got suspiciously high day_cost: {self.day_cost}. It should be in p / kWh.")

        if self.night_cost is not None and self.night_cost < 1.0:
            raise ValueError("Got suspiciously low night_cost: {self.night_cost}. It should be in p / kWh.")
        if self.night_cost is not None and self.night_cost > 100.0:
            raise ValueError("Got suspiciously high night_cost: {self.night_cost}. It should be in p / kWh.")

        if self.peak_cost is not None and self.peak_cost < 1.0:
            raise ValueError("Got suspiciously low peak_cost: {self.peak_cost}. It should be in p / kWh.")
        if self.peak_cost is not None and self.peak_cost > 200.0:
            raise ValueError("Got suspiciously high peak_cost: {self.peak_cost}. It should be in p / kWh.")

        return self


class BaselineTariffRequest(TariffRequest):
    """Request for creating a baseline tariff with the bundle metadata specifically excluded."""

    bundle_metadata: None = None


class TariffProviderEnum(StrEnum):
    octopus = "octopus"
    Synthetic = "synthetic"


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
    day_cost: float | None = pydantic.Field(
        default=None,
        examples=[23.7, 25.9, 14.0],
        description="For a synthetic tariff, the fixed cost for 'day' periods in p/kWh."
        " If None, it wasn't relevant for this tariff type.",
    )
    night_cost: float | None = pydantic.Field(
        default=None,
        examples=[20.7, 22.9, 12.0],
        description="For a synthetic tariff, the fixed cost for 'night' periods in p / kWh."
        " Will most commonly be lower than 'day'."
        " If None, it wasn't relevant for this tariff type.",
    )
    peak_cost: float | None = pydantic.Field(
        default=None,
        examples=[33.7, 35.9, 24.0],
        description="For a synthetic tariff, the fixed cost for 'peak' periods in p / kWh."
        " Will most commonly be higher than 'day'."
        " If None, it wasn't relevant for this tariff type.",
    )
