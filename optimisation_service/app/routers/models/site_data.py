from enum import Enum
from os import PathLike

from pydantic import UUID4, BaseModel, Field


class FileLoc(str, Enum):
    remote = "remote"
    local = "local"


class SiteData(BaseModel):
    loc: FileLoc = Field(
        examples=["local", "remote"], description="Location of data. Either in local directory or in remote database."
    )
    path: PathLike | None = None
    key: UUID4 | None = None
