from enum import Enum
from os import PathLike

from pydantic import UUID4, BaseModel, Field


class FileLoc(Enum | str):
    database = "database"
    local = "local"


class SiteData(BaseModel):
    loc: FileLoc = Field(
        examples=["local", "database"], description="Location of data. Either in local directory or on database"
    )
    path: PathLike | None = None
    key: UUID4 | None = None
