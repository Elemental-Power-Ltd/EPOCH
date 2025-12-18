"""Custom types that we will use across all internal modules."""

type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None
