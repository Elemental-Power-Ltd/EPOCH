"""Models for Air Source Heat Pump data requests and responses."""

import pydantic


# ruff: noqa: D101
class ASHPCOPResponse(pydantic.BaseModel):
    data: list[list[float]] = pydantic.Field(
        examples=[
            [
                [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 40.0, 50.0, 60.0, 70.0],
                [-15.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.99, 1.0, 1.0, 1.0],
                [-10.0, 1.0, 1.0, 1.0, 0.99, 0.99, 1.0, 0.96, 0.99, 1.0, 0.96],
            ]
        ],
        description="""
        Row major ASHP lookup table.
        First element of each row should be the row's index: Output (send) hot water temperature in °C for COP lookup.
        First row should be column headers: the Ambient air temperatures in °C for COP lookup.
        """,
    )
