import pydantic
from pydantic import Field

from .core import site_id_field, site_id_t


class RenewablesRequest(pydantic.BaseModel):
    site_id: site_id_t = site_id_field
    start_ts: pydantic.AwareDatetime
    end_ts: pydantic.AwareDatetime
    azimuth: float | None = Field(
        default=None,
        examples=[178.0, 182.0, None],
        description="Angle from compass north, 180° is due south. For None, use the optimum azimuth.",
    )
    tilt: float | None = Field(
        default=None,
        examples=[30.0, 40.0, None],
        description="Tilt from the horizontal, 90° is vertical. For None, use the optimum tilt.",
    )
    tracking: bool = Field(default=False, examples=[False, True], description="Whether these panels use single axis tracking.")
