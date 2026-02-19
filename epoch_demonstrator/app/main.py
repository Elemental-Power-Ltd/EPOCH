import json
import logging
import os
import typing
from pathlib import Path

from epoch_simulator import Simulator, TaskData
from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.internal_models import (
    BatteryMode,
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
    DemoResult,
    GridInfo,
    HeatInfo,
    InsulationInfo,
    Location,
    PanelInfo,
    SimulationRequest,
)
from app.utils import report_data_to_pydantic, simulation_result_to_pydantic

logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

fastapi_kwargs: dict[str, typing.Any] = {}

if os.environ.get("PRODUCTION", False):
    fastapi_kwargs.update({
        "docs_urls": None,
        "redoc_url": None,
        "openapi_url": None,
    })

app = FastAPI(**fastapi_kwargs)

# we need relative paths from the project root for both the data files and the gui
ROOT_DIR = Path(__file__).resolve().parent.parent


DATA_PATHS = {
    (loc, bldg): Path(f"{loc}_{bldg}.json".lower())
    for loc in typing.get_args(Location)
    for bldg in typing.get_args(BuildingType)
}


def make_site_data(location: Location, building: BuildingType) -> str:
    """Make site data json for Epoch ingestion from pre-canned data."""
    return (ROOT_DIR / "data" / DATA_PATHS[location, building]).read_text()


def make_task_data(
    panels: list[PanelInfo],
    heat: HeatInfo,
    insulation: InsulationInfo,
    battery: BatteryInfo | None,
    grid: GridInfo,
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

    TARIFF_MAP = {"Fixed": 0, "Agile": 1, "Peak": 2, "Overnight": 3}

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
        grid=Grid(grid_import=999, tariff_index=TARIFF_MAP[grid.import_tariff], export_tariff=grid.export_tariff),
        energy_storage_system=EnergyStorageSystem(
            capacity=battery.capacity,
            charge_power=battery.power,
            discharge_power=battery.power,
            battery_mode=BatteryMode.CONSUME_PLUS,
        )
        if battery
        else None,
        gas_heater=GasHeater(maximum_output=heat.heat_power, incumbent=True) if heat.heat_source == "Boiler" else None,
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
async def simulate(request: SimulationRequest) -> DemoResult:
    """
    Run A simulation.

    Transform the simplified request into an EPOCH compatible TaskData,SiteData pair and simulate with them.

    Parameters
    ----------
    request
        A simplified set of options to modify a site

    Returns
    -------
        The resulting simulation, in our GUI's format
    """
    site_data_json = make_site_data(request.location, request.building)
    sdj = json.loads(site_data_json)

    # if the request is for a boiler, use the baseline boiler's values
    baseline_boiler_output = sdj["baseline"]["gas_heater"]["maximum_output"]
    if request.heat.heat_source == "Boiler":
        # horrible mutation!
        request.heat.heat_power = baseline_boiler_output

    task_data_json = make_task_data(request.panels, request.heat, request.insulation, request.battery, request.grid)

    # only apply the boiler upgrade scheme for domestic buildings
    use_boiler_upgrade_scheme = request.building == "Domestic"
    config_json = make_config_data(use_boiler_upgrade_scheme)

    task_data = TaskData.from_json(task_data_json)
    simulator = Simulator.from_json(site_data_json, config_json)
    result = simulator.simulate_scenario(task_data, request.full_reporting)

    report_data_pydantic = report_data_to_pydantic(result.report_data) if result.report_data is not None else None
    metrics = simulation_result_to_pydantic(result)
    days_of_interest: list[typing.Any] = []

    return DemoResult(
        metrics=metrics,
        task_data=json.loads(task_data_json),
        site_data=sdj if request.full_reporting else None,
        report_data=report_data_pydantic,
        days_of_interest=days_of_interest,
    )


GUI_FILE = ROOT_DIR / "app" / "simple_gui.html"


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(GUI_FILE)
