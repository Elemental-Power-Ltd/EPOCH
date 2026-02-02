"""Endpoints to handle running individual simulations of EPOCH."""

import logging
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Body

from app.dependencies import HttpClientDep
from app.internal.database.site_data import get_latest_site_data_bundle, get_saved_epoch_input
from app.internal.days_of_interest import detect_days_of_interest
from app.internal.epoch.converters import simulation_result_to_pydantic
from app.models.epoch_types import ReportData
from app.models.epoch_types.config import Config
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.simulate import (
    FullResult,
    GetSavedSiteDataRequest,
    ReproduceSimulationRequest,
    RunSimulationRequest,
)
from app.models.site_data import EpochSiteData, site_metadata_t
from epoch_simulator import Simulator, TaskData

router = APIRouter()
logger = logging.getLogger("default")


@router.post("/run-simulation")
async def run_simulation(request: RunSimulationRequest, http_client: HttpClientDep) -> FullResult:
    """
    Run a simulation of a single site in EPOCH with full reporting enabled.

    Parameters
    ----------
    request
        Details about the simulation to reproduce
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Full result from the simulation to run
    """
    logger.info("Running single simulation")

    epoch_data = await get_latest_site_data_bundle(site_data=request.site_data, http_client=http_client)

    return do_simulation(epoch_data, request.task_data, request.config)


@router.post("/reproduce-simulation")
async def reproduce_simulation(request: ReproduceSimulationRequest, http_client: HttpClientDep) -> FullResult:
    """
    Re-run a simulation of EPOCH with full reporting enabled.

    This method will obtain the configuration settings used in the original Optimisation Run to reproduce the result.
    If the original result was obtained using local data, the result cannot be reproduced and an error will be returned.


    Parameters
    ----------
    request
        Details about the simulation to reproduce
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Full result from the simulation
    """
    logger.info(f"Reproducing simulation for {request.site_id} from portfolio {request.portfolio_id}")
    saved_input = await get_saved_epoch_input(
        portfolio_id=request.portfolio_id, site_id=request.site_id, http_client=http_client
    )

    return do_simulation(saved_input.site_data, saved_input.task_data, saved_input.site_config)


@router.post("/get-latest-site-data")
async def get_latest_site_data(http_client: HttpClientDep, site_data: Annotated[site_metadata_t, Body()]) -> EpochSiteData:
    """
    Serve an EPOCH compatible SiteData using the most recent bundle for this site.

    Parameters
    ----------
    site_data
        Data to request from the database
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Site data in EPOCH format
    """
    return await get_latest_site_data_bundle(site_data=site_data, http_client=http_client)


@router.post("/get-saved-site-data")
async def get_saved_site_data(request: GetSavedSiteDataRequest, http_client: HttpClientDep) -> EpochSiteData:
    """
    Fetch the exact SiteData that was used to produce a result in the database.

    Parameters
    ----------
    request
        Request to send to the database
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
        Parsed data in EPOCH format
    """
    saved_input = await get_saved_epoch_input(
        portfolio_id=request.portfolio_id, site_id=request.site_id, http_client=http_client
    )
    return saved_input.site_data


def do_simulation(epoch_data: EpochSiteData, task_data: TaskDataPydantic, config: Config) -> FullResult:
    """
    Run a simulation for a given set of site data and taskData.

    This is an internal wrapper that shouldn't be exposed.

    Parameters
    ----------
    epoch_data
        The EPOCH SiteData represented in JSON.
    task_data
        The EPOCH TaskData represented in JSON.

    Returns
    -------
        Full result from the simulated scenario
    """
    sim = Simulator.from_json(epoch_data.model_dump_json(), config.model_dump_json())
    pytd = TaskData.from_json(task_data.model_dump_json())

    res = sim.simulate_scenario(pytd, fullReporting=True)

    report_data_pydantic = report_data_to_pydantic(res.report_data) if res.report_data is not None else None

    metrics = simulation_result_to_pydantic(res)
    if report_data_pydantic is not None:
        days_of_interest = detect_days_of_interest(
            report_data=report_data_pydantic,
            site_data=epoch_data,
            task_data=task_data,
            timestamps=pd.date_range(
                epoch_data.start_ts, epoch_data.end_ts - pd.Timedelta(minutes=30), freq=pd.Timedelta(minutes=30)
            ),
        )
    else:
        days_of_interest = []
    return FullResult(
        report_data=report_data_pydantic,
        metrics=metrics,
        task_data=task_data,
        site_data=epoch_data,
        days_of_interest=days_of_interest,
    )


def report_data_to_dict(report_data: ReportData) -> dict[str, list[float]]:
    """
    Convert the ReportData type returned as part of a SimulationResult into a more generic dict type.

    This is a convenience method to make the type we provide to the GUI generic (for now).

    Parameters
    ----------
    report_data
        The python bindings for the EPOCH ReportData struct

    Returns
    -------
        A dictionary representation of the report_data
    """

    def filter_report_data_fields(fields: list[str]) -> list[str]:
        """
        Crude method of finding the useful report data's fields.

        Filter out the methods that start with "__" and "_pybind11_conduit_v1_".

        Parameters
        ----------
        fields
            list of fields to filter.

        Returns
        -------
            list of filtered fields.
        """
        return [field for field in fields if field != "_pybind11_conduit_v1_" and not field.startswith("__")]

    report_dict = {}
    if report_data is not None:
        fields = filter_report_data_fields(fields=dir(report_data))

        # all fields are currently numpy arrays
        # we want the non-zero arrays
        for field in fields:
            vector = getattr(report_data, field)
            if vector.any():
                # convert the numpy array to a python list
                report_dict[field] = list(vector)
    return report_dict


def report_data_to_pydantic(report_data: ReportData) -> ReportData:
    """
    Convert the C++ / Pybind report_data type into a pydantic model (via a json dict).

    Parameters
    ----------
    report_data
        pybind / C++ output report data

    Returns
    -------
    ReportData
        pydantic type
    """
    return ReportData.model_validate(report_data_to_dict(report_data))
