"""Site Ranges are written into the database by the Optimisation service, so we just accept any JSON-like thing."""

# ruff: noqa: D101

import pydantic

from .core import dataset_id_t, site_id_field, site_id_t


class DataBundleMetadata(pydantic.BaseModel):
    bundle_id: dataset_id_t = pydantic.Field(description="Bundle ID referring to this specific collection of datasets.")
    site_id: site_id_t = site_id_field
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    created_at: pydantic.AwareDatetime


type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None

type SiteRange = dict[str, Jsonable]
