"""
Endpoints to handle running individual simulations of EPOCH
"""

import json
import logging
import tempfile

from fastapi import APIRouter, HTTPException

from app.internal.datamanager import DataManagerDep
from app.internal.epoch_utils import Simulator, TaskData, convert_sim_result
from app.models.simulate import FullResult, ReproduceSimulationRequest, RunSimulationRequest
from app.models.site_data import DatasetTypeEnum, LocalMetaData

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

    await data_manager.hydrate_site_with_latest_dataset_ids(request.site_data)

    dataset_entries = await data_manager.fetch_specific_datasets(request.site_data)

    return do_simulation(data_manager, dataset_entries, request.task_data)


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

    repro_config = await data_manager.get_result_configuration(request.portfolio_id)

    site_data = repro_config.site_data[request.site_id]

    necessary_datasets = [
        DatasetTypeEnum.GasMeterData,
        DatasetTypeEnum.RenewablesGeneration,
        DatasetTypeEnum.HeatingLoad,
        DatasetTypeEnum.CarbonIntensity,
        DatasetTypeEnum.ASHPData,
        DatasetTypeEnum.ImportTariff,
    ]
    # Check that the dataset_ids have been saved to the database for this result
    for key in necessary_datasets:
        if site_data.__getattribute__(key) is None:
            raise HTTPException(400, detail=f"Cannot reproduce a result without known {key} dataset ID")
    if (
        site_data.__getattribute__(DatasetTypeEnum.ElectricityMeterData) is None
        and site_data.__getattribute__(DatasetTypeEnum.ElectricityMeterDataSynthesised) is None
    ):
        raise HTTPException(
            400,
            detail="Cannot reproduce a result without known ElectricityMeterData or ElectricityMeterDataSynthesised dataset ID",
        )

    dataset_entries = await data_manager.fetch_specific_datasets(site_data)

    return do_simulation(data_manager, dataset_entries, repro_config.task_data[request.site_id])


def do_simulation(data_manager, dataset_entries, task_data):
    """
    Internal function to run a simulation for a given set of site data and taskData
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

    """
    with tempfile.TemporaryDirectory(prefix="simulate_repro_") as repro_dir:
        data_manager.write_input_data_to_files(dataset_entries, repro_dir)

        sim = Simulator(inputDir=repro_dir)
        pytd = TaskData.from_json(json.dumps(task_data))

        res = sim.simulate_scenario(pytd, fullReporting=True)

        report_dict = report_data_to_dict(res.report_data)
        objectives = convert_sim_result(res)

        return FullResult(report_data=report_dict, objectives=objectives)


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
