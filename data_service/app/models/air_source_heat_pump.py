"""Models for Air Source Heat Pump data requests and responses."""

import pydantic


# ruff: noqa: D101
class ASHPCOPResponse(pydantic.BaseModel):
    index: list[float] = pydantic.Field(
        examples=[[-15.0, -10.0, -7.0, -2.0, 2.0, 7.0, 12.0, 15.0, 20.0, 25.0, 30.0, 35.0, 43.0]],
        description="Ambient air temperatures in °C for COP lookup.",
    )
    columns: list[float] = pydantic.Field(
        examples=[[[25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0]]],
        description="Output (send) hot water temperature in °C for COP lookup.",
    )
    data: list[list[float]] = pydantic.Field(
        examples=[[[4.91, 5.23], [4.2, 4.7]]], description="COP (output heat: input elec) ratios at these temperatures."
    )
    index_names: list[str] = pydantic.Field(
        examples=[["temperature"]], description="Name of the index to use in reconstructing a dataframe."
    )
