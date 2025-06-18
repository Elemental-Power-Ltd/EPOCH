from enum import Enum, StrEnum

from pydantic import BaseModel, Field

from app.models.epoch_types.task_data_type import SolarPanel, TaskData


class SamplingMethod(StrEnum):
    RANDOM = "RANDOM"
    ESTIMATE = "ESTIMATE"


# these define the dictionary-style definition of a site range
value_t = bool | int | float | Enum
asset_t = dict[str, value_t | list[value_t]]
site_range_t = dict[str, asset_t | list[asset_t]]


class ParsedAsset(BaseModel):
    fixed: dict[str, value_t | None] = {}
    ranged: dict[str, list[value_t]] = {}
    num_values: list[int] = []


class AssetParameter(BaseModel):
    asset_name: str
    attr_name: str
    repeat_index: int | None = None


class RepeatAnnotatedSolarPanel(SolarPanel):
    index_tracker: int = Field(
        description="Index used within the genetic algorithm code to re-associate a partial TaskData Solar Panel "
                    "with the correct SiteRange Solar Panel"
    )


class AnnotatedTaskData(TaskData):
    """An annotated TaskData to allow re-associating repeat parameters with their SiteRange equivalent."""
    solar_panels: list[RepeatAnnotatedSolarPanel] | None = None  # type: ignore
