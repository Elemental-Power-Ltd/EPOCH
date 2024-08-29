from enum import Enum
from os import PathLike
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field


class FileLoc(str, Enum):
    remote = "remote"
    local = "local"


class DataDuration(str, Enum):
    year = "year"


class RemoteMetaData(BaseModel):
    loc: Literal[FileLoc.remote] = Field(
        examples=["remote"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    start_ts: AwareDatetime = Field(description="Datetime to retrieve data from. Only relevant for remote files.")
    duration: DataDuration = Field(description="Length of time to retrieve data for. Only relevant for remote files.")


class LocalMetaData(BaseModel):
    loc: Literal[FileLoc.local] = Field(
        examples=["local"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    path: PathLike = Field(examples=["./tests/data/benchmarks/var-3/InputData"], description="If a local file, the path to it.")


SiteMetaData = RemoteMetaData | LocalMetaData
