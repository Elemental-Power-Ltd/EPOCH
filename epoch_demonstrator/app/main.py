import logging
import typing
from pathlib import Path

from epoch_simulator import Simulator, TaskData
from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.internal_models import (
    Building,
    Config,
    EnergyStorageSystem,
    GasHeater,
    Grid,
    HeatPump,
    PydanticTaskData,
    SolarPanel,
)
from app.models import (
    BatteryInfo,
    BuildingType,
    HeatInfo,
    InsulationInfo,
    Location,
    PanelInfo,
    SimulationRequest,
    SimulationResult,
)
from app.utils import report_data_to_dict

logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI()


DATA_PATHS = {
    (loc, bldg): Path(f"{loc}_{bldg}.json".lower())
    for loc in typing.get_args(Location)
    for bldg in typing.get_args(BuildingType)
}


def make_site_data(location: Location, building: BuildingType) -> str:
    """Make site data json for Epoch ingestion from pre-canned data."""
    return Path(f"./epoch_demonstrator/data/{DATA_PATHS[location, building]}").read_text()


def make_task_data(
    panels: list[PanelInfo],
    heat: HeatInfo,
    insulation: InsulationInfo,
    battery: BatteryInfo | None,
) -> str:
    """Make task data json for Epoch ingestion."""
    DIR_TO_YIELD_IDX = {"East": 0, "North": 1, "South": 2, "West": 3}

    INTERVENTIONS_LIST = [
        [],  # index 0
        ["loft"],  # index 1
        ["cladding"],  # index 2
        ["double_glazing"],  # index 3
        ["loft", "cladding"],  # index 4
        ["loft", "double_glazing"],  # index 5
        ["cladding", "double_glazing"],  # index 6
        ["loft", "cladding", "double_glazing"],  # index 7
    ]

    def insulation_to_index(insulation: InsulationInfo) -> int:
        interventions = []
        if insulation.loft:
            interventions.append("loft")
        if insulation.cladding:
            interventions.append("cladding")
        if insulation.double_glazing:
            interventions.append("double_glazing")

        return INTERVENTIONS_LIST.index(interventions)

    task_data = PydanticTaskData(
        building=Building(fabric_intervention_index=insulation_to_index(insulation)),
        grid=Grid(grid_import=999),
        energy_storage_system=EnergyStorageSystem(
            capacity=battery.capacity,
            charge_power=battery.power,
            discharge_power=battery.power,
        )
        if battery
        else None,
        gas_heater=GasHeater(maximum_output=heat.heat_power) if heat.heat_source == "Boiler" else None,
        heat_pump=HeatPump(heat_power=heat.heat_power) if heat.heat_source == "HeatPump" else None,
        solar_panels=[
            SolarPanel(
                yield_scalar=panel.solar_peak,
                yield_index=DIR_TO_YIELD_IDX[panel.direction],
            )
            for panel in panels
        ],
    )

    return task_data.model_dump_json(exclude_none=True)


def make_config_data(use_boiler_upgrade_scheme: bool = False) -> str:
    config = Config(
        capex_limit=999999999,
        use_boiler_upgrade_scheme=use_boiler_upgrade_scheme,
        general_grant_funding=0,
        npv_time_horizon=10,
        npv_discount_factor=0,
    )

    return config.model_dump_json(exclude_none=True)


@app.post("/simulate")
async def simulate(request: SimulationRequest) -> SimulationResult:
    site_data_json = make_site_data(request.location, request.building)
    task_data_json = make_task_data(request.panels, request.heat, request.insulation, request.battery)
    use_boiler_upgrade_scheme = bool(request.building == "Domestic")
    config_json = make_config_data(use_boiler_upgrade_scheme)

    task_data = TaskData.from_json(task_data_json)
    simulator = Simulator.from_json(site_data_json, config_json)
    result = simulator.simulate_scenario(task_data, request.full_reporting)

    return SimulationResult(
        comparison=result.comparison,  # type: ignore
        metrics=result.metrics,  # type: ignore
        baseline_metrics=result.baseline_metrics,  # type: ignore
        scenario_capex_breakdown=result.scenario_capex_breakdown,  # type: ignore
        report_data=report_data_to_dict(result.report_data) if request.full_reporting else None,
    )


BASE_DIR = Path(__file__).resolve().parent
GUI_FILE = BASE_DIR / "simple_gui.html"


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(GUI_FILE)
