"""
Functions for Air Source Heat Pump efficiency look-up tables.

Generally, ASHPs will have difference heat out:energy in (Coefficient of Performance, or COP)
ratios depending on the input and output temperatures.
These endpoints should provide quick look-up tables for those coefficients of performance.
"""

import pandas as pd
from fastapi import APIRouter

from ..models.air_source_heat_pump import ASHPCOPResponse
from ..models.core import DatasetIDWithTime

router = APIRouter()


@router.post("/get-ashp-input")
async def get_ashp_input(params: DatasetIDWithTime) -> ASHPCOPResponse:
    """
    Get the ASHP input temperature coefficients of performance.

    Here, the index is "air temperatures" and the columns are "output water temperatures" in °C.
    You should be able to linearly interpolate between these rows and columns to get a COP
    at a specific ambient air:output water temperature point.

    Currently, this function ignores the parameters you send and returns one specific example from a file.

    Parameters
    ----------
    *params*
        Dataset, start timestamp and end timestamp information. Currently ignored.

    Returns
    -------
    *ashp_input_response*
        Coefficient of performance lookup table, with air temperatures in the index, water temperatures in the columns,
        and COP values as a 2D array in data.
    """
    _ = params  # we ignore these, but mark them as used.

    dataframe = pd.read_csv("./data/CSVASHPinput.csv").set_index("0")
    dataframe.index.name = "temperature"

    results = dataframe.to_dict(orient="tight")
    return ASHPCOPResponse(
        index=results["index"],
        columns=results["columns"],
        data=results["data"],
        index_names=results["index_names"],
        column_names=results["column_names"],
    )


@router.post("/get-ashp-output")
async def get_ashp_output(params: DatasetIDWithTime) -> ASHPCOPResponse:
    """
    Get the ASHP output temperature coefficients of performance.

    Here, the index is "air temperatures" and the columns are "output water temperatures" in °C.
    You should be able to linearly interpolate between these rows and columns to get an COP
    at a specific ambient air:output water temperature point.

    Currently, this function ignores the parameters you send and returns one specific example from a file.

    Parameters
    ----------
    *params*
        Dataset, start timestamp and end timestamp information. Currently ignored.

    Returns
    -------
    *ashp_input_response*
        Coefficient of performance lookup table, with air temperatures in the index, water temperatures in the columns,
        and COP values as a 2D array in data.
    """
    _ = params  # we ignore these, but mark them as used.

    dataframe = pd.read_csv("./data/CSVASHPoutput.csv").set_index("0")
    dataframe.index.name = "temperature"

    results = dataframe.to_dict(orient="tight")
    return ASHPCOPResponse(
        index=results["index"],
        columns=results["columns"],
        data=results["data"],
        index_names=results["index_names"],
        column_names=results["column_names"],
    )
