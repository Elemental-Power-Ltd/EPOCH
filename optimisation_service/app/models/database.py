from typing import Annotated

from pydantic import UUID4, UUID7, AwareDatetime, BaseModel, Field

type dataset_id_t = Annotated[UUID4 | UUID7, "String serialised UUID, either UUIDv4 or UUIDv7"]
type bundle_id_t = Annotated[UUID4 | UUID7, "String serialised UUID, either UUIDv4 or UUIDv7"]
type site_id_t = str


class BundleMetadata(BaseModel):
    bundle_id: dataset_id_t = Field(
        examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv7) of a bundle."
    )
    start_ts: AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"],
        description="The start timestamp of the bundle.",
    )
    end_ts: AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The end timestamp of the bundle.",
    )
