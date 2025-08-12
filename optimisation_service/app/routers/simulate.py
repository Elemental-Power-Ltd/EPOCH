"""Endpoints to handle running individual simulations of EPOCH."""

import logging

from epoch_simulator import Simulator, TaskData
from fastapi import APIRouter, HTTPException

from app.internal.datamanager import DataManagerDep
from app.internal.epoch_utils import convert_sim_result
from app.models.epoch_types import ReportData
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic
from app.models.simulate import (
    FullResult,
    GetSavedSiteDataRequest,
    ReproduceSimulationRequest,
    RunSimulationRequest,
)
from app.models.site_data import EpochSiteData, LocalMetaData, RemoteMetaData

router = APIRouter()
logger = logging.getLogger("default")


@router.post("/run-simulation")
async def run_simulation(request: RunSimulationRequest, data_manager: DataManagerDep) -> FullResult:
    """
    Run a simulation of a single site in EPOCH with full reporting enabled.

    Parameters
    ----------
    request
        Details about the simulation to reproduce
    data_manager
        Data manager with a database connection

    Returns
    -------
        Full result from the simulation to run
    """
    logger.info("Running single simulation")

    if isinstance(request.site_data, LocalMetaData):
        raise HTTPException(400, detail="Simulation from local data is not supported")

    epoch_data = await data_manager.get_latest_site_data(request.site_data)

    return do_simulation(epoch_data, request.task_data)


@router.post("/reproduce-simulation")
async def reproduce_simulation(request: ReproduceSimulationRequest, data_manager: DataManagerDep) -> FullResult:
    """
    Re-run a simulation of EPOCH with full reporting enabled.

    This method will obtain the configuration settings used in the original Optimisation Run to reproduce the result.
    If the original result was obtained using local data, the result cannot be reproduced and an error will be returned.


    Parameters
    ----------
    request
        Details about the simulation to reproduce
    data_manager
        Data manager with a database connection

    Returns
    -------
        Full result from the simulation
    """
    logger.info(f"Reproducing simulation for {request.site_id} from portfolio {request.portfolio_id}")
    saved_input = await data_manager.get_saved_epoch_input(request.portfolio_id, request.site_id)

    return do_simulation(saved_input.site_data, saved_input.task_data)


@router.post("/get-latest-site-data")
async def get_latest_site_data(site_data: RemoteMetaData, data_manager: DataManagerDep) -> EpochSiteData:
    """
    Serve an EPOCH compatible SiteData using the most recently generated dataset of each type.

    Parameters
    ----------
    site_data
        Data to request from the database
    data_manager
        Data handler with database connection

    Returns
    -------
        Site data in EPOCH format
    """
    return await data_manager.get_latest_site_data(site_data)


@router.post("/get-saved-site-data")
async def get_saved_site_data(request: GetSavedSiteDataRequest, data_manager: DataManagerDep) -> EpochSiteData:
    """
    Fetch the exact SiteData that was used to produce a result in the database.

    Parameters
    ----------
    request
        Request to send to the database
    data_manager
        Data manager with database connection

    Returns
    -------
        Parsed data in EPOCH format
    """
    saved_input = await data_manager.get_saved_epoch_input(request.portfolio_id, request.site_id)
    return saved_input.site_data


def do_simulation(epoch_data: EpochSiteData, task_data: TaskDataPydantic) -> FullResult:
    """
    Run a simulation for a given set of site data and taskData.

    This is an internal wrapper that shouldn't be exposed.

    Parameters
    ----------
    data_manager
        A data manager to handle IO operations
    dataset_entries
        The full timeseries for the site
    task_data
        The EPOCH TaskData represented in JSON

    Returns
    -------
        Full result from the simulated scenario
    """
    assert task_data.config is not None
    sim = Simulator.from_json(epoch_data.model_dump_json(), task_data.config.model_dump_json())
    pytd = TaskData.from_json(task_data.model_dump_json())

    res = sim.simulate_scenario(pytd, fullReporting=True)

    if res.report_data is not None:
        report_data_pydantic = report_data_to_pydantic(res.report_data)
    else:
        report_data_pydantic = None

    objectives = convert_sim_result(res)

    return FullResult(report_data=report_data_pydantic, metrics=objectives, task_data=task_data, site_data=epoch_data)


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
    report_dict = {}
    if report_data is not None:
        # Crude method of finding the fields
        # Look for all the methods in the report data that don't start with "__"
        fields = [field for field in dir(report_data) if not field.startswith("__")]

        # all fields are currently numpy arrays
        # we want the non-zero arrays
        for field in fields:
            vector = getattr(report_data, field)
            if vector:
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
