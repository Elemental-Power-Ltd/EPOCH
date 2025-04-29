"""
Store and access Pydantic models for various endpoints.

This directory should have an almost parallel structure to `../routers/`,
with each py file in there having a corresponding file in here.

Each endpoint may have a request model and a return model, which should go in their parallel file.
If the model is re-used, then it should go in `core.py`.
"""

# this slightly weird style is ruff making sure that everything is used (I think?)

from .carbon_intensity import CarbonIntensityEntry as CarbonIntensityEntry
from .carbon_intensity import CarbonIntensityMetadata as CarbonIntensityMetadata
from .core import client_id_field as client_id_field
from .core import client_id_t as client_id_t
from .core import dataset_id_field as dataset_id_field
from .core import dataset_id_t as dataset_id_t
from .core import site_id_field as site_id_field
from .core import site_id_t as site_id_t
from .epoch_types import ReportData as ReportData
from .epoch_types import TaskDataPydantic as TaskDataPydantic
from .heating_load import EpochHeatingEntry as EpochHeatingEntry
from .heating_load import HeatingLoadEntry as HeatingLoadEntry
from .heating_load import HeatingLoadMetadata as HeatingLoadMetadata
from .import_tariffs import TariffMetadata as TariffMetadata
from .import_tariffs import TariffRequest as TariffRequest
from .meter_data import GasDatasetEntry as GasDatasetEntry
from .optimisation import PortfolioOptimisationResult as PortfolioOptimisationResult
from .optimisation import SiteOptimisationResult as SiteOptimisationResult
from .optimisation import TaskConfig as TaskConfig
from .renewables import EpochRenewablesEntry as EpochRenewablesEntry
from .renewables import RenewablesMetadata as RenewablesMetadata
from .renewables import RenewablesRequest as RenewablesRequest
from .weather import WeatherDatasetEntry as WeatherDatasetEntry
from .weather import WeatherRequest as WeatherRequest
