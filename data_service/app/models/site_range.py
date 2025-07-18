"""Site Ranges are written into the database by the Optimisation service, so we just accept any JSON-like thing."""

from ..internal.epl_typing import Jsonable

type SiteRange = dict[str, Jsonable]
