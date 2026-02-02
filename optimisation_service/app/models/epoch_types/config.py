from pydantic import BaseModel, Field

from ..epl_typing import Jsonable

class Config(BaseModel):
    capex_limit: float = Field(
        default=2500000,
        description='The maximum capital expenditure (CAPEX) allowed at this site in pounds.',
        ge=0.0,
        title='CAPEX Limit',
    )
    use_boiler_upgrade_scheme: bool = Field(
        default=False,
        description='Apply funding from the boiler upgrade scheme (if eligible).',
        title='Use Boiler Upgrade Scheme',
    )
    general_grant_funding: float = Field(
        default=0,
        description='Apply unconditional funding up to this value in £.',
        ge=0.0,
        title='General Grant Funding',
    )
    npv_time_horizon: int = Field(
        default=10,
        description='The number of years to forecast over for the net-present-value calculations.',
        ge=1,
        title='NPV time horizon',
    )
    npv_discount_factor: float = Field(
        default=0.0,
        description='The decimal discount factor to apply to future years in the net-present-value calculations.',
        title='NPV discount factor',
    )
    capex_model: Jsonable | None = Field(default=None, description="A weakly typed cost model that is passed directly through to EPOCH.")
    opex_model: Jsonable | None = Field(default=None, description="A weakly typed cost model that is passed directly through to EPOCH.")