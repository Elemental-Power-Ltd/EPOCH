from typing import Annotated

from pydantic import AwareDatetime, BaseModel, Field, UUID4, UUID7

dataset_id_field = Field(
    examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv7) of a dataset."
)
type dataset_id_t = Annotated[UUID4 | UUID7, "String serialised UUID, either UUIDv4 or UUIDv7"]
type site_id_t = str


class DatasetIDWithTime(BaseModel):
    dataset_id: dataset_id_t = dataset_id_field
    start_ts: AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
    )
    end_ts: AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
    )
