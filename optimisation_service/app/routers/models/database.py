from typing import Annotated

from pydantic import UUID4, AwareDatetime, BaseModel, Field

dataset_id_field = Field(
    examples=["805fb659-1cac-44f3-a1f9-85dc82178f53"], description="Unique ID (generally a UUIDv4) of a dataset."
)


class DatasetIDWithTime(BaseModel):
    dataset_id: Annotated[UUID4, "String serialised UUID"] = dataset_id_field
    start_ts: AwareDatetime = Field(
        examples=["2024-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
    )
    end_ts: AwareDatetime = Field(
        examples=["2024-05-31T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
    )
