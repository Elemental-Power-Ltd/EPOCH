from app.internal.heuristics.asset_heuristics import (
    EnergyStorageSystemHeuristic,
    HeatPumpHeuristic,
    SolarHeuristic,
    get_all_estimates,
)
from app.models.site_data import EpochSiteData


class TestHeatPump:
    def test_heat_power(self, default_epoch_data: EpochSiteData) -> None:
        N = len(default_epoch_data.building_eload)
        timestamps = [
            default_epoch_data.start_ts + (default_epoch_data.end_ts - default_epoch_data.start_ts) * i / (N - 1)
            for i in range(N)
        ]
        HeatPumpHeuristic.heat_power(
            building_hload=default_epoch_data.building_hload,
            ashp_input_table=default_epoch_data.ashp_input_table,
            ashp_output_table=default_epoch_data.ashp_output_table,
            air_temperature=default_epoch_data.air_temperature,
            timestamps=timestamps,
            ashp_mode=2.0,
        )


class TestRenewables:
    def test_yield_scalars(self, default_epoch_data: EpochSiteData) -> None:
        SolarHeuristic.yield_scalar(
            solar_yield=default_epoch_data.solar_yields[0],
            building_eload=default_epoch_data.building_eload,
        )


class TestEnergyStorageSystem:
    def test_capacity(self, default_epoch_data: EpochSiteData) -> None:
        N = len(default_epoch_data.building_eload)
        timestamps = [
            default_epoch_data.start_ts + (default_epoch_data.end_ts - default_epoch_data.start_ts) * i / (N - 1)
            for i in range(N)
        ]
        EnergyStorageSystemHeuristic.capacity(building_eload=default_epoch_data.building_eload, timestamps=timestamps)

    def test_ccharge_power(self, default_epoch_data: EpochSiteData) -> None:
        N = len(default_epoch_data.building_eload)
        timestamps = [
            default_epoch_data.start_ts + (default_epoch_data.end_ts - default_epoch_data.start_ts) * i / (N - 1)
            for i in range(N)
        ]
        solar_scale = SolarHeuristic.yield_scalar(
            solar_yield=default_epoch_data.solar_yields[0],
            building_eload=default_epoch_data.building_eload,
        )
        EnergyStorageSystemHeuristic.charge_power(
            solar_yield=default_epoch_data.solar_yields[0], timestamps=timestamps, solar_scale=solar_scale
        )

    def test_discharge_power(self, default_epoch_data: EpochSiteData) -> None:
        N = len(default_epoch_data.building_eload)
        timestamps = [
            default_epoch_data.start_ts + (default_epoch_data.end_ts - default_epoch_data.start_ts) * i / (N - 1)
            for i in range(N)
        ]
        EnergyStorageSystemHeuristic.discharge_power(building_eload=default_epoch_data.building_eload, timestamps=timestamps)


class TestGetAllEstimates:
    def test_good_inputs(self, default_epoch_data: EpochSiteData) -> None:
        estimates = get_all_estimates(default_epoch_data)
        assert isinstance(estimates["heat_pump"]["heat_power"], float)
        assert isinstance(estimates["energy_storage_system"]["capacity"], float)
        assert isinstance(estimates["energy_storage_system"]["charge_power"], float)
        assert isinstance(estimates["energy_storage_system"]["discharge_power"], float)
        assert isinstance(estimates["solar_panels"]["yield_scalar"], float)
