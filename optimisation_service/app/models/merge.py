"""Pydantic models associdated to merge.py."""

from pydantic import BaseModel

from app.models.constraints import Constraints
from app.models.core import Task
from app.models.database import bundle_id_t, site_id_t
from app.models.epoch_types.site_range_type import Config, SiteRange
from app.models.ga_utils import AnnotatedTaskData


class SiteInfo(BaseModel):
    """Site level information required to merge site scenairos into portfolio scenarios."""

    site_id: site_id_t
    bundle_id: bundle_id_t
    config: Config
    constraints: Constraints
    site_range: SiteRange
    scenarios: list[AnnotatedTaskData]


class PortfolioMergeRequest(BaseModel):
    """Information required to merge site scenairos into portfolio scenarios."""

    sites: list[SiteInfo]
    client_id: str
    task_name: str


class MergeOperator(BaseModel):
    name: str = "MergeOperator"
    hyperparameters: None = None


class MergeTask(Task):
    optimiser: MergeOperator = MergeOperator()  # type: ignore[assignment]
