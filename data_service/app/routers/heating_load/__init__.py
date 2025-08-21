"""Heating load endpoints and API routers."""

from .generate_heating_loads import generate_heating_load as generate_heating_load
from .get_heating_loads import get_air_temp as get_air_temp
from .get_heating_loads import get_dhw_load as get_dhw_load
from .get_heating_loads import get_heating_load as get_heating_load
from .phpp import list_phpp as list_phpp
from .phpp import upload_phpp as upload_phpp
from .router import api_router as api_router
