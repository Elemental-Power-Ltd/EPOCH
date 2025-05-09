"""Site Ranges are written into the database by the Optimisation service, so we just accept any JSON-like thing."""

type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None

type SiteRange = dict[str, Jsonable]
