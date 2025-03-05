"""
Endpoints to handle running individual simulations of EPOCH
"""

import json
import logging

from epoch_simulator import Simulator
from fastapi import APIRouter, HTTPException

from app.internal.datamanager import DataManagerDep, EpochSiteData
from app.internal.epoch_utils import TaskData, convert_sim_result
from app.models.simulate import (
    FullResult,
    GetSavedSiteDataRequest,
    ReproduceSimulationRequest,
    RunSimulationRequest,
    TaskDataType,
)
from app.models.site_data import LocalMetaData, RemoteMetaData

router = APIRouter()
logger = logging.getLogger("default")


@router.post("/run-simulation")
async def run_simulation(request: RunSimulationRequest, data_manager: DataManagerDep) -> FullResult:
    """
    Run a simulation of a single site in EPOCH with full reporting enabled


    Parameters
    ----------
    request
    data_manager

    Returns
    -------

    """
    logger.info("Running single simulation")

    if isinstance(request.site_data, LocalMetaData):
        raise HTTPException(400, detail="Simulation from local data is not supported")

    epoch_data = await data_manager.get_latest_site_data(request.site_data)

    return do_simulation(epoch_data, request.task_data)


@router.post("/reproduce-simulation")
async def reproduce_simulation(request: ReproduceSimulationRequest, data_manager: DataManagerDep) -> FullResult:
    """
    Re-run a simulation of EPOCH with full reporting enabled

    This method will obtain the configuration settings used in the original Optimisation Run to reproduce the result.
    If the original result was obtained using local data, the result cannot be reproduced and an error will be returned.


    Parameters
    ----------
    request
    data_manager

    Returns
    -------

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
    data_manager

    Returns
    -------

    """
    return await data_manager.get_latest_site_data(site_data)


@router.post("/get-saved-site-data")
async def get_saved_site_data(request: GetSavedSiteDataRequest, data_manager: DataManagerDep) -> EpochSiteData:
    """
    Fetch the exact SiteData that was used to produce a result in the database.

    Parameters
    ----------
    request
    data_manager

    Returns
    -------

    """
    saved_input = await data_manager.get_saved_epoch_input(request.portfolio_id, request.site_id)
    return saved_input.site_data


def do_simulation(epoch_data: EpochSiteData, task_data: TaskDataType):
    """
    Internal function to run a simulation for a given set of site data and taskData
    Parameters
    ----------
    data_manager
        A data manager to handle IO operations
    dataset_entries
        The full timeseries for the site```
    task_data
        The EPOCH TaskData represented in JSON

    Returns
    -------

    """
    sim = Simulator.from_json(epoch_data.model_dump_json())
    pytd = TaskData.from_json(json.dumps(task_data))

    res = sim.simulate_scenario(pytd, fullReporting=True)

    report_dict = report_data_to_dict(res.report_data)
    objectives = convert_sim_result(res)

    return FullResult(report_data=report_dict, objectives=objectives, task_data=task_data, site_data=epoch_data)


def report_data_to_dict(report_data) -> dict[str, list[float]]:
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
            if len(vector):
                # convert the numpy array to a python list
                report_dict[field] = list(vector)
    return report_dict
