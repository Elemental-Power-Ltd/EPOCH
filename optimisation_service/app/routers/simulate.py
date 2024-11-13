"""
Endpoints to handle running individual simulations of EPOCH
"""

import logging
import tempfile

from fastapi import APIRouter, HTTPException

from app.internal.datamanager import DataManagerDep
from app.internal.task_data_wrapper import PyTaskData, Simulator
from app.models.simulate import FullResult, ReproduceSimulationRequest
from app.models.site_data import LocalMetaData

router = APIRouter()
logger = logging.getLogger("default")


@router.post("/reproduce-simulation")
async def reproduce_simulation(request: ReproduceSimulationRequest, data_manager: DataManagerDep) -> FullResult:
    """
    Re-run a simulation of EPOCH to obtain the verbose reporting

    This method will obtain the configuration settings used in the original Optimisation Run to reproduce the result.
    If the original result was obtained using local data, the result cannot be reproduced and an error will be returned.


    Parameters
    ----------
    request
    data_manager

    Returns
    -------

    """

    logger.info(f"Reproducing simulation {request.result_id}")

    repro_config = await data_manager.get_result_configuration(request.result_id)

    if isinstance(repro_config.site_data, LocalMetaData):
        raise HTTPException(400, detail="Cannot reproduce a result from local data")

    # Check that the dataset_ids have been saved to the database for this result
    if not repro_config.site_data.dataset_ids:
        raise HTTPException(400, detail="Cannot reproduce a result without known dataset IDs")

    dataset_entries = await data_manager.fetch_specific_datasets(repro_config.site_data)

    with tempfile.TemporaryDirectory(prefix="simulate_repro_") as repro_dir:
        data_manager.write_input_data_to_files(dataset_entries, repro_dir)

        sim = Simulator(inputDir=repro_dir)
        pytd = PyTaskData(**repro_config.task_data.model_dump())

        res = sim.simulate_scenario(pytd, fullReporting=True)

        report_dict = report_data_to_dict(res.report_data)

        objectives = {
            "CAPEX": res.capex,
            "Carbon Balance": res.carbon_balance,
            "Cost Balance": res.cost_balance,
            "Payback Horizon": res.payback_horizon,
            "Annualised Cost": res.annualised_cost,
        }

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
