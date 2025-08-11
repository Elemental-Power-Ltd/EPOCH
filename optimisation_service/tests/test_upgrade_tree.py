import app.internal.upgrade_tree.generate_results as gr
from app.models.epoch_types.task_data_type import Building as BuildingTD
from app.models.epoch_types.task_data_type import GasHeater as GasHeaterTD
from app.models.epoch_types.task_data_type import HeatPump as HeatPumpTD
from app.models.epoch_types.task_data_type import SolarPanel as SolarPanelTD
from app.models.epoch_types.task_data_type import TaskData as TaskDataPydantic

class TestCheckChanges:
    def test_gas_to_ashp(self) -> None:
        """Test that we correctly treat replacing a gas heater with an heat pump."""
        start = TaskDataPydantic(
            building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0),
            gas_heater=GasHeaterTD(maximum_output=40.0),
        )

        end = TaskDataPydantic(
            building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0), heat_pump=HeatPumpTD(heat_power=100.0)
        )
        diff = gr.analyse_differences(start, end)
        assert "heat_pump" in diff
        assert "gas_heater" not in diff

    def test_gas_to_ashp_backup(self) -> None:
        """Test that we correctly treat having a small boiler alongside a heat pump.."""
        start = TaskDataPydantic(
            building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0),
            gas_heater=GasHeaterTD(maximum_output=40.0),
        )

        end = TaskDataPydantic(
            building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0),
            heat_pump=HeatPumpTD(heat_power=100.0),
            gas_heater=GasHeaterTD(maximum_output=10.0),
        )
        diff = gr.analyse_differences(start, end)
        assert "heat_pump" in diff
        assert "gas_heater" in diff
        assert isinstance(diff["gas_heater"], GasHeaterTD)
        assert diff["gas_heater"].maximum_output == 10.0

    def test_replace_solar(self) -> None:
        """Test that we replace all the solar panels at once."""
        start = TaskDataPydantic(
            building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0),
            solar_panels=[SolarPanelTD(yield_scalar=10, yield_index=0)],
        )

        end = TaskDataPydantic(
            building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0),
            solar_panels=[SolarPanelTD(yield_scalar=10, yield_index=0), SolarPanelTD(yield_scalar=10, yield_index=0)],
        )
        diff = gr.analyse_differences(start, end)
        assert "solar_panels" in diff
        assert isinstance(diff["solar_panels"], list)
        assert len(diff["solar_panels"]) == 2

    def test_replace_fabric(self) -> None:
        """Test that we replace the fabric correctly."""
        start = TaskDataPydantic(building=BuildingTD(fabric_intervention_index=0, incumbent=True, age=50.0))

        end = TaskDataPydantic(building=BuildingTD(fabric_intervention_index=1, incumbent=True, age=50.0))
        diff = gr.analyse_differences(start, end)
        assert len(diff) == 1
        assert "building" in diff
