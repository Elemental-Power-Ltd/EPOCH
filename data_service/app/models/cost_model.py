# ruff: noqa: D100, D101
import datetime

import pydantic

from app.internal.epl_typing import Jsonable
from app.internal.utils.uuid import uuid7
from app.models.core import dataset_id_t


class CostModelResponse(pydantic.BaseModel):
    cost_model_id: dataset_id_t = pydantic.Field(description="ID for this cost model.", default_factory=uuid7)
    model_name: str | None = pydantic.Field(description="Human readable name for this cost model, if available.", default=None)
    capex_model: Jsonable
    opex_model: Jsonable
    created_at: pydantic.AwareDatetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC), description="When this cost model was created"
    )
